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
```
├── data 
│   └── raw_chats.csv       # Local sample data
├── dbt_management          # dbt Core folder
│   ├── analyses
│   ├── dbt_project.yml
│   ├── macros
│   ├── models
│   │   ├── sources.yml
│   │   ├── staging
│   │   │   ├── schema.yml
│   │   │   └── stg_chat_messages.sql
│   │   └── transform
│   │       └── cleaned_message.sql
│   ├── profiles.yml        # DB Connection config
│   ├── README.md
│   ├── snapshots
│   ├── target
│   └── tests
│       └── assert_no_empty_messages.sql
├── logs
├── output
│   ├── cleaned_messages.csv
│   └── cleaned_messages.db
├── python_scripts
│   ├── chat_process.py
│   └── __init__.py
├── README.md
└── requirements.txt        # Dependencies (pandas, dbt-core, etc.)
```

## Données
J'ai créé un jeu de données simple avec 3 colonnes :

- timestamp: Date et heure du message
- chat_identifier: identifiant d'une session chat
- chat_message: contenu du message

Le jeu de données contient plusieurs lignes pour un même chat_identifier pour reproduire le cas des "splits messages".

## Installation et dépendances

- Pré-requis : Python >= 3.11
- [Duckdb](https://duckdb.org/install/?platform=linux&environment=cli)
- Se placer à la racine du projet, créer un environnement virtuel python: `python3 -m venv .venv`
- Activer l'environnement virtuel: `source .venv/bin/activate`
- Installer les dépendances : `pip install -r requirements.txt`


## Exécution

- Pour le Data Management des messages version Python : 
    - Lancer `python python_scripts/chat_process.py`
    - Le résultat se trouve dans le fichier `output/cleaned_messages.csv`
- Pour le Data Management des messages version DBT : 
    - Lancer `dbt run`
    - Le résultat se trouve dans la base de données : `output/cleaned_messages.db`
        - Lancer `duckdb`
        - `ATTACH '../output/cleaned_messages.db' AS cleaned_messages;`
        - `SELECT * FROM cleaned_messages.cleaned_messages;`
    - Pour les lancer les tests : `dbt test`