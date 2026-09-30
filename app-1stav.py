import json
import re
import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Quiz Automatismes - Calcul & Algèbre", layout="wide")

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
    s = saisie_eleve.lower().replace(" ", "")
    s = s.replace("*", "").replace("x", "x")
    s = re.sub(r'\)\w\(', ')(', s)

    reponses_valides = [
        "(4x+3)(4x-3)",
        "(4x-3)(4x+3)"
    ]
    return s in reponses_valides

# ---------------------------------------------------------
# STOCKAGE CENTRALISÉ (PARTAGÉ ENTRE TOUS LES APPAREILS)
# ---------------------------------------------------------
@st.cache_resource
def get_global_database():
    return {
        "scores": {},        # {pseudo: score_total}
        "responses": {},     # {pseudo: {q_id: rep}}
        "notes_cours": {},   # {pseudo: note_cours}
        "show_correction": False
    }

db = get_global_database()

# Fragment qui boucle toutes les 2s tant que la correction n'est pas activée
@st.fragment(run_every=2)
def waiting_screen_fragment():
    if db["show_correction"]:
        st.rerun()
    else:
        st.info("En attente du lancement de la correction par l'enseignant...")

# Barre latérale : Commutateur Vue Élève / Vue Enseignant
mode = st.sidebar.radio("Mode d'affichage", ["Smartphone Élève", "Écran Projeté (Classement)"])

