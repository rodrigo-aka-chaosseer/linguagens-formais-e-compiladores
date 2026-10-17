"""Builder da AST: converte a árvore de parsing do ANTLR em nós de `ast_nos`.

Um método visit<Regra> por regra de LocaScriptParser.g4.
Recebe o CommonTokenStream para recuperar os espaços dos ramos, que o
lexer manda para o canal HIDDEN.
"""
from __future__ import annotations

from antlr4 import Token

from ast_nos import (
    Caso, Formatador, Interpolacao, No, NumeroPlural, Mensagem, Selecao,
    TagUI, TextoLiteral, TipoTag, Variavel,
)
from LocaScriptParserVisitor import LocaScriptParserVisitor  # gerado pelo ANTLR


def _pos(ctx) -> dict:
    """Posição do primeiro token da regra."""
    return {"linha": ctx.start.line, "coluna": ctx.start.column}


def _pos_tok(tok) -> dict:
    return {"linha": tok.line, "coluna": tok.column}


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
    def __init__(self, tokens):
        super().__init__()
        self._tokens = tokens

    # --- apoio -----------------------------------------------------------
    def _espaco_antes(self, tok) -> str:
        """Espaços (canal HIDDEN) entre o token anterior e `tok`."""
        ocultos = self._tokens.getHiddenTokensToLeft(
            tok.tokenIndex, Token.HIDDEN_CHANNEL
        )
        return "".join(t.text for t in ocultos) if ocultos else ""

    def _itens(self, itens_ctx, bordas: bool = False) -> list[No]:
        """Visita uma lista de `item`, achatando tags e recolocando espaços.

        O espaço ENTRE itens é preservado; o espaço antes do primeiro item
        só entra se `bordas=True` (usado dentro de tags).
        """
        saida: list[No] = []
        for i, c in enumerate(itens_ctx):
            if i > 0 or bordas:
                tok = c.start
                ws = self._espaco_antes(tok)
                if ws:
                    saida.append(TextoLiteral(valor=ws, **_pos_tok(tok)))
            r = self.visit(c)
            saida.extend(r if isinstance(r, list) else [r])
        return _mesclar_textos(saida)

    # --- raiz e itens ----------------------------------------------------
    def visitMensagem(self, ctx):
        return Mensagem(itens=self._itens(ctx.item()), **_pos(ctx))

    def visitItem(self, ctx):
        if ctx.TEXTO() or ctx.TEXTO_B():
            tok = (ctx.TEXTO() or ctx.TEXTO_B()).getSymbol()
            return TextoLiteral(valor=tok.text, **_pos_tok(tok))
        if ctx.ESCAPE():
            tok = ctx.ESCAPE().getSymbol()
            # `\{` -> `{`, `\\` -> `\`: descarta a barra invertida
            return TextoLiteral(valor=tok.text[1:], **_pos_tok(tok))
        if ctx.VALOR_NUMERICO():
            return NumeroPlural(**_pos_tok(ctx.VALOR_NUMERICO().getSymbol()))
        return self.visit(ctx.interpolacao() or ctx.selecao() or ctx.tag())

    # --- blocos ----------------------------------------------------------
    def visitInterpolacao(self, ctx):
        ident = ctx.IDENT().getSymbol()
        return Interpolacao(
            variavel=Variavel(nome=ident.text, **_pos_tok(ident)),
            formatadores=[self.visit(f) for f in ctx.formatador()],
            **_pos(ctx),
        )

    def visitSelecao(self, ctx):
        ident = ctx.IDENT().getSymbol()
        return Selecao(
            variavel=Variavel(nome=ident.text, **_pos_tok(ident)),
            casos=[self.visit(r) for r in ctx.ramo()],
            **_pos(ctx),
        )

    def visitFormatador(self, ctx):
        args = ctx.argumentos()
        return Formatador(
            nome=ctx.IDENT().getText(),
            argumentos=self.visit(args) if args else [],
            **_pos(ctx),
        )

    def visitArgumentos(self, ctx):
        return [self.visit(a) for a in ctx.argumento()]

    def visitArgumento(self, ctx):
        return ctx.getText()

    def visitRamo(self, ctx):
        chave = ctx.chave()
        return Caso(
            chave=chave.getText(),
            eh_padrao=chave.CASO_PADRAO() is not None,
            itens=self._itens(ctx.item()),
            **_pos(ctx),
        )

    # --- tags de UI (planas na AST: abertura e fechamento são irmãs) ------
    def visitTag(self, ctx):
        itens = self._itens(ctx.item(), bordas=True)
        if ctx.item():  # espaço antes do fechamento, p.ex. "<b>x </b>"
            ws = self._espaco_antes(ctx.tagFecha().start)
            if ws:
                itens = _mesclar_textos(
                    itens + [TextoLiteral(valor=ws, **_pos(ctx.tagFecha()))]
                )
        return [self.visit(ctx.tagAbre()), *itens, self.visit(ctx.tagFecha())]

    def visitTagAbre(self, ctx):
        valor = ctx.valorTag()
        return TagUI(
            tipo=TipoTag.ABERTURA,
            nome=ctx.TAG_IDENT().getText(),
            valor=self.visit(valor) if valor else None,
            **_pos(ctx),
        )

    def visitTagFecha(self, ctx):
        ident = ctx.TAG_IDENT()
        return TagUI(
            tipo=TipoTag.FECHAMENTO,
            nome=ident.getText() if ident else None,
            **_pos(ctx),
        )

    def visitValorTag(self, ctx):
        return ctx.getText()
