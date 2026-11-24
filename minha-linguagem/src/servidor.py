"""Servidor HTTP do playground da LocaScript.

Local (a partir da raiz do projeto):
    python src/servidor.py                       # http://127.0.0.1:5000  (FLASK_DEBUG=1 liga o modo debug)

Produção (o Dockerfile faz isto):
    gunicorn --chdir src servidor:app

Rotas:
    GET  /            página do playground (static/index.html)
    GET  /saude       verificação de saúde para o host
    POST /analisar    {"texto": "..."}                                   -> resultado de processar()
    POST /renderizar  {"texto": "...", "valores": {...}, "idioma": "pt"}  -> mensagem renderizada
"""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from interpretador import ErroDeIdioma, renderizar, validar_idioma
from processar import processar, processar_com_arvore

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ESTATICA = RAIZ / "static"

TAMANHO_MAXIMO_BYTES = 50_000
TAMANHO_MAXIMO_CORPO = 256_000   # o JSON inclui valores, idioma e escapes
MAXIMO_VARIAVEIS = 200
TAMANHO_MAXIMO_VALOR = 2_000

app = Flask(__name__, static_folder=str(PASTA_ESTATICA), static_url_path="/static")
app.json.ensure_ascii = False  # acentos e emojis legíveis no JSON
app.config["MAX_CONTENT_LENGTH"] = TAMANHO_MAXIMO_CORPO

# A página usa script e estilo inline e só fala com o próprio servidor.
_CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


@app.after_request
def _cabecalhos_de_seguranca(resposta):
    resposta.headers.setdefault("Content-Security-Policy", _CSP)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("Referrer-Policy", "no-referrer")
    return resposta


@app.get("/")
def pagina_inicial():
    return send_from_directory(PASTA_ESTATICA, "index.html")


@app.get("/saude")
def saude():
    return jsonify(status="ok")


@app.post("/analisar")
def analisar_endpoint():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not isinstance(dados.get("texto"), str):
        return jsonify(erro='envie um JSON no formato {"texto": "..."}'), 400

    texto = dados["texto"]
    if len(texto.encode("utf-8")) > TAMANHO_MAXIMO_BYTES:
        return jsonify(erro=f"texto maior que {TAMANHO_MAXIMO_BYTES} bytes"), 413

    return jsonify(processar(texto))


def _valores_validos(valores) -> bool:
    """`valores`: objeto com texto, número ou null; sem booleanos nem estruturas."""
    if not isinstance(valores, dict) or len(valores) > MAXIMO_VARIAVEIS:
        return False
    for v in valores.values():
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            return False
        if isinstance(v, str) and len(v) > TAMANHO_MAXIMO_VALOR:
            return False
    return True


@app.post("/renderizar")
def renderizar_endpoint():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not isinstance(dados.get("texto"), str):
        return jsonify(erro='envie um JSON com "texto" (e, opcionalmente, "valores" e "idioma")'), 400

    texto = dados["texto"]
    valores = dados.get("valores", {})
    idioma = dados.get("idioma", "pt")

    if not _valores_validos(valores):
        return jsonify(erro=(
            f'"valores" deve ser um objeto com até {MAXIMO_VARIAVEIS} entradas, '
            "cada uma texto, número ou null")), 400
    if len(texto.encode("utf-8")) > TAMANHO_MAXIMO_BYTES:
        return jsonify(erro=f"texto maior que {TAMANHO_MAXIMO_BYTES} bytes"), 413
    try:
        validar_idioma(idioma)
    except ErroDeIdioma as e:
        return jsonify(erro=str(e)), 400

    analise, arvore = processar_com_arvore(texto)
    resposta = {
        "ok": analise["ok"],
        "diagnosticos": analise["diagnosticos"],
        "variaveis": analise["variaveis"],
        "texto": None,
        "trechos": [],
        "avisos": [],
    }
    if analise["ok"] and arvore is not None:
        try:
            resposta.update(renderizar(arvore, valores, idioma).para_dict())
        except RecursionError:
            return jsonify(erro="mensagem aninhada demais para ser renderizada"), 422
    return jsonify(resposta)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
