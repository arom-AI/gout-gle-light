import os
import json
import streamlit as st
import openai
import requests
from serpapi import GoogleSearch
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import base64

# 🌍 Activation de la recherche web (via checkbox)
st.set_page_config(page_title="Goût-gle", page_icon="🍷")

# Nouveau Titre propre et stylé
st.markdown(
    """
    <div style='text-align: center; margin-top: -30px; margin-bottom: 30px;'>
        <h1 style='font-size: 3em;'>🍷 Goût-gle – Ton assistant gastronomique</h1>
        <p style='font-size: 1.2em; color: #ccc;'>Pose une question sur le vin, les plats, les accords…</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 🔐 API Keys
env_openai_key = os.getenv("OPENAI_API_KEY")
env_serpapi_key = os.getenv("SERPAPI_KEY")
client = openai.OpenAI(api_key=env_openai_key)

# 📂 Chargement des morceaux de base de données
base = []
for filename in sorted(os.listdir("data")):
    if filename.endswith(".json"):
        with open(os.path.join("data", filename), "r", encoding="utf-8") as f:
            try:
                base += json.load(f)
            except Exception as e:
                st.warning(f"Erreur dans {filename} : {e}")

# 🔎 Recherche contextuelle locale
def find_relevant_context(question):
    question_words = question.lower().split()
    results = []
    for item in base:
        if any(word in item["contenu"].lower() for word in question_words):
            results.append(item["contenu"])
    return "\n".join(results[:3])

# 🌐 Recherche web (SerpAPI) avec liens
def search_web(query):
    search = GoogleSearch({
        "q": query + " site:.ch",
        "api_key": env_serpapi_key,
        "num": 5,
        "hl": "fr"
    })
    results = search.get_dict()
    passages = []
    if "organic_results" in results:
        for res in results["organic_results"]:
            if "snippet" in res and "link" in res:
                passages.append(f"{res['snippet']}\n🔗 {res['link']}")
    return "\n\n".join(passages[:3])

# 🧠 Initialisation de l'historique
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique basé en Suisse. Tu privilégies les sources locales (.ch), donnes les prix en CHF, et fournis les URLs quand tu trouves des références. Donne des réponses précises, agréables et claires."}
    ]

# 💬 Affichage de la conversation
st.markdown("## 💬 Conversation")
for msg in st.session_state.history[1:]:
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div style='background-color:#1f2937; padding:10px; border-radius:10px; margin:10px 0; color:white'>
                <b>👤 Toi :</b><br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(
            f"""
            <div style='background-color:#f3f4f6; padding:10px; border-radius:10px; margin:10px 0; color:black'>
                <b>🍷 Goût-gle :</b><br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)


# 🧾 Entrée utilisateur
st.markdown("---")

# Barre de question
question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)", key="question_input")

# Ligne de boutons : Demander / Internet / Upload
col1, col2, col3 = st.columns([1.5, 1, 0.5])

with col1:
    ask_button = st.button("🚀 Demander à Goût-gle", use_container_width=True)

with col2:
    use_web = st.checkbox("🌐 Internet", key="use_web")

with col3:
    toggle_upload = st.checkbox("➕", key="toggle_upload", label_visibility="collapsed")

uploaded_image = None
if toggle_upload:
    uploaded_image = st.file_uploader("📁 Uploade ton fichier image (.jpg, .jpeg, .png)", type=["jpg", "jpeg", "png"])

if ask_button and question:
    local_context = find_relevant_context(question)
    web_context = search_web(question) if use_web else ""

    messages = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique basé en Suisse. Tu analyses vins, plats et accords."},
        {"role": "user", "content": f"""
Voici la question : {question}

Voici des extraits internes :
{local_context}

Voici des recherches web :
{web_context}

Si une image est jointe, analyse-la pour extraire toute information pertinente.
"""}
    ]

    if uploaded_image:  # <-- À l'intérieur du if ask_button and question
        image_bytes = uploaded_image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        messages.append({
          "role": "user",
          "content": [
              {"type": "text", "text": """Voici une image d'un produit lié au monde de la boisson ou de l'alimentation. Analyse-la attentivement.

Décris précisément ce que tu identifies (bouteille, étiquette, marque, type de boisson, informations visibles).
Base-toi uniquement sur ce que tu vois pour répondre.

Puis, en fonction du produit reconnu, fournis une réponse complète et adaptée :
- S'il s'agit d'un vin :
  - Domaine, cuvée, millésime, mention spéciale
  - Histoire éventuelle du domaine
  - Qualité du millésime
  - Fourchette de prix indicative
  - Accord mets-vins recommandé
  - Profil gustatif attendu
  - Température de service
  - Potentiel de garde

- S'il s'agit d'un spiritueux (whisky, rhum, gin, etc.) :
  - Nom du producteur, gamme, type (single malt, blend, rhum agricole…)
  - Informations sur l’origine
  - Arômes dominants et profil gustatif attendu
  - Degré d’alcool
  - Fourchette de prix
  - Conseils de dégustation (pur, avec glaçons, en cocktail…)

- S'il s'agit d'une bière :
  - Brasserie, nom de la bière
  - Type de bière (IPA, stout, lager, etc.)
  - Profil gustatif et caractéristiques principales
  - Degré d'alcool
  - Accord mets-bière

- S'il s'agit d'un soft drink (soda, jus, eau…) :
  - Marque, type exact de boisson
  - Informations nutritionnelles éventuelles
  - Positionnement du produit (premium, classique, artisanal…)

- Pour tout autre produit :
  - Décris de manière factuelle et complète ce que tu vois
  - Donne des informations utiles si disponibles
  - Ne fais pas d'hypothèses hasardeuses.

Reste clair, structuré et agréable à lire. Utilise si possible des bullet points pour rendre la lecture facile.
"""},

              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}

          ]
       })


    with st.spinner("Goût-gle réfléchit à une réponse raffinée... 🍷"):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

st.markdown("</div>", unsafe_allow_html=True)

# 🧼 Sidebar reset
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique basé en Suisse. Tu privilégies les sources locales (.ch), donnes les prix en CHF, et fournis les URLs quand tu trouves des références. Donne des réponses précises, agréables et claires."}
        ]
        st.rerun()
