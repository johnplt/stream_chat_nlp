import io
import os
import time
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# --- Configuration des Variables & Clé API Hugging Face ---
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

st.set_page_config(
    page_title="StreamChat NLP — Classification Multilingue",
    page_icon="⚡",
    layout="wide",
)

# Initialisation du client officiel Hugging Face
@st.cache_resource
def get_hf_client():
    if not HF_TOKEN:
        st.error("⚠️ Clé HF_TOKEN non configurée.")
        st.stop()
    return InferenceClient(token=HF_TOKEN)

client = get_hf_client()

def get_embeddings(texts: list) -> np.ndarray:
    """Génère les embeddings vectoriels proprement via le SDK officiel."""
    try:
        # Utilisation de la méthode dédiée feature_extraction du SDK
        response = client.feature_extraction(
            text=texts,
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        arr = np.array(response)
        
        # Mean pooling si le tableau contient la dimension des tokens
        if arr.ndim == 3:
            arr = np.mean(arr, axis=1)
            
        return arr
    except Exception as e:
        st.error(f"Erreur lors de la génération des embeddings : {e}")
        st.stop()


def cosine_similarity_np(vec_a: np.ndarray, vec_b: np.ndarray) -> np.ndarray:
    """Calcule la similarité cosinus matricielle sans PyTorch (ultra léger en RAM)."""
    dot_product = np.dot(vec_a, vec_b.T)
    norm_a = np.linalg.norm(vec_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(vec_b, axis=1, keepdims=True)
    return dot_product / (norm_a * norm_b.T)


@st.cache_data
def get_category_embeddings_cached(categories_tuple):
    """Mise en cache des embeddings des catégories métiers."""
    return get_embeddings(list(categories_tuple))


# --- Dictionnaires de Données : Catégories et Exemples Synchronisés par Domaine ---
DOMAIN_DATA = {
    "Fintech & Trading": {
        "categories": [
            "Exécution d'Ordres (Achat, Vente)",
            "Alimentation du Compte (Dépôt, Retrait, Virement)",
            "Support Technique (Connexion, Erreur App)",
            "Analyse de Marché (Actualités, Cours, Tendances)",
            "Conformité & Légal (KYC, Fiscalité, Vérification)",
        ],
        "examples": {
            "Anglais": "I want to place an order to buy 50 shares of Apple.",
            "Français": (
                "Mon virement de 500 euros vers mon compte de trading"
                " n'apparaît toujours pas."
            ),
            "Espagnol": (
                "No puedo acceder a la plataforma de negociación desde la app"
                " móvil."
            ),
            "Allemand": (
                "Wie hoch sind die steuerlichen Gebühren für diesen"
                " Aktienverkauf?"
            ),
            "Chinois": "我想查询我昨天的转账记录是否成功。",
        },
    },
    "Santé & Support Médical": {
        "categories": [
            "Prise de Rendez-vous & Annulation",
            "Demande d'Ordonnance & Renouvellement",
            "Symptômes & Orientation Médicale",
            "Facturation & Prise en Charge Mutuelle",
            "Assistance Technique Plateforme",
        ],
        "examples": {
            "Français": (
                "Bonjour, je voudrais annuler mon rendez-vous de demain avec le"
                " Dr Martin."
            ),
            "Anglais": "Can I get a renewal for my asthma prescription?",
            "Espagnol": (
                "Tengo dolor de cabeza fuerte y fiebre desde ayer por la"
                " noche."
            ),
            "Allemand": (
                "Übernimmt die Krankenkasse die Kosten für diese Untersuchung?"
            ),
            "Italien": "Impossibile prenotare una visita sull'applicazione.",
        },
    },
    "E-Commerce & Service Client": {
        "categories": [
            "Suivi de Commande & Livraison",
            "Retour & Remboursement",
            "Information Produit & Stock",
            "Problème de Paiement",
            "Réclamation & Avis",
        ],
        "examples": {
            "Espagnol": "Mi paquete no ha llegado y la fecha de entrega ya pasó.",
            "Français": (
                "Je souhaite retourner cet article qui est trop petit et"
                " obtenir un remboursement."
            ),
            "Anglais": "My credit card was charged twice for the same purchase.",
            "Allemand": (
                "Ist diese Jacke auch in der Größe L wieder lieferbar?"
            ),
            "Portugais": (
                "O produto chegou danificado e com a embalagem aberta."
            ),
        },
    },
    "Personnalisé": {
        "categories": [
            "Urgent / Action Requise",
            "Question Générale",
            "Support Technique",
            "Feedback / Suggestion",
        ],
        "examples": {
            "Français": (
                "Problème majeur : l'application crash à chaque tentative de"
                " connexion !"
            ),
            "Anglais": "How can I update my profile personal information?",
            "Espagnol": (
                "Sugerencia: sería genial añadir un modo oscuro a la interfaz."
            ),
        },
    },
}

# --- Sidebar : Configuration & Taxonomie ---
st.sidebar.title("⚙️ Configuration MLOps")
domain = st.sidebar.selectbox("Cas d'usage Métier :", list(DOMAIN_DATA.keys()))

selected_categories_text = st.sidebar.text_area(
    "Catégories à classifier :",
    value="\n".join(DOMAIN_DATA[domain]["categories"]),
    height=180,
)

categories = [
    cat.strip()
    for cat in selected_categories_text.split("\n")
    if cat.strip()
]

# Calcul/Recupération des embeddings des catégories (mise en cache)
with st.spinner("Synchronisation des vecteurs de catégories..."):
    category_embeddings = get_category_embeddings_cached(tuple(categories))

# --- Header & Vision Produit / MLOps ---
st.title("⚡ StreamChat NLP Hub")

st.markdown("""
> **À quoi sert cette application ?**
> 
> Cette plateforme permet de **catégoriser automatiquement les messages clients** (support, réclamations, questions) dans plus de 50 langues, afin d'envoyer chaque demande directement à la bonne équipe.
> 
> * **Inférence Serverless :** Utilise l'API d'inférence de Hugging Face pour une empreinte mémoire quasi-nulle (~70 Mo RAM) et des réponses rapides.
> * **Catégories modifiables à la volée :** La liste des catégories dans la barre de gauche peut être personnalisée à tout moment sans aucun ré-entraînement du modèle.
> * **Deux modes d'utilisation :** 
>    1. **En temps réel :** Pour trier les messages dès qu'ils arrivent sur un chat ou un formulaire.
>    2. **Par lot (Batch) :** Pour traiter et nettoyer des fichiers de données historiques.
""")

st.divider()

# --- Mode d'utilisation (Onglets) ---
tab1, tab2 = st.tabs(
    ["💬 Test Temps Réel (Single Message)", "📁 Traitement Batch (Import CSV)"]
)

# --- TAB 1 : Single Message ---
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Message entrant")

        domain_examples = DOMAIN_DATA[domain]["examples"]
        selected_sample = st.selectbox(
            "Exemples multilingues pour ce domaine :",
            ["-- Saisir un texte libre --"]
            + [
                f"{langue} : {texte[:45]}..."
                for langue, texte in domain_examples.items()
            ],
        )

        if selected_sample != "-- Saisir un texte libre --":
            langue_key = selected_sample.split(" : ")[0]
            default_text = domain_examples[langue_key]
        else:
            default_text = ""

        user_input = st.text_area(
            "Saisie du message :",
            value=default_text,
            height=110,
            placeholder="Tapez un message dans n'importe quelle langue...",
        )

        btn_run = st.button(
            "Pousser au pipeline 🚀", type="primary", use_container_width=True
        )

    with col2:
        st.subheader("Résultats d'Inférence")
        if btn_run and user_input.strip():
            with st.spinner("Analyse sémantique en cours..."):
                # Obtenir embedding du message via l'API
                msg_emb = get_embeddings([user_input])

                # Calcul similarité avec NumPy
                scores = cosine_similarity_np(msg_emb, category_embeddings)[0]
                best_idx = int(np.argmax(scores))

                # Affichage des résultats
                st.metric(
                    "Score de Confiance", f"{float(scores[best_idx]):.1%}"
                )
                st.success(
                    f"**Catégorie attribuée :** {categories[best_idx]}"
                )

                df_res = pd.DataFrame({
                    "Catégorie": categories,
                    "Score de similarité": [float(s) for s in scores],
                }).sort_values("Score de similarité", ascending=False)

                st.dataframe(
                    df_res, use_container_width=True, hide_index=True
                )
        elif btn_run:
            st.warning("Veuillez saisir un message.")

# --- TAB 2 : Batch Processing CSV ---
with tab2:
    st.subheader("Importation & Traitement Batch (Engine)")
    st.markdown(
        "Téléversez un fichier CSV de volumétrie historique pour classifier"
        " automatiquement l'ensemble des messages."
    )

    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])

    if uploaded_file is not None:
        df_batch = pd.read_csv(uploaded_file)
        st.write("Aperçu des données reçues :", df_batch.head(3))

        text_column = st.selectbox(
            "Sélectionner la colonne contenant le texte :", df_batch.columns
        )

        if st.button("Lancer la classification Batch ⚙️", type="primary"):
            t_start = time.perf_counter()

            texts = df_batch[text_column].astype(str).tolist()

            with st.spinner(f"Traitement API de {len(texts)} messages..."):
                embeddings = get_embeddings(texts)
                cos_sim_matrix = cosine_similarity_np(
                    embeddings, category_embeddings
                )

                best_indices = np.argmax(cos_sim_matrix, axis=1)
                best_scores = [
                    float(cos_sim_matrix[i, best_indices[i]])
                    for i in range(len(texts))
                ]

                df_batch["predicted_category"] = [
                    categories[idx] for idx in best_indices
                ]
                df_batch["confidence_score"] = [
                    round(s, 3) for s in best_scores
                ]

            total_time = time.perf_counter() - t_start
            st.success(
                f"✅ {len(df_batch)} messages classés en {total_time:.2f}"
                f" secondes ({total_time/len(df_batch)*1000:.1f} ms/msg)."
            )

            st.dataframe(df_batch, use_container_width=True)

            csv_buffer = io.StringIO()
            df_batch.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Télécharger le CSV enrichi",
                data=csv_buffer.getvalue(),
                file_name="classified_batch_results.csv",
                mime="text/csv",
            )