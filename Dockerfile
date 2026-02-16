# 1. Use a Python base
FROM python:3.10-slim

# 2. Install C++ compiler for FastText
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Pre-download the FastText language model
RUN wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin -P /app/models/

# 5. Copy your project code
COPY . .

# On copie le dossier data local dans un dossier data à l'intérieur de /app
COPY data/ data/

# 6. Execute the pipeline
ENTRYPOINT ["/bin/bash", "run_pipeline.sh"]