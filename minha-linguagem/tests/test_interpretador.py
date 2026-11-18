"""Testes do interpretador: renderização com valores, idioma, plural e formatadores."""
import json

import pytest

from interpretador import ErroDeIdioma, renderizar
from semantica import analisar

NBSP = "\xa0"
PLURAL = "{ $n -> [one] # coisa [*] # coisas }"


def r(texto, valores=None, idioma="pt"):
    return renderizar(analisar(texto), valores or {}, idioma)


def txt(texto, valores=None, idioma="pt"):
    return r(texto, valores, idioma).texto


# --- texto e variáveis -------------------------------------------------------
def test_interpolacao_simples():
    res = r("Olá, { $nome }!", {"nome": "Aria"})
    assert res.texto == "Olá, Aria!" and res.avisos == []


def test_texto_sem_variaveis():
    assert txt("Bem-vindo à masmorra! 😀") == "Bem-vindo à masmorra! 😀"


def test_escapes_sao_renderizados_como_literais():
    assert txt(r"chaves \{ $x \} e \# e \\") == "chaves { $x } e # e \\"


def test_numero_em_interpolacao_segue_o_idioma():
    assert txt("{ $d }", {"d": 1234.5}, "pt") == "1.234,5"
    assert txt("{ $d }", {"d": 1234.5}, "en") == "1,234.5"


def test_inteiro_nao_ganha_casas():
    assert txt("{ $d }", {"d": 12}) == "12"


# --- pluralização ------------------------------------------------------------------
LOOT = "Você encontrou { $q -> [zero] nenhuma moeda. [one] 1 moeda de ouro. [*] # moedas de ouro. }"


@pytest.mark.parametrize("q,esperado", [
    (0, "Você encontrou nenhuma moeda."),
    (1, "Você encontrou 1 moeda de ouro."),
    (5, "Você encontrou 5 moedas de ouro."),
    (1234, "Você encontrou 1.234 moedas de ouro."),
])
def test_exemplo_do_readme(q, esperado):
    assert txt(LOOT, {"q": q}) == esperado


def test_zero_casa_antes_da_categoria_cldr():
    # em pt_BR o CLDR classifica 0 como `one`; [zero] precisa vencer
    assert txt("{ $n -> [zero] nada [one] um [*] muitos }", {"n": 0}, "pt_BR") == "nada"


def test_sem_zero_vale_a_regra_do_idioma():
    assert txt(PLURAL, {"n": 0}, "pt_BR") == "0 coisa"   # CLDR: 0 é `one` em pt_BR
    assert txt(PLURAL, {"n": 0}, "pt_PT") == "0 coisas"  # e `other` em pt_PT
    assert txt(PLURAL, {"n": 0}, "en") == "0 coisas"


def test_categorias_do_russo():
    fonte = "{ $n -> [one] # um [few] # poucos [many] # muitos [*] # outro }"
    esperado = {1: "1 um", 2: "2 poucos", 5: "5 muitos", 21: "21 um", 22: "22 poucos"}
    for n, saida in esperado.items():
        assert txt(fonte, {"n": n}, "ru") == saida


def test_categoria_sem_ramo_cai_no_padrao():
    assert txt("{ $n -> [one] # um [*] # varios }", {"n": 2}, "ru") == "2 varios"


def test_fracao_usa_a_regra_do_idioma():
    assert txt(PLURAL, {"n": 1.5}, "en") == "1.5 coisas"


def test_numero_como_texto_numerico_e_aceito():
    assert txt(PLURAL, {"n": "5"}) == "5 coisas"


def test_numero_negativo_nao_quebra():
    assert txt(PLURAL, {"n": -1}, "en") == "-1 coisa"


def test_selecao_so_com_padrao_aceita_cerquilha():
    assert txt("{ $n -> [*] # itens }", {"n": 1234.5}, "en") == "1,234.5 itens"


def test_cerquilha_refere_se_a_selecao_mais_interna():
    fonte = "{ $a -> [one] { $b -> [one] # B [*] # B* } [*] # A* }"
    assert txt(fonte, {"a": 1, "b": 7}, "en") == "7 B*"


def test_cerquilha_depois_da_selecao_interna_volta_para_a_externa():
    fonte = "{ $a -> [one] { $b -> [*] x } # A [*] y }"
    assert txt(fonte, {"a": 1, "b": 2}, "en") == "x 1 A"


# --- gênero/papel ----------------------------------------------------------------------
GENERO = "{ $g -> [fem] Ela [*] Ele } perdeu"


def test_selecao_de_genero():
    assert txt(GENERO, {"g": "fem"}) == "Ela perdeu"
    assert txt(GENERO, {"g": "outro"}) == "Ele perdeu"


def test_genero_diferencia_maiusculas():
    assert txt(GENERO, {"g": "FEM"}) == "Ele perdeu"


# --- formatadores ------------------------------------------------------------------------
@pytest.mark.parametrize("fonte,valor,idioma,esperado", [
    ("{ $v | moeda(BRL) }", 1234.5, "pt", f"R${NBSP}1.234,50"),
    ("{ $v | moeda(BRL) }", 1234.5, "en", "R$1,234.50"),
    ("{ $v | moeda(BRL, 0) }", 1234.5, "pt", f"R${NBSP}1.235"),
    ("{ $v | moeda(JPY) }", 1234.5, "en", "¥1,235"),
    ("{ $v | arredondar(2) }", 3.14159, "pt", "3,14"),
    ("{ $v | arredondar(2) }", 3.1, "pt", "3,10"),
    ("{ $v | arredondar(0) }", 2.5, "pt", "3"),
    ("{ $v | arredondar(1) | moeda(BRL) }", 1.26, "pt", f"R${NBSP}1,30"),
])
def test_formatadores_numericos(fonte, valor, idioma, esperado):
    assert txt(fonte, {"v": valor}, idioma) == esperado


