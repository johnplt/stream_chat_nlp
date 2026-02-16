# manage_chat_messages

## Question 1: Cas des « split message ». 

Proposition de stratégie pour la gestion des "split message":
- Je propose de regrouper par l'identifiant CHATROOM selon le procédé suivant =>
    - Préservation de la séquence : il faut trier par date et heur avant de joindre les chaînes afin de garantir que le message ait un sens.
    - Agrégation: agréger par CHATROOM et rassembler les messages d'un même chat
    
- Pour illustrer cette proposition, j'ai développé une version python et une version DBT. La structure du projet, l'installation et l'éxécution des programmes sont détaillés plus loin.
- Version Python : Tout ce procédé peut être réalisé en Python simplement avec la librairie pandas (voir `python_scripts/process_chats.py`). La version Python est pertinente notamment si les données sont traitées via un « flux » (par exemple, lorsque des messages arrivent via une API).
- Pertinence de DBT : Bien que la partie classification des messages avec des algorithmes NLP sera fait en Python, DBT reste pertinent pour la partie gestion de la base en amont (tests sur les colonnes, transformations, "nettoyages") à l'aide de SQL, GROUP BY ou les fonctions window. La version DBT permet de créer une base de données propre et dédupliquée sur lequel peut s'appuyer avec garantie le modèle de classification (voir dossier `dbt_management`).

## Question 2: Généralisation au multilingue.

Pour généraliser le modèle de classification plusieurs stratégies sont possibles. Cependant, pour respecter la contrainte de 500ms maximum de traitement par message, les modèles d'apprentissage profond lourds (comme BERT ou GPT) sont à écarter comme échangé ensemble. Il est néanmoins possible d'utiliser des modèles d'apprentissage automatique plus léger sans créer une pipeline distinct pour chaque langue. 

### Première stratégie : Traduction + modèle anglais
Cette stratégie se concentre autour de FastText pour la détection de la langue + le modèle de classification déjà existant pour la catégorisation des messages. Ces méthodes restent efficaces en termes de CPU et de temps d'exécution.

Les étapes de l' algorithme :
1. Détection rapide (FastText) : Si le niveau de confiance est faible (<70% par exemple, seuil arbitraire) ou si le texte est trop court (<1 ou 2 mots), redirection vers une révision manuelle.

2. Classification : 
    - Si la langue détectée est l'anglais : On applique le modèle existant (anglais) pour la classification
    - Si la langue est détectée mais qu'il s'agit d'une autre langue que l'anglais, on utilise la traduction vers l'anglais puis application du modèle existant pour la classification
    - Si la langue n'est pas détectée, révision manuelle

Pour tester cette réflexion, j'ai créé un script Python  (voir `python_scripts/message_audit.py`) qui classe les messages et réalise les étapes ci-dessous. L'idée est d'essayer de gérer la contrainte de 500 ms tout en gérant plusieurs langues et en fournissant une piste d'audit (durée et résultats par étape).
1. FastText (détection de la langue) : le modèle local le plus rapide pour obtenir à la fois la langue et le score de confiance.

2. Règle de décision et traduction:
    - Score de confiance (<70%): Flag « Révision manuelle » immédiate pour éviter les erreurs et gagner du temps.
    - Langue anglaise: OK, pas de traduction.
    - Autres langues : Traduction avec un traducteur approfondi (backend Google). Cette solution utilise une API et pour les messages courts (10 à 20 mots), elle répond généralement dans un délai assez court.
    - Timing : J'utilise time.perf_counter() pour calculer les durées avec une précision à la nanoseconde près pour chaque transition.

Les résultats (`output/audit_messages.csv`) sont plutôt satisfaisants en terme de timing, il faudrait tester sur de vraies données pour la cohérence des résultats.

### Deuxième stratégie : Modèle multilingue léger
Plutôt que d'utiliser un gros modèle (comme GPT-4 ou BERT), Il est possible d'utilisé un encodeur multilingue. Ce type d'encodeur a été entraîné à comprendre la signification sémantique dans différentes langues dans un seul espace vectoriel.

Le modèle `MiniLM-L12-v2` (multilingue) est un bon candidat car très rapide, il peut effectuer des inférences dans des délais très court sur un processeur standard. Il n'est pas nécessaire de traduire le texte ici, le modèle peut prendre en input plusieurs langues. Il s'agit d'un modèle de classification sans apprentissage, cela fonctionne parce que le modèle a été pré-entraîné sur une quantité massive de texte afin de comprendre les relations entre les mots. Au lieu de rechercher une étiquette spécifique qui lui a été « enseignée », il calcule à la volée la proximité sémantique entre un texte et des catégories. Ce modèle supporte plus de 50 langues.

