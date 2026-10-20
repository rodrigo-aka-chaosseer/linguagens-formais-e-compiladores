import pytest
from api_parser import ErroSintatico, parse
from ast_nos import NumeroPlural, TextoLiteral

BUG = pytest.mark.xfail(strict=True, raises=ErroSintatico)



def test_cifrao_literal_em_ramo():
    # README: texto literal é qualquer caractere fora dos reservados
    parse("{ $x -> [*] custa 5$ }")



def test_arroba_literal_em_ramo():
    parse("{ $x -> [*] contato@site.com }")


@pytest.mark.xfail(strict=True)
def test_comentario_dentro_de_ramo():
    # esperado: '##' descartado; hoje vira dois NumeroPlural
    sel = parse("{ $x -> [*] a ## nota\n}").itens[0]
    assert not any(isinstance(i, NumeroPlural) for i in sel.casos[0].itens)


@pytest.mark.xfail(strict=True)
def test_comentario_inicial_nao_deixa_quebra_de_linha():
    # o '\n' após o comentário sobra como TextoLiteral
    assert parse("## nota\nolá").itens == [TextoLiteral(valor="olá")]


@pytest.mark.xfail(strict=True)
def test_espaco_entre_tag_vazia_em_ramo_e_preservado():
    # _itens só reinsere espaço entre itens; com tag sem filhos ele se perde
    sel = parse("{ $x -> [*] <b> </b> }").itens[0]
    texto = "".join(i.valor for i in sel.casos[0].itens if isinstance(i, TextoLiteral))
    assert texto == " "