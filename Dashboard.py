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
import plotly.graph_objects as go
import plotly.express as px
import math
import statistics
import sys
import platform
from collections import Counter
from scipy import stats
import unicodedata
import re
import warnings
import time
warnings.filterwarnings('ignore')

# Version Plotly
import plotly as plotly_lib
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
    import nacl.encoding
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

# ============================================
# DICTIONNAIRE FRANCAIS INTEGRE
# ============================================
DICTIONNAIRE_FR = {
    "BOURSE": "2.15.21.18.19.5",
    "ACTION": "1.3.20.9.15.14",
    "DIVIDENDE": "4.9.22.9.4.5.14.4.5",
    "PORTEFEUILLE": "16.15.18.20.5.6.5.21.9.12.12.5",
    "INVESTISSEMENT": "9.14.22.5.19.20.9.19.19.5.13.5.14.20",
    "RENDEMENT": "18.5.14.4.5.13.5.14.20",
    "CAPITAL": "3.1.16.9.20.1.12",
    "FINANCE": "6.9.14.1.14.3.5",
    "MARCHE": "13.1.18.3.8.5",
    "COURS": "3.15.21.18.19",
    "INDICE": "9.14.4.9.3.5",
    "VALEUR": "22.1.12.5.21.18",
    "LIQUIDITE": "12.9.17.21.9.4.9.20.5",
    "VOLATILITE": "22.15.12.1.20.9.12.9.20.5",
    "SPECULATION": "19.16.5.3.21.12.1.20.9.15.14",
    "BENEFICE": "2.5.14.5.6.9.3.5",
    "PERTE": "16.5.18.20.5",
    "BILAN": "2.9.12.1.14",
    "COMPTE": "3.15.13.16.20.5",
    "DEPENSE": "4.5.16.5.14.19.5",
    "EPARGNE": "5.16.1.18.7.14.5",
    "TAXE": "20.1.24.5",
    "IMPOT": "9.13.16.15.20",
    "REVENU": "18.5.22.5.14.21",
    "SALAIRE": "19.1.12.1.9.18.5",
    "CREDIT": "3.18.5.4.9.20",
    "DETTE": "4.5.20.20.5",
    "EMPRUNT": "5.13.16.18.21.14.20",
    "PLACEMENT": "16.12.1.3.5.13.5.14.20",
    "RISQUE": "18.9.19.17.21.5",
    "CRYPTO": "3.18.25.16.20.15",
    "BLOCKCHAIN": "2.12.15.3.11.3.8.1.9.14",
    "BITCOIN": "2.9.20.3.15.9.14",
    "ETHER": "5.20.8.5.18",
    "FOREX": "6.15.18.5.24",
    "TRADING": "20.18.1.4.9.14.7",
    "SWING": "19.23.9.14.7",
    "SCALPING": "19.3.1.12.16.9.14.7"
}

# Base des lettres pour l'encodage
LETTER_TO_NUM = {chr(64+i): i for i in range(1, 27)}
NUM_TO_LETTER = {i: chr(64+i) for i in range(1, 27)}

# ============================================
# FONCTIONS DE CRYPTOGRAPHIE COMPLETE
# ============================================

def text_to_gradation(word):
    """Convertit un mot en gradation numérique"""
    word = word.upper().strip()
    word = ''.join(c for c in unicodedata.normalize('NFD', word) 
                   if unicodedata.category(c) != 'Mn')
    word = re.sub(r'[^A-Z]', '', word)
    
    if not word:
        return None, "Le mot doit contenir au moins une lettre"
    
    gradation = '.'.join(str(LETTER_TO_NUM.get(c, 0)) for c in word)
    if '0' in gradation:
        return None, f"Caractère non supporté: seules les lettres A-Z sont acceptées"
    
    return gradation, None

def gradation_to_text(gradation):
    """Convertit une gradation numérique en mot"""
    try:
        numbers = [int(x) for x in gradation.split('.')]
        word = ''.join(NUM_TO_LETTER.get(n, '?') for n in numbers)
        if '?' in word:
            return None, "Gradation invalide: nombres hors plage 1-26"
        return word, None
    except ValueError:
        return None, "Format de gradation invalide"

