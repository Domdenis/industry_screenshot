# -*- coding: utf-8 -*-
"""
Captures d'écran Streamlit :
• Découverte automatique via sitemap ou scan de la home
• Login interactif pour récupérer les cookies automatiquement
• Sous-pages /industry/slug & /node/123 capturées en mode connecté
• Gestion automatique des fenêtres de consentement aux cookies
"""

import os, re, time, zipfile, xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO
from urllib.parse import urljoin, urlparse

import pandas as pd, requests, streamlit as st
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
# ⚙️ STREAMLIT
# ─────────────────────────────────────────────────────────────
# st.set_page_config est geré dans app.py
st.title("📸 Captures automatiques de pages web")

# Session state pour le login
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

def folder_browser():
    """Navigateur de dossiers Streamlit complet"""
    
    # Initialiser le chemin courant
    if "current_path" not in st.session_state:
        st.session_state.current_path = os.path.expanduser("~")  # Commencer par le home
    
    current_path = st.session_state.current_path
    
    # Afficher le chemin courant
    st.write(f"**📍 Chemin actuel :** `{current_path}`")
    
    # Boutons de navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if os.name == 'nt':  # Windows
            if st.button("💾 Racine C:\\", key="root_drive"):
                st.session_state.current_path = "C:\\"
                st.rerun()
        else:  # Linux / Mac
            if st.button("📂 Racine /", key="root_drive"):
                st.session_state.current_path = "/"
                st.rerun()
    
    with col2:
        if st.button("🏠 Home", key="home_btn"):
            st.session_state.current_path = os.path.expanduser("~")
            st.rerun()
    
    with col3:
        if current_path != os.path.dirname(current_path):  # Pas déjà à la racine
            if st.button("⬆️ Parent", key="parent_btn"):
                parent = os.path.dirname(current_path)
                st.session_state.current_path = parent
                st.rerun()
    
    # Lister les dossiers et fichiers
    try:
        items = []
        for item in sorted(os.listdir(current_path)):
            if not item.startswith('.'):  # Masquer les fichiers cachés
                full_path = os.path.join(current_path, item)
                try:
                    if os.path.isdir(full_path):
                        items.append((item, full_path, True))  # True = dossier
                except:
                    pass
        
        if not items:
            st.info("📭 Aucun dossier trouvé")
        else:
            # Afficher les dossiers
            st.write("**📂 Dossiers disponibles :**")
            for idx, (name, path, is_dir) in enumerate(items):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📁 {name}")
                with col2:
                    if st.button("📂 Ouvrir", key=f"open_{idx}"):
                        st.session_state.current_path = path
                        st.rerun()
        
        # Bouton pour sélectionner le dossier courant
        st.divider()
        if st.button("✅ Sélectionner ce dossier", key="select_folder"):
            st.session_state.selected_folder = current_path
            st.session_state.show_folder_picker = False
            st.success(f"✅ Dossier sélectionné : {current_path}")
            st.rerun()
        
    except PermissionError:
        st.error(f"❌ Accès refusé : {current_path}")
    except Exception as e:
        st.error(f"❌ Erreur : {e}")

