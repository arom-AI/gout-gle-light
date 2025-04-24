import os
import json
import streamlit as st
import openai
import requests

# Config Streamlit
st.set_page_config(page_title="Goût-gle", page_icon="🍷")
st.title("🍷 Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords…")

# API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
serpapi_key = os.getenv("SERPAPI_KEY")

# Chargement des fichiers JSON découpés
def load_data():
    data = []
    for filename in sorted(os.listdir("data")):
        if filename.endswith(".json") and filename.startswith("part_"):
            try:
                with open(os.path.join("data", filename), "r", encoding="utf-8") as f:
                    part = json.load(f)
                    data.extend(part)
            except Exception as e:
                st.warning(f"Erreur dans {filename} : {e}")
    return data

base = load_data()

# Recherche dans la base de connaissances
def find_relevant_context(question):
    question_words = question.lower().split()
    results = []
    for item in base:
        if any(word in item["contenu"].lower() for word in question_words):
            results.append(item["contenu"])
    return "\n".join(results[:3])

# Recherche via SerpAPI
def search_web_with_serpapi(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": serpapi_key,
        "hl": "fr",
        "gl": "fr"
    }
    try:
        res = requests.get("https://serpapi.com/search", params=params)
        results = res.json()
        snippets = []
        for r in results.get("organic_results", []):
            if "snippet" in r:
                snippets.append(r["snippet"])
        return "\n".join(snippets[:3])
    except Exception as e:
        return f"(Erreur SerpAPI : {e})"

# Mémorisation historique
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
    ]

# Sidebar : reset
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
        ]
        st.rerun()

    use_web = st.checkbox("🔎 Inclure une recherche web", value=False)

# Affichage de la conversation
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

# Entrée utilisateur
question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)")
if st.button("Demander à Goût-gle") and question:
    contexte = find_relevant_context(question)
    web_data = search_web_with_serpapi(question) if use_web and serpapi_key else ""
    full_context = f"{contexte}\n\n🔍 Infos web :\n{web_data}" if web_data else contexte

    st.session_state.history.append({"role": "user", "content": question})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=st.session_state.history + [
                    {"role": "user", "content": f"Voici des extraits de documents pour t'aider :\n{full_context}"}
                ],
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
