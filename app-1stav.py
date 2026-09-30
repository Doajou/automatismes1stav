import json
import re
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Quiz Automatismes", page_icon="⚡", layout="centered")

# Chargement des questions
@st.cache_data
def charger_questions():
    with open("questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

QUESTIONS = charger_questions()

# Fonction de nettoyage et vérification pour la question ouverte (Item 16)
def verifier_factorisation_16x2_9(saisie_eleve):
    if not saisie_eleve:
        return False
    # Nettoyage : minuscules, suppression des espaces
    s = saisie_eleve.lower().replace(" ", "")
    # Remplacement des symboles de multiplication
    s = s.replace("*", "").replace("x", "x")
    # Suppression d'un 'x' isolé entre deux parenthèses ex: (4x+3)x(4x-3) -> (4x+3)(4x-3)
    s = re.sub(r'\)\w\(', ')(', s)

    reponses_valides = [
        "(4x+3)(4x-3)",
        "(4x-3)(4x+3)"
    ]
    return s in reponses_valides

# Titre
st.title("⚡ Quiz Automatismes - Calcul & Algèbre")
st.write("Réponds aux 5 questions ci-dessous sans calculatrice.")
st.divider()

# Gestion de la soumission avec st.session_state
if "soumis" not in st.session_state:
    st.session_state.soumis = False

user_answers = {}

# Formulaire pour éviter le rechargement à chaque clic
with st.form("quiz_form"):
    for q in QUESTIONS:
        st.markdown(f"### Question {q['id']}")
        st.write(f"**{q['enonce']}**")
        
        if q["type"] == "qcm":
            user_answers[q["id"]] = st.radio(
                "Choisis la bonne réponse :",
                options=q["options"],
                key=f"q_{q['id']}",
                index=None
            )
        elif q["type"] == "ouverte":
            if "explication" in q:
                st.caption(q["explication"])
            user_answers[q["id"]] = st.text_input(
                "Ta réponse :",
                key=f"q_{q['id']}",
                placeholder="Ex : (4x+3)(4x-3)"
            )
            
        st.divider()

    btn_valider = st.form_submit_button("Valider mes réponses 🚀", use_container_width=True)

# Traitement après validation
if btn_valider:
    st.session_state.soumis = True

if st.session_state.soumis:
    score = 0
    st.header("📊 Résultats")
    
    for q in QUESTIONS:
        rep = user_answers.get(q["id"])
        est_correct = False
        
        if q["type"] == "qcm":
            if rep == q["rep_correcte"]:
                est_correct = True
                score += 1
            st.write(f"**Question {q['id']} :** {'✅ Correct' if est_correct else '❌ Incorrect'}")
            if not est_correct:
                st.caption(f"La bonne réponse était : **{q['rep_correcte']}**")
                
        elif q["type"] == "ouverte":
            if verifier_factorisation_16x2_9(rep):
                est_correct = True
                score += 1
            st.write(f"**Question {q['id']} :** {'✅ Correct' if est_correct else '❌ Incorrect'}")
            if not est_correct:
                st.caption("Formes attendues : **(4x + 3)(4x - 3)** ou **(4x - 3)(4x + 3)**")

    st.subheader(f"Score final : {score} / {len(QUESTIONS)}")
    if score == len(QUESTIONS):
        st.balloons()