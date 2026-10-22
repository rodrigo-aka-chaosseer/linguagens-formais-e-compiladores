"""Testes de aceitação e rejeição sintática"""
import pytest

from api_parser import ErroSintatico, parse

VALIDOS = {
    "vazio": "",
    "texto_puro": "Bem-vindo à masmorra!",
    "unicode_e_emoji": "日本語 Привет مرحبا 😀 { $nome }",
    "ola": "Olá, { $nome }!",
    "espacos_insensiveis": "{$nome}",
    "formatador": "Custa { $valor | moeda(BRL) }.",
    "formatadores_encadeados": "{ $valor | arredondar(2) | moeda(BRL) }",
    "formatador_sem_argumento": "{ $nome | maiusculo }",
    "selecao_genero": (
        "{ $genero ->\n"
        "    [masculino] O jogador\n"
        "    [feminino]  A jogadora\n"
        "    [*]         O(a) jogador(a)\n"
        "} { $nome } subiu de nível!"
    ),
    "pluralizacao": (
        "Você encontrou { $quantidade ->\n"
        "    [zero]  nenhuma moeda.\n"
        "    [one]   1 moeda de ouro.\n"
        "    [*]     # moedas de ouro.\n"
        "}"
    ),
    "tags": "<bold>forte</bold> e <color=#FF0000>vermelho</>",
    "tag_com_nome_de_cor": "<color=yellow>{ $atacante_nome }</>",
    "escapes": r"chaves \{ \} cifrão \$ sustenido \# barra \\",
    "dano": (
        "<color=yellow>{ $atacante_nome }</> causou { $dano } de dano!\n"
        "{ $vitima_genero ->\n"
        "    [fem] Ela perdeu\n"
        "    [*]   Ele perdeu\n"
        "} { $pocoes ->\n"
        "    [one]  # poção de vida.\n"
        "    [*]    # poções de vida.\n"
        "}"
    ),
}

INVALIDOS = {
    "bloco_nao_fechado": "Olá, { $nome",
    "variavel_sem_cifrao": "{ nome }",
    "cifrao_sem_nome": "{ $ }",
    "identificador_com_digito_inicial": "{ $1nome }",
    "identificador_com_acento": "{ $jogadór }",
    "bloco_vazio": "{ }",
    "selecao_sem_casos": "{ $x -> }",
    "caso_nao_fechado": "{ $x -> [one um [*] varios }",
    "caso_sem_chave": "{ $x -> [] texto [*] outro }",
    "pipe_sem_formatador": "{ $x | }",
    "formatador_parenteses_abertos": "{ $x | moeda(BRL }",
    "tag_nao_fechada": "<color=red texto",
    "chave_fechando_solta": "texto } solto",
}


@pytest.mark.parametrize("fonte", VALIDOS.values(), ids=VALIDOS.keys())
def test_aceita(fonte):
    parse(fonte)  # não deve levantar


@pytest.mark.parametrize("fonte", INVALIDOS.values(), ids=INVALIDOS.keys())
def test_rejeita(fonte):
    with pytest.raises(ErroSintatico):
        parse(fonte)


def test_erro_informa_linha_e_coluna():
    with pytest.raises(ErroSintatico) as exc:
        parse("primeira linha\n{ nome }")
    d = exc.value.diagnosticos[0]
    assert d.linha == 2
    assert d.coluna >= 0


def test_bloco_nao_fechado_aponta_para_ultima_linha():
    with pytest.raises(ErroSintatico) as exc:
        parse("ok\nok\n{ $x")
    assert exc.value.diagnosticos[-1].linha == 3


def test_mensagem_do_erro_contem_posicao():
    with pytest.raises(ErroSintatico) as exc:
        parse("{ nome }")
    assert "linha 1" in str(exc.value)
