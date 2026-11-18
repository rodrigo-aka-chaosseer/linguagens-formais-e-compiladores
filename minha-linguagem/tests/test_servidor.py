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
