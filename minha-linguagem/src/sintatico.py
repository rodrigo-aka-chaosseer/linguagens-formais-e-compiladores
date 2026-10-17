"""
sintatico.py — Analisador sintático da LocaScript.

Uso:
    python src/sintatico.py exemplos/dano.loca
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gerado"))

from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Tree import TerminalNode
from LocaScript import LocaScript as LocaScriptLexer
from LocaScriptParser import LocaScriptParser


def imprimir_arvore(arvore, parser):
    """Imprime regras e tokens como uma árvore indentada."""

    def rotulo(no):
        if isinstance(no, TerminalNode):
            token = no.getSymbol()
            nome = "EOF" if token.type == -1 else parser.symbolicNames[token.type]
            return f"{nome} {token.text!r} ({token.line}:{token.column})"
        return parser.ruleNames[no.getRuleIndex()]

    def visitar(no, prefixo="", ultimo=True, raiz=False):
        print(
            rotulo(no)
            if raiz
            else prefixo + ("└── " if ultimo else "├── ") + rotulo(no)
        )
        filhos = [] if isinstance(no, TerminalNode) else list(no.getChildren())
        for indice, filho in enumerate(filhos):
            prefixo_filho = prefixo
            if not raiz:
                prefixo_filho += "    " if ultimo else "│   "
            visitar(
                filho,
                prefixo_filho,
                ultimo=indice == len(filhos) - 1,
            )

    visitar(arvore, raiz=True)


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

    imprimir_arvore(arvore, parser)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python src/sintatico.py <arquivo.loca>", file=sys.stderr)
        sys.exit(2)
    analisar(sys.argv[1])
