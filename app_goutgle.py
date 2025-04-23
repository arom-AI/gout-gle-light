import os
import json
import streamlit as st
from openai import OpenAI

# 👉 Assure-toi que ta clé API est bien dans les variables d'env
# ou définis-la ici temporairement (pas en prod)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Chargement de la base de connaissances
with open("database.json", "r", encoding="utf-8") as f:
    base = json.load(f)

# Fonction de recherche simple (par mots-clés)
def find_relevant_context(question):
    question_words = question.lower().split()
    results = []
    for item in base:
        if any(word in item["contenu"].lower() for word in question_words):
            results.append(item["contenu"])
    return "\n".join(results[:3])  # On limite à 3 extraits max

# Fonction d’appel à l’API OpenAI
def ask_goutgle(question):
    contexte = find_relevant_context(question)
    prompt = f"""Tu es Goût-gle, un expert en cuisine, sommellerie et gastronomie.
Voici une question : {question}
Voici des extraits de documents pour t'aider :
{contexte}

Réponds de manière claire, experte et agréable à lire.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es Goût-gle, un expert gastronomique."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Interface Streamlit
st.set_page_config(page_title="Goût-gle", page_icon="🍷")
st.title("🍷 Goût-gle – Ton assistant gastronomique")
st.markdown("Pose une question sur le vin, les plats, les accords…")

question = st.text_input("❓ Ta question (ex : Quel vin avec une raclette ?)")

if st.button("Demander à Goût-gle") and question:
    with st.spinner("Goût-gle réfléchit à une réponse raffinée..."):
        try:
            reponse = ask_goutgle(question)
            st.markdown(f"### ✅ Réponse de Goût-gle\n{reponse}")
        except Exception as e:
            st.error(f"❌ Une erreur est survenue : {e}")
