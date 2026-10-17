"""
sintatico.py — Analisador sintático da LocaScript.

Uso:
    python src/sintatico.py exemplos/dano.loca
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gerado"))

from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener
from LocaScript import LocaScript as LocaScriptLexer
from LocaScriptParser import LocaScriptParser


class Coletor(ErrorListener):
    def __init__(self):
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.erros.append((line, column, msg))


def analisar(caminho):
    lexer = LocaScriptLexer(FileStream(caminho, encoding="utf-8"))
    parser = LocaScriptParser(CommonTokenStream(lexer))
    coletor = Coletor()
    for r in (lexer, parser):
        r.removeErrorListeners()
        r.addErrorListener(coletor)

    arvore = parser.mensagem()

    if lexer._mode != lexer.DEFAULT_MODE:
        coletor.erros.append(("fim", "-", "bloco, tag ou parenteses nao fechado"))

    if coletor.erros:
        for linha, coluna, msg in coletor.erros:
            print(f"ERRO: linha {linha}, coluna {coluna}: {msg}", file=sys.stderr)
        sys.exit(1)

    print(arvore.toStringTree(recog=parser))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python src/sintatico.py <arquivo.loca>", file=sys.stderr)
        sys.exit(2)
    analisar(sys.argv[1])