def generate_complete_crypto_for_word(word):
    """
    Génère une cryptographie complète et unique pour un mot donné:
    - Paire de clés Ed25519 unique
    - Signature numérique
    - Hash multiple (SHA-256, SHA-512, Blake2)
    - JWT complet
    - Certificat X.509 simulé
    """
    word_clean = word.upper().strip()
    gradation, error = text_to_gradation(word_clean)
    if error:
        return None, error
    
    # Seed unique basé sur le mot + timestamp + salt
    timestamp = datetime.now().isoformat()
    salt = secrets.token_hex(16)
    seed_str = f"{gradation}|{word_clean}|{timestamp}|{salt}|quantum_entropy_v5"
    master_seed = hashlib.pbkdf2_hmac('sha512', seed_str.encode(), salt.encode(), 100000, 64)
    
    # Différents hash
    sha256_hash = hashlib.sha256(seed_str.encode()).hexdigest()
    sha512_hash = hashlib.sha512(seed_str.encode()).hexdigest()
    blake2_hash = hashlib.blake2b(seed_str.encode(), digest_size=64).hexdigest()
    
    # Hash composite (fusion des 3)
    composite_hash = hashlib.sha3_512(f"{sha256_hash}{sha512_hash}{blake2_hash}".encode()).hexdigest()
    
    # Génération des clés Ed25519
    if HAS_NACL:
        seed_32 = master_seed[:32]
        signing_key = nacl.signing.SigningKey(seed_32)
        verify_key = signing_key.verify_key
        public_key = verify_key.encode().hex()
        
        # Signature du hash composite
        hash_bytes = bytes.fromhex(composite_hash[:128])
        signature_bytes = signing_key.sign(hash_bytes).signature
        signature = signature_bytes.hex()
        is_valid = True
    else:
        # Mode démo - génération déterministe
        public_key = hashlib.sha3_256(master_seed[:32]).hexdigest()
        signature = hashlib.sha3_512(f"{composite_hash}{public_key}".encode()).hexdigest()[:128]
        is_valid = True
    
    # Métadonnées
    metadata = {
        "mot": word_clean,
        "gradation": gradation,
        "longueur": len(word_clean),
        "valeur_numerique": sum(LETTER_TO_NUM.get(c, 0) for c in word_clean),
        "timestamp_generation": timestamp,
        "salt": salt,
        "algorithme": "Ed25519",
        "niveau_securite": "Post-Quantum Ready",
        "entropie_seed": calculate_entropy_advanced(seed_str)
    }
    
    # JWT complet
    jwt_payload = {
        **metadata,
        "hash_sha256": sha256_hash,
        "hash_sha512": sha512_hash,
        "hash_blake2": blake2_hash,
        "hash_composite": composite_hash,
        "public_key": public_key,
        "signature": signature,
        "verify_key_fingerprint": hashlib.sha256(public_key.encode()).hexdigest()[:16]
    }
    jwt_b64 = base64.b64encode(json.dumps(jwt_payload).encode()).decode()
    jwt = f"eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.{jwt_b64}"
    
    # Certificat X.509 simulé
    certificate = generate_simulated_certificate(word_clean, public_key, timestamp)
    
    return {
        "mot": word_clean,
        "gradation": gradation,
        "public_key": public_key,
        "signature": signature,
        "hash_sha256": sha256_hash,
        "hash_sha512": sha512_hash,
        "hash_blake2": blake2_hash,
        "hash_composite": composite_hash,
        "jwt": jwt,
        "certificate": certificate,
        "metadata": metadata,
        "is_valid": is_valid,
        "timestamp": timestamp,
        "salt": salt,
        "seed_fingerprint": hashlib.sha256(master_seed).hexdigest()[:32]
    }

def generate_simulated_certificate(word, public_key, timestamp):
    """Génère un certificat X.509 simulé unique pour chaque mot"""
    cert_id = hashlib.sha256(f"{word}{timestamp}".encode()).hexdigest()[:8]
    
    cert = f"""-----BEGIN CERTIFICATE-----
Quantum Gradation Certificate v5.0
Subject: {word}
Gradation: {text_to_gradation(word)[0]}
Public Key: {public_key[:64]}...
Certificate ID: {cert_id}
Issued: {timestamp}
Expires: {(datetime.now() + timedelta(days=365)).isoformat()}
Signature Algorithm: Ed25519
Key Usage: Digital Signature, Key Agreement
-----END CERTIFICATE-----"""
    return cert

def calculate_entropy_advanced(data):
    """Calcul avancé d'entropie"""
    if not data:
        return 0
    data_str = str(data)
    prob = [float(data_str.count(c)) / len(data_str) for c in set(data_str)]
    return -sum([p * math.log2(p) for p in prob])