# ---------------------------------------------------------
# MODE 1 : INTERFACE SMARTPHONE ÉLÈVE
# ---------------------------------------------------------
if mode == "Smartphone Élève":
    st.title("Quiz Automatismes - Calcul & Algèbre")
    
    already_submitted = st.session_state.get("submitted_pseudo", None)
    
    # Si le classement a été réinitialisé par l'enseignant, on débloque l'élève
    if already_submitted and already_submitted not in db["scores"]:
        st.session_state.submitted_pseudo = None
        st.session_state.etape = "quiz"
        st.session_state.compteur_tentatives = 0
        already_submitted = None

    # Initialisation des variables de session pour la navigation
    if "etape" not in st.session_state:
        st.session_state.etape = "quiz"
    if "compteur_tentatives" not in st.session_state:
        st.session_state.compteur_tentatives = 0

    # CAS 1 : LA CORRECTION EST ACTIVÉE PAR L'ENSEIGNANT
    if db["show_correction"]:
        st.header("Correction détaillée")
        
        if already_submitted and already_submitted in db["responses"]:
            score_eleve = db["scores"][already_submitted]
            st.success(f"Note finale pour **{already_submitted}** : **{score_eleve} / {len(QUESTIONS)}**")
            st.divider()
            
            user_res = db["responses"][already_submitted]
            
            for q in QUESTIONS:
                st.markdown(f"### Question {q['id']}")
                st.write(f"**{q['enonce']}**")
                
                rep_eleve = user_res.get(q["id"], "Aucune réponse")
                est_correct = False
                
                if q["type"] == "qcm":
                    est_correct = (rep_eleve == q["rep_correcte"])
                    vrai_txt = q["rep_correcte"]
                else:
                    est_correct = verifier_factorisation_16x2_9(rep_eleve)
                    vrai_txt = "(4x + 3)(4x - 3)"
                
                col1, col2 = st.columns(2)
                col1.metric("Ta réponse", str(rep_eleve))
                col2.metric("Réponse attendue", vrai_txt)
                
                if est_correct:
                    st.caption("Correct (+1 pt)")
                else:
                    st.caption("Incorrect (0 pt)")
                    
                st.divider()
        else:
            st.info("La correction est affichée au tableau. Vous n'avez pas soumis de réponses pour cette session.")

    # CAS 2 : ÉLÈVE AYANT DÉJÀ SOUMIS (EN ATTENTE DE CORRECTION)
    elif already_submitted and already_submitted in db["scores"]:
        st.success(f"Réponses enregistrées pour **{already_submitted}** !")
        st.info("Merci pour l'évaluation ! Tes réponses ont bien été transmises. La correction s'affichera dès que le professeur l'aura lancée au tableau.")
        
        waiting_screen_fragment()

    # CAS 3 : ÉTAPE 2 - ÉVALUATION DU COURS (3 ESSAIS MAX PUIS LOCK)
    elif st.session_state.etape == "note_cours":
        st.subheader("Évaluation du cours")
        st.write("Avant de valider, donne une note à la séance d'aujourd'hui :")

        # Callback déclenché dès que l'élève relâche le slider
        def forcer_dix_et_compter():
            st.session_state.note_slider = 10
            st.session_state.compteur_tentatives += 1

        if "note_slider" not in st.session_state:
            st.session_state.note_slider = 5

        # Verrouillage si 3 essais ont été faits
        est_verrouille = st.session_state.compteur_tentatives >= 3

        note = st.slider(
            "Note sur 10 :", 
            min_value=0, 
            max_value=10, 
            key="note_slider",
            disabled=est_verrouille,
            on_change=forcer_dix_et_compter
        )

        if est_verrouille:
            st.caption("Eh bien, quel honneur !")
        elif note == 10:
            if st.session_state.compteur_tentatives == 2:
                st.caption("Non, vraiment, merci beaucoup, ça me touche énormément !")
            else:
                st.caption("Merci pour ce 10/10 parfait !")

        if st.button("Envoyer mes réponses", type="primary", use_container_width=True):
            pseudo_clean = st.session_state.temp_pseudo
            db["scores"][pseudo_clean] = st.session_state.temp_score
            db["responses"][pseudo_clean] = st.session_state.temp_answers
            db["notes_cours"][pseudo_clean] = note
            st.session_state.submitted_pseudo = pseudo_clean
            st.rerun()

    # CAS 4 : ÉTAPE 1 - SAISIE DU QUIZ
    else:
        pseudo = st.text_input("Entre ton prénom et la première lettre de nom si besoin (si jamais tu ne veux pas, écris anonyme et le nombre de ton choix):", key="user_pseudo")
        
        if pseudo:
            pseudo_clean = pseudo.strip()
            
            if pseudo_clean in db["scores"]:
                st.warning(f"**{pseudo_clean}** a déjà envoyé ses réponses.")
            else:
                st.subheader(f"Bonjour {pseudo_clean} !")
                st.write("Réponds aux questions sans calculatrice :")
                
                user_answers = {}
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
                        user_answers[q["id"]] = st.text_input(
                            "Ta réponse :",
                            key=f"q_{q['id']}"
                        )
                    st.divider()
                
                if st.button("Suivant", type="primary", use_container_width=True):
                    score_total = 0
                    for q in QUESTIONS:
                        rep = user_answers.get(q["id"])
                        if q["type"] == "qcm" and rep == q["rep_correcte"]:
                            score_total += 1
                        elif q["type"] == "ouverte" and verifier_factorisation_16x2_9(rep):
                            score_total += 1
                    
                    st.session_state.temp_pseudo = pseudo_clean
                    st.session_state.temp_score = score_total
                    st.session_state.temp_answers = user_answers
                    st.session_state.etape = "note_cours"
                    st.session_state.compteur_tentatives = 0
                    st.rerun()

