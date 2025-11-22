# -*- coding: utf-8 -*-
"""
Captures d'écran Streamlit - Compatible Streamlit Cloud
Détecte l'environnement et désactive Selenium si nécessaire
"""

import os
import sys
import streamlit as st

# Détecter si on est sur Streamlit Cloud
IS_STREAMLIT_CLOUD = os.environ.get('STREAMLIT_SERVER_HEADLESS') == 'true'

st.title("Captures automatiques de pages web")

if IS_STREAMLIT_CLOUD:
    # ============================================================
    # MESSAGE POUR STREAMLIT CLOUD
    # ============================================================
    st.warning("""
    ⚠️ **LIMITATION : Outil de capture non disponible sur Streamlit Cloud**
    
    **Pourquoi ?** Selenium/Chrome requiert un navigateur desktop, qui n'est pas 
    disponible dans l'environnement Streamlit Cloud.
    """)
    
    st.info("""
    📌 **Solutions :**
    
    1. **Utiliser cet outil en LOCAL** : 
       - Télécharger le projet
       - Exécuter : `python run.py`
       - L'outil fonctionne 100%
    
    2. **Service alternatif** :
       - Utiliser une API de screenshot (ScrapingBee, ScreenshotAPI, etc.)
       - Intégration payante mais fonctionne sur Cloud
    
    3. **Utiliser l'autre outil** :
       - Cliquez sur "Recadrage d'images" dans le menu
       - Celui-ci fonctionne parfaitement sur Cloud ✅
    """)
    
    st.markdown("---")
    
    st.subheader("Autres outils disponibles")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✂️ **Recadrage d'images** - FONCTIONNE SUR CLOUD ✅")
        st.write("Accédez à cet outil dans le menu latéral")
    
else:
    # ============================================================
    # CODE ORIGINAL (Local uniquement)
    # ============================================================
    import re
    import time
    import zipfile
    import xml.etree.ElementTree as ET
    from datetime import datetime
    from io import BytesIO
    from urllib.parse import urljoin, urlparse
    
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    
    # ─────────────────────────────────────────────────────────────
    # ⚙️ CONFIGURATION
    # ─────────────────────────────────────────────────────────────
    COOKIE_BUTTON_SELECTOR = "button.cm-btn.cm-btn-success.cm-btn-info.cm-btn-accept"
    
    # ─────────────────────────────────────────────────────────────
    # SESSION STATE
    # ─────────────────────────────────────────────────────────────
    if "cookies_dict" not in st.session_state:
        st.session_state.cookies_dict = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_driver" not in st.session_state:
        st.session_state.login_driver = None
    if "excluded_pages" not in st.session_state:
        st.session_state.excluded_pages = set()
    if "discovered_pages" not in st.session_state:
        st.session_state.discovered_pages = []
    if "selected_folder" not in st.session_state:
        st.session_state.selected_folder = None
    if "show_folder_picker" not in st.session_state:
        st.session_state.show_folder_picker = False
    if "current_path" not in st.session_state:
        st.session_state.current_path = os.path.expanduser("~")
    
    # ─────────────────────────────────────────────────────────────
    # OUTILS
    # ─────────────────────────────────────────────────────────────
    def start_login(base_url):
        """Lance un navigateur pour que l'utilisateur se connecte"""
        o = Options()
        o.add_argument("--no-sandbox")
        o.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=o)
        driver.set_window_size(1920, 1080)
        driver.get(base_url)
        
        st.session_state.login_driver = driver
        return driver
    
    def finish_login():
        """Récupère les cookies après la connexion"""
        if st.session_state.login_driver:
            try:
                cookies_list = st.session_state.login_driver.get_cookies()
                cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
                st.session_state.login_driver.quit()
                st.session_state.login_driver = None
                return cookies_dict
            except Exception as e:
                st.error(f"Erreur lors de la récupération des cookies: {e}")
                return None
        return None
    
    def discover_site_pages(base_url):
        """Découvre automatiquement les pages du site"""
        pages = []
        
        try:
            # Essayer via sitemap
            sitemap_url = urljoin(base_url, '/sitemap.xml')
            response = requests.get(sitemap_url, timeout=5)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                for url_elem in root.findall('ns:url', namespace):
                    loc = url_elem.find('ns:loc', namespace)
                    if loc is not None:
                        url = loc.text
                        parsed = urlparse(url)
                        path = parsed.path
                        if path.startswith('/'):
                            path = path[1:]
                        pages.append(path)
                
                return sorted(set(pages))
        except:
            pass
        
        # Fallback: scanner la page d'accueil
        try:
            response = requests.get(base_url, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/'):
                    path = href[1:]
                    if path and not path.endswith(('jpg', 'png', 'pdf', 'css', 'js')):
                        pages.append(path)
        except:
            pass
        
        return sorted(set(pages))
    
    def capture_screens(pages, base_url, authenticated=False, out_dir="captures", cookies=None, log=None):
        """Capture les pages web"""
        if log is None:
            log = []
        
        for page in pages:
            try:
                o = Options()
                o.add_argument("--no-sandbox")
                o.add_argument("--disable-gpu")
                o.add_argument("--headless")
                
                driver = webdriver.Chrome(options=o)
                driver.set_window_size(1920, 1080)
                
                url = urljoin(base_url, page)
                
                if authenticated and cookies:
                    driver.get(url)
                    for name, value in cookies.items():
                        try:
                            driver.add_cookie({'name': name, 'value': value})
                        except:
                            pass
                
                driver.get(url)
                time.sleep(2)
                
                # Essayer d'accepter les cookies
                try:
                    button = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, COOKIE_BUTTON_SELECTOR))
                    )
                    button.click()
                    time.sleep(1)
                except:
                    pass
                
                # Créer le dossier
                os.makedirs(out_dir, exist_ok=True)
                
                # Screenshot
                filename = f"{out_dir}/{page.replace('/', '_')}.png"
                driver.save_screenshot(filename)
                
                log.append({
                    "Page": page,
                    "URL": url,
                    "Status": "Captured",
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                st.success(f"✅ Capturée: {page}")
                
                driver.quit()
                
            except Exception as e:
                log.append({
                    "Page": page,
                    "URL": urljoin(base_url, page),
                    "Status": f"Error: {str(e)[:50]}",
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.warning(f"⚠️  Erreur: {page}")
    
    # ─────────────────────────────────────────────────────────────
    # INTERFACE
    # ─────────────────────────────────────────────────────────────
    st.write("Outil de captures d'écran automatiques pour pages web")
    
    base_url = st.text_input("URL du site a capturer", "https://exemple.com")
    
    if st.button("🌐 Ouvrir navigateur"):
        start_login(base_url)
        st.info("Connectez-vous puis cliquez sur 'J'ai termine'")
        st.rerun()
    
    if st.button("✅ J'ai termine"):
        cookies = finish_login()
        if cookies:
            st.session_state.cookies_dict = cookies
            st.session_state.logged_in = True
            st.rerun()
    
    if st.session_state.logged_in:
        st.success("✅ Connecte !")
    
    if st.button("📸 Lancer les captures"):
        with st.spinner("Decouverte des pages..."):
            pages = discover_site_pages(base_url)
        
        st.info(f"Pages trouvees: {len(pages)}")
        
        log = []
        capture_screens(pages[:5], base_url, False, "captures", log=log)
        
        if log:
            df = pd.DataFrame(log)
            st.dataframe(df)
