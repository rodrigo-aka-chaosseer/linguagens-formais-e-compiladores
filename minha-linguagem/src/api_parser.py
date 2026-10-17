"""API pública da E3: `parse(texto) -> Programa`.

Erros léxicos e sintáticos são coletados com linha e coluna e levantados
juntos como `ErroSintatico`.
"""
from __future__ import annotations

from dataclasses import dataclass

from antlr4 import CommonTokenStream, InputStream, Lexer
from antlr4.error.ErrorListener import ErrorListener

from ast_nos import Mensagem
from construtor_ast import ConstrutorAst
from LocaScript import LocaScript                  # lexer (nome do lexer grammar)
from LocaScriptParser import LocaScriptParser      # parser gerado


@dataclass(frozen=True)
class Diagnostico:
    linha: int
    coluna: int
    mensagem: str

    def __str__(self) -> str:
        return f"linha {self.linha}, coluna {self.coluna}: {self.mensagem}"


class ErroSintatico(Exception):
    def __init__(self, diagnosticos: list[Diagnostico]):
        self.diagnosticos = diagnosticos
        super().__init__("\n".join(str(d) for d in diagnosticos))


class _ColetorErros(ErrorListener):
    def __init__(self):
        super().__init__()
        self.diagnosticos: list[Diagnostico] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.diagnosticos.append(Diagnostico(line, column, msg))


def parse(texto: str) -> Mensagem:
    coletor = _ColetorErros()

    lexer = LocaScript(InputStream(texto))
    lexer.removeErrorListeners()
    lexer.addErrorListener(coletor)

    tokens = CommonTokenStream(lexer)
    tokens.fill()  # força o lexer a chegar ao EOF

    # Bloco ou tag não fechado: o lexer termina fora do modo padrão.
    if lexer._mode != Lexer.DEFAULT_MODE:
        coletor.diagnosticos.append(
            Diagnostico(lexer.line, lexer.column, "bloco ou tag não fechado")
        )

    parser = LocaScriptParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(coletor)
    arvore = parser.mensagem()

    if coletor.diagnosticos:
        raise ErroSintatico(coletor.diagnosticos)
    return ConstrutorAst(tokens).visit(arvore)
