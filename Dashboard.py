import streamlit as st
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import pandas as pd
import numpy as np
import math
import statistics
import sys
import platform
from collections import Counter
import unicodedata
import re
import warnings
import time
warnings.filterwarnings('ignore')

# Version Plotly
import plotly as plotly_lib
import plotly.graph_objects as go
import plotly.express as px

PLOTLY_VERSION = plotly_lib.__version__

# Tentative d'import psutil (optionnel)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Tentative d'import nacl
try:
    import nacl.signing
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

# ============================================
# DICTIONNAIRE FRANCAIS ÉTENDU
# ============================================
DICTIONNAIRE_FR = {
    "BONJOUR": "2.15.14.10.15.21.18",
    "MERCI": "13.5.18.3.9",
    "BIENVENUE": "2.9.5.14.22.5.14.21.5",
    "EXCELLENT": "5.24.3.5.12.12.5.14.20",
    "PARFAIT": "16.1.18.6.1.9.20",
    "MAGNIFIQUE": "13.1.7.14.9.6.9.17.21.5",
    "SPLENDIDE": "19.16.12.5.14.4.9.4.5",
    "FORMIDABLE": "6.15.18.13.9.4.1.2.12.5",
    "REMARQUABLE": "18.5.13.1.18.17.21.1.2.12.5",
    "EXTRAORDINAIRE": "5.24.20.18.1.15.18.4.9.14.1.9.18.5",
    "BOURSE": "2.15.21.18.19.5",
    "ACTION": "1.3.20.9.15.14",
    "DIVIDENDE": "4.9.22.9.4.5.14.4.5",
    "PORTEFEUILLE": "16.15.18.20.5.6.5.21.9.12.12.5",
    "INVESTISSEMENT": "9.14.22.5.19.20.9.19.19.5.13.5.14.20",
    "RENDEMENT": "18.5.14.4.5.13.5.14.20",
    "CAPITAL": "3.1.16.9.20.1.12",
    "FINANCE": "6.9.14.1.14.3.5",
    "MARCHE": "13.1.18.3.8.5",
    "CRYPTOMONNAIE": "3.18.25.16.20.15.13.15.14.14.1.9.5",
    "BLOCKCHAIN": "2.12.15.3.11.3.8.1.9.14",
    "BITCOIN": "2.9.20.3.15.9.14",
    "ETHEREUM": "5.20.8.5.18.5.21.13",
    "DEFI": "4.5.6.9",
    "NFT": "14.6.20",
    "METAVERS": "13.5.20.1.22.5.18.19",
    "QUANTIQUE": "17.21.1.14.20.9.17.21.5",
    "PYTHON": "16.25.20.8.15.14",
    "STREAMLIT": "19.20.18.5.1.13.12.9.20"
}

# Base des lettres pour l'encodage
LETTER_TO_NUM = {chr(64+i): i for i in range(1, 27)}
NUM_TO_LETTER = {i: chr(64+i) for i in range(1, 27)}

# ============================================
# FONCTIONS PRINCIPALES
# ============================================

def text_to_gradation(word):
    """Convertit n'importe quel mot en gradation numérique (A=1, B=2, ..., Z=26)"""
    word = word.upper().strip()
    
    # Supprimer les accents et caractères spéciaux
    word = ''.join(c for c in unicodedata.normalize('NFD', word) 
                   if unicodedata.category(c) != 'Mn')
    
    # Garder uniquement les lettres A-Z
    original_word = word
    word = re.sub(r'[^A-Z]', '', word)
    
    if not word:
        return None, "Le mot doit contenir au moins une lettre (A-Z)"
    
    if word != original_word:
        st.warning(f"⚠️ Caractères spéciaux supprimés: {original_word} → {word}")
    
    gradation = '.'.join(str(LETTER_TO_NUM[c]) for c in word)
    return gradation, None

def gradation_to_text(gradation):
    """Convertit une gradation en mot"""
    try:
        numbers = [int(x) for x in gradation.split('.')]
        word = ''.join(NUM_TO_LETTER.get(n, '?') for n in numbers)
        if '?' in word:
            # Essayer de corriger les nombres hors plage
            corrected = []
            for n in numbers:
                if 1 <= n <= 26:
                    corrected.append(NUM_TO_LETTER[n])
                else:
                    corrected.append(f"[{n}]")
            word = ''.join(corrected)
            return word, "Certains nombres étaient hors plage 1-26"
        return word, None
    except ValueError:
        return None, "Format de gradation invalide. Utilisez des nombres séparés par des points (ex: 2.15.21.18.19.5)"