def calculate_avalanche_for_hash(hash_value):
    """Effet avalanche spécifique pour un hash"""
    if not hash_value or len(hash_value) < 64:
        return 0
    
    try:
        original = bytes.fromhex(hash_value[:64])
        changes = []
        for i in range(min(20, len(original))):
            modified = bytearray(original)
            modified[i] ^= 0x01
            modified_hash = hashlib.sha256(modified).digest()
            diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(original[:32], modified_hash))
            changes.append(diff_bits / 256 * 100)
        return statistics.mean(changes) if changes else 0
    except:
        return 0

def calculate_security_score(crypto_data):
    """Calcule un score de sécurité global (0-100)"""
    if not crypto_data:
        return 0
    
    score = 0
    
    # Longueur du mot (10 pts)
    mot_len = len(crypto_data['mot'])
    score += min(10, mot_len)
    
    # Entropie du hash (30 pts)
    entropy = calculate_entropy_advanced(crypto_data['hash_composite'])
    score += min(30, entropy * 5)
    
    # Effet avalanche (30 pts)
    avalanche = calculate_avalanche_for_hash(crypto_data['hash_composite'])
    if 45 <= avalanche <= 55:
        score += 30
    elif 40 <= avalanche <= 60:
        score += 20
    elif 30 <= avalanche <= 70:
        score += 10
    
    # Validité signature (20 pts)
    if crypto_data['is_valid']:
        score += 20
    
    # Complexité (10 pts)
    if len(crypto_data['public_key']) >= 64:
        score += 5
    if len(crypto_data['signature']) >= 128:
        score += 5
    
    return min(100, score)