def check_existing_connection(base_url):
    """Vérifie si l'utilisateur est déjà connecté au site"""
    try:
        o = Options()
        o.add_argument("--headless=new")
        o.add_argument("--no-sandbox")
        o.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=o)
        driver.set_window_size(1920, 1080)
        driver.get(base_url)
        time.sleep(2)
        
        # Récupérer tous les cookies
        cookies_list = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
        
        # Chercher des cookies de session/auth
        session_cookies = [c for c in cookies_list if 'session' in c['name'].lower() or 'auth' in c['name'].lower()]
        
        # Chercher aussi des indicateurs HTML de connexion (logout button, user menu, etc)
        try:
            logout_indicators = driver.find_elements(By.CSS_SELECTOR, "[href*='logout'], [href*='disconnect']")
            has_logout = len(logout_indicators) > 0
        except:
            has_logout = False
        
        driver.quit()
        
        if session_cookies or has_logout:
            return True, cookies_dict
        else:
            return False, None
    except Exception as e:
        return False, None
    """Vérifie si l'utilisateur est déjà connecté au site"""
    try:
        o = Options()
        o.add_argument("--headless=new")
        o.add_argument("--no-sandbox")
        o.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=o)
        driver.set_window_size(1920, 1080)
        driver.get(base_url)
        time.sleep(2)
        
        # Récupérer tous les cookies
        cookies_list = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
        
        # Chercher des cookies de session/auth
        session_cookies = [c for c in cookies_list if 'session' in c['name'].lower() or 'auth' in c['name'].lower()]
        
        # Chercher aussi des indicateurs HTML de connexion (logout button, user menu, etc)
        try:
            logout_indicators = driver.find_elements(By.CSS_SELECTOR, "[href*='logout'], [href*='disconnect'], button:has-text('Logout')")
            has_logout = len(logout_indicators) > 0
        except:
            has_logout = False
        
        driver.quit()
        
        if session_cookies or has_logout:
            return True, cookies_dict
        else:
            return False, None
    except Exception as e:
        return False, None

def open_directory_picker():
    """Affiche un sélecteur de dossiers Streamlit"""
    st.write("**📁 Sélectionnez le dossier de destination :**")
    
    # Option 1 : Dossiers courants
    current_dir = os.getcwd()
    try:
        available_dirs = [d for d in os.listdir(current_dir) 
                         if os.path.isdir(os.path.join(current_dir, d)) and not d.startswith('.')]
    except:
        available_dirs = []
    
    if available_dirs:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Dossiers disponibles :**")
            selected_dir = st.selectbox("Choisir un dossier", available_dirs, key="folder_select")
            full_path = os.path.join(current_dir, selected_dir)
            if st.button("✅ Utiliser ce dossier"):
                st.session_state.selected_folder = full_path
                st.success(f"✅ Dossier sélectionné : {full_path}")
                return full_path
    
    # Option 2 : Chemin personnalisé
    with st.expander("📝 Ou entrez un chemin personnalisé"):
        custom_path = st.text_input("Chemin complet du dossier", placeholder="/home/user/captures ou C:\\Users\\user\\captures")
        if custom_path:
            if os.path.isdir(custom_path):
                if st.button("✅ Utiliser ce chemin"):
                    st.session_state.selected_folder = custom_path
                    st.success(f"✅ Dossier sélectionné : {custom_path}")
                    return custom_path
            else:
                st.error(f"❌ Le chemin n'existe pas : {custom_path}")
    
    return None

def finish_login():
    """Récupère les cookies du driver ouvert"""
    if not st.session_state.login_driver:
        st.error("Pas de navigateur ouvert !")
        return None
    
    try:
        driver = st.session_state.login_driver
        time.sleep(1)  # Petit délai pour que les cookies soient bien définis
        
        # Récupérer les cookies
        cookies_list = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
        
        st.success(f"✅ {len(cookies_list)} cookies récupérés")
        st.write(f"**Cookies détectés :**")
        for cookie in cookies_list:
            st.write(f"  • {cookie['name']}")
        
        with st.expander("🍪 Voir tous les détails des cookies"):
            st.json(cookies_dict)
        
        driver.quit()
        st.session_state.login_driver = None
        st.info("🔒 Navigateur fermé")
        
        return cookies_dict
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
        return None

def accept_cookies(driver, timeout=5):
    """Accepte la fenêtre de consentement aux cookies"""
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, COOKIE_BUTTON_SELECTOR))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
        return True
    except TimeoutException:
        return False
    except Exception:
        return False

