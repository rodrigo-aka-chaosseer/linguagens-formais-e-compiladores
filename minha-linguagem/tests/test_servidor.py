import pytest

pytest.importorskip("flask")

from servidor import TAMANHO_MAXIMO_BYTES, app


@pytest.fixture
def cliente():
    return app.test_client()


def test_analisar_ok(cliente):
    r = cliente.post("/analisar", json={"texto": "Olá, { $nome }!"})
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["ok"] is True
    assert corpo["variaveis"] == [{"nome": "nome", "tipo": None}]


def test_analisar_com_erro_continua_200(cliente):
    r = cliente.post("/analisar", json={"texto": "{ nome }"})
    assert r.status_code == 200
    assert r.get_json()["ok"] is False


def test_acentos_nao_sao_escapados(cliente):
    r = cliente.post("/analisar", json={"texto": "poção"})
    assert "poção".encode("utf-8") in r.data


@pytest.mark.parametrize("corpo", [None, [], {"texto": 3}, {"outro": "x"}])
def test_corpo_invalido(cliente, corpo):
    r = cliente.post("/analisar", json=corpo)
    assert r.status_code == 400


def test_corpo_que_nao_e_json(cliente):
    r = cliente.post("/analisar", data="texto solto", content_type="text/plain")
    assert r.status_code == 400


def test_texto_grande_demais(cliente):
    r = cliente.post("/analisar", json={"texto": "a" * (TAMANHO_MAXIMO_BYTES + 1)})
    assert r.status_code == 413


# --- /renderizar ---------------------------------------------------------------
def renderizar_post(cliente, **corpo):
    return cliente.post("/renderizar", json=corpo)


def test_renderizar_ok(cliente):
    r = renderizar_post(cliente, texto="Você tem { $n -> [one] # moeda [*] # moedas }.",
                        valores={"n": 1234}, idioma="pt")
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["ok"] is True
    assert corpo["texto"] == "Você tem 1.234 moedas."
    assert corpo["variaveis"] == [{"nome": "n", "tipo": "numero"}]
    assert corpo["avisos"] == []


def test_renderizar_devolve_estilo_das_tags(cliente):
    corpo = renderizar_post(cliente, texto="<color=#FF0000>{ $x }</color>",
                            valores={"x": "oi"}).get_json()
    assert corpo["trechos"] == [
        {"texto": "oi", "estilo": [{"tag": "color", "valor": "#FF0000"}], "ausente": False}
    ]


def test_renderizar_idioma_padrao_e_pt(cliente):
    corpo = renderizar_post(cliente, texto="{ $d }", valores={"d": 1234.5}).get_json()
    assert corpo["texto"] == "1.234,5"


def test_renderizar_texto_invalido_devolve_diagnosticos(cliente):
    r = renderizar_post(cliente, texto="{ $x -> [one] a }", valores={"x": 1})
    corpo = r.get_json()
    assert r.status_code == 200 and corpo["ok"] is False
    assert corpo["diagnosticos"][0]["fase"] == "semantico"
    assert corpo["texto"] is None and corpo["trechos"] == []


def test_renderizar_variavel_ausente_vira_aviso(cliente):
    corpo = renderizar_post(cliente, texto="Olá, { $nome }!").get_json()
    assert corpo["texto"] == "Olá, {$nome}!"
    assert corpo["avisos"] and corpo["trechos"][1]["ausente"] is True


@pytest.mark.parametrize("corpo", [
    {"texto": "x", "idioma": "xx_YY"},
    {"texto": "x", "idioma": 3},
    {"texto": "x", "valores": []},
    {"texto": "x", "valores": {"a": True}},
    {"texto": "x", "valores": {"a": [1]}},
    {"texto": "x", "valores": {"a": "y" * 2001}},
    {"outro": "x"},
])
def test_renderizar_corpo_invalido(cliente, corpo):
    assert renderizar_post(cliente, **corpo).status_code == 400


def test_renderizar_texto_grande_demais(cliente):
    r = renderizar_post(cliente, texto="a" * (TAMANHO_MAXIMO_BYTES + 1))
    assert r.status_code == 413
