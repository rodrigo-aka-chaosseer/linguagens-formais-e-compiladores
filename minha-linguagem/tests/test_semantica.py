"""Testes da análise semântica (E4). As regras R1..R17 estão em
docs/especificacao.md, seção 8."""
import pytest

from api_parser import ErroSintatico
from ast_nos import Mensagem, TagUI, TipoTag
from semantica import ErroSemantico, analisar, verificar


def mensagens(texto):
    """Mensagens dos erros semânticos ([] se o texto for válido)."""
    try:
        analisar(texto)
    except ErroSemantico as e:
        return [d.mensagem for d in e.diagnosticos]
    return []


def aceita(texto):
    assert mensagens(texto) == []


def rejeita(texto, trecho):
    achadas = mensagens(texto)
    assert any(trecho in m for m in achadas), achadas


# --- exemplo completo ------------------------------------------------------
def test_exemplo_dano_valido():
    aceita(
        "<color=#FFFF00>{ $atacante_nome }</color> causou { $dano } de dano!\n"
        "{ $vitima_genero ->\n"
        "    [fem] Ela perdeu\n"
        "    [*]   Ele perdeu\n"
        "} { $pocoes ->\n"
        "    [one]  # poção de vida.\n"
        "    [*]    # poções de vida.\n"
        "}"
    )


# --- R1: ramo padrão ---------------------------------------------------------
def test_selecao_sem_padrao():
    rejeita("{ $x -> [one] a }", "sem ramo padrão")


def test_dois_ramos_padrao():
    rejeita("{ $x -> [*] a [*] b }", "mais de um ramo padrão")


def test_other_nao_substitui_o_padrao():  # R6
    rejeita("{ $x -> [one] a [other] b }", "sem ramo padrão")


def test_padrao_em_qualquer_posicao():
    aceita("{ $x -> [*] a [one] b }")


# --- R4, R5: chaves ------------------------------------------------------------
def test_chave_repetida():
    rejeita("{ $x -> [one] a [one] b [*] c }", "repetida")


def test_mistura_de_cldr_e_genero():
    rejeita("{ $x -> [one] a [masculino] b [*] c }", "mistura")


# --- R7, R8: aceitos sem aviso ---------------------------------------------------
def test_ramo_vazio_e_aceito():
    aceita("{ $x -> [one] [*] a }")


def test_selecao_so_com_padrao_e_aceita():
    aceita("{ $x -> [*] a }")


# --- R3: '#' ---------------------------------------------------------------------
def test_cerquilha_em_selecao_de_genero():
    rejeita("{ $g -> [fem] # [*] x }", "só pode ser usado em seleção de pluralização")


def test_cerquilha_em_pluralizacao():
    aceita("{ $n -> [one] # coisa [*] # coisas }")


def test_cerquilha_em_selecao_so_com_padrao():
    aceita("{ $n -> [*] # coisas }")


def test_cerquilha_refere_se_a_selecao_mais_interna():
    rejeita("{ $n -> [one] { $g -> [fem] # [*] x } [*] y }", "só pode ser usado")
    aceita("{ $g -> [fem] { $n -> [one] # [*] # } [*] x }")


# --- R2: pareamento de tags ----------------------------------------------------------
def test_fechamento_sem_nome_e_erro_sintatico():
    with pytest.raises(ErroSintatico):
        analisar("<b>x</>")


def test_tags_aninhadas_corretas():
    aceita("<b><i>x</i></b>")


def test_tag_fechada_com_nome_errado():
    rejeita("<b>x</i>", "fecha <b>")


def test_ordem_de_fechamento_cruzada():
    msgs = mensagens("<b><i>x</b></i>")
    assert len(msgs) == 2
    assert all("a última tag aberta deve ser fechada primeiro" in m for m in msgs)


def test_tag_dentro_de_ramo():
    aceita("{ $g -> [fem] <b>Ela</b> [*] Ele }")
    rejeita("{ $g -> [fem] <b>Ela</i> [*] Ele }", "fecha <b>")


def test_fechamento_sem_abertura_em_ast_montada_a_mao():
    arvore = Mensagem(itens=[TagUI(tipo=TipoTag.FECHAMENTO, nome="b", linha=1, coluna=0)])
    assert any("sem tag de abertura" in d.mensagem for d in verificar(arvore))


def test_abertura_sem_fechamento_em_ast_montada_a_mao():
    arvore = Mensagem(itens=[TagUI(tipo=TipoTag.ABERTURA, nome="b", linha=1, coluna=0)])
    assert any("não foi fechada" in d.mensagem for d in verificar(arvore))


