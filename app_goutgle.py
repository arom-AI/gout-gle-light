import os
import json
import streamlit as st
import requests
from serpapi import GoogleSearch
from openai import OpenAI

# 📌 Client OpenAI moderne
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
serpapi_key = os.getenv("SERPAPI_KEY")

st.set_page_config(page_title="Goût-gle", page_icon="🍷")
st.markdown("🍷", unsafe_allow_html=True)
st.title("Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords…")

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

# 🔎 Recherche web (SerpAPI)
def search_web(query):
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": serpapi_key,
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
    except Exception as e:
        return f"Erreur SerpAPI : {e}"

# 🧠 Initialisation conversation
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
        st.markdown(f"<div style='background-color:#1f2937; padding:10px; border-radius:10px; margin:10px 0; color:white'><b>👤 Toi :</b><br>{msg['content']}</div>", unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f"<div style='background-color:#f3f4f6; padding:10px; border-radius:10px; margin:10px 0; color:black'><b>🍷 Goût-gle :</b><br>{msg['content']}</div>", unsafe_allow_html=True)

# 🧾 Entrée utilisateur
question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)")
if st.button("Demander à Goût-gle") and question:
    st.session_state.history.append({"role": "user", "content": question})
    local_context = find_relevant_context(question)
    web_context = search_web(question) if use_web else ""

    if local_context:
        st.session_state.history.append({"role": "system", "content": f"📀 Infos extraites de la base :\n{local_context}"})
    if web_context:
        st.session_state.history.append({"role": "system", "content": f"📜 Infos trouvées sur Internet :\n{web_context}"})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=st.session_state.history
            )
            reponse = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": reponse})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
