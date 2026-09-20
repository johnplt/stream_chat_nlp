# ⚡ StreamChat NLP Hub

> **Plateforme MLOps de classification sémantique multilingue temps réel (< 500 ms SLA) et batch.**  
> Routage intelligent et assainissement de messages multi-secteurs (Fintech, Santé, E-Commerce).

---

## Vision Produit & Choix d'Architecture

### 1. Zero-Shot & Taxonomie Dynamique
Plutôt que d'entraîner ou de *fine-tuner* un modèle par domaine métier, la plateforme s'appuie sur la **recherche de similarité vectorielle** (`paraphrase-multilingual-MiniLM-L12-v2`).
* **Avantage :** Modification des catégories métiers à chaud sans aucun réentraînement.
* **Support Multilingue :** Alignement sémantique natif sur +50 langues sans passer par une étape de traduction coûteuse.

### 2. Sobriété Numérique vs LLMs
Là où l'appel à un LLM (GPT-4 / Llama-3) introduit une latence de 1 à 3 secondes et un coût récurrent par API :
* **Inférence CPU ultra-rapide :** ~15-30 ms par message.
* **SLA garanti :** Largement sous la barre des 500 ms exigés pour du chat temps réel.
* **Coût d'infrastructure :** Inférence locale sans dépendance à des APIs payantes.

### 3. Architecture Hybride (Batch & Online)
* **Mode Batch (Data Engineering) :** Traitement de volumes historiques via **dbt** et **DuckDB** pour dédupliquer, assainir et re-fusionner les *split messages* fragmentés.
* **Mode Online / Temps Réel (MLOps & UI) :** Application Streamlit / API pour la classification instantanée et le routage des messages entrants.

---

## 🛠️ Stack Technique

* **Package Manager & Environment :** `uv` (Fast Python packaging written in Rust)
* **Model & Inference :** `sentence-transformers`, `torch` (Inférence vectorielle)
* **Language Detection :** `fasttext-wheel`
* **Data Processing & Analytics :** `duckdb`, `dbt-duckdb`, `pandas`
* **Application & UI :** `streamlit`
* **Containerization & CI/CD :** `Docker`, `GitHub Actions`

---

## 🚀 Lancement Rapide (Local)

Le projet utilise **`uv`** pour la gestion ultra-rapide des dépendances.

```bash
# 1. Cloner le projet
git clone
cd stream_chat_nlp

# 2. Synchroniser l'environnement virtuel avec uv
uv sync

# 3. Lancer l'application Streamlit
uv run streamlit run streamlit_app.py
```

---

## 🐳 Déploiement Docker
L'image est optimisée avec pré-téléchargement des modèles pour éviter tout délai au démarrage du conteneur.

```
# Build de l'image Docker
docker build -t stream_chat_nlp .

# Lancement du conteneur
docker run -p 8501:8501 stream_chat_nlp
```

---

## Pipeline CI/CD

Le projet inclut un workflow GitHub Actions (.github/workflows/ci.yml) qui :

1. Valide l'installation de l'environnement isolé avec uv.

2. Vérifie la syntaxe Python.

3. Exécute un test d'inférence vectorielle unitaire pour garantir la qualité du modèle en déploiement continu.

## Licence
Projet sous licence MIT. Libre réutilisation et modification.