def get_h4_text(driver):
    """Extrait le texte du H4 à l'intérieur de .ck-content"""
    try:
        # Chercher spécifiquement le H4 dans la classe ck-content
        h4_element = driver.find_element(By.CSS_SELECTOR, ".ck-content h4, .ck-content > h4")
        text = h4_element.text.strip()
        
        if text:
            # Nettoyer le texte pour l'utiliser comme nom de fichier
            text = re.sub(r'[<>:"/\\|?*]', '', text)  # Supprimer caractères interdits
            text = re.sub(r'\s+', '_', text)  # Remplacer espaces par underscores
            text = text[:50]  # Limiter la longueur
            return text
        
        return None
    except Exception as e:
        return None

def capture_full_page(driver, path):
    h = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, h + 200);  time.sleep(2)
    driver.save_screenshot(path)

def discover_site_pages(base_url, max_pages=200):
    pages = set()

    # 1) robots.txt → Sitemap:
    try:
        txt = requests.get(urljoin(base_url, "/robots.txt"), timeout=5).text
        smaps = [l.split(":", 1)[1].strip()
                 for l in txt.splitlines() if l.lower().startswith("sitemap:")]
    except Exception:
        smaps = []

    if not smaps:
        smaps.append(urljoin(base_url, "/sitemap.xml"))

    for sm in smaps:
        try:
            root = ET.fromstring(requests.get(sm, timeout=8).text)
            for loc in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                p = urlparse(loc.text).path.lstrip("/")
                if p: pages.add(p)
        except Exception:
            pass

    # 2) fallback : scan de la home
    if not pages:
        try:
            soup = BeautifulSoup(requests.get(base_url, timeout=10).text,"html.parser")
            for a in soup.select('a[href^="/"]'):
                p = urlparse(a["href"]).path.lstrip("/").split("#")[0]
                if p: pages.add(p)
        except Exception:
            pass

    pages.add("")  # /
    return sorted(pages)[:max_pages]

