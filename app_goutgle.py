import os
import json
import streamlit as st
import openai
import requests
from serpapi import GoogleSearch

# 🌍 Activation de la recherche web (via checkbox)
st.set_page_config(page_title="Goût-gle", page_icon="🍷")
st.markdown("🍷", unsafe_allow_html=True)
st.title("Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords…")

# 🔐 API Keys
env_openai_key = os.getenv("OPENAI_API_KEY")
env_serpapi_key = os.getenv("SERPAPI_KEY")
openai.api_key = env_openai_key

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

# 🌐 Recherche web (SerpAPI)
def search_web(query):
    search = GoogleSearch({
        "q": query,
        "api_key": env_serpapi_key,
        "num": 5,
        "hl": "fr"
    })
    results = search.get_dict()
    passages = []
    if "organic_results" in results:
        for res in results["organic_results"]:
            if "snippet" in res:
                passages.append(res["snippet"])
    return "\n".join(passages[:3])

# 🧠 Initialisation de l'historique
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
    ]

# 🧼 Sidebar reset
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
        ]
        st.rerun()

    use_web = st.checkbox("🔎 Inclure une recherche web", value=False)

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
question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)")
if st.button("Demander à Goût-gle") and question:
    local_context = find_relevant_context(question)
    web_context = search_web(question) if use_web else ""

    prompt = f"""
    Voici une question : {question}
    
    Voici des extraits de documents pour t'aider :
    {local_context}

    Résultats de recherche web récents :
    {web_context}

    Réponds de façon claire, experte et agréable à lire.
    """
    st.session_state.history.append({"role": "user", "content": question})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            response = openai.completions.create(  # ✅ Utilisation de la nouvelle méthode
                model="gpt-4",
                messages=st.session_state.history + [{"role": "user", "content": prompt}],
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
