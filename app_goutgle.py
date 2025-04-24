import os
import json
import streamlit as st
import openai  # ✅ CORRECT

# Clé API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration Streamlit
st.set_page_config(page_title="Goût-gle", page_icon="🍷")
st.title("🍷 Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords…")

# Chargement base de données
with open("database.json", "r", encoding="utf-8") as f:
    base = json.load(f)

# Recherche contextuelle dans la base
def find_relevant_context(question):
    question_words = question.lower().split()
    results = []
    for item in base:
        if any(word in item["contenu"].lower() for word in question_words):
            results.append(item["contenu"])
    return "\n".join(results[:3])

# Initialisation mémoire conversation
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
    ]

# Bouton réinitialiser la conversation
with st.sidebar:
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.history = [
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."}
        ]
        st.rerun()  # ✅ mis à jour

# Affichage conversation en bulles
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
    prompt = f"""Voici une question : {question}
Voici des extraits de documents pour t'aider :
{contexte}"""

    st.session_state.history.append({"role": "user", "content": question})

    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            response = openai.chat.completions.create(  # ✅ nouvelle API
                model="gpt-4",
                messages=st.session_state.history,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            st.rerun()  # ✅ mis à jour
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
