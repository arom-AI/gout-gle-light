import os
import json
import streamlit as st
import openai
import requests
from serpapi import GoogleSearch
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

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

# Si toggle activé ➡️ afficher le file uploader
uploaded_content = ""
if toggle_upload:
    uploaded_file = st.file_uploader("📁 Uploade ton fichier (.txt, .pdf, .jpg, .png)", type=["txt", "pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        if file_extension == "txt":
            uploaded_content = uploaded_file.read().decode("utf-8")
        elif file_extension == "pdf":
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                uploaded_content += page.extract_text()
        elif file_extension in ["jpg", "jpeg", "png"]:
            image = Image.open(uploaded_file)
            try:
                uploaded_content = pytesseract.image_to_string(image, lang="eng+fra")
            except pytesseract.TesseractNotFoundError:
                st.error("❌ Tesseract OCR n'est pas installé correctement.")
            except pytesseract.TesseractError:
           # Si la langue fra n'est pas installée, fallback en anglais seulement
                uploaded_content = pytesseract.image_to_string(image, lang="eng")

   

        else:
            st.warning("❗ Format de fichier non supporté pour l'instant.")

# Quand on clique sur Demander à Goût-gle
if ask_button and question:
    local_context = find_relevant_context(question)
    web_context = search_web(question) if use_web else ""

prompt = f"""
Voici la question de l'utilisateur : {question}

Utilise toutes les informations suivantes pour répondre :

- 📚 Documents internes pertinents :
{local_context}

- 🌍 Résultats web récents :
{web_context}

- 🖼️ Texte extrait de l'image ou du fichier uploadé :
{uploaded_content}

Si du texte est disponible depuis l'image ou le fichier, analyse-le et utilise-le en priorité pour ta réponse. Sinon, utilise les autres sources. Réponds de manière experte, détaillée et agréable à lire.
"""

    st.session_state.history.append({"role": "user", "content": question})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée... 🍷"):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.history + [{"role": "user", "content": prompt}],
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
