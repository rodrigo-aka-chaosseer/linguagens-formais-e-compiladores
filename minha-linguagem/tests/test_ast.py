"""Testes de estrutura da AST.

Os textos dentro de casos são comparados com .strip(): a decisão de aparar
ou não os espaços ao redor do corpo do caso ainda é do time.
"""
from api_parser import parse
from ast_nos import (
    Caso, Interpolacao, NumeroPlural, Mensagem, Selecao, TagUI,
    TextoLiteral, TipoTag,
)


def tipos(no):
    return [type(i).__name__ for i in no.itens]


def texto_do_caso(caso: Caso) -> str:
    return "".join(i.valor for i in caso.itens if isinstance(i, TextoLiteral)).strip()


# --- texto e interpolação ------------------------------------------------
def test_mensagem_vazia():
    assert parse("") == Mensagem(itens=[])


def test_texto_puro():
    prog = parse("Olá, mundo")
    assert prog.itens == [TextoLiteral(valor="Olá, mundo")]


def test_unicode_preservado():
    prog = parse("日本語 😀 { $n }")
    assert prog.itens[0].valor == "日本語 😀 "


def test_interpolacao_simples():
    prog = parse("Olá, { $nome }!")
    assert tipos(prog) == ["TextoLiteral", "Interpolacao", "TextoLiteral"]
    interp = prog.itens[1]
    assert interp.variavel.nome == "nome"  # sem o `$`
    assert interp.formatadores == []


def test_espacos_em_bloco_sao_insensiveis():
    assert parse("{$x}") == parse("{   $x   }")
    assert parse("{$v|moeda(BRL)}") == parse("{ $v | moeda( BRL ) }")


def test_espacos_em_texto_sao_preservados():
    prog = parse("  a  { $x }  b  ")
    assert prog.itens[0].valor == "  a  "
    assert prog.itens[2].valor == "  b  "


# --- formatadores --------------------------------------------------------
def test_formatador_com_argumento():
    interp = parse("{ $valor | moeda(BRL) }").itens[0]
    assert [f.nome for f in interp.formatadores] == ["moeda"]
    assert interp.formatadores[0].argumentos == ["BRL"]


def test_formatadores_encadeados_em_ordem():
    interp = parse("{ $v | arredondar(2) | moeda(BRL) }").itens[0]
    assert [f.nome for f in interp.formatadores] == ["arredondar", "moeda"]
    assert interp.formatadores[0].argumentos == ["2"]


def test_formatador_sem_argumento():
    interp = parse("{ $v | maiusculo }").itens[0]
    assert interp.formatadores[0].argumentos == []


# --- seleção e pluralização ---------------------------------------------
GENERO = (
    "{ $genero ->\n"
    "    [masculino] O jogador\n"
    "    [feminino]  A jogadora\n"
    "    [*]         O(a) jogador(a)\n"
    "} { $nome } subiu de nível!"
)


def test_selecao_chaves_e_padrao():
    sel = parse(GENERO).itens[0]
    assert isinstance(sel, Selecao)
    assert sel.variavel.nome == "genero"
    assert [c.chave for c in sel.casos] == ["masculino", "feminino", "*"]
    assert [c.eh_padrao for c in sel.casos] == [False, False, True]


def test_selecao_corpo_dos_casos():
    sel = parse(GENERO).itens[0]
    assert [texto_do_caso(c) for c in sel.casos] == [
        "O jogador", "A jogadora", "O(a) jogador(a)",
    ]


def test_texto_apos_selecao_continua_no_nivel_raiz():
    prog = parse(GENERO)
    assert tipos(prog) == ["Selecao", "TextoLiteral", "Interpolacao", "TextoLiteral"]


PLURAL = (
    "Você encontrou { $quantidade ->\n"
    "    [zero]  nenhuma moeda.\n"
    "    [one]   1 moeda de ouro.\n"
    "    [*]     # moedas de ouro.\n"
    "}"
)