def fetch_industry_detail_pages(base_url, cookies_dict=None, max_pages=1000):
    """Scroll + 'Show more' → renvoie /industry/* et /node/*"""
    try:
        o = Options(); o.add_argument("--headless=new"), o.add_argument("--no-sandbox"), o.add_argument("--disable-gpu")
        d = webdriver.Chrome(options=o); d.set_window_size(1920, 1080)

        d.get(base_url)
        
        # Injecter les cookies si disponibles
        if cookies_dict:
            for cookie_name, cookie_val in cookies_dict.items():
                try:
                    d.add_cookie({"name": cookie_name, "value": cookie_val, "domain": urlparse(base_url).hostname, "path": "/"})
                except Exception:
                    pass
            d.get(base_url)
            # Accepter les cookies
            accept_cookies(d)
            time.sleep(2)

        industry_url = f"{base_url.rstrip('/')}/industry"
        st.info(f"🔗 Accès à {industry_url}…")
        d.get(industry_url)
        time.sleep(3)
        
        # Vérifier si les éléments sont présents
        try:
            WebDriverWait(d, 15).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a[href*='/industry/'], a[href*='/node/']")))
        except TimeoutException:
            st.error(f"❌ Aucune page industry/node trouvée sur {industry_url}")
            st.warning("Possibilités :")
            st.warning("  • Vérifiez que vous êtes connecté (cliquez sur 'Se connecter')")
            st.warning("  • Vérifiez que vous avez les droits d'accès")
            st.warning("  • Vérifiez que la page /industry existe")
            d.quit()
            return []
        
        prev = 0
        iterations = 0
        max_iterations = 20
        
        while iterations < max_iterations:
            iterations += 1
            try:
                btn = WebDriverWait(d, 3).until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'show') "
                               "or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'plus')]")))
                d.execute_script("arguments[0].click();", btn); time.sleep(1.5)
            except TimeoutException:
                pass
            
            d.execute_script("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(2)
            links = d.find_elements(By.CSS_SELECTOR, "a[href*='/industry/'], a[href*='/node/']")
            
            if len(links) == prev: 
                st.success(f"✅ {len(links)} pages trouvées")
                break
            prev = len(links)
            st.write(f"   📄 {len(links)} pages détectées…")

        pat = re.compile(r"^/(industry/[^/]+|node/\d+)$", re.I)
        pages = {m.group(1).lower() for a in links
                 if (p := urlparse(a.get_attribute("href")).path) and (m := pat.match(p))}
        d.quit()
        return sorted(pages)[:max_pages]
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des pages : {str(e)}")
        try:
            d.quit()
        except:
            pass
        return []

def show_funny_loader():
    """Affiche un loader amusant avec animation"""
    loaders = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    emojis = ["📸", "🎬", "📷", "🎞️", "📹"]
    messages = [
        "Capture en cours... 📸",
        "Chargement des pages... ⏳",
        "Traitement en cours... 🔄",
        "C'est du lourd ! 💪",
        "Patience patience... ⏳",
        "Ça chauffe ! 🔥",
        "En plein travail... 👷",
        "Magie en cours... ✨"
    ]
    return loaders, emojis, messages

def capture_screens(pages, base_url, logged, out="captures", cookies_dict=None, log=None):
    os.makedirs(out, exist_ok=True)
    o = Options(); o.add_argument("--headless=new"), o.add_argument("--no-sandbox"), o.add_argument("--disable-gpu")
    d = webdriver.Chrome(options=o); d.set_window_size(1920, 1080)

    if logged and cookies_dict:
        st.info("🔐 Cookies injectés"); d.get(base_url)
        
        # Injecter tous les cookies
        for cookie_name, cookie_val in cookies_dict.items():
            try:
                d.add_cookie({"name": cookie_name, "value": cookie_val,
                              "domain": urlparse(base_url).hostname, "path": "/"})
            except Exception:
                pass
        
        d.get(base_url)
        # Accepter les cookies
        accept_cookies(d)
        time.sleep(2)

    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    loaders, emojis, messages = show_funny_loader()
    
    total_pages = len(pages)
    captured = 0
    
    for idx, p in enumerate(pages):
        url = f"{base_url.rstrip('/')}/{p.lstrip('/')}"
        safe = p.strip("/").replace("/", "_") or "home"
        folder = os.path.join(out, "industry") if safe.startswith(("industry_", "node_")) else out
        os.makedirs(folder, exist_ok=True)
        
        # Animation loader
        loader_char = loaders[idx % len(loaders)]
        emoji = emojis[idx % len(emojis)]
        message = messages[idx % len(messages)]
        
        status_text.write(f"{loader_char} {emoji} {message} ({idx + 1}/{total_pages})")
        
        st.write(f"🔗 {url}")
        try:
            d.get(url); WebDriverWait(d, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body"))); time.sleep(4)
            
            # Essayer de récupérer le texte H4
            h4_text = get_h4_text(d)
            
            # Créer le nom du fichier
            if h4_text:
                fname = f"{h4_text}_{'logged' if logged else 'guest'}.png"
                tag_label = "📝 H4"
            else:
                fname = f"{safe}_{'logged' if logged else 'guest'}.png"
                tag_label = "🔗 Path"
            
            path = os.path.join(folder, fname)
            capture_full_page(d, path); 
            st.success(f"✅ {fname} ({tag_label})")
            captured += 1
            if log is not None:
                log.append({"Fichier": fname, "URL": url, "Mode": "connecté" if logged else "invité",
                            "H4": h4_text or "N/A",
                            "Horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        except Exception as e:  # noqa: BLE001
            st.error(f"❌ {url} : {e}")
        
        # Mise à jour barre de progression
        progress = (idx + 1) / total_pages
        progress_bar.progress(progress)
    
    status_text.empty()
    progress_bar.empty()
    st.balloons()  # Confettis à la fin ! 🎉
    st.success(f"🎉 {captured}/{total_pages} pages capturées avec succès !")
    d.quit()

def is_industry(path):  # helper
    return path.lstrip("/").startswith(("industry/", "node/"))

# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────
base_url = st.text_input("🌐 URL de base", "https://rhumato38e.medicalcongress.online")

# ─────────────────────────────────────────────────────────────
# SECTION LOGIN
# ─────────────────────────────────────────────────────────────
st.subheader("🔐 Authentification")

st.info("💡 Cliquez sur 'Ouvrir le navigateur' pour vous connecter, puis 'J'ai terminé' une fois la connexion faite")

col1, col2 = st.columns(2)
with col1:
    if st.button("🌐 Ouvrir navigateur", key="open_login"):
        start_login(base_url)
        st.info("✅ Navigateur ouvert ! Connectez-vous puis cliquez sur 'J'ai terminé'")
        st.rerun()

with col2:
    if st.button("✅ J'ai terminé", key="finish_login"):
        cookies = finish_login()
        if cookies:
            st.session_state.cookies_dict = cookies
            st.session_state.logged_in = True
            st.rerun()

# Afficher l'état du navigateur
if st.session_state.login_driver:
    st.warning("⏳ Navigateur ouvert en attente...")

# Afficher l'état de connexion
if st.session_state.logged_in and st.session_state.cookies_dict:
    st.success("✅ Connecté avec succès !")
    with st.expander("🍪 Voir les cookies"):
        st.json(st.session_state.cookies_dict)
    
    if st.button("🚪 Se déconnecter"):
        st.session_state.cookies_dict = None
        st.session_state.logged_in = False
        st.rerun()
else:
    st.warning("❌ Non connecté - Le mode connecté ne sera pas disponible")

st.divider()

# Configuration des paramètres
col_ind1, col_ind2 = st.columns([2, 1])
with col_ind1:
    incl_ind = st.checkbox("🔁 Inclure les sous-pages des industries", value=True)
with col_ind2:
    max_ind_pages = st.number_input("Max pages industry", min_value=1, max_value=1000, value=1000, 
                                    help="Limite le nombre de pages industry/node à capturer")

# Option pour ne capturer que les industry
only_industry = st.checkbox("⭐ Ne capturer QUE les pages industry/node (pas les pages normales)", value=False)

# ✅ Zone de texte pour pages manuelles
pages_text = st.text_area(
    "📝 Chemins des pages à capturer (optionnel, un par ligne)", "")

# Répertoire de destination avec file picker
st.subheader("📂 Dossier de destination")

col_out1, col_out2 = st.columns([4, 1])
with col_out1:
    out_dir = st.text_input("Chemin du dossier", "captures", help="Le dossier où seront sauvegardées les captures")
with col_out2:
    if st.button("📁 Parcourir", key="browse_folder"):
        st.session_state.show_folder_picker = True

# Afficher le navigateur de dossiers si demandé
if st.session_state.show_folder_picker:
    with st.expander("📂 Navigateur de dossiers", expanded=True):
        folder_browser()
    
    if st.button("❌ Fermer", key="close_folder_picker"):
        st.session_state.show_folder_picker = False
        st.rerun()

# Utiliser le dossier sélectionné
if st.session_state.selected_folder:
    out_dir = st.session_state.selected_folder
    st.info(f"✅ Dossier sélectionné : {out_dir}")

st.info(f"🍪 **Classe du bouton d'acceptation des cookies :** `{COOKIE_BUTTON_SELECTOR}`")

# Nom du fichier ZIP à télécharger
col_zip1, col_zip2 = st.columns([3, 1])
with col_zip1:
    zip_name_input = st.text_input("📦 Nom du fichier ZIP à télécharger", "captures", 
                                   help="Ex: captures_rhumato, my_screenshots")
with col_zip2:
    # Afficher le nom final
    final_zip_display = zip_name_input if zip_name_input.endswith('.zip') else zip_name_input + '.zip'
    st.write(f"✅ {final_zip_display}")

if st.button("📸 Lancer les captures"):
    log = []

    # 1) découverte auto
    with st.spinner("🔎 Découverte automatique des pages..."):
        pages = discover_site_pages(base_url)
    st.success(f"{len(pages)} pages trouvées.")

    # 2) pages forcées
    forced = [l.strip().lstrip("/") for l in pages_text.splitlines() if l.strip()]
    if forced:
        st.info(f"➕ {len(forced)} pages ajoutées manuellement.")
        pages.extend(forced)

    # 3) industries
    if incl_ind:
        with st.spinner("➕ Récupération des sous-pages industry/node..."):
            pages += fetch_industry_detail_pages(base_url, st.session_state.cookies_dict, max_ind_pages)

    # déduplication
    pages = sorted(set(pages))
    st.session_state.discovered_pages = pages

    # ─────────────────────────────────────────────────────────────
    # AFFICHER LES PAGES POUR SÉLECTION
    # ─────────────────────────────────────────────────────────────
    st.subheader("📋 Pages découvertes - Sélectionnez celles à capturer")
    
    # Trier les pages : industry d'abord, ensuite les autres
    industry_pages = [p for p in pages if is_industry(p)]
    normal_pages = [p for p in pages if not is_industry(p) and "live" not in p.lower()]
    
    with st.expander("🔍 Voir toutes les pages", expanded=True):
        col1, col2 = st.columns(2)
        
        # Pages industry
        with col1:
            st.write(f"**🏢 Pages Industry ({len(industry_pages)})**")
            for page in industry_pages:
                key = f"industry_{page}"
                if key not in st.session_state:
                    st.session_state[key] = True
                selected = st.checkbox(page, value=st.session_state[key], key=key)
                if not selected:
                    st.session_state.excluded_pages.add(page)
                elif page in st.session_state.excluded_pages:
                    st.session_state.excluded_pages.discard(page)
        
        # Pages normales
        with col2:
            st.write(f"**📄 Pages Normales ({len(normal_pages)})**")
            for page in normal_pages:
                key = f"normal_{page}"
                if key not in st.session_state:
                    st.session_state[key] = not only_industry  # Décochez par défaut si only_industry
                selected = st.checkbox(page, value=st.session_state[key], key=key)
                if not selected:
                    st.session_state.excluded_pages.add(page)
                elif page in st.session_state.excluded_pages:
                    st.session_state.excluded_pages.discard(page)
    
    # Appliquer le filtre only_industry
    if only_industry:
        pages_to_capture = [p for p in pages if is_industry(p)]
    else:
        pages_to_capture = [p for p in pages if p not in st.session_state.excluded_pages]
    
    st.success(f"✅ {len(pages_to_capture)} pages vont être capturées")

    # ─────────────────────────────────────────────────────────────
    # CAPTURER LES PAGES
    # ─────────────────────────────────────────────────────────────
    
    # 4) invité (exclut industry/node + live)
    if not only_industry:
        guest = [p for p in pages_to_capture if not is_industry(p) and "live" not in p.lower()]
        if guest:
            st.subheader(f"Mode invité 🕵️ ({len(guest)} pages)")
            capture_screens(guest, base_url, False, out_dir, log=log)
    
    # 5) connecté
    st.subheader("Mode connecté 🔐")
    if st.session_state.logged_in and st.session_state.cookies_dict:
        capture_screens(pages_to_capture, base_url, True, out_dir, st.session_state.cookies_dict, log)
    else:
        if only_industry or len([p for p in pages_to_capture if is_industry(p)]) > 0:
            st.warning("⚠️ Non connecté : mode connecté ignoré.")

    # 6) Excel & ZIP
    if log:
        pd.DataFrame(log).to_excel(os.path.join(out_dir, "liste_captures.xlsx"), index=False)
    
    with st.spinner("📦 Création du fichier ZIP..."):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for r, _, f in os.walk(out_dir):
                for file in f:
                    z.write(os.path.join(r, file), arcname=os.path.relpath(os.path.join(r, file), out_dir))
    
    # Utiliser le nom personnalisé du ZIP
    final_zip_name = zip_name_input if zip_name_input.endswith('.zip') else zip_name_input + '.zip'
    
    st.download_button(
        "⬇️ Télécharger les captures", 
        buf.getvalue(), 
        file_name=final_zip_name,
        mime="application/zip"
    )
