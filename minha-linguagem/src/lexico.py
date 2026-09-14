"""
lexico.py — Analisador léxico da LocaScript.

Uso:
    python src/lexico.py exemplos/ola.loca

Depende do código gerado pelo ANTLR a partir de gramatica/LocaScript.g4.
Antes de rodar, gere o lexer com:

    bash gerar.sh

Isso cria a pasta gerado/ com LocaScriptLexer.py (não versionada no Git).
"""

import sys
import os

# Torna a pasta gerado/ (na raiz do projeto) importável.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gerado"))

from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener
from LocaScript import LocaScript as LocaScriptLexer  # type: ignore[reportMissingImports]


class ColetorDeErros(ErrorListener):
    """Reporta erros léxicos com linha e coluna, sem derrubar o processo."""

    def __init__(self):
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.erros.append((line, column, msg))


def nome_do_token(lexer, tipo):
    """Converte o índice numérico do tipo de token no seu nome (ex: 'IDENT')."""
    if tipo == -1:
        return "EOF"
    return lexer.symbolicNames[tipo]


def tokenizar(caminho):
    entrada = FileStream(caminho, encoding="utf-8")
    lexer = LocaScriptLexer(entrada)

    coletor = ColetorDeErros()
    lexer.removeErrorListeners()
    lexer.addErrorListener(coletor)

    stream = CommonTokenStream(lexer)
    stream.fill()

    total = 0
    for token in stream.tokens:
        if token.type == -1:  # EOF
            continue
        nome = nome_do_token(lexer, token.type)
        print(f"{nome} '{token.text}' linha {token.line}")
        total += 1
        if nome == "NUMERO_MALFORMADO":
            coletor.erros.append(
                (token.line, token.column, f"numero malformado: '{token.text}'")
            )

    # Se o arquivo terminar sem o lexer voltar ao modo padrao, um bloco
    # "{ ... }" ou uma tag "< ... >" ficou sem fechar.
    if lexer._mode != lexer.DEFAULT_MODE:
        ultimo = stream.tokens[-2] if len(stream.tokens) > 1 else None
        linha = ultimo.line if ultimo else "?"
        coletor.erros.append((linha, "-", "bloco ou tag nao fechado ate o fim do arquivo"))

    if coletor.erros:
        for linha, coluna, msg in coletor.erros:
            print(
                f"ERRO LEXICO: linha {linha}, coluna {coluna}: {msg}",
                file=sys.stderr,
            )
        print(f"{total} tokens reconhecidos ({len(coletor.erros)} erro(s))")
        sys.exit(1)

    print(f"{total} tokens reconhecidos")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python src/lexico.py <arquivo.loca>", file=sys.stderr)
        sys.exit(2)
    tokenizar(sys.argv[1])