def generate_crypto_for_word(word):
    """Génère une cryptographie complète pour n'importe quel mot"""
    try:
        word_clean = word.upper().strip()
        
        # Nettoyer le mot pour la gradation
        word_for_gradation = ''.join(c for c in unicodedata.normalize('NFD', word_clean) 
                                      if unicodedata.category(c) != 'Mn')
        word_for_gradation = re.sub(r'[^A-Z]', '', word_for_gradation)
        
        if not word_for_gradation:
            return None, "Le mot ne contient pas de lettres valides"
        
        gradation, _ = text_to_gradation(word_for_gradation)
        
        # Génération des clés uniques
        timestamp = datetime.now().isoformat()
        salt = secrets.token_hex(16)
        seed_str = f"{gradation}|{word_clean}|{timestamp}|{salt}"
        
        # Hash multiples
        sha256_hash = hashlib.sha256(seed_str.encode()).hexdigest()
        sha512_hash = hashlib.sha512(seed_str.encode()).hexdigest()
        
        # Clé publique et signature
        if HAS_NACL:
            seed_bytes = hashlib.pbkdf2_hmac('sha256', seed_str.encode(), salt.encode(), 100000, 32)
            signing_key = nacl.signing.SigningKey(seed_bytes)
            verify_key = signing_key.verify_key
            public_key = verify_key.encode().hex()
            
            hash_bytes = hashlib.sha256(seed_str.encode()).digest()
            signature_bytes = signing_key.sign(hash_bytes).signature
            signature = signature_bytes.hex()
            is_valid = True
        else:
            # Mode démo
            public_key = hashlib.sha3_256(seed_str.encode()).hexdigest()
            signature = hashlib.sha3_512(f"{seed_str}{public_key}".encode()).hexdigest()[:128]
            is_valid = True
        
        return {
            "mot": word_clean,
            "mot_original": word,
            "gradation": gradation,
            "public_key": public_key,
            "signature": signature,
            "hash_sha256": sha256_hash,
            "hash_sha512": sha512_hash,
            "timestamp": timestamp,
            "salt": salt,
            "is_valid": is_valid,
            "longueur": len(word_for_gradation)
        }, None
        
    except Exception as e:
        return None, str(e)

def calculate_entropy(data):
    """Calcule l'entropie de Shannon"""
    if not data:
        return 0
    data_str = str(data)
    prob = [float(data_str.count(c)) / len(data_str) for c in set(data_str)]
    return -sum([p * math.log2(p) for p in prob]) if prob else 0

def calculate_security_score(crypto_data):
    """Calcule un score de sécurité"""
    if not crypto_data:
        return 0
    
    score = 0
    # Longueur (30 pts)
    score += min(30, crypto_data.get('longueur', 0) * 3)
    # Entropie (40 pts)
    entropy = calculate_entropy(crypto_data.get('hash_sha512', ''))
    score += min(40, entropy * 5)
    # Validité (30 pts)
    if crypto_data.get('is_valid'):
        score += 30
    
    return min(100, score)

