"""Análise semântica da LocaScript (E4).

Recebe a AST produzida por `api_parser.parse` e verifica as regras que a
gramática não consegue expressar. As regras estão descritas na seção 8 de
docs/especificacao.md; os números (R1, R2...) dos comentários abaixo são os
mesmos daquela seção.

Como biblioteca:
    from semantica import analisar
    arvore = analisar(texto)   # levanta ErroSintatico ou ErroSemantico

Pela linha de comando (a partir da raiz do projeto):
    python src/semantica.py exemplos/dano.loca
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

# Torna a pasta gerado/ importável (mesma convenção de lexico.py/sintatico.py).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gerado"))

from api_parser import Diagnostico, ErroSintatico, parse  # noqa: E402
from ast_nos import (  # noqa: E402
    Caso, Interpolacao, Mensagem, No, NumeroPlural, Selecao, TagUI, TipoTag,
    Visitante,
)

# ---------------------------------------------------------------------------
# Tabelas de regras
# ---------------------------------------------------------------------------

CATEGORIAS_CLDR = frozenset({"zero", "one", "two", "few", "many", "other"})

# R9: `color` é a única tag com valor verificado: '#' + 6 dígitos hexadecimais.
COR_HEX = re.compile(r"#[0-9A-Fa-f]{6}")


class Tipo(Enum):
    NUMERO = "número"
    TEXTO = "texto"


@dataclass(frozen=True)
class Argumento:
    nome: str
    descricao: str                      # aparece na mensagem de erro
    valido: Callable[[str], bool]


@dataclass(frozen=True)
class EspecFormatador:
    entrada: Tipo
    saida: Tipo
    argumentos: tuple[Argumento, ...] = ()
    obrigatorios: int = 0               # os N primeiros argumentos são obrigatórios


def _eh_inteiro(texto: str) -> bool:
    return re.fullmatch(r"[0-9]+", texto) is not None


def _eh_codigo_moeda(texto: str) -> bool:
    return re.fullmatch(r"[A-Z]{3}", texto) is not None


_CASAS = Argumento("casas", "um inteiro maior ou igual a 0", _eh_inteiro)

# R15: tabela fixa de formatadores.
FORMATADORES: dict[str, EspecFormatador] = {
    "moeda": EspecFormatador(
        Tipo.NUMERO, Tipo.TEXTO,
        (Argumento("código", "um código de 3 letras maiúsculas (ex.: BRL)",
                   _eh_codigo_moeda), _CASAS),
        obrigatorios=1,
    ),
    "arredondar": EspecFormatador(Tipo.NUMERO, Tipo.NUMERO, (_CASAS,), obrigatorios=1),
    "maiusculo": EspecFormatador(Tipo.TEXTO, Tipo.TEXTO),
    "minusculo": EspecFormatador(Tipo.TEXTO, Tipo.TEXTO),
}


# ---------------------------------------------------------------------------
# Erro e verificador
# ---------------------------------------------------------------------------

class ErroSemantico(Exception):
    def __init__(self, diagnosticos: list[Diagnostico]):
        self.diagnosticos = diagnosticos
        super().__init__("\n".join(str(d) for d in diagnosticos))


@dataclass(frozen=True)
class _Uso:
    """Primeiro uso de uma variável com tipo definido (para R14)."""
    tipo: Tipo
    linha: int
    motivo: str


def _classificar(sel: Selecao) -> tuple[list[str], list[str]]:
    """Separa as chaves (exceto `*`) em categorias CLDR e chaves de gênero/papel."""
    chaves = [c.chave for c in sel.casos if not c.eh_padrao]
    return (
        [k for k in chaves if k in CATEGORIAS_CLDR],
        [k for k in chaves if k not in CATEGORIAS_CLDR],
    )


def _tipo_da_selecao(sel: Selecao) -> Optional[Tipo]:
    cldr, genero = _classificar(sel)
    if cldr and not genero:
        return Tipo.NUMERO
    if genero and not cldr:
        return Tipo.TEXTO
    return None  # só `[*]` (neutra) ou mistura (R5, já reportada)


class Verificador(Visitante):
    def __init__(self):
        self.diagnosticos: list[Diagnostico] = []
        self._selecoes: list[Selecao] = []     # pilha; a mais interna no topo
        self._usos: dict[str, _Uso] = {}       # variável -> primeiro uso tipado

    def _erro(self, no: No, mensagem: str):
        self.diagnosticos.append(Diagnostico(no.linha, no.coluna, mensagem))

    # --- listas de itens: pareamento de tags (R2, R9) -----------------------
    # Mensagem e Caso são os dois lugares onde tags aparecem como irmãs.
    def visitar_Mensagem(self, no: Mensagem):
        self._verificar_tags(no.itens)
        self.visitar_generico(no)

    def visitar_Caso(self, no: Caso):
        self._verificar_tags(no.itens)
        self.visitar_generico(no)

    def _verificar_tags(self, itens: list[No]):
        pilha: list[TagUI] = []
        for item in itens:
            if not isinstance(item, TagUI):
                continue
            if item.tipo is TipoTag.ABERTURA:
                self._verificar_valor_da_tag(item)
                pilha.append(item)
                continue
            # fechamento
            if item.nome is None:
                self._erro(item, "fechamento de tag sem nome; use </nome>")
                if pilha:
                    pilha.pop()
            elif not pilha:
                self._erro(item, f"</{item.nome}> sem tag de abertura correspondente")
            else:
                aberta = pilha.pop()
                if item.nome != aberta.nome:
                    self._erro(
                        item,
                        f"</{item.nome}> fecha <{aberta.nome}> (aberta na linha "
                        f"{aberta.linha}); a última tag aberta deve ser fechada primeiro",
                    )
        for aberta in pilha:
            self._erro(aberta, f"tag <{aberta.nome}> não foi fechada")

    def _verificar_valor_da_tag(self, tag: TagUI):
        if tag.nome != "color":
            return  # R9: demais tags são livres
        if tag.valor is None:
            self._erro(tag, "<color> exige um valor no formato #RRGGBB "
                            "(ex.: <color=#FF0000>)")
        elif not COR_HEX.fullmatch(tag.valor):
            self._erro(tag, f"valor '{tag.valor}' inválido em <color>: esperado '#' "
                            "seguido de 6 dígitos hexadecimais (ex.: #FF0000)")

    # --- seleção (R1, R4, R5, R6, R14) ---------------------------------------
    def visitar_Selecao(self, no: Selecao):
        nome = no.variavel.nome

        padroes = [c for c in no.casos if c.eh_padrao]
        if not padroes:
            self._erro(no, f"seleção de ${nome} sem ramo padrão [*]")
        for extra in padroes[1:]:
            self._erro(extra, f"mais de um ramo padrão [*] na seleção de ${nome}")

        vistas: set[str] = set()
        for caso in no.casos:
            if caso.eh_padrao:
                continue
            if caso.chave in vistas:
                self._erro(caso, f"chave [{caso.chave}] repetida na seleção de ${nome}")
            vistas.add(caso.chave)

        cldr, genero = _classificar(no)
        if cldr and genero:
            self._erro(
                no,
                f"seleção de ${nome} mistura categorias plurais "
                f"({', '.join(sorted(set(cldr)))}) e chaves de gênero/papel "
                f"({', '.join(sorted(set(genero)))})",
            )

        tipo = _tipo_da_selecao(no)
        if tipo is Tipo.NUMERO:
            self._registrar_uso(nome, tipo, no, "seleção por categoria plural")
        elif tipo is Tipo.TEXTO:
            self._registrar_uso(nome, tipo, no, "seleção por gênero/papel")

        self._selecoes.append(no)
        self.visitar_generico(no)
        self._selecoes.pop()

    # --- '#' (R3) -------------------------------------------------------------
    def visitar_NumeroPlural(self, no: NumeroPlural):
        if not self._selecoes:  # o léxico já impede; defesa para ASTs montadas à mão
            self._erro(no, "'#' fora de uma seleção")
            return
        sel = self._selecoes[-1]  # a seleção mais interna
        cldr, genero = _classificar(sel)
        if genero and not cldr:
            self._erro(no, f"'#' só pode ser usado em seleção de pluralização, mas "
                           f"${sel.variavel.nome} usa chaves de gênero/papel")
        elif not genero:
            self._registrar_uso(sel.variavel.nome, Tipo.NUMERO, no, "marcador '#'")
        # se há mistura (R5), o erro já foi dado na seleção

    # --- interpolação e formatadores (R14, R15, R16) -------------------------
    def visitar_Interpolacao(self, no: Interpolacao):
        nome = no.variavel.nome
        atual: Optional[Tipo] = None   # tipo do valor ao longo da cadeia
        primeiro = True
        for f in no.formatadores:
            spec = FORMATADORES.get(f.nome)
            if spec is None:
                self._erro(f, f"formatador desconhecido '{f.nome}' "
                              f"(disponíveis: {', '.join(sorted(FORMATADORES))})")
                atual, primeiro = None, False
                continue

            self._verificar_argumentos(f, spec)

            if primeiro:
                self._registrar_uso(nome, spec.entrada, f, f"formatador '{f.nome}'")
            elif atual is not None and atual is not spec.entrada:
                self._erro(
                    f,
                    f"'{f.nome}' espera {spec.entrada.value}, mas recebe "
                    f"{atual.value} (saída do formatador anterior)",
                )
            atual, primeiro = spec.saida, False

    def _verificar_argumentos(self, f, spec: EspecFormatador):
        n = len(f.argumentos)
        maximo = len(spec.argumentos)
        if not spec.obrigatorios <= n <= maximo:
            faixa = (str(maximo) if spec.obrigatorios == maximo
                     else f"{spec.obrigatorios} a {maximo}")
            self._erro(f, f"'{f.nome}' espera {faixa} argumento(s), recebeu {n}")
            return
        for i, valor in enumerate(f.argumentos):
            arg = spec.argumentos[i]
            if not arg.valido(valor):
                self._erro(f, f"argumento {i + 1} de '{f.nome}' ({arg.nome}) "
                              f"deve ser {arg.descricao}, recebeu '{valor}'")

    # --- tipos das variáveis (R14) ---------------------------------------------
    def _registrar_uso(self, nome: str, tipo: Tipo, no: No, motivo: str):
        anterior = self._usos.get(nome)
        if anterior is None:
            self._usos[nome] = _Uso(tipo, no.linha, motivo)
        elif anterior.tipo is not tipo:
            self._erro(
                no,
                f"${nome} é usada como {tipo.value} ({motivo}), mas na linha "
                f"{anterior.linha} foi usada como {anterior.tipo.value} "
                f"({anterior.motivo})",
            )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def verificar(arvore: Mensagem) -> list[Diagnostico]:
    """Devolve os diagnósticos semânticos da AST, ordenados por posição."""
    v = Verificador()
    v.visitar(arvore)
    return sorted(set(v.diagnosticos), key=lambda d: (d.linha, d.coluna, d.mensagem))


class _ColetorDeVariaveis(Visitante):
    def __init__(self):
        self.nomes: list[str] = []   # ordem da primeira aparição

    def _anotar(self, nome: str):
        if nome not in self.nomes:
            self.nomes.append(nome)

    def visitar_Interpolacao(self, no: Interpolacao):
        self._anotar(no.variavel.nome)

    def visitar_Selecao(self, no: Selecao):
        self._anotar(no.variavel.nome)
        self.visitar_generico(no)


def variaveis(arvore: Mensagem) -> dict[str, Optional[Tipo]]:
    """Variáveis da mensagem, na ordem em que aparecem, com o tipo inferido (R14).

    O tipo é `None` quando a variável é neutra (só `{ $x }` ou só `[*]`). Em caso
    de conflito de tipos, vale o do primeiro uso.
    """
    v = Verificador()
    v.visitar(arvore)
    coletor = _ColetorDeVariaveis()
    coletor.visitar(arvore)
    return {n: (v._usos[n].tipo if n in v._usos else None) for n in coletor.nomes}


def analisar(texto: str) -> Mensagem:
    """Léxico + sintático + semântico. Devolve a AST se tudo estiver correto."""
    arvore = parse(texto)  # levanta ErroSintatico
    diagnosticos = verificar(arvore)
    if diagnosticos:
        raise ErroSemantico(diagnosticos)
    return arvore


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python src/semantica.py <arquivo.loca>", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        texto = f.read()
    try:
        analisar(texto)
    except ErroSintatico as e:
        for d in e.diagnosticos:
            print(f"ERRO SINTÁTICO: {d}", file=sys.stderr)
        return 1
    except ErroSemantico as e:
        for d in e.diagnosticos:
            print(f"ERRO SEMÂNTICO: {d}", file=sys.stderr)
        return 1
    print("OK: sem erros semânticos")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