# ---------------------------------------------------------
# MODE 2 : ÉCRAN PROJETÉ (VIDÉOPROJECTEUR)
# ---------------------------------------------------------
else:
    st.title("Classement en direct")
    
    # État local d'affichage du classement côté enseignant
    if "reveal_stage" not in st.session_state:
        st.session_state.reveal_stage = 0  # 0: Masqué, 1: 5e, 2: 4e, 3: 3e, 4: 2e, 5: 1er, 6: Tout
    
    if db["scores"]:
        col_note = f"Note (/{len(QUESTIONS)})"
        df_complet = pd.DataFrame(
            list(db["scores"].items()), 
            columns=["Élève", col_note]
        )
        
        # Tri stable : préserve l'ordre d'arrivée exact en cas de notes égales
        df_complet = df_complet.sort_values(by=col_note, ascending=False, kind="stable").reset_index(drop=True)
        df_complet.index += 1
        
        st.write(f"**{len(db['scores'])} élève(s) ont répondu**")

        # LOGIQUE D'AFFICHAGE DU CLASSEMENT DYNAMIQUE
        stage = st.session_state.reveal_stage
        
        if stage == 0:
            st.warning("Classement masqué. Cliquez sur les boutons ci-dessous pour lancer la révélation.")
        else:
            if stage == 6:
                st.subheader("Classement complet")
                st.dataframe(df_complet, use_container_width=True, height=350)
            else:
                st.subheader("Top 5 en cours de révélation...")
                
                # Progression de la 5e à la 1re place
                indices_a_montrer = [5 - i - 1 for i in range(stage)]
                
                for idx in indices_a_montrer:
                    if idx < len(df_complet):
                        row = df_complet.iloc[idx]
                        rang = idx + 1
                        st.markdown(f"### Rang #{rang} : **{row['Élève']}** — `{row[col_note]}/{len(QUESTIONS)} pts`")
                    st.divider()

        # CONTRÔLES DE RÉVÉLATION DU CLASSEMENT
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if stage < 5:
                prochain_rang = 5 - stage
                if st.button(f"Révéler la {prochain_rang}e place"):
                    st.session_state.reveal_stage += 1
                    st.rerun()
            elif stage == 5:
                st.success("Top 5 totalement révélé !")

        with c2:
            if st.button("Afficher TOUT le classement"):
                st.session_state.reveal_stage = 6
                st.rerun()

        with c3:
            if st.button("Masquer le classement"):
                st.session_state.reveal_stage = 0
                st.rerun()

    else:
        st.info("En attente des premières réponses des élèves...")
    
    st.divider()
    
    # BOUTONS GÉNÉRAUX ENSEIGNANT
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Rafraîchir les données"):
            st.rerun()
    with col2:
        btn_label = "Masquer la correction" if db["show_correction"] else "Afficher la correction"
        if st.button(btn_label, type="primary"):
            db["show_correction"] = not db["show_correction"]
            st.rerun()
    with col3:
        if st.button("Réinitialiser la session"):
            db["scores"].clear()
            db["responses"].clear()
            db["notes_cours"].clear()
            db["show_correction"] = False
            st.session_state.reveal_stage = 0
            st.rerun()

    # SECTION CORRECTION AU TABLEAU & MOYENNE DU COURS
    if db["show_correction"]:
        st.divider()
        st.subheader("Synthèse & Correction générale")
        
        # Affichage de la moyenne accordée au cours par les élèves
        if db["notes_cours"]:
            notes_list = list(db["notes_cours"].values())
            moyenne_cours = sum(notes_list) / len(notes_list)
            st.metric("Appréciation moyenne du cours par la classe", f"{moyenne_cours:.1f} / 10")
            st.divider()

        if db["responses"]:
            nb_eleves = len(db["responses"])
            
            for q in QUESTIONS:
                st.markdown(f"#### Question {q['id']} : {q['enonce']}")
                
                nb_reussite = 0
                for user_resp in db["responses"].values():
                    rep = user_resp.get(q["id"])
                    if q["type"] == "qcm" and rep == q["rep_correcte"]:
                        nb_reussite += 1
                    elif q["type"] == "ouverte" and verifier_factorisation_16x2_9(rep):
                        nb_reussite += 1
                
                pct = int((nb_reussite / nb_eleves) * 100) if nb_eleves > 0 else 0
                st.progress(pct / 100, text=f"Taux de réussite : {pct}% ({nb_reussite}/{nb_eleves})")
                
                if q["type"] == "qcm":
                    st.caption(f"Réponse attendue : **{q['rep_correcte']}**")
                else:
                    st.caption("Réponse attendue : **(4x + 3)(4x - 3)**")
                st.divider()
        else:
            st.info("Aucune réponse enregistrée pour afficher la synthèse.")