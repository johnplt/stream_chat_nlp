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
- Version Python : Tout ce procédé peut être réalisé en Python simplement avec la librairie pandas (voir `python_scripts/process_chats.py`). La version Python est pertinente notamment si les données sont traitées via un « flux » (par exemple, lorsque des messages arrivent via une API).
- Pertinence de DBT : Bien que la partie classification des messages avec des algorithmes NLP sera fait en Python, DBT reste pertinent pour la partie gestion de la base en amont (tests sur les colonnes, transformations, "nettoyages") à l'aide de SQL, GROUP BY ou les fonctions window. La version DBT permet de créer une base de données propre et dédupliquée sur lequel peut s'appuyer avec garantie le modèle de classification (voir dossier `dbt_management`).

## Question 2: Généralisation au multilingue.

Pour généraliser le modèle de classification sans créer une pipeline distinct pour chaque langue, une approche d'intégration multilingue est possible. Cependant pour respecter la contrainte de 500ms maximum de traitement par message, les modèles d'apprentissage profond lourds (comme BERT ou GPT) sont à écarter  et il est possible d'utiliser des modèles d'apprentissage automatique plus léger.

On peut donc recentrer la stratégie autour de FastText pour la détection de la langue et TF-IDF + Linear Classifiers pour la catégorisation. Ces méthodes sont efficaces en termes de CPU et peuvent s'exécuter en moins de 10 ms par message.

Proposition d'une stratégie en plusieurs étapes :
1. Détection rapide (FastText) : Si le niveau de confiance est faible (<70% par exemple, à tester et discuter) ou si le texte est trop court (<1 ou 2 mots), redirection vers une révision manuelle.

2. Classification : 
    - Si langue détecté est l'anglais : On fait tourner le modèle existant
    - Si la langue est détecté mais qu'il s'agit d'une autre langue que l'anglais, on utilise la traduction vers l'anglais ou révision manuelle
    - Sinon, révision manuelle

Pour tester cette réflexion j'ai créé un script Python qui classe les messages réalise les étapes ci-dessous. L'idée est d'essayer de gérer la contrainte de 500 ms tout en gérant plusieurs langues et en fournissant une piste d'audit (durée et résultats par étape).
1. FastText (détection de la langue) : le modèle local le plus rapide (moins de 5 ms) pour obtenir à la fois la langue et le score de confiance.

2. Règle de décision et traduction:
    - Score de confiance (<70%): Flag « Révision manuelle » immédiate pour éviter les erreurs et gagner du temps.
    - Anglais: Flag "OK" et on skippe la traduction.
    - Autres langues : Traduction avec un traducteur approfondi (backend Google). Cette solution utilise une API et pour les messages courts (10 à 20 mots), elle répond généralement dans un délai de 200 à 400 ms.
    - Timing : J'utilise time.perf_counter() pour calculer les durées avec une précision à la nanoseconde près pour chaque transition.

Les résultats sont satisfaisants en terme de timing. 

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
│   ├── classified_messages.csv
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
- Se placer à la racine du projet
- Pour le Data Management des messages version Python : 
    - Lancer `python python_scripts/chat_process.py`
    - Le résultat se trouve dans le fichier `output/cleaned_messages.csv`
- Pour le Data Management des messages version DBT : 
    - Lancer `dbt run --project-dir ./dbt_management --profiles-dir ./dbt_management`
    - Le résultat se trouve dans la base de données : `output/cleaned_messages.db`
        - Lancer `duckdb`
        - `ATTACH 'output/cleaned_messages.db' AS cleaned_messages;`
        - `SELECT * FROM cleaned_messages.cleaned_messages;`
    - Pour les lancer les tests : `dbt test --project-dir ./dbt_management --profiles-dir ./dbt_management`
- Pour la classification langue + timing :
    - Lancer directement le script Python à partir du fichier CSV => `python python_scripts/message_classification.py --source csv --input_path output/
cleaned_messages.csv`
    - ou Lancer `sh run_pipeline.sh`, script sh d'exécution de toute la pipeline dépendances + dbt + classification Python.