def test_formatadores_de_texto():
    assert txt("{ $t | maiusculo }", {"t": "aria"}) == "ARIA"
    assert txt("{ $t | minusculo }", {"t": "ARIA"}) == "aria"


# --- tags de UI ------------------------------------------------------------------------------
def test_tags_viram_estilo_dos_trechos():
    res = r("<color=#FF0000>{ $nome }</color> venceu", {"nome": "Aria"})
    assert [(t.texto, t.estilo) for t in res.trechos] == [
        ("Aria", (("color", "#FF0000"),)),
        (" venceu", ()),
    ]


def test_tags_aninhadas_acumulam_estilo():
    res = r("<b>a<i>b</i>c</b>")
    assert [(t.texto, [n for n, _ in t.estilo]) for t in res.trechos] == [
        ("a", ["b"]), ("b", ["b", "i"]), ("c", ["b"]),
    ]


def test_ramo_herda_o_estilo_de_fora():
    res = r("<b>{ $g -> [fem] Ela [*] Ele }</b>", {"g": "fem"})
    assert [(t.texto, t.estilo) for t in res.trechos] == [("Ela", (("b", None),))]


def test_tag_dentro_do_ramo_nao_vaza():
    res = r("{ $g -> [fem] <b>Ela</b> [*] Ele } perdeu", {"g": "fem"})
    assert [(t.texto, t.estilo) for t in res.trechos] == [("Ela", (("b", None),)), (" perdeu", ())]


# --- valores com problema (avisos, sem exceção) ---------------------------------------------------
def test_variavel_ausente_vira_marcador_e_aviso():
    res = r("Olá, { $nome }!")
    assert res.texto == "Olá, {$nome}!"
    assert [t.ausente for t in res.trechos] == [False, True, False]
    assert len(res.avisos) == 1 and "não informado" in res.avisos[0].mensagem


def test_valor_nulo_conta_como_ausente():
    assert txt("{ $x }", {"x": None}) == "{$x}"


def test_valor_nao_numerico_em_plural_usa_o_padrao():
    res = r(PLURAL, {"n": "abc"})
    assert res.texto == "# coisas"   # ramo [*], com '#' sem valor
    assert any("não é numérico" in a.mensagem for a in res.avisos)


def test_cerquilha_sem_numero_vira_marcador():
    res = r(PLURAL)   # n ausente
    assert any("não informado" in a.mensagem for a in res.avisos)
    assert any(t.ausente and t.texto == "#" for t in res.trechos)


def test_booleano_e_rejeitado():
    res = r("{ $x }", {"x": True})
    assert res.texto == "{$x}" and res.avisos


def test_formatador_numerico_com_texto_avisa():
    res = r("{ $v | moeda(BRL) }", {"v": "abc"})
    assert res.texto == "{$v}" and any("numérica" in a.mensagem for a in res.avisos)


def test_numero_fora_do_limite_e_rejeitado():
    res = r("{ $v | arredondar(2) }", {"v": 1e30})
    assert res.texto == "{$v}" and res.avisos


def test_genero_sem_valor_avisa_e_usa_padrao():
    res = r(GENERO)
    assert res.texto == "Ele perdeu" and res.avisos


def test_genero_com_numero_avisa_e_usa_padrao():
    res = r(GENERO, {"g": 3})
    assert res.texto == "Ele perdeu" and res.avisos


# --- idioma ---------------------------------------------------------------------------------------------------
def test_idioma_desconhecido():
    with pytest.raises(ErroDeIdioma):
        r("x", idioma="xx_YY")


@pytest.mark.parametrize("idioma", ["", "  ", None, 3])
def test_idioma_invalido(idioma):
    with pytest.raises(ErroDeIdioma):
        r("x", idioma=idioma)


@pytest.mark.parametrize("idioma", ["pt", "pt-BR", "pt_BR", "en-US", "ru"])
def test_formas_aceitas_de_idioma(idioma):
    assert txt("ok", idioma=idioma) == "ok"


# --- exemplo completo -----------------------------------------------------------------------------------------
DANO = (
    "<color=#FFFF00>{ $atacante_nome }</color> causou { $dano } de dano!\n"
    "{ $vitima_genero ->\n"
    "    [fem] Ela perdeu\n"
    "    [*]   Ele perdeu\n"
    "} { $pocoes ->\n"
    "    [one]  # poção de vida.\n"
    "    [*]    # poções de vida.\n"
    "}"
)


def test_exemplo_dano():
    valores = {"atacante_nome": "Aria", "dano": 12, "vitima_genero": "fem", "pocoes": 3}
    res = r(DANO, valores)
    assert res.texto == "Aria causou 12 de dano!\nEla perdeu 3 poções de vida."
    assert res.avisos == []
    assert res.trechos[0].estilo == (("color", "#FFFF00"),)


def test_resultado_e_serializavel():
    d = r(DANO, {"atacante_nome": "A", "dano": 1, "vitima_genero": "fem", "pocoes": 1}).para_dict()
    json.dumps(d, ensure_ascii=False)
    assert d["trechos"][0]["estilo"] == [{"tag": "color", "valor": "#FFFF00"}]
