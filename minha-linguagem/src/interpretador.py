"""Interpretador da LocaScript: renderiza uma mensagem com valores de variáveis.

Recebe a AST **já validada** (ver semantica.py) e devolve o texto final como uma
lista de trechos com estilo, mais os avisos de execução. As regras estão na
seção 9 de docs/especificacao.md.

    from semantica import analisar
    from interpretador import renderizar

    arvore = analisar("Você tem { $n -> [one] # moeda [*] # moedas }.")
    resultado = renderizar(arvore, {"n": 5}, idioma="pt")
    resultado.texto            # "Você tem 5 moedas."
    resultado.avisos           # problemas de execução (valor faltando etc.)

Problemas de execução (variável sem valor, valor de tipo errado) não levantam
exceção: viram avisos e a renderização continua.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Optional, Union

from babel import Locale, UnknownLocaleError
from babel.numbers import format_currency, format_decimal, get_currency_precision

from ast_nos import (
    Caso, Interpolacao, Mensagem, No, NumeroPlural, Selecao, TagUI, TextoLiteral,
    TipoTag,
)
from semantica import CATEGORIAS_CLDR, FORMATADORES, Tipo

LIMITE_NUMERO = Decimal("1e15")   # com no máximo 10 casas, cabe na precisão do Decimal
_AUSENTE = object()


class ErroDeIdioma(ValueError):
    """O código de idioma não é reconhecido (ex.: 'xx_YY')."""


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

Estilo = tuple[tuple[str, Optional[str]], ...]  # tags ativas: (("color", "#FF0000"), ...)


@dataclass(frozen=True)
class Trecho:
    texto: str
    estilo: Estilo = ()
    ausente: bool = False      # True: marcador de valor que não foi informado


@dataclass(frozen=True)
class Aviso:
    linha: int
    coluna: int
    mensagem: str


@dataclass
class Resultado:
    trechos: list[Trecho] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)

    @property
    def texto(self) -> str:
        return "".join(t.texto for t in self.trechos)

    def para_dict(self) -> dict:
        return {
            "texto": self.texto,
            "trechos": [
                {
                    "texto": t.texto,
                    "estilo": [{"tag": n, "valor": v} for n, v in t.estilo],
                    "ausente": t.ausente,
                }
                for t in self.trechos
            ],
            "avisos": [
                {"linha": a.linha, "coluna": a.coluna, "mensagem": a.mensagem}
                for a in self.avisos
            ],
        }


# ---------------------------------------------------------------------------
# Números e formatação
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Numero:
    valor: Decimal
    casas: Optional[int] = None   # casas fixas, definidas por arredondar(n)


def validar_idioma(idioma: str) -> Locale:
    """Converte 'pt', 'pt-BR', 'en_US'... em Locale, ou levanta ErroDeIdioma."""
    if not isinstance(idioma, str) or not idioma.strip():
        raise ErroDeIdioma("idioma vazio")
    try:
        return Locale.parse(idioma.strip().replace("-", "_"))
    except (UnknownLocaleError, ValueError, TypeError) as erro:
        raise ErroDeIdioma(f"idioma desconhecido: '{idioma}'") from erro


def _para_decimal(valor: Any) -> Optional[Decimal]:
    """Converte int/float/str numérica em Decimal finito e dentro do limite."""
    if isinstance(valor, bool):
        return None
    try:
        if isinstance(valor, (int, float)):
            d = Decimal(str(valor))
        elif isinstance(valor, str):
            d = Decimal(valor.strip())
        else:
            return None
    except InvalidOperation:
        return None
    if not d.is_finite() or abs(d) > LIMITE_NUMERO:
        return None
    return d


def _arredondar(valor: Decimal, casas: int) -> Decimal:
    """Arredonda metade para cima (2,5 -> 3), como se aprende na escola."""
    return valor.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)


def _formatar_numero(n: _Numero, locale: Locale) -> str:
    if n.casas is None:
        return format_decimal(n.valor, locale=locale)           # até 3 casas
    padrao = "#,##0" + ("." + "0" * n.casas if n.casas else "")
    return format_decimal(n.valor, format=padrao, locale=locale)


def _formatar_moeda(n: _Numero, codigo: str, casas: Optional[int], locale: Locale) -> str:
    digitos = casas if casas is not None else get_currency_precision(codigo)
    valor = _arredondar(n.valor, digitos)
    padrao = locale.currency_formats["standard"].pattern
    if re.search(r"\.0+", padrao):
        decimais = "." + "0" * digitos if digitos else ""
        padrao = re.sub(r"\.0+", decimais, padrao)
        return format_currency(valor, codigo, format=padrao, locale=locale,
                               currency_digits=False)
    return format_currency(valor, codigo, locale=locale)


# ---------------------------------------------------------------------------
# Renderizador
# ---------------------------------------------------------------------------

class _Renderizador:
    def __init__(self, valores: dict[str, Any], locale: Locale):
        self._valores = valores
        self._locale = locale
        self.trechos: list[Trecho] = []
        self.avisos: list[Aviso] = []

    # --- apoio ---------------------------------------------------------------
    def _aviso(self, no: No, mensagem: str):
        self.avisos.append(Aviso(no.linha, no.coluna, mensagem))

    def _emitir(self, texto: str, estilo: list, ausente: bool = False):
        if not texto:
            return
        atual = tuple(estilo)
        if self.trechos and not ausente:
            ultimo = self.trechos[-1]
            if not ultimo.ausente and ultimo.estilo == atual:
                self.trechos[-1] = Trecho(ultimo.texto + texto, atual)
                return
        self.trechos.append(Trecho(texto, atual, ausente))

    def _valor(self, nome: str) -> Any:
        valor = self._valores.get(nome, _AUSENTE)
        return _AUSENTE if valor is None else valor

    def _numero(self, valor: Any) -> Optional[_Numero]:
        if isinstance(valor, _Numero):
            return valor
        d = _para_decimal(valor)
        return None if d is None else _Numero(d)

    # --- itens ---------------------------------------------------------------
    def itens(self, itens: list[No], estilo: list, plural: Optional[_Numero]):
        estilo = list(estilo)   # tags abertas aqui não vazam para fora do trecho
        for item in itens:
            if isinstance(item, TextoLiteral):
                self._emitir(item.valor, estilo)
            elif isinstance(item, NumeroPlural):
                self._numero_plural(item, estilo, plural)
            elif isinstance(item, TagUI):
                if item.tipo is TipoTag.ABERTURA:
                    estilo.append((item.nome, item.valor))
                elif estilo:
                    estilo.pop()
            elif isinstance(item, Interpolacao):
                self._interpolar(item, estilo)
            elif isinstance(item, Selecao):
                self._selecionar(item, estilo)

    def _numero_plural(self, no: NumeroPlural, estilo: list, plural: Optional[_Numero]):
        if plural is None:
            self._aviso(no, "'#' sem valor numérico para mostrar")
            self._emitir("#", estilo, ausente=True)
        else:
            self._emitir(_formatar_numero(plural, self._locale), estilo)

    # --- interpolação e formatadores ------------------------------------------
    def _interpolar(self, no: Interpolacao, estilo: list):
        nome = no.variavel.nome
        marcador = "{$" + nome + "}"
        bruto = self._valor(nome)
        if bruto is _AUSENTE:
            self._aviso(no, f"valor de ${nome} não informado")
            self._emitir(marcador, estilo, ausente=True)
            return

        atual: Union[_Numero, str, None]
        if isinstance(bruto, bool):
            atual = None
        elif isinstance(bruto, (int, float)):
            atual = self._numero(bruto)
        else:
            atual = bruto if isinstance(bruto, str) else None
        if atual is None:
            self._aviso(no, f"valor de ${nome} tem tipo inválido")
            self._emitir(marcador, estilo, ausente=True)
            return

        for f in no.formatadores:
            atual = self._aplicar(f, atual, nome)
            if atual is None:
                self._emitir(marcador, estilo, ausente=True)
                return

        texto = atual if isinstance(atual, str) else _formatar_numero(atual, self._locale)
        self._emitir(texto, estilo)

    def _aplicar(self, f, atual: Union[_Numero, str], nome: str):
        """Aplica um formatador; devolve _Numero, str, ou None se o valor não serve."""
        spec = FORMATADORES.get(f.nome)
        if spec is None:   # a análise semântica já rejeita; defesa
            self._aviso(f, f"formatador desconhecido '{f.nome}'")
            return None

        if spec.entrada is Tipo.NUMERO:
            n = self._numero(atual)
            if n is None:
                self._aviso(f, f"${nome} não é numérica para '{f.nome}': '{atual}'")
                return None
            if f.nome == "moeda":
                casas = int(f.argumentos[1]) if len(f.argumentos) > 1 else None
                return _formatar_moeda(n, f.argumentos[0], casas, self._locale)
            casas = int(f.argumentos[0])   # arredondar
            return _Numero(_arredondar(n.valor, casas), casas)

        texto = atual if isinstance(atual, str) else _formatar_numero(atual, self._locale)
        return texto.upper() if f.nome == "maiusculo" else texto.lower()

    # --- seleção -------------------------------------------------------------
    def _selecionar(self, no: Selecao, estilo: list):
        nome = no.variavel.nome
        chaves = [c.chave for c in no.casos if not c.eh_padrao]
        padrao = next((c for c in no.casos if c.eh_padrao), None)
        bruto = self._valor(nome)

        if any(k in CATEGORIAS_CLDR for k in chaves) or not chaves:
            # Pluralização (ou só `[*]`, que ainda pode usar '#').
            n = None if bruto is _AUSENTE else self._numero(bruto)
            if n is None and chaves:
                motivo = "não informado" if bruto is _AUSENTE else f"não é numérico: '{bruto}'"
                self._aviso(no, f"valor de ${nome} {motivo}; usando o ramo padrão [*]")
            ramo = self._ramo_plural(no, n) if n is not None else padrao
            plural = n
        else:
            # Gênero/papel: compara o texto com as chaves.
            plural = None
            if bruto is _AUSENTE:
                self._aviso(no, f"valor de ${nome} não informado; usando o ramo padrão [*]")
                ramo = padrao
            elif not isinstance(bruto, str):
                self._aviso(no, f"valor de ${nome} deveria ser texto; usando o ramo padrão [*]")
                ramo = padrao
            else:
                ramo = next((c for c in no.casos if not c.eh_padrao and c.chave == bruto),
                            padrao)

        if ramo is None:   # a análise semântica exige [*]; defesa
            self._aviso(no, f"nenhum ramo escolhido para ${nome}")
            return
        self.itens(ramo.itens, estilo, plural)

    def _ramo_plural(self, no: Selecao, n: _Numero) -> Optional[Caso]:
        por_chave = {c.chave: c for c in no.casos if not c.eh_padrao}
        padrao = next((c for c in no.casos if c.eh_padrao), None)
        # `[zero]` casa quando o valor é exatamente 0, em qualquer idioma
        # (o CLDR só tem a categoria `zero` em alguns, como o árabe).
        if n.valor == 0 and "zero" in por_chave:
            return por_chave["zero"]
        categoria = self._locale.plural_form(n.valor)
        return por_chave.get(categoria, padrao)


def renderizar(arvore: Mensagem, valores: dict[str, Any], idioma: str = "pt") -> Resultado:
    """Renderiza a AST validada com `valores` (variável -> int, float ou str).

    Levanta ErroDeIdioma se `idioma` não for reconhecido. Problemas com os valores
    viram `Resultado.avisos`.
    """
    locale = validar_idioma(idioma)
    r = _Renderizador(valores, locale)
    r.itens(arvore.itens, [], None)
    return Resultado(r.trechos, r.avisos)