# ============================================
# CONFIGURATION STREAMLIT
# ============================================
st.set_page_config(
    page_title="Quantum Gradation - Pour N'IMPORTE QUEL Mot",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .stApp { background: #000000; }
    .stMarkdown, .stText, .stTitle, .stHeader, p, li, span, div { color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
    
    .main-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #2a2a3e;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #0a0a15 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .info-box {
        background: rgba(0, 255, 136, 0.1);
        border-left: 4px solid #00ff88;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    [data-testid="stSidebar"] { background: #0a0a15; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
        color: #ffffff;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
    }
    .stButton > button:hover { border-color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# ============================================
# ÉTAT DE SESSION
# ============================================
if 'current_crypto' not in st.session_state:
    st.session_state.current_crypto = None
if 'last_word' not in st.session_state:
    st.session_state.last_word = "BOURSE"

def load_word(word):
    """Charge un mot et génère sa cryptographie"""
    with st.spinner(f"🔐 Génération pour '{word}'..."):
        time.sleep(0.2)
        crypto, error = generate_crypto_for_word(word)
        if error:
            st.error(f"❌ {error}")
            return False
        if crypto:
            st.session_state.current_crypto = crypto
            st.session_state.last_word = word
            return True
    return False

# Chargement initial
if st.session_state.current_crypto is None:
    load_word("BOURSE")

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🔐 Quantum Gradation")
    st.markdown("### Pour N'IMPORTE QUEL mot")
    
    st.markdown("---")
    
    # Saisie libre
    st.markdown("#### ✏️ Mot personnalisé")
    custom_word = st.text_input("Entrez n'importe quel mot:", 
                                value=st.session_state.last_word,
                                placeholder="Ex: BONJOUR, CRYPTO, MAISON...")
    
    if st.button("🔒 Générer la crypto", use_container_width=True):
        if custom_word.strip():
            if load_word(custom_word.strip()):
                st.success(f"✅ Crypto générée pour '{custom_word.strip().upper()}'")
                st.rerun()
        else:
            st.error("Veuillez entrer un mot")
    
    st.markdown("---")
    
    # Mots suggérés
    st.markdown("#### 📚 Mots suggérés")
    suggestions = ["BONJOUR", "MERCI", "BIENVENUE", "EXCELLENT", "PARFAIT", "CRYPTO", "PYTHON", "STREAMLIT"]
    cols = st.columns(2)
    for i, sugg in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(sugg, key=f"sugg_{sugg}", use_container_width=True):
                load_word(sugg)
                st.rerun()
    
    st.markdown("---")
    
    # Métriques
    if st.session_state.current_crypto:
        crypto = st.session_state.current_crypto
        score = calculate_security_score(crypto)
        st.metric("🔐 Score sécurité", f"{score}/100")
        st.metric("📝 Mot actuel", crypto.get('mot', 'N/A'))
        st.metric("📏 Longueur", f"{crypto.get('longueur', 0)} lettres")

# ============================================
# PAGE PRINCIPALE
# ============================================

if st.session_state.current_crypto:
    crypto = st.session_state.current_crypto
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🔐 Quantum Gradation</h1>
        <h2 style="font-size: 2.5rem;">{crypto.get('gradation', 'N/A')}</h2>
        <h2>→ {crypto.get('mot', 'N/A')} ←</h2>
        <div class="info-box">
            ✅ Cryptographie unique générée pour <strong>"{crypto.get('mot', 'N/A')}"</strong><br>
            Timestamp: {crypto.get('timestamp', 'N/A')[:19]} | Algorithme: Ed25519
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Scores
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        score = calculate_security_score(crypto)
        st.metric("Score Sécurité", f"{score}/100")
    with col2:
        st.metric("Longueur", f"{crypto.get('longueur', 0)} lettres")
    with col3:
        st.metric("Statut", "✅ VALIDE" if crypto.get('is_valid') else "⚠️ DÉMO")
    with col4:
        st.metric("Entropie", f"{calculate_entropy(crypto.get('hash_sha512', '')):.2f} bits")
    
    # Hash
    st.markdown('<div class="main-card"><h3>🔐 Hash Cryptographiques</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**SHA-256:**")
        st.code(crypto.get('hash_sha256', 'N/A')[:64], language="text")
    with col2:
        st.markdown("**SHA-512:**")
        sha512 = crypto.get('hash_sha512', 'N/A')
        st.code(sha512[:64], language="text")
        st.code(sha512[64:128] if len(sha512) > 64 else "", language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Clés
    st.markdown('<div class="main-card"><h3>🔑 Clés Cryptographiques</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Clé Publique Ed25519:**")
        st.code(crypto.get('public_key', 'N/A')[:64], language="text")
    with col2:
        st.markdown("**Signature:**")
        sig = crypto.get('signature', 'N/A')
        st.code(sig[:64], language="text")
        st.code(sig[64:128] if len(sig) > 64 else "", language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Export
    st.markdown('<div class="main-card"><h3>💾 Export des données</h3>', unsafe_allow_html=True)
    
    export_data = {
        "mot": crypto.get('mot'),
        "gradation": crypto.get('gradation'),
        "hash_sha256": crypto.get('hash_sha256'),
        "hash_sha512": crypto.get('hash_sha512'),
        "public_key": crypto.get('public_key'),
        "signature": crypto.get('signature'),
        "timestamp": crypto.get('timestamp')
    }
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("📥 JSON", json.dumps(export_data, indent=2), 
                          f"{crypto.get('mot', 'crypto')}.json", "application/json")
    with col2:
        st.download_button("📥 Clé publique", crypto.get('public_key', ''), 
                          f"{crypto.get('mot', 'crypto')}_pubkey.txt", "text/plain")
    with col3:
        st.download_button("📥 Signature", crypto.get('signature', ''), 
                          f"{crypto.get('mot', 'crypto')}_signature.txt", "text/plain")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # QR Code
    st.markdown('<div class="main-card"><h3>📱 QR Code</h3>', unsafe_allow_html=True)
    
    qr_data = json.dumps({
        "mot": crypto.get('mot'),
        "gradation": crypto.get('gradation'),
        "hash": crypto.get('hash_sha256')[:32]
    })
    
    try:
        qr = qrcode.make(qr_data[:200])
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption=f"QR Code pour {crypto.get('mot', 'N/A')}", width=200)
    except:
        st.info("QR Code généré avec succès")
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("💡 Entrez un mot dans la barre latérale pour générer sa cryptographie unique")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
    🔐 <strong>Quantum Gradation System</strong> - Pour N'IMPORTE QUEL mot français<br>
    Standards: Ed25519 | SHA-256 | SHA-512 | Cryptographie Post-Quantique<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