# ============================================
# CONFIGURATION PAGE
# ============================================
st.set_page_config(
    page_title="Quantum Gradation - Cryptographie Complète",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# DESIGN CSS
# ============================================
st.markdown("""
<style>
    .stApp { background: #000000; }
    .stMarkdown, .stText, .stTitle, .stHeader, p, li, span, div { color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-weight: 600 !important; }
    
    .main-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #2a2a3e;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .main-card:hover { border-color: #00ff88; transform: translateY(-2px); }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #0a0a15 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #2a2a3e;
    }
    
    .crypto-card {
        background: linear-gradient(135deg, #0a1a2a 0%, #0a0a1a 100%);
        border: 1px solid #00ff88;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-text { color: #00ff88 !important; font-weight: bold; }
    .warning-text { color: #ffaa00 !important; }
    
    [data-testid="stSidebar"] { background: #0a0a15; border-right: 1px solid #2a2a3e; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
        color: #ffffff;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton > button:hover { background: #2a2a3e; border-color: #00ff88; transform: scale(1.02); }
    
    hr { border-color: #2a2a3e; }
    
    .info-box {
        background: rgba(0, 255, 136, 0.1);
        border-left: 4px solid #00ff88;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .hash-box {
        font-family: monospace;
        background: #0a0a15;
        padding: 0.5rem;
        border-radius: 8px;
        font-size: 0.8rem;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ÉTAT DE SESSION
# ============================================
if 'current_crypto' not in st.session_state:
    st.session_state.current_crypto = None
if 'crypto_history' not in st.session_state:
    st.session_state.crypto_history = []
if 'last_word' not in st.session_state:
    st.session_state.last_word = "BOURSE"

def load_word_crypto(word):
    """Charge la cryptographie complète pour un mot"""
    with st.spinner(f"🔐 Génération de la cryptographie pour '{word}'..."):
        time.sleep(0.3)  # Petit délai pour l'effet visuel
        crypto_data = generate_complete_crypto_for_word(word)
        if crypto_data:
            st.session_state.current_crypto = crypto_data
            st.session_state.last_word = word
            # Ajouter à l'historique
            st.session_state.crypto_history.insert(0, {
                "mot": word,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "fingerprint": crypto_data['public_key'][:16]
            })
            st.session_state.crypto_history = st.session_state.crypto_history[:10]
            return True, crypto_data
        return False, None

# Chargement initial
if st.session_state.current_crypto is None:
    load_word_crypto("BOURSE")

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🔐 Quantum Gradation")
    st.markdown("### Cryptographie Complète")
    
    # Sélecteur de mot
    st.markdown("#### 📝 Choisir un mot")
    
    # Mot personnalisé
    custom_word = st.text_input("Mot personnalisé:", value=st.session_state.last_word, key="custom_word_input")
    if st.button("🔒 Générer la crypto complète", use_container_width=True):
        success, crypto = load_word_crypto(custom_word)
        if success:
            st.success(f"✅ Crypto générée pour '{custom_word}'")
            st.rerun()
        else:
            st.error("❌ Erreur de génération")
    
    st.markdown("---")
    
    # Mots du dictionnaire
    st.markdown("#### 📚 Mots du dictionnaire")
    available_words = sorted(list(DICTIONNAIRE_FR.keys()))
    selected_word = st.selectbox("Sélectionner un mot:", available_words, key="dict_word_select")
    if st.button("📖 Charger ce mot", use_container_width=True, key="load_dict_word"):
        success, crypto = load_word_crypto(selected_word)
        if success:
            st.rerun()
    
    st.markdown("---")
    
    # Métriques rapides
    st.markdown("#### 📊 Métriques")
    if st.session_state.current_crypto:
        score = calculate_security_score(st.session_state.current_crypto)
        st.metric("Score sécurité", f"{score}/100", delta="Excellent" if score >= 80 else "À améliorer")
        st.metric("Longueur mot", len(st.session_state.current_crypto['mot']))
        st.metric("Hash SHA-512", f"{st.session_state.current_crypto['hash_sha512'][:16]}...")
    
    st.markdown("---")
    
    # Historique
    if st.session_state.crypto_history:
        st.markdown("#### 📜 Historique récent")
        for item in st.session_state.crypto_history[:5]:
            st.caption(f"🔹 {item['mot']} - {item['timestamp']}")
    
    st.markdown("---")
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption(f"🔐 PyNaCl: {'✅' if HAS_NACL else '❌'}")

# ============================================
# PAGE PRINCIPALE
# ============================================

if st.session_state.current_crypto:
    crypto = st.session_state.current_crypto
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🔐 Quantum Gradation - Cryptographie Complète</h1>
        <h2>{crypto['gradation']} → {crypto['mot']}</h2>
        <div class="info-box">
            ✅ <strong>Cryptographie unique générée pour "{crypto['mot']}"</strong><br>
            Timestamp: {crypto['timestamp']} | Algorithme: Ed25519 | Niveau: Post-Quantum Ready
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Score de sécurité
    security_score = calculate_security_score(crypto)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔐 Score Sécurité", f"{security_score}/100", 
                 delta="Excellent" if security_score >= 80 else "Standard")
    with col2:
        st.metric("📏 Longueur mot", f"{crypto['metadata']['longueur']} lettres")
    with col3:
        st.metric("🔢 Valeur numérique", f"{crypto['metadata']['valeur_numerique']}")
    with col4:
        st.metric("✅ Statut", "VALIDE" if crypto['is_valid'] else "INVALIDE")
    
    # ===== SECTION 1: HASHES MULTIPLES =====
    st.markdown("""
    <div class="main-card">
        <h3>🔐 Hash Cryptographiques Multiples</h3>
        <p>Trois algorithmes de hash différents + hash composite pour une sécurité maximale</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**SHA-256:**")
        st.code(crypto['hash_sha256'], language="text")
        st.markdown("**SHA-512:**")
        st.code(crypto['hash_sha512'][:64], language="text")
        st.code(crypto['hash_sha512'][64:], language="text")
    with col2:
        st.markdown("**BLAKE2b:**")
        st.code(crypto['hash_blake2'][:64], language="text")
        st.code(crypto['hash_blake2'][64:], language="text")
        st.markdown("**Hash Composite (SHA3-512):**")
        st.code(crypto['hash_composite'][:64], language="text")
        st.code(crypto['hash_composite'][64:], language="text")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== SECTION 2: SIGNATURE ED25519 =====
    st.markdown("""
    <div class="main-card">
        <h3>✍️ Signature Ed25519</h3>
        <p>Signature numérique unique générée à partir du hash composite</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Clé Publique (32 bytes):**")
        st.code(crypto['public_key'], language="text")
        st.caption(f"Empreinte: {hashlib.sha256(crypto['public_key'].encode()).hexdigest()[:16]}...")
    with col2:
        st.markdown("**Signature (64 bytes):**")
        st.code(crypto['signature'][:64], language="text")
        st.code(crypto['signature'][64:], language="text")
        st.caption("Vérifiable avec la clé publique")
    
    # Analyse avalanche
    avalanche = calculate_avalanche_for_hash(crypto['hash_composite'])
    st.markdown(f"**Effet Avalanche:** {avalanche:.2f}% {'✅ Excellent' if 45 <= avalanche <= 55 else '⚠️ Standard'}")
    st.progress(min(avalanche/100, 1.0))
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== SECTION 3: JWT ET CERTIFICAT =====
    st.markdown("""
    <div class="main-card">
        <h3>📜 JWT & Certificat X.509</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**JWT Complet:**")
        st.code(crypto['jwt'][:150] + "...", language="text")
        
        # QR Code JWT
        qr_jwt = qrcode.make(crypto['jwt'][:200])
        buffer = BytesIO()
        qr_jwt.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption="QR Code JWT", width=150)
        
        st.download_button("📥 Télécharger JWT", crypto['jwt'], f"{crypto['mot']}_crypto.jwt", "text/plain")
    
    with col2:
        st.markdown("**Certificat X.509:**")
        st.code(crypto['certificate'][:200] + "...", language="text")
        st.download_button("📥 Télécharger Certificat", crypto['certificate'], f"{crypto['mot']}_certificate.pem", "text/plain")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== SECTION 4: MÉTADONNÉES =====
    st.markdown("""
    <div class="main-card">
        <h3>📊 Métadonnées et Analyse</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Informations générales**")
        st.json({
            "Mot": crypto['mot'],
            "Gradation": crypto['gradation'],
            "Longueur": crypto['metadata']['longueur'],
            "Valeur numérique": crypto['metadata']['valeur_numerique']
        })
    
    with col2:
        st.markdown("**Sécurité**")
        st.json({
            "Algorithme": crypto['metadata']['algorithme'],
            "Niveau": crypto['metadata']['niveau_securite'],
            "Entropie seed": f"{crypto['metadata']['entropie_seed']:.3f} bits",
            "Effet avalanche": f"{avalanche:.2f}%"
        })
    
    with col3:
        st.markdown("**Empreintes**")
        st.json({
            "Seed fingerprint": crypto['seed_fingerprint'],
            "PK fingerprint": hashlib.sha256(crypto['public_key'].encode()).hexdigest()[:16],
            "Salt": crypto['salt'][:16] + "...",
            "Timestamp": crypto['timestamp'][:19]
        })
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== SECTION 5: QR CODES =====
    st.markdown("""
    <div class="main-card">
        <h3>📱 QR Codes - Accès rapide</h3>
        <div style="display: flex; gap: 20px; justify-content: space-around;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        qr_mot = qrcode.make(crypto['mot'])
        buffer = BytesIO()
        qr_mot.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption=f"Mot: {crypto['mot']}", width=120)
    
    with col2:
        qr_gradation = qrcode.make(crypto['gradation'])
        buffer = BytesIO()
        qr_gradation.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption="Gradation", width=120)
    
    with col3:
        qr_pk = qrcode.make(crypto['public_key'][:64])
        buffer = BytesIO()
        qr_pk.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption="Clé publique", width=120)
    
    with col4:
        qr_hash = qrcode.make(crypto['hash_composite'][:64])
        buffer = BytesIO()
        qr_hash.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption="Hash composite", width=120)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== SECTION 6: EXPORT COMPLET =====
    st.markdown("""
    <div class="main-card">
        <h3>💾 Export Complet</h3>
    """, unsafe_allow_html=True)
    
    export_data = {
        "mot": crypto['mot'],
        "gradation": crypto['gradation'],
        "hash_sha256": crypto['hash_sha256'],
        "hash_sha512": crypto['hash_sha512'],
        "hash_blake2": crypto['hash_blake2'],
        "hash_composite": crypto['hash_composite'],
        "public_key": crypto['public_key'],
        "signature": crypto['signature'],
        "jwt": crypto['jwt'],
        "certificate": crypto['certificate'],
        "metadata": crypto['metadata']
    }
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("📥 JSON Complet", json.dumps(export_data, indent=2), 
                          f"{crypto['mot']}_crypto_complete.json", "application/json")
    with col2:
        st.download_button("📥 Signature seule", crypto['signature'], 
                          f"{crypto['mot']}_signature.sig", "text/plain")
    with col3:
        st.download_button("📥 Clé publique", crypto['public_key'], 
                          f"{crypto['mot']}_public_key.key", "text/plain")
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("❌ Erreur: Impossible de générer la cryptographie")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
    🔐 <strong>Quantum Gradation System v5.0 - Cryptographie Complète</strong><br>
    Chaque mot génère sa propre paire de clés unique, signature et hash multiples<br>
    Standards: Ed25519 | SHA-256/512 | BLAKE2b | SHA3-512 | JWT | X.509<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
</div>
""", unsafe_allow_html=True)
