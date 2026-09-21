# StreamChat NLP Hub

**Classer et trier automatiquement les messages clients dans +50 langues en temps réel et par lot.**

---

## À quoi sert ce projet ?

Dans le service client d'une entreprise (Fintech, Santé, E-Commerce), des milliers de messages peuvent arirver chaque jour et parfois dans des langues différentes. Les trier à la main ou créer des règles rigides prend du temps et coûte cher.

**StreamChat NLP** permet de :
1. **Identifier le sujet d'un message instantanément** (ex: problème de paiement, demande d'ordonnance, suivi de livraison) peu importe la langue du client.
2. **Rediriger automatiquement le message** vers la bonne équipe ou le bon service client.
3. **Traiter des volumes historiques (mode Batch)** pour nettoyer, dédoubler et analyser les données passées avec DuckDB et dbt.

## Pourquoi cette approche plutôt qu'un LLM (ex: ChatGPT) ?
* **Exécution rapide & légère :** Au lieu d'attendre la réponse plus lourde et distante d'un grand modèle de langage, la classification s'effectue localement sur le serveur.
* **Économique et sobre :** Tourne sur un simple processeur (CPU), sans abonnement API coûteux ni besoin de cartes graphiques (GPU).
* **Flexible :** Tu peux modifier ou ajouter de nouvelles catégories à tout moment dans l'application sans devoir ré-entraîner le modèle.

---

## Architecture Hybride (Batch & Online)
* **Mode Batch (Data Engineering) :** Traitement de volumes historiques via **dbt** et **DuckDB** pour dédupliquer, assainir et re-fusionner les *split messages* fragmentés.
* **Mode Online / Temps Réel (MLOps & UI) :** Application Streamlit / API pour la classification instantanée et le routage des messages entrants.

---

## Stack Technique

* **Langage & Environnement :** Python 3.11, `uv` (gestionnaire de packages ultra-rapide)
* **Modèle NLP :** Sentence-Transformers (`paraphrase-multilingual-MiniLM-L12-v2`)
* **Traitement de données :** DuckDB, dbt, Pandas
* **Interface & Déploiement :** Streamlit, Docker, GitHub Actions (CI/CD), Railway

---

## Lancer le projet en local

Le projet utilise **`uv`** pour installer les dépendances en quelques secondes.

```bash
# 1. Cloner le projet
git clone git-url
cd stream_chat_nlp

# 2. Installer les dépendances avec uv
uv sync

# 3. Lancer l'application
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