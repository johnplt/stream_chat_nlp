# 1. Base Python
FROM python:3.11-slim

# 2. Copier uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Dépendances système pour FastText et C++
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Installation des dépendances Python via uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 5. PRÉ-TÉLÉCHARGEMENT DU MODÈLE FASTTEXT
# Requis pour éviter d'attendre le téléchargement à chaque démarrage de conteneur
RUN mkdir -p /app/models && \
    wget -q https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin -O /app/models/lid.176.bin

# 6. Copier le reste du projet
COPY . .

EXPOSE 8501

# 7. Lancement de l'application Streamlit via uv
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]