# --- R9, R10: valor das tags ------------------------------------------------------------
def test_color_com_hex_valido():
    aceita("<color=#ff00AA>x</color>")


@pytest.mark.parametrize("tag", [
    "<color=yellow>x</color>",     # nome de cor
    "<color=#FFF>x</color>",       # 3 dígitos
    "<color=#FFFFFFFF>x</color>",  # 8 dígitos
    "<color>x</color>",            # sem valor
])
def test_color_invalido(tag):
    assert mensagens(tag)


def test_outras_tags_sao_livres():
    aceita("<bold>x</bold> <b=qualquer>y</b> <italic=#FFF>z</italic>")


# --- R15: formatadores --------------------------------------------------------------------
def test_formatador_desconhecido():
    rejeita("{ $x | inventado }", "desconhecido")


@pytest.mark.parametrize("fonte", [
    "{ $v | moeda(BRL) }",
    "{ $v | moeda(BRL, 2) }",
    "{ $v | arredondar(2) }",
    "{ $t | maiusculo }",
    "{ $t | minusculo }",
])
def test_formatadores_validos(fonte):
    aceita(fonte)


@pytest.mark.parametrize("fonte,trecho", [
    ("{ $v | moeda }", "espera 1 a 2"),
    ("{ $v | moeda(BRL, 2, 3) }", "espera 1 a 2"),
    ("{ $v | arredondar }", "espera 1"),
    ("{ $v | arredondar(1, 2) }", "espera 1"),
    ("{ $t | maiusculo(1) }", "espera 0"),
    ("{ $v | moeda(brl) }", "código de 3 letras"),
    ("{ $v | moeda(BRL, 2.5) }", "inteiro"),
    ("{ $v | arredondar(x) }", "inteiro"),
    ("{ $v | arredondar(11) }", "de 0 a 10"),
    ("{ $v | moeda(BRL, 11) }", "de 0 a 10"),
])
def test_argumentos_invalidos(fonte, trecho):
    rejeita(fonte, trecho)


# --- R16: encadeamento --------------------------------------------------------------------------
def test_encadeamento_numero_para_numero_para_texto():
    aceita("{ $v | arredondar(2) | moeda(BRL) }")


def test_encadeamento_texto_para_numero_e_erro():
    rejeita("{ $v | moeda(BRL) | arredondar(2) }", "espera número, mas recebe texto")


def test_encadeamento_texto_para_moeda_e_erro():
    rejeita("{ $t | maiusculo | moeda(BRL) }", "espera número, mas recebe texto")


# --- R14: tipo da variável ---------------------------------------------------------------------------
def test_mesma_variavel_como_numero_e_texto_por_formatadores():
    rejeita("{ $x | moeda(BRL) } { $x | maiusculo }", "foi usada como número")


def test_plural_e_formatador_de_texto():
    rejeita("{ $n -> [one] a [*] b } { $n | maiusculo }", "foi usada como número")


def test_genero_e_formatador_de_texto_sao_compativeis():
    aceita("{ $g -> [fem] a [*] b } { $g | maiusculo }")


def test_numero_em_formatador_e_em_plural_sao_compativeis():
    aceita("{ $n | moeda(BRL) } { $n -> [one] # [*] # }")


def test_variaveis_diferentes_nao_conflitam():
    aceita("{ $a | moeda(BRL) } { $b | maiusculo }")


def test_conflito_aponta_para_o_segundo_uso_e_cita_o_primeiro():
    with pytest.raises(ErroSemantico) as exc:
        analisar("{ $x | moeda(BRL) }\n{ $x | maiusculo }")
    d = exc.value.diagnosticos[0]
    assert d.linha == 2
    assert "linha 1" in d.mensagem


# --- infraestrutura --------------------------------------------------------------------------------------
def test_erros_sao_coletados_e_ordenados():
    with pytest.raises(ErroSemantico) as exc:
        analisar("{ $x -> [one] a }\n<color=yellow>y</color>")
    linhas = [d.linha for d in exc.value.diagnosticos]
    assert linhas == sorted(linhas) and len(linhas) >= 2


def test_erro_sintatico_passa_direto():
    with pytest.raises(ErroSintatico):
        analisar("{ nome }")


def test_mensagem_do_erro_contem_posicao():
    with pytest.raises(ErroSemantico) as exc:
        analisar("ok\n{ $x -> [one] a }")
    assert "linha 2" in str(exc.value)
