"""Nós da AST da LocaScript (contrato E3: gramática <-> Builder/Visitor).

Requer Python 3.10+ (dataclass kw_only).

Regras do contrato:
- Todo nó tem `linha` e `coluna` (token inicial), fora da comparação (==),
  para os testes compararem só a estrutura.
- TextoLiteral.valor já vem com os escapes resolvidos (\\{ -> {).
- Tags são planas: TagUI de abertura e de fechamento são nós irmãos.
  O pareamento é validado na análise semântica (E4-A).
- NumeroPlural é o `#`. Seu uso fora de um Caso é erro semântico.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Optional


class TipoTag(Enum):
    ABERTURA = "abertura"
    FECHAMENTO = "fechamento"


@dataclass
class No:
    linha: int = field(default=0, kw_only=True, compare=False)
    coluna: int = field(default=0, kw_only=True, compare=False)

    def filhos(self) -> list["No"]:
        """Nós filhos diretos, na ordem de declaração dos campos."""
        resultado: list[No] = []
        for f in fields(self):
            valor = getattr(self, f.name)
            if isinstance(valor, No):
                resultado.append(valor)
            elif isinstance(valor, list):
                resultado.extend(v for v in valor if isinstance(v, No))
        return resultado

    def para_dict(self) -> dict:
        """Estrutura sem posições, útil em testes e depuração."""
        saida: dict = {"no": type(self).__name__}
        for f in fields(self):
            if f.name in ("linha", "coluna"):
                continue
            valor = getattr(self, f.name)
            if isinstance(valor, No):
                valor = valor.para_dict()
            elif isinstance(valor, list):
                valor = [v.para_dict() if isinstance(v, No) else v for v in valor]
            elif isinstance(valor, Enum):
                valor = valor.value
            saida[f.name] = valor
        return saida


@dataclass
class Mensagem(No):
    itens: list[No] = field(default_factory=list)


@dataclass
class TextoLiteral(No):
    valor: str = ""


@dataclass
class NumeroPlural(No):
    """O marcador `#` dentro de um caso de pluralização."""


@dataclass
class Variavel(No):
    nome: str = ""  # sem o `$`


@dataclass
class Formatador(No):
    nome: str = ""
    argumentos: list[str] = field(default_factory=list)  # ex.: ["BRL"]


@dataclass
class Interpolacao(No):
    variavel: Optional[Variavel] = None
    formatadores: list[Formatador] = field(default_factory=list)


@dataclass
class Caso(No):
    chave: str = ""            # "masculino", "one", "*"
    eh_padrao: bool = False    # True quando a chave é `*`
    itens: list[No] = field(default_factory=list)


@dataclass
class Selecao(No):
    variavel: Optional[Variavel] = None
    casos: list[Caso] = field(default_factory=list)


@dataclass
class TagUI(No):
    tipo: TipoTag = TipoTag.ABERTURA
    nome: Optional[str] = None   # None em `</>`
    valor: Optional[str] = None  # `#FF0000` em <color=#FF0000>


class Visitante:
    """Percorre a AST. Sobrescreva `visitar_<NomeDoNo>` onde precisar."""

    def visitar(self, no: No):
        metodo = getattr(self, f"visitar_{type(no).__name__}", self.visitar_generico)
        return metodo(no)

    def visitar_generico(self, no: No):
        for filho in no.filhos():
            self.visitar(filho)
