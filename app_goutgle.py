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
def search_web(query, force_general=False):
    results = []
    wine_keywords = ["vin", "château", "millésime", "cuvée", "grand cru", "appellation"]

    if any(word in query.lower() for word in wine_keywords) and not force_general:
        # Si c'est probablement un vin, viser Vivino + Wine-Searcher
        sites = ["vivino.com", "wine-searcher.com"]
    else:
        # Sinon, recherche classique sur tout internet
        sites = [""]

    for site in sites:
        search_query = f"{query} site:{site}" if site else query
        search = GoogleSearch({
            "q": search_query,
            "api_key": env_serpapi_key,
            "num": 3,
            "hl": "fr"
        })
        data = search.get_dict()
        if "organic_results" in data:
            for res in data["organic_results"]:
                if "snippet" in res and "link" in res:
                    results.append(f"{res['snippet']}\n🔗 {res['link']}")
    return "\n\n".join(results[:6])


# 🧠 Initialisation de l'historique
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique basé en Suisse. Tu privilégies les sources locales (.ch), donnes les prix en CHF, et fournis les URLs quand tu trouves des références. Donne des réponses précises, agréables et claires."}
    ]

if "questions_a_poser" not in st.session_state:
    st.session_state.questions_a_poser = []

if "reponses_questions" not in st.session_state:
    st.session_state.reponses_questions = {}

if "generer_reponse" not in st.session_state:
    st.session_state.generer_reponse = False



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

if st.session_state.questions_a_poser:
    st.markdown("### 🛠️ Merci de compléter :")
    for idx, question_text in enumerate(st.session_state.questions_a_poser):
        response = st.text_input(question_text, key=f"question_{idx}")
        st.session_state.reponses_questions[idx] = response

    if st.button("📜 Générer la fiche complète"):
        st.session_state.generer_reponse = True
else:
    st.session_state.generer_reponse = False


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

    st.session_state.messages = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique basé en Suisse, ultra rigoureux."},
        {"role": "user", "content": f"Question : {question}\n\nContexte interne : {local_context}\n\nContexte web : {web_context}"}
    ]

    infos_detectees = []

    # 🖼️ Analyse image seulement ici
    if uploaded_image:
        image_bytes = uploaded_image.read()
        mime_type = uploaded_image.type  # Exemple 'image/jpeg' ou 'image/png'
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"

        try:
            vision_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Décris précisément ce que tu vois sur cette image."},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ],
                temperature=0
            )
            infos_detectees = vision_response.choices[0].message.content.strip().lower()

        except Exception as e:
            st.warning(f"❗ Impossible d'analyser l'image : {e}")



        # 🧠 Maintenant générer les questions complémentaires
        questions = []
        if "rouge" not in infos_detectees and "blanc" not in infos_detectees and "rosé" not in infos_detectees:
            questions.append("Peux-tu préciser si c'est un vin rouge, blanc ou rosé ?")

        if "appellation" not in infos_detectees:
            questions.append("Peux-tu préciser l'appellation exacte du vin ?")

        if "degré" not in infos_detectees and "%" not in infos_detectees:
            questions.append("Quel est le degré d'alcool indiqué ?")

        st.session_state.questions_a_poser = questions

                # ⬇️ AJOUTE ICI ce nouveau bloc :
        if not st.session_state.questions_a_poser:
             try:
                 with st.spinner("Goût-gle rédige une réponse initiale... 🍷"):
                     response = client.chat.completions.create(
                         model="gpt-4o",
                         messages=st.session_state.messages,
                         temperature=0.7
                     )
                     answer = response.choices[0].message.content.strip()

                     st.session_state.history.append({"role": "assistant", "content": answer})

           except Exception as e:
               st.error(f"❌ Erreur lors de la réponse initiale : {e}")



with st.spinner("Goût-gle réfléchit à une réponse raffinée... 🍷"):
    if st.session_state.generer_reponse:
        # Ajoutons les réponses utilisateur dans le prompt
        infos_complementaires = "\n".join(
            f"- {st.session_state.reponses_questions[idx]}" for idx in st.session_state.reponses_questions
        )

        # On rajoute les infos complémentaires à notre conversation
        st.session_state.messages.append(
            {"role": "user", "content": f"Voici les précisions utilisateur manquantes :\n{infos_complementaires}\n\nGénère maintenant la fiche complète ultra détaillée."}
        )

        with st.spinner("Goût-gle compile toutes les informations... 🍷"):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages,
                    temperature=0.7
                )
                answer = response.choices[0].message.content.strip()

                st.session_state.history.append({"role": "assistant", "content": answer})
                st.session_state.questions_a_poser = []
                st.session_state.reponses_questions = {}
                st.session_state.generer_reponse = False

                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la réponse complète : {e}")





st.markdown("</div>", unsafe_allow_html=True)

# 🧼 Sidebar reset
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique basé en Suisse. Tu privilégies les sources locales (.ch), donnes les prix en CHF, et fournis les URLs quand tu trouves des références. Donne des réponses précises, agréables et claires."}
        ]
        st.rerun()
