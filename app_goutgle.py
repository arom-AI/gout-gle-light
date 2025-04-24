import os
import json
import glob
import streamlit as st
import openai

# Config OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Config Streamlit
st.set_page_config(page_title="Goût-gle", page_icon="🍷")
st.title("🍷 Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords…")

# Chargement de tous les fichiers découpés
base = []
for file in sorted(glob.glob("data/part_*.json")):
    with open(file, "r", encoding="utf-8") as f:
        try:
            base.extend(json.load(f))
        except Exception as e:
            st.warning(f"Erreur dans {file} : {e}")

# Recherche contextuelle
def find_relevant_context(question):
    question_words = question.lower().split()
    results = []
    for item in base:
        if any(word in item["contenu"].lower() for word in question_words):
            results.append(item["contenu"])
    return "\n".join(results[:3])

# Historique conversation
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
    ]

# Sidebar : réinitialisation
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
        ]
        st.rerun()

# Affichage conversation
st.markdown("## 💬 Conversation")
for msg in st.session_state.history[1:]:
    style = "background-color:#1f2937; color:white" if msg["role"] == "user" else "background-color:#f3f4f6; color:black"
    icon = "👤 Toi :" if msg["role"] == "user" else "🍷 Goût-gle :"
    st.markdown(
        f"<div style='{style}; padding:10px; border-radius:10px; margin:10px 0'><b>{icon}</b><br>{msg['content']}</div>",
        unsafe_allow_html=True
    )

# Champ de saisie
question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)")
if st.button("Demander à Goût-gle") and question:
    contexte = find_relevant_context(question)
    st.session_state.history.append({"role": "user", "content": question})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.history,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
