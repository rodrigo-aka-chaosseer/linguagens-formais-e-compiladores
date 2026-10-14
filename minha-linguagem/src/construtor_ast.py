"""Builder da AST: converte a árvore de parsing do ANTLR em nós de `ast_nos`.

Um método por rótulo/regra da gramática LocaScriptParser.g4.
Ajuste os imports conforme a pasta onde o ANTLR gerou os artefatos.
"""
from __future__ import annotations

from ast_nos import (
    Caso, Formatador, Interpolacao, No, NumeroPlural, Programa, Selecao,
    TagUI, TextoLiteral, TipoTag, Variavel,
)
from LocaScriptParserVisitor import LocaScriptParserVisitor  # gerado pelo ANTLR


def _pos(ctx) -> dict:
    """Posição do primeiro token da regra."""
    return {"linha": ctx.start.line, "coluna": ctx.start.column}


def _mesclar_textos(itens: list[No]) -> list[No]:
    """Junta TextoLiteral adjacentes (o lexer emite texto e escapes separados)."""
    saida: list[No] = []
    for item in itens:
        if (
            saida
            and isinstance(item, TextoLiteral)
            and isinstance(saida[-1], TextoLiteral)
        ):
            saida[-1].valor += item.valor
        else:
            saida.append(item)
    return saida


class ConstrutorAst(LocaScriptParserVisitor):
    def _conteudos(self, lista) -> list[No]:
        return _mesclar_textos([self.visit(c) for c in lista])

    # --- raiz e conteúdo -------------------------------------------------
    def visitPrograma(self, ctx):
        return Programa(itens=self._conteudos(ctx.conteudo()), **_pos(ctx))

    def visitTextoLiteral(self, ctx):
        return TextoLiteral(valor=ctx.TEXTO().getText(), **_pos(ctx))

    def visitEscapeLiteral(self, ctx):
        # `\{` -> `{`, `\\` -> `\`: descarta a barra invertida
        return TextoLiteral(valor=ctx.ESCAPE().getText()[1:], **_pos(ctx))

    def visitNumeroPlural(self, ctx):
        return NumeroPlural(**_pos(ctx))

    def visitBlocoConteudo(self, ctx):
        return self.visit(ctx.bloco())

    def visitTagConteudo(self, ctx):
        return self.visit(ctx.tag())

    # --- blocos ----------------------------------------------------------
    def visitInterpolacao(self, ctx):
        return Interpolacao(
            variavel=self.visit(ctx.variavel()),
            formatadores=[self.visit(f) for f in ctx.formatador()],
            **_pos(ctx),
        )

    def visitSelecao(self, ctx):
        return Selecao(
            variavel=self.visit(ctx.variavel()),
            casos=[self.visit(c) for c in ctx.caso()],
            **_pos(ctx),
        )

    def visitVariavel(self, ctx):
        return Variavel(nome=ctx.IDENT().getText(), **_pos(ctx))

    def visitFormatador(self, ctx):
        return Formatador(
            nome=ctx.IDENT().getText(),
            argumentos=[self.visit(a) for a in ctx.argumento()],
            **_pos(ctx),
        )

    def visitArgumento(self, ctx):
        return ctx.getText()

    def visitCaso(self, ctx):
        chave = ctx.chaveCaso()
        return Caso(
            chave=chave.getText(),
            eh_padrao=chave.CASO_PADRAO() is not None,
            itens=self._conteudos(ctx.conteudo()),
            **_pos(ctx),
        )

    # --- tags de UI ------------------------------------------------------
    def visitTagAbertura(self, ctx):
        valor = ctx.valorTag()
        return TagUI(
            tipo=TipoTag.ABERTURA,
            nome=ctx.IDENT().getText(),
            valor=self.visit(valor) if valor else None,
            **_pos(ctx),
        )

    def visitTagFechamento(self, ctx):
        ident = ctx.IDENT()
        return TagUI(
            tipo=TipoTag.FECHAMENTO,
            nome=ident.getText() if ident else None,
            **_pos(ctx),
        )

    def visitValorTag(self, ctx):
        return ctx.getText()