def test_pluralizacao_categorias():
    sel = parse(PLURAL).itens[1]
    assert [c.chave for c in sel.casos] == ["zero", "one", "*"]
    assert sel.casos[2].eh_padrao


def test_numero_plural_vira_no_proprio():
    padrao = parse(PLURAL).itens[1].casos[2]
    assert any(isinstance(i, NumeroPlural) for i in padrao.itens)
    assert "moedas de ouro." in texto_do_caso(padrao)


def test_digito_literal_no_caso_nao_e_numero_plural():
    um = parse(PLURAL).itens[1].casos[1]
    assert not any(isinstance(i, NumeroPlural) for i in um.itens)
    assert "1 moeda de ouro." == texto_do_caso(um)


# --- tags de UI ----------------------------------------------------------
def test_tags_abertura_e_fechamento_planas():
    prog = parse("<color=#FF0000>vermelho</>")
    assert tipos(prog) == ["TagUI", "TextoLiteral", "TagUI"]
    abre, _, fecha = prog.itens
    assert (abre.tipo, abre.nome, abre.valor) == (TipoTag.ABERTURA, "color", "#FF0000")
    assert (fecha.tipo, fecha.nome) == (TipoTag.FECHAMENTO, None)


def test_tag_sem_atributo_e_fechamento_nomeado():
    prog = parse("<bold>forte</bold>")
    abre, _, fecha = prog.itens
    assert (abre.nome, abre.valor) == ("bold", None)
    assert fecha.tipo == TipoTag.FECHAMENTO and fecha.nome == "bold"


def test_hash_dentro_de_tag_nao_e_numero_plural():
    prog = parse("<color=#00FF00>x</>")
    assert not any(isinstance(i, NumeroPlural) for i in prog.itens)


def test_interpolacao_entre_tags():
    prog = parse("<color=yellow>{ $atacante_nome }</>")
    assert tipos(prog) == ["TagUI", "Interpolacao", "TagUI"]


# --- escapes -------------------------------------------------------------
def test_escapes_resolvidos_e_mesclados():
    prog = parse(r"a \{ b \} c \$ d \# e \\ f")
    assert prog.itens == [TextoLiteral(valor="a { b } c $ d # e \\ f")]


def test_escape_nao_abre_bloco():
    assert tipos(parse(r"\{ $x \}")) == ["TextoLiteral"]


# --- exemplo completo (README) ------------------------------------------
DANO = (
    "<color=yellow>{ $atacante_nome }</> causou { $dano } de dano!\n"
    "{ $vitima_genero ->\n"
    "    [fem] Ela perdeu\n"
    "    [*]   Ele perdeu\n"
    "} { $pocoes ->\n"
    "    [one]  # poção de vida.\n"
    "    [*]    # poções de vida.\n"
    "}"
)


def test_exemplo_dano_sequencia_de_nos():
    assert tipos(parse(DANO)) == [
        "TagUI", "Interpolacao", "TagUI",
        "TextoLiteral", "Interpolacao", "TextoLiteral",
        "Selecao", "TextoLiteral", "Selecao",
    ]


def test_exemplo_dano_chaves():
    prog = parse(DANO)
    genero, pocoes = prog.itens[6], prog.itens[8]
    assert [c.chave for c in genero.casos] == ["fem", "*"]
    assert [c.chave for c in pocoes.casos] == ["one", "*"]


# --- posições ------------------------------------------------------------
def test_posicao_do_no():
    prog = parse("ab\n{ $x }")
    interp = prog.itens[1]
    assert isinstance(interp, Interpolacao)
    assert (interp.linha, interp.coluna) == (2, 0)


def test_posicao_do_caso():
    sel = parse("{ $x ->\n  [one] a\n  [*] b\n}").itens[0]
    assert sel.casos[0].linha == 2
    assert sel.casos[1].linha == 3
