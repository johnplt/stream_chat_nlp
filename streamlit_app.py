import time
import io
import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util

st.set_page_config(
    page_title="StreamChat NLP — Classification Multilingue",
    page_icon="⚡",
    layout="wide"
)

# --- Chargement du modèle NLP ---
@st.cache_resource
def load_model():
    return SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

with st.spinner("Initialisation du moteur NLP multilingue..."):
    model = load_model()

# --- Dictionnaires de Données : Catégories et Exemples Synchronisés par Domaine ---
DOMAIN_DATA = {
    "Fintech & Trading": {
        "categories": [
            "Exécution d'Ordres (Achat, Vente)",
            "Alimentation du Compte (Dépôt, Retrait, Virement)",
            "Support Technique (Connexion, Erreur App)",
            "Analyse de Marché (Actualités, Cours, Tendances)",
            "Conformité & Légal (KYC, Fiscalité, Vérification)"
        ],
        "examples": {
            "Anglais": "I want to place an order to buy 50 shares of Apple.",
            "Français": "Mon virement de 500 euros vers mon compte de trading n'apparaît toujours pas.",
            "Espagnol": "No puedo acceder a la plataforma de negociación desde la app móvil.",
            "Allemand": "Wie hoch sind die steuerlichen Gebühren für diesen Aktienverkauf?",
            "Chinois": "我想查询我昨天的转账记录是否成功。"
        }
    },
    "Santé & Support Médical": {
        "categories": [
            "Prise de Rendez-vous & Annulation",
            "Demande d'Ordonnance & Renouvellement",
            "Symptômes & Orientation Médicale",
            "Facturation & Prise en Charge Mutuelle",
            "Assistance Technique Plateforme"
        ],
        "examples": {
            "Français": "Bonjour, je voudrais annuler mon rendez-vous de demain avec le Dr Martin.",
            "Anglais": "Can I get a renewal for my asthma prescription?",
            "Espagnol": "Tengo dolor de cabeza fuerte y fiebre desde ayer por la noche.",
            "Allemand": "Übernimmt die Krankenkasse die Kosten für diese Untersuchung?",
            "Italien": "Impossibile prenotare una visita sull'applicazione."
        }
    },
    "E-Commerce & Service Client": {
        "categories": [
            "Suivi de Commande & Livraison",
            "Retour & Remboursement",
            "Information Produit & Stock",
            "Problème de Paiement",
            "Réclamation & Avis"
        ],
        "examples": {
            "Espagnol": "Mi paquete no ha llegado y la fecha de entrega ya pasó.",
            "Français": "Je souhaite retourner cet article qui est trop petit et obtenir un remboursement.",
            "Anglais": "My credit card was charged twice for the same purchase.",
            "Allemand": "Ist diese Jacke auch in der Größe L wieder lieferbar?",
            "Portugais": "O produto chegou danificado e com a embalagem aberta."
        }
    },
    "Personnalisé": {
        "categories": [
            "Urgent / Action Requise",
            "Question Générale",
            "Support Technique",
            "Feedback / Suggestion"
        ],
        "examples": {
            "Français": "Problème majeur : l'application crash à chaque tentative de connexion !",
            "Anglais": "How can I update my profile personal information?",
            "Espagnol": "Sugerencia: sería genial añadir un modo oscuro a la interfaz."
        }
    }
}

# --- Sidebar : Configuration & Taxonomie ---
st.sidebar.title("⚙️ Configuration MLOps")
domain = st.sidebar.selectbox("Cas d'usage Métier :", list(DOMAIN_DATA.keys()))

selected_categories_text = st.sidebar.text_area(
    "Catégories à classifier :",
    value="\n".join(DOMAIN_DATA[domain]["categories"]),
    height=180
)

categories = [cat.strip() for cat in selected_categories_text.split("\n") if cat.strip()]

@st.cache_data
def get_category_embeddings(_model, categories_tuple):
    return _model.encode(list(categories_tuple), convert_to_tensor=True)

category_embeddings = get_category_embeddings(model, tuple(categories))

# --- Header & Vision Produit / MLOps ---
st.title("⚡ StreamChat NLP Hub")