J'ai également testé cette stratégie sur quelques exemples de données. Je démontre ici la faisabilité mais le mieux est de tester sur des données réelles pour trancher sur la pertinence d'un tel modèle.
    - Script : `python_scripts/messages_classification_multilingue.py`
    - Résultats : `output/classified_messages.csv`

### Troisième stratégie : 
Une autre stratégie serait d'utiliser Fasttext pour détecter la langue (comme dans la première stratégie) et avoir un modèle de classification pour chaque langue (ce qui peut être contraignant si l'on doit gérer beaucoup de langues).

### Discussion
Je pense qu'il n'y a pas de réponse stricte et définitive et qu'il faudrait tester les approches les plus viables au regard des contraintes et des données.

Pour rester sous la barre des 500 ms, la stratégie la plus efficace consisterait à utiliser un modèle multilingue hybride et se passer de l'étape de traduction:

    - Utiliser FastText pour un tri initial rapide afin de filtrer le bruit (ou d'identifier la langue)
    - Acheminer les messages hautement fiables vers un algo mixte 
        - modèle actuel pour l'anglais 
        - modèle de langage multilingue léger pour une classification sémantique

## Structure du projet
manage_chat_messages/
```
├── data
│   └── raw_chats.csv
├── dbt_management
│   ├── analyses
│   ├── dbt_project.yml
│   ├── macros
│   ├── models
│   │   ├── sources.yml
│   │   ├── staging
│   │   │   ├── schema.yml
│   │   │   └── stg_chat_messages.sql
│   │   └── transform
│   │       └── cleaned_messages.sql
│   ├── profiles.yml
│   ├── README.md
│   ├── snapshots
│   └── tests
│       └── assert_no_empty_messages.sql
├── logs
├── output
│   ├── audit_messages.csv
│   ├── classified_messages.csv
│   ├── cleaned_messages.csv
│   └── cleaned_messages.db
├── python_scripts
│   ├── chat_process.py
│   ├── __init__.py
│   ├── messages_audit.py
│   ├── messages_classification_multilingue.py
│   └── tests
│       └── test_chat_process.py
├── README.md
├── requirements.txt
└── run_pipeline.sh
```

## Données
J'ai créé un jeu de données simple avec 3 colonnes :

- timestamp: Date et heure du message
- chat_identifier: identifiant unique d'une session chat 
- chat_message: contenu du message

Le jeu de données contient plusieurs lignes pour un même chat_identifier pour reproduire le cas des "splits messages".

J'ai travaillé avec un simple fichier csv mais il est possible de modifier assez facilement ce code pour une exécution depuis des tables d'une base PostgreSQL. 
    - Python : librairie **SQLAlchemy**
    - DBT : librairie **dbt-postgres **(connecteur postgreSQL) + extension duckdb postgres

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
    - Pour lancer les tests unitaires Python `pytest python_scripts/tests/`
- Pour le Data Management des messages version DBT : 
    - Lancer `dbt run --project-dir ./dbt_management --profiles-dir ./dbt_management`
    - Le résultat se trouve dans la base de données : `output/cleaned_messages.db`
        - Lancer `duckdb`
        - `ATTACH 'output/cleaned_messages.db' AS cleaned_messages;`
        - `SELECT * FROM cleaned_messages.cleaned_messages;`
    - Pour les lancer les tests : `dbt test --project-dir ./dbt_management --profiles-dir ./dbt_management`
- Pour l'audit Langue + Timing :
    - Lancer directement le script Python à partir du fichier CSV => `python python_scripts/messages_audit.py --source csv --input_path output/cleaned_messages.csv`
    - ou Lancer `sh run_pipeline.sh`, script sh d'exécution de toute la pipeline dépendances + dbt + audit + classification Python.
- Pour la Classification multilingue :
    - Lancer directement le script Python à partir du fichier CSV => `python python_scripts/messages_classification_multilingue.py --source csv --input_path output/cleaned_messages.csv`
    - ou Lancer `sh run_pipeline.sh`, script sh d'exécution de toute la pipeline dépendances + dbt + audit + classification Python.
