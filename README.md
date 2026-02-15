# manage_chat_messages

- TIMESTAMP
- CHATROOM
- BROKER
- MESSAGE
- CURRENCY/PAIR
- TENOR
- MARKET
- RANK

## Question 1: Cas des « split message ». 

Proposition de stratégie pour la gestion des "split message":
- Pour fusionner correctement ces messages, je comprends qu'il faut faire la distinction entre deux messages envoyés à la suite par un même broker et un message fractionné par le système.

- Je propose de regrouper par l'identifiant CHATROOM selon le procédé suivant.
    - Seuil de fenêtre temporelle : nous partons du principe que si un message appartenant au même broker arrive dans un intervalle de temps très court (par exemple, < 5 secondes), il s'agit de la suite de la ligne précédente.
    - Préservation de la séquence : nous devons trier par horodatage avant de joindre les chaînes afin de garantir que le message ait un sens.
- Pour illustrer cette proposition, j'ai développé une version python et une version DBT. La structure du projet, l'installation et l'éxécution des programmes sont détaillés plus loin.
- Version Python : Tout ce procédé peut être réalisé en Python simplement avec la librairie pandas (voir `python_scripts/process_chats.py`). La version Pyhton est pertinente notamment sles données sont traitées via un « flux » (par exemple, lorsque des messages arrivent via une API).
- Pertinence de DBT : Bien que la partie classification des messages avec des algorithmes NLP sera fait en Python, DBT reste pertinent pour la partie gestion de la base en amont, les tests sur les colonnes, les transformations et "nettoyages" à l'aide de SQL, GROUP BY ou les fonctions windows. La version DBT permet de créer une base de données propre et dédupliquée sur lequel peut s'appuyer avec garantie le modèle de classification (voir dossier `dbt_management`).

## Question 2: Généralisation au multilingue.

To generalize your classification model without building a separate pipeline for every language, I recommend a Cross-Lingual Embedding approach.

Strategy: M-BERT or XLM-RoBERTa
Instead of translating everything to English (which is expensive and loses financial nuance), use a transformer model pre-trained on multiple languages simultaneously.

Shared Vector Space: Use models like paraphrase-multilingual-MiniLM-L12-v2. These models map different languages (e.g., "Buy order" and "Ordre d'achat") into the same mathematical space.

Zero-Shot Learning: Train your classifier on your English labeled data. Because the underlying embeddings are cross-lingual, the model will often correctly classify French or Spanish messages even if it has never seen them during training.

Language Identification (LangID): Implement a lightweight pre-processor (like fastText) to flag the language. If the language is unsupported or "low confidence," route it to a "Manual Review" bucket.

Handling "The Unknown": Use an Out-of-Distribution (OOD) detection layer. If the model's prediction confidence is low across all categories, label it as "Unclassified/Other" rather than forcing it into a category.

## Structure du projet
manage_chat_messages/
├── dbt_project/              # dbt Core folder
│   ├── models/
│   │   ├── staging/          # Raw data cleaning
│   │   │   └── stg_chat_logs.sql
│   │   └── intermediate/     # The "merging" logic
│   │       └── int_merged_messages.sql
│   ├── dbt_project.yml
│   └── profiles.yml          # DB Connection config
├── scripts/                  # Python logic
│   ├── __init__.py
│   └── chat_process.py          # The Python code provided previously
├── data/
│   └── raw_chats.csv         # Local csv data
├── requirements.txt          # Dependencies (pandas, dbt-core, etc.)
└── README.md

## Données
J'ai créé un jeu de données simple evc 3 colonnes :

- timestamp: Date et heure du message
- chat_identifier: identifiant d'une session chat
- chat_message: contenu du message

Le jeu de données contient plusieurs lignes pour un même chat_identifier pour reproduire le cas des "splits messages".

## Installation 

- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- dbt run

## Installation et dépendances

## Exécution