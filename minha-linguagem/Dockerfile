# --- Etapa 1: gera o lexer/parser com o ANTLR (precisa de Java) -------------
FROM python:3.12-slim AS gerar
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir antlr4-tools==0.2.2
WORKDIR /app
COPY gerar.sh ./
COPY gramatica/ ./gramatica/
RUN bash gerar.sh          # usa ANTLR 4.13.2 (definido em gerar.sh); escreve em /app/gerado

# --- Etapa 2: imagem final, só Python ---------------------------------------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY static/ ./static/
COPY --from=gerar /app/gerado ./gerado/

# Render define PORT (padrão 10000). Workers "sync" + timeout: uma entrada
# patológica derruba só aquele worker em vez de travar o servidor.
CMD ["sh", "-c", "exec gunicorn --chdir src --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 20 --access-logfile - servidor:app"]
