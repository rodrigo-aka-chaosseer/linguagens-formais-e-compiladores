"""Processa uma mensagem LocaScript e devolve tudo como dados simples (JSON).

Feito para o playground: em vez de levantar exceções, `processar` devolve

    {
      "ok": bool,                      # True se não há nenhum diagnóstico
      "diagnosticos": [                # ordenados por posição
        {"fase": "lexico" | "sintatico" | "semantico" | "interno",
         "linha": int,                 # a partir de 1
         "coluna": int,                # a partir de 0
         "comprimento": int,           # tamanho a sublinhar (>= 1)
         "mensagem": str},
      ],
      "tokens": [{"linha", "coluna", "tipo", "texto", "oculto"}],
      "ast": dict | None,              # None se houve erro léxico/sintático
      "variaveis": [{"nome": str, "tipo": "numero" | "texto" | None}],
    }

A análise semântica só roda quando não há erro léxico nem sintático.
"""
from __future__ import annotations

import os
import sys
from dataclasses import fields
from enum import Enum

# Torna a pasta gerado/ importável (mesma convenção de lexico.py/sintatico.py).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gerado"))

from antlr4 import CommonTokenStream, InputStream  # noqa: E402
from antlr4.error.ErrorListener import ErrorListener  # noqa: E402

from ast_nos import No  # noqa: E402
from construtor_ast import ConstrutorAst  # noqa: E402
from LocaScript import LocaScript  # noqa: E402
from LocaScriptParser import LocaScriptParser  # noqa: E402
from semantica import variaveis, verificar  # noqa: E402


def _diag(fase: str, linha: int, coluna: int, comprimento: int, mensagem: str) -> dict:
    return {
        "fase": fase,
        "linha": linha,
        "coluna": coluna,
        "comprimento": max(1, comprimento),
        "mensagem": mensagem,
    }


def _comprimento(simbolo) -> int:
    """Tamanho a sublinhar para o token que causou o erro."""
    if simbolo is None or simbolo.type == -1:  # sem token, ou EOF
        return 1
    primeira_linha = (simbolo.text or "").split("\n")[0]
    return max(1, len(primeira_linha))


class _Coletor(ErrorListener):
    def __init__(self, fase: str):
        super().__init__()
        self._fase = fase
        self.itens: list[dict] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.itens.append(
            _diag(self._fase, line, column, _comprimento(offendingSymbol), msg)
        )


def _ast_json(no: No) -> dict:
    """Como No.para_dict(), mas mantendo linha/coluna (o playground precisa delas)."""
    saida: dict = {"no": type(no).__name__, "linha": no.linha, "coluna": no.coluna}
    for f in fields(no):
        if f.name in ("linha", "coluna"):
            continue
        valor = getattr(no, f.name)
        if isinstance(valor, No):
            valor = _ast_json(valor)
        elif isinstance(valor, list):
            valor = [_ast_json(v) if isinstance(v, No) else v for v in valor]
        elif isinstance(valor, Enum):
            valor = valor.value
        saida[f.name] = valor
    return saida


def _processar(texto: str) -> dict:
    lexico = _Coletor("lexico")
    sintatico = _Coletor("sintatico")

    lexer = LocaScript(InputStream(texto))
    lexer.removeErrorListeners()
    lexer.addErrorListener(lexico)
    fluxo = CommonTokenStream(lexer)
    fluxo.fill()

    tokens = [
        {
            "linha": t.line,
            "coluna": t.column,
            "tipo": lexer.symbolicNames[t.type],
            "texto": t.text,
            "oculto": t.channel != 0,
        }
        for t in fluxo.tokens
        if t.type != -1
    ]

    # `3.` é reconhecido pelo lexer como token (não como erro): reporta aqui.
    for t in tokens:
        if t["tipo"] == "NUMERO_MALFORMADO":
            lexico.itens.append(_diag(
                "lexico", t["linha"], t["coluna"], len(t["texto"]),
                f"número malformado: '{t['texto']}' (falta dígito depois do ponto)",
            ))

    # Bloco ou tag aberto até o fim do arquivo: o lexer termina fora do modo padrão.
    if lexer._mode != lexer.DEFAULT_MODE:
        lexico.itens.append(
            _diag("lexico", lexer.line, lexer.column, 1, "bloco ou tag não fechado")
        )

    parser = LocaScriptParser(fluxo)
    parser.removeErrorListeners()
    parser.addErrorListener(sintatico)
    arvore = parser.mensagem()

    # O parser reclama do mesmo ponto que o lexer já apontou: mantém só o léxico.
    posicoes_lexicas = {(d["linha"], d["coluna"]) for d in lexico.itens}
    sintaticos = [
        d for d in sintatico.itens if (d["linha"], d["coluna"]) not in posicoes_lexicas
    ]

    diagnosticos = lexico.itens + sintaticos
    ast = None
    nomes: dict = {}

    if not diagnosticos:
        mensagem = ConstrutorAst(fluxo).visit(arvore)
        ast = _ast_json(mensagem)
        diagnosticos = [
            _diag("semantico", d.linha, d.coluna, 1, d.mensagem)
            for d in verificar(mensagem)
        ]
        nomes = variaveis(mensagem)

    diagnosticos.sort(key=lambda d: (d["linha"], d["coluna"], d["fase"]))
    return {
        "ok": not diagnosticos,
        "diagnosticos": diagnosticos,
        "tokens": tokens,
        "ast": ast,
        "variaveis": [
            {"nome": n, "tipo": t.name.lower() if t else None} for n, t in nomes.items()
        ],
    }


def processar(texto: str) -> dict:
    """Ponto de entrada. Nunca levanta por causa do conteúdo do texto."""
    try:
        return _processar(texto)
    except RecursionError:
        # Seleções/tags aninhadas demais estouram a recursão do Python.
        return {
            "ok": False,
            "diagnosticos": [_diag(
                "interno", 1, 0, 1,
                "mensagem aninhada demais para ser analisada",
            )],
            "tokens": [],
            "ast": None,
            "variaveis": [],
        }