st.markdown("""
> **À quoi sert cette application ?**
> 
> Cette plateforme permet de **catégoriser automatiquement les messages clients** (support, réclamations, questions) dans plus de 50 langues, afin d'envoyer chaque demande directement à la bonne équipe.
> 
> * **Inférence légère sur CPU :** Utilise un modèle compact et optimisé. C'est une alternative sobre, rapide et économique au recours systématique à des LLMs payants (comme GPT-4).
> * **Catégories modifiables à la volée :** La liste des catégories dans la barre de gauche peut être personnalisée à tout moment sans aucun ré-entraînement du modèle.
> * **Deux modes d'utilisation :** 
>   1. **En temps réel :** Pour trier les messages dès qu'ils arrivent sur un chat ou un formulaire.
>   2. **Par lot (Batch) :** Pour traiter et nettoyer des fichiers de données historiques avec **dbt / DuckDB**.
""")

st.divider()

# --- Mode d'utilisation (Onglets) ---
tab1, tab2 = st.tabs(["💬 Test Temps Réel (Single Message)", "📁 Traitement Batch (Import CSV)"])

# --- TAB 1 : Single Message ---
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Message entrant")
        
        # Exemples adaptés spécifiquement au domaine sélectionné
        domain_examples = DOMAIN_DATA[domain]["examples"]
        selected_sample = st.selectbox(
            "Exemples multilingues pour ce domaine :", 
            ["-- Saisir un texte libre --"] + [f"{langue} : {texte[:45]}..." for langue, texte in domain_examples.items()]
        )
        
        if selected_sample != "-- Saisir un texte libre --":
            langue_key = selected_sample.split(" : ")[0]
            default_text = domain_examples[langue_key]
        else:
            default_text = ""
            
        user_input = st.text_area("Saisie du message :", value=default_text, height=110, placeholder="Tapez un message dans n'importe quelle langue...")
        
        btn_run = st.button("Pousser au pipeline 🚀", type="primary", use_container_width=True)

    with col2:
        st.subheader("Résultats d'Inférence")
        if btn_run and user_input.strip():
            msg_emb = model.encode(user_input, convert_to_tensor=True)
            scores = util.cos_sim(msg_emb, category_embeddings)[0]
            
            best_idx = scores.argmax().item()
            
            # Affichage direct du score de confiance et du résultat
            st.metric("Score de Confiance", f"{float(scores[best_idx]):.1%}")
            st.success(f"**Catégorie attribuée :** {categories[best_idx]}")
            
            df_res = pd.DataFrame({"Catégorie": categories, "Score de similarité": [float(s) for s in scores]}).sort_values("Score de similarité", ascending=False)
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        elif btn_run:
            st.warning("Veuillez saisir un message.")

# --- TAB 2 : Batch Processing CSV ---
with tab2:
    st.subheader("Importation & Traitement Batch (dbt / Engine)")
    st.markdown("Téléversez un fichier CSV de volumétrie historique pour classifier automatiquement l'ensemble des messages.")
    
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    
    if uploaded_file is not None:
        df_batch = pd.read_csv(uploaded_file)
        st.write("Aperçu des données reçues :", df_batch.head(3))
        
        text_column = st.selectbox("Sélectionner la colonne contenant le texte :", df_batch.columns)
        
        if st.button("Lancer la classification Batch ⚙️", type="primary"):
            t_start = time.perf_counter()
            
            texts = df_batch[text_column].astype(str).tolist()
            embeddings = model.encode(texts, convert_to_tensor=True, batch_size=32)
            
            cos_sim_matrix = util.cos_sim(embeddings, category_embeddings)
            
            best_indices = cos_sim_matrix.argmax(dim=1).tolist()
            best_scores = [float(cos_sim_matrix[i][best_indices[i]]) for i in range(len(texts))]
            
            df_batch["predicted_category"] = [categories[idx] for idx in best_indices]
            df_batch["confidence_score"] = [round(s, 3) for s in best_scores]
            
            total_time = time.perf_counter() - t_start
            st.success(f"✅ {len(df_batch)} messages classés en {total_time:.2f} secondes ({total_time/len(df_batch)*1000:.1f} ms/msg).")
            
            st.dataframe(df_batch, use_container_width=True)
            
            csv_buffer = io.StringIO()
            df_batch.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Télécharger le CSV enrichi",
                data=csv_buffer.getvalue(),
                file_name="classified_batch_results.csv",
                mime="text/csv"
            )