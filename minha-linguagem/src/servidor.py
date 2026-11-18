"""Servidor HTTP do playground da LocaScript.

Rodar (a partir da raiz do projeto):
    python src/servidor.py
    # ou: flask --app src/servidor run

Endpoint:
    POST /analisar   corpo JSON {"texto": "..."}   ->   resultado de processar()
"""
from __future__ import annotations

from flask import Flask, jsonify, request

from processar import processar

TAMANHO_MAXIMO_BYTES = 50_000

app = Flask(__name__)
app.json.ensure_ascii = False  # acentos e emojis legíveis no JSON


@app.post("/analisar")
def analisar_endpoint():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not isinstance(dados.get("texto"), str):
        return jsonify(erro='envie um JSON no formato {"texto": "..."}'), 400

    texto = dados["texto"]
    if len(texto.encode("utf-8")) > TAMANHO_MAXIMO_BYTES:
        return jsonify(erro=f"texto maior que {TAMANHO_MAXIMO_BYTES} bytes"), 413

    return jsonify(processar(texto))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
