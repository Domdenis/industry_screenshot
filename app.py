# -*- coding: utf-8 -*-
"""
Wrapper d'encodage UTF-8 pour Streamlit Cloud
Force l'encodage UTF-8 sans dépendre des scripts shell
"""

import sys
import io
import os

# Force UTF-8 encoding globally
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set environment variable
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Now import Streamlit AFTER setting encoding
import streamlit as st

st.set_page_config(
    page_title="Suite d'Outils",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "app_mode" not in st.session_state:
    st.session_state.app_mode = None

st.sidebar.title("Suite d'Outils")
st.sidebar.divider()

mode = st.sidebar.radio(
    "Selectionnez un outil :",
    options=["Accueil", "Captures d'ecran", "Recadrage d'images"],
    key="app_selector"
)

st.sidebar.divider()
st.sidebar.markdown("""
**A propos:**
- **Captures d'ecran**: Capture automatique de pages web
- **Recadrage d'images**: Recadrer et nettoyer des images PNG
""")

# ============================================================
# PAGE D'ACCUEIL
# ============================================================
if mode == "Accueil":
    st.title("Suite d'Outils Streamlit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Captures d'ecran automatiques
        
        Cet outil permet de :
        - Decouvrir automatiquement les pages d'un site
        - Se connecter et capturer des pages
        - Gerer automatiquement les fenetres de consentement
        - Telecharger toutes les captures en ZIP
        
        **Cliquez sur "Captures d'ecran" dans la barre laterale.**
        """)
    
    with col2:
        st.markdown("""
        ### Recadrage et suppression d'images
        
        Cet outil permet de :
        - Recadrer vos images PNG interactivement
        - Supprimer des zones horizontales
        - Traiter plusieurs images a la fois
        - Generer un rapport Excel
        
        **Cliquez sur "Recadrage d'images" dans la barre laterale.**
        """)
    
    st.divider()
    st.markdown("""
    ### Comment utiliser ?
    
    1. **Selectionnez un outil** dans la barre laterale
    2. **Suivez les etapes** indiquees
    3. **Telechargez les resultats**
    """)

# ============================================================
# OUTIL 1: CAPTURES D'ÉCRAN
# ============================================================
elif mode == "Captures d'ecran":
    try:
        exec(open("pages/1_captures.py").read())
    except FileNotFoundError:
        st.error("Le fichier 'pages/1_captures.py' n'a pas ete trouve.")
        st.info("Assurez-vous que le fichier est dans le dossier 'pages/'")

# ============================================================
# OUTIL 2: RECADRAGE D'IMAGES
# ============================================================
elif mode == "Recadrage d'images":
    try:
        exec(open("pages/2_crop.py").read())
    except FileNotFoundError:
        st.error("Le fichier 'pages/2_crop.py' n'a pas ete trouve.")
        st.info("Assurez-vous que le fichier est dans le dossier 'pages/'")
