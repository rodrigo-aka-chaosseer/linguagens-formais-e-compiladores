"""Testes de processar(): pipeline completo devolvendo dados simples."""
import json

from processar import processar


def fases(r):
    return [d["fase"] for d in r["diagnosticos"]]


def test_mensagem_valida():
    r = processar("Olá, { $nome }!")
    assert r["ok"] is True
    assert r["diagnosticos"] == []
    assert r["ast"]["no"] == "Mensagem"
    assert [t["tipo"] for t in r["tokens"] if not t["oculto"]][:2] == ["TEXTO", "ABRE_BLOCO"]
    assert r["variaveis"] == [{"nome": "nome", "tipo": None}]


def test_resultado_e_serializavel_em_json():
    json.dumps(processar("<b>{ $x -> [one] # [*] y }</b> 日本語 😀"))


def test_erro_lexico():
    r = processar("Olá { $nome @ }!")
    assert fases(r) == ["lexico"]
    assert (r["diagnosticos"][0]["linha"], r["diagnosticos"][0]["coluna"]) == (1, 12)
    assert r["ast"] is None


def test_erro_sintatico():
    r = processar("{ nome }")
    assert "sintatico" in fases(r)
    assert "lexico" not in fases(r)
    assert r["ast"] is None


def test_erro_semantico_mantem_ast_e_variaveis():
    r = processar("{ $x -> [one] a }")
    assert fases(r) == ["semantico"]
    assert r["ast"]["no"] == "Mensagem"
    assert r["variaveis"] == [{"nome": "x", "tipo": "numero"}]


def test_semantica_nao_roda_com_erro_sintatico():
    r = processar("{ $x -> [one] a } { nome }")
    assert "semantico" not in fases(r)


def test_numero_malformado_nao_duplica_diagnostico():
    r = processar("{ $v | arredondar(3.) }")
    na_posicao = [d for d in r["diagnosticos"] if (d["linha"], d["coluna"]) == (1, 18)]
    assert [d["fase"] for d in na_posicao] == ["lexico"]
    assert "malformado" in na_posicao[0]["mensagem"]


def test_bloco_nao_fechado():
    r = processar("Olá, { $nome")
    assert "lexico" in fases(r)
    assert r["ok"] is False


def test_diagnosticos_ordenados_por_posicao():
    r = processar("{ $x -> [one] a }\n<color=yellow>y</color>\n{ $x | maiusculo }")
    pos = [(d["linha"], d["coluna"]) for d in r["diagnosticos"]]
    assert pos == sorted(pos) and len(pos) >= 3


def test_comprimento_cobre_o_token():
    r = processar("{ $x | arredondar(3.) }")
    assert max(d["comprimento"] for d in r["diagnosticos"]) >= 2  # '3.'


def test_tipos_das_variaveis():
    r = processar("{ $n -> [one] # [*] # } { $g -> [fem] a [*] b } { $x }")
    assert r["variaveis"] == [
        {"nome": "n", "tipo": "numero"},
        {"nome": "g", "tipo": "texto"},
        {"nome": "x", "tipo": None},
    ]


def test_ast_tem_posicoes():
    r = processar("ab\n{ $x }")
    interp = r["ast"]["itens"][1]
    assert (interp["no"], interp["linha"], interp["coluna"]) == ("Interpolacao", 2, 0)


def test_aninhamento_extremo_nao_levanta():
    r = processar("{ $x -> [*] " * 3000 + "}" * 3000)
    assert r["ok"] is False
    assert isinstance(r["diagnosticos"], list)


def test_texto_vazio():
    r = processar("")
    assert r["ok"] is True and r["variaveis"] == []
