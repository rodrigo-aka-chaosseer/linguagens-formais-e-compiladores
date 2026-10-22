"""
lexico.py — Analisador léxico da LocaScript.

Uso:
    python src/lexico.py exemplos/ola.loca

Depende do código gerado pelo ANTLR a partir de gramatica/LocaScript.g4.
Antes de rodar, gere o lexer com:

    # Windows (PowerShell): .\\gerar.ps1
    # Linux/macOS: bash gerar.sh

Isso cria a pasta gerado/ com LocaScript.py (não versionada no Git).
"""

import sys
import os

# Torna a pasta gerado/ (na raiz do projeto) importável.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gerado"))

from antlr4 import FileStream, CommonTokenStream, Token
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

    linhas = []
    for token in stream.tokens:
        if token.type == -1:  # EOF
            continue
        if token.channel != 0:  # espaços dos ramos (canal HIDDEN)
            continue
        nome = nome_do_token(lexer, token.type)
        linhas.append(
            (str(token.line), str(token.column), nome, repr(token.text))
        )
        if nome == "NUMERO_MALFORMADO":
            coletor.erros.append(
                (token.line, token.column, f"numero malformado: '{token.text}'")
            )

    cabecalhos = ("LINHA", "COLUNA", "TIPO", "TEXTO")
    larguras = [len(cabecalho) for cabecalho in cabecalhos]
    for linha in linhas:
        for indice, valor in enumerate(linha):
            larguras[indice] = max(larguras[indice], len(valor))

    print("Posições de coluna começam em 0.")
    print(
        "  ".join(
            cabecalho.ljust(larguras[indice])
            for indice, cabecalho in enumerate(cabecalhos)
        )
    )
    print("  ".join("-" * largura for largura in larguras))
    for linha in linhas:
        print(
            "  ".join(
                valor.ljust(larguras[indice])
                for indice, valor in enumerate(linha)
            )
        )

    total = len(linhas)

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
