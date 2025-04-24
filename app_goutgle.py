import os
import json
import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch

# 🔑 Clés API (via secrets)
openai_api_key = os.getenv("OPENAI_API_KEY")
serpapi_api_key = os.getenv("SERPAPI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# 🕹️ Config Streamlit
st.set_page_config(page_title="Goût-gle", page_icon="🍇")
st.title("\ud83c\udf47 Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords...")

# 📲 Option recherche web
use_web = st.sidebar.checkbox("🔍 Inclure une recherche web")

# 📂 Chargement des morceaux JSON
def load_chunks():
    data = []
    for filename in sorted(os.listdir("data")):
        if filename.endswith(".json"):
            with open(os.path.join("data", filename), "r", encoding="utf-8") as f:
                try:
                    data.extend(json.load(f))
                except Exception as e:
                    st.warning(f"Erreur dans {filename} : {e}")
    return data

chunks = load_chunks()

# 🔢 Recherche dans la base
def find_relevant_context(question):
    words = question.lower().split()
    results = [item["contenu"] for item in chunks if any(w in item["contenu"].lower() for w in words)]
    return "\n".join(results[:3])

# 🔎 Recherche web (SerpAPI)
def get_web_results(query):
    search = GoogleSearch({"q": query, "api_key": serpapi_api_key})
    results = search.get_dict()
    if "error" in results:
        return f"[Erreur SerpAPI] {results['error']}"
    organic = results.get("organic_results", [])
    return "\n".join([r.get("snippet", "") for r in organic[:3]])

# 🔍 Mémoire conversation
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
    ]

# 📅 Reset
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
        ]
        st.rerun()

# 🎨 Affichage des messages
st.markdown("## 🤝 Conversation")
for msg in st.session_state.history[1:]:
    if msg["role"] == "user":
        st.markdown(
            f"""
            <div style='background-color:#1f2937; padding:10px; border-radius:10px; color:white;'>
                <b>👤 Toi :</b><br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(
            f"""
            <div style='background-color:#f3f4f6; padding:10px; border-radius:10px; color:black;'>
                <b>🍇 Goût-gle :</b><br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)

# 📃 Entrée utilisateur
question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)")
if st.button("Demander à Goût-gle") and question:
    contexte = find_relevant_context(question)
    web_snippets = get_web_results(question) if use_web and serpapi_api_key else ""

    prompt = f"Voici une question : {question}\n\n"
    if contexte:
        prompt += f"Voici des extraits de documents :\n{contexte}\n\n"
    if web_snippets:
        prompt += f"Voici des résultats web récents :\n{web_snippets}\n\n"
    prompt += "Réponds avec expertise, clarté et un style agréable."

    st.session_state.history.append({"role": "user", "content": question})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.history,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
