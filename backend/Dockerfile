FROM python:3.12-slim AS builder

# G-02: estágio de build isolado — gcc/libpq-dev só existem aqui
# (necessários para compilar psycopg2 e afins), nunca no layer final que
# roda em produção. Reduz a imagem e a superfície de ataque.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENV=production

# libpq5 (runtime da lib C usada por psycopg2) sem o -dev/gcc do build.
# curl mantido: usado pelo healthcheck de plataforma (Railway).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app
COPY --from=builder /install /usr/local

COPY alembic.ini /app/
COPY alembic /app/alembic
COPY app /app/app

# G-02: non-root — um processo comprometido não ganha privilégio de
# root no container à toa.
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
