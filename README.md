# 🛠️ Suite d'Outils Streamlit

Une application Streamlit intégrée offrant deux outils puissants :
- **📸 Captures d'écran automatiques** : Capture d'écran de pages web avec authentification
- **✂️ Recadrage d'images** : Recadrage et suppression de zones dans des images PNG

## 📋 Contenu du projet

```
.
├── app.py                      # Application principale avec menu de sélection
├── requirements.txt            # Dépendances Python
├── .streamlit/
│   └── config.toml            # Configuration Streamlit
└── pages/
    ├── 1_captures.py          # Outil de captures d'écran
    └── 2_crop.py              # Outil de recadrage d'images
```

## 🚀 Installation locale

### Prérequis
- Python 3.8+
- pip
- Chrome/Chromium (pour Selenium)

### Étapes

1. **Cloner ou télécharger le projet**
```bash
git clone <votre-repo>
cd suite-outils
```

2. **Créer un environnement virtuel (recommandé)**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**
```bash
streamlit run app.py
```

L'application s'ouvrira à `http://localhost:8501`

## ☁️ Déploiement sur Streamlit Cloud

### Instructions de déploiement

1. **Préparer votre dépôt GitHub**
   - Créez un dépôt GitHub avec tous les fichiers du projet
   - Assurez-vous que `requirements.txt` et `app.py` sont à la racine
   - Assurez-vous que le dossier `pages/` contient les deux outils

2. **Aller sur Streamlit Cloud**
   - Allez à https://streamlit.io/cloud
   - Cliquez sur "New app"
   - Connectez-vous avec votre compte GitHub

3. **Configurer le déploiement**
   - **Repository** : Sélectionnez votre dépôt
   - **Branch** : `main` (ou votre branche)
   - **Main file path** : `app.py`

4. **Cliquer sur "Deploy"**

Streamlit Cloud installera automatiquement les dépendances et lancera votre app !

### Points importants pour Streamlit Cloud

- ✅ ChromeDriver : Streamlit Cloud inclut Chromium, donc Selenium fonctionne
- ✅ Stockage temporaire : Les fichiers sont stockés dans `/tmp` (ils sont effacés après la session)
- ✅ Limite de upload : 500 MB par défaut
- ❌ Accès au système de fichiers local : Limité

## 🎯 Utilisation

### 📸 Captures d'écran automatiques

**Fonctionnalités :**
- Découverte automatique des pages via sitemap ou scan HTML
- Connexion interactive avec sauvegarde des cookies
- Capture en mode authentifié ou invité
- Gestion automatique des pop-ups de consentement
- Export en ZIP avec rapport Excel

**Étapes :**
1. Entrez l'URL du site à capturer
2. (Optionnel) Authentifiez-vous via le navigateur ouvert
3. Configurez les paramètres de capture
4. Sélectionnez les pages à capturer
5. Téléchargez le ZIP avec les captures

### ✂️ Recadrage d'images

**Fonctionnalités :**
- Recadrage interactif des images PNG
- Application du recadrage à plusieurs images
- Suppression de zones horizontales
- Rapport Excel avec l'historique des opérations
- Export en ZIP

**Étapes :**
1. Chargez une ou plusieurs images PNG
2. Effectuez le recadrage sur la première image
3. (Optionnel) Sélectionnez une zone à supprimer
4. Appliquez les transformations à toutes les images
5. Téléchargez le ZIP résultant

## 🛠️ Configuration

### Fichier `.streamlit/config.toml`

Le fichier de configuration inclut :
- **Thème** : Couleurs et police personnalisées
- **Serveur** : Limite de taille d'upload, sécurité XSRF
- **Client** : Interface minimale

Vous pouvez modifier ces paramètres selon vos besoins.

### Fichier `requirements.txt`

Les dépendances principales :
- `streamlit` : Framework web
- `Pillow` : Traitement d'images
- `pandas` : Gestion de données
- `openpyxl` : Écriture Excel
- `streamlit-cropper` : Widget de recadrage
- `beautifulsoup4` : Parsing HTML
- `selenium` : Automation navigateur

## 🐛 Dépannage

### Problème : "Module not found" sur Streamlit Cloud
**Solution** : Assurez-vous que `requirements.txt` contient toutes les dépendances nécessaires

### Problème : Selenium ne fonctionne pas
**Solution** : Streamlit Cloud inclut Chromium. Si vous avez une erreur, vérifiez que les versions de Selenium et Chromium sont compatibles

### Problème : Images ne se chargent pas
**Solution** : Vérifiez que vous chargez des fichiers PNG. Le format est spécifié comme PNG uniquement.

### Problème : Fichiers sont effacés après la session
**Solution** : C'est normal sur Streamlit Cloud. Les fichiers sont temporaires et effacés automatiquement pour des raisons de sécurité.

## 📝 Notes importantes

1. **Session State** : L'application utilise `st.session_state` pour persister les données entre les interactions. Chaque session utilisateur a son propre état.

2. **Sécurité** : 
   - Sur Streamlit Cloud, ne stockez pas d'informations sensibles
   - Les cookies sont stockés en session et effacés après
   - Les fichiers uploadés sont temporaires

3. **Performance** :
   - Les captures d'écran peuvent être lentes (10-30 secondes par page)
   - Le recadrage d'images est rapide (quelques secondes)

4. **Limites Streamlit Cloud** :
   - Pas de persistance de fichiers entre les sessions
   - Ressources CPU/RAM limitées
   - Upload maximum 500 MB

## 🤝 Contribution

Pour modifier ou améliorer l'application :

1. Modifiez `app.py` pour la structure générale
2. Modifiez `pages/1_captures.py` pour l'outil de captures
3. Modifiez `pages/2_crop.py` pour l'outil de recadrage
4. Testez localement avec `streamlit run app.py`
5. Commitez et poussez vers GitHub

Streamlit Cloud redéploiera automatiquement !

## 📄 Licence

À définir selon vos besoins

## 💬 Support

Pour des questions sur :
- **Streamlit** : https://docs.streamlit.io
- **Selenium** : https://www.selenium.dev/documentation/
- **Streamlit Cloud** : https://docs.streamlit.io/streamlit-cloud

---

**Version 1.0** - Novembre 2024
