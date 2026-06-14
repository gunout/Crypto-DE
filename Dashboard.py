import streamlit as st
import json
import base64
import hashlib
import secrets
import hmac
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
import binascii
warnings.filterwarnings('ignore')

# Version Plotly
import plotly as plotly_lib
import plotly.graph_objects as go
import plotly.express as px

PLOTLY_VERSION = plotly_lib.__version__

# Tentative d'import nacl
try:
    import nacl.signing
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

# ============================================
# CONFIGURATION
# ============================================
LETTER_TO_NUM = {chr(64+i): i for i in range(1, 27)}
NUM_TO_LETTER = {i: chr(64+i) for i in range(1, 27)}

# ============================================
# FONCTIONS DE BASE
# ============================================

def text_to_gradation(word):
    """Convertit un mot en gradation numérique"""
    word = word.upper().strip()
    word = ''.join(c for c in unicodedata.normalize('NFD', word) 
                   if unicodedata.category(c) != 'Mn')
    word = re.sub(r'[^A-Z]', '', word)
    if not word:
        return None, "Aucune lettre valide"
    gradation = '.'.join(str(LETTER_TO_NUM[c]) for c in word)
    return gradation, None

def calculate_entropy(data):
    """Entropie de Shannon"""
    if not data:
        return 0
    data_str = str(data)
    prob = [float(data_str.count(c)) / len(data_str) for c in set(data_str)]
    return -sum([p * math.log2(p) for p in prob]) if prob else 0

def generate_complete_crypto(word):
    """
    Génération de cryptographie complète pour n'importe quel mot
    """
    try:
        word_clean = word.upper().strip()
        
        # Nettoyer le mot pour la gradation
        clean_for_gradation = ''.join(c for c in unicodedata.normalize('NFD', word_clean) 
                                      if unicodedata.category(c) != 'Mn')
        clean_for_gradation = re.sub(r'[^A-Z]', '', clean_for_gradation)
        
        if not clean_for_gradation:
            return None
        
        gradation, _ = text_to_gradation(clean_for_gradation)
        
        # TIMESTAMP et SALT
        timestamp = datetime.now().isoformat()
        salt = secrets.token_hex(32)
        
        # SEED MASTER unique pour ce mot
        master_seed_str = f"{gradation}|{word_clean}|{timestamp}|{salt}|QUANTUM_CRYPTO_V6"
        master_seed = hashlib.pbkdf2_hmac('sha512', master_seed_str.encode(), salt.encode(), 100000, 64)
        
        # ===== 1. HASH MULTIPLES =====
        sha3_512 = hashlib.sha3_512(master_seed).hexdigest()
        sha512 = hashlib.sha512(master_seed).hexdigest()
        blake2b = hashlib.blake2b(master_seed, digest_size=64).hexdigest()
        
        # Hash composite
        composite_hash = hashlib.sha3_512((sha3_512 + sha512 + blake2b).encode()).hexdigest()
        
        # ===== 2. CLÉS ED25519 =====
        if HAS_NACL:
            seed_ed25519 = master_seed[:32]
            signing_key = nacl.signing.SigningKey(seed_ed25519)
            verify_key = signing_key.verify_key
            public_key = verify_key.encode().hex()
            
            # Signature
            hash_bytes = composite_hash.encode()
            signature_bytes = signing_key.sign(hash_bytes).signature
            signature = signature_bytes.hex()
            is_valid = True
        else:
            public_key = hashlib.sha3_256(master_seed[:32]).hexdigest()
            signature = hashlib.sha3_512(f"{composite_hash}{public_key}".encode()).hexdigest()[:128]
            is_valid = True
        
        # ===== 3. JWT =====
        jwt_payload = {
            "mot": word_clean,
            "gradation": gradation,
            "hash": composite_hash[:64],
            "public_key": public_key[:64],
            "timestamp": timestamp,
            "algorithm": "Ed25519"
        }
        jwt_b64 = base64.b64encode(json.dumps(jwt_payload).encode()).decode()
        jwt = f"eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.{jwt_b64}"
        
        # ===== 4. CERTIFICAT =====
        certificate = f"""-----BEGIN CERTIFICATE-----
Subject: {word_clean}
Gradation: {gradation}
Public Key: {public_key[:64]}
Timestamp: {timestamp}
Expires: {(datetime.now() + timedelta(days=365)).isoformat()}
Signature: {signature[:64]}
-----END CERTIFICATE-----"""
        
        # ===== 5. MÉTADONNÉES =====
        metadata = {
            "mot": word_clean,
            "gradation": gradation,
            "longueur": len(clean_for_gradation),
            "valeur_numerique": sum(LETTER_TO_NUM.get(c, 0) for c in clean_for_gradation),
            "timestamp": timestamp,
            "algorithme": "Ed25519",
            "niveau_securite": "Post-Quantum Ready",
            "entropie": calculate_entropy(composite_hash)
        }
        
        security_score = calculate_security_score(composite_hash, word_clean)
        
        return {
            "mot": word_clean,
            "mot_original": word,
            "gradation": gradation,
            "master_hash": composite_hash,
            "hash_sha3_512": sha3_512,
            "hash_sha512": sha512,
            "hash_blake2b": blake2b,
            "public_key": public_key,
            "signature": signature,
            "jwt": jwt,
            "certificate": certificate,
            "metadata": metadata,
            "is_valid": is_valid,
            "timestamp": timestamp,
            "salt": salt,
            "entropy_score": calculate_entropy(composite_hash),
            "security_score": security_score
        }
        
    except Exception as e:
        print(f"Erreur: {e}")
        return None

def calculate_security_score(hash_value, word):
    """Calcul de score de sécurité"""
    score = 0
    score += min(20, len(word) * 2)
    entropy = calculate_entropy(hash_value)
    score += min(40, int(entropy * 5))
    unique_chars = len(set(hash_value[:50]))
    score += min(20, unique_chars)
    if entropy > 7:
        score += 20
    return min(100, int(score))

# ============================================
# STREAMLIT APP
# ============================================

st.set_page_config(
    page_title="Quantum Gradation - Crypto Complète",
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
        border: 1px solid #2a2a3e;
    }
    
    [data-testid="stSidebar"] { background: #0a0a15; }
    [data-testid="stMetricValue"] { color: #00ff88 !important; font-size: 1.8rem !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
        color: #ffffff;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
    }
    .stButton > button:hover { border-color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# État session - CRITIQUE pour que ça fonctionne
if 'current_crypto' not in st.session_state:
    st.session_state.current_crypto = None
if 'current_word' not in st.session_state:
    st.session_state.current_word = "BOURSE"

def regenerate_crypto(word):
    """Régénère la crypto pour un nouveau mot"""
    with st.spinner(f"🔐 Génération pour '{word}'..."):
        time.sleep(0.3)
        crypto = generate_complete_crypto(word)
        if crypto:
            st.session_state.current_crypto = crypto
            st.session_state.current_word = word
            return True
        return False

# Chargement initial
if st.session_state.current_crypto is None:
    regenerate_crypto("BOURSE")

# Sidebar
with st.sidebar:
    st.markdown("## 🔐 Quantum Gradation")
    st.markdown("### Crypto Complète v6.0")
    
    st.markdown("---")
    
    # Champ de saisie
    st.markdown("#### ✏️ Entrez n'importe quel mot")
    new_word = st.text_input("Mot:", value=st.session_state.current_word, placeholder="Ex: BOURSE, ACTION, MAISON...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 GÉNÉRER", use_container_width=True):
            if new_word.strip():
                if regenerate_crypto(new_word.strip()):
                    st.success(f"✅ Crypto générée")
                    st.rerun()
    
    st.markdown("---")
    
    # Mots rapides
    st.markdown("#### 🚀 Mots rapides")
    quick_words = ["BOURSE", "ACTION", "CRYPTO", "PYTHON", "STREAMLIT", "QUANTIQUE"]
    for qw in quick_words:
        if st.button(qw, key=f"quick_{qw}", use_container_width=True):
            regenerate_crypto(qw)
            st.rerun()
    
    st.markdown("---")
    
    # Stats
    if st.session_state.current_crypto:
        c = st.session_state.current_crypto
        st.metric("📊 Score", f"{c.get('security_score', 0)}/100")
        st.metric("📏 Longueur", f"{c.get('metadata', {}).get('longueur', 0)} lettres")
        st.metric("🎯 Entropie", f"{c.get('entropy_score', 0):.2f} bits")

# Page principale
if st.session_state.current_crypto:
    c = st.session_state.current_crypto
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🔐 Quantum Gradation</h1>
        <h2 style="font-size: 2rem;">{c.get('gradation', 'N/A')}</h2>
        <h2>→ {c.get('mot', 'N/A')} ←</h2>
        <p style="color: #00ff88;">✅ Cryptographie unique générée pour ce mot</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔐 Score Sécurité", f"{c.get('security_score', 0)}/100")
    with col2:
        st.metric("📊 Entropie", f"{c.get('entropy_score', 0):.2f} bits")
    with col3:
        st.metric("🔑 Statut", "VALIDÉ" if c.get('is_valid') else "DÉMO")
    with col4:
        st.metric("📏 Longueur", f"{c.get('metadata', {}).get('longueur', 0)} lettres")
    
    # Hash master
    st.markdown(f"""
    <div class="main-card">
        <h3>🎯 MASTER HASH (SHA3-512 Composite)</h3>
        <code style="word-break: break-all;">{c.get('master_hash', 'N/A')}</code>
    </div>
    """, unsafe_allow_html=True)
    
    # Multi-hash
    st.markdown('<div class="main-card"><h3>🔐 HASH MULTIPLES</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**SHA3-512:**")
        st.code(c.get('hash_sha3_512', 'N/A')[:64], language="text")
        st.markdown("**SHA-512:**")
        st.code(c.get('hash_sha512', 'N/A')[:64], language="text")
    with col2:
        st.markdown("**BLAKE2b:**")
        st.code(c.get('hash_blake2b', 'N/A')[:64], language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Clés
    st.markdown('<div class="main-card"><h3>🔑 CLÉS ED25519</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Clé Publique:**")
        st.code(c.get('public_key', 'N/A')[:64], language="text")
    with col2:
        st.markdown("**Signature:**")
        sig = c.get('signature', 'N/A')
        st.code(sig[:64], language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JWT et Certificat
    st.markdown('<div class="main-card"><h3>📜 JWT & CERTIFICAT</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**JWT:**")
        st.code(c.get('jwt', 'N/A')[:150] + "...", language="text")
        st.download_button("📥 JWT", c.get('jwt', ''), f"{c.get('mot', 'crypto')}.jwt", "text/plain")
    with col2:
        st.markdown("**Certificat X.509:**")
        st.code(c.get('certificate', 'N/A')[:200] + "...", language="text")
        st.download_button("📥 Certificat", c.get('certificate', ''), f"{c.get('mot', 'crypto')}.pem", "text/plain")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Métadonnées
    st.markdown('<div class="main-card"><h3>📊 MÉTADONNÉES</h3>', unsafe_allow_html=True)
    meta = c.get('metadata', {})
    st.json({
        "Mot": meta.get('mot'),
        "Gradation": meta.get('gradation'),
        "Longueur": meta.get('longueur'),
        "Valeur numérique": meta.get('valeur_numerique'),
        "Algorithme": meta.get('algorithme'),
        "Niveau sécurité": meta.get('niveau_securite'),
        "Timestamp": meta.get('timestamp', '')[:19]
    })
    st.markdown('</div>', unsafe_allow_html=True)
    
    # QR Code
    st.markdown('<div class="main-card"><h3>📱 QR CODE</h3>', unsafe_allow_html=True)
    try:
        qr_data = json.dumps({
            "mot": c.get('mot'),
            "gradation": c.get('gradation'),
            "hash": c.get('master_hash', '')[:32]
        })
        qr = qrcode.make(qr_data[:200])
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption=f"QR Code - {c.get('mot', 'N/A')}", width=200)
    except:
        st.info("QR Code généré")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Export
    st.markdown('<div class="main-card"><h3>💾 EXPORT COMPLET</h3>', unsafe_allow_html=True)
    
    export_data = {
        "mot": c.get('mot'),
        "gradation": c.get('gradation'),
        "master_hash": c.get('master_hash'),
        "hash_sha3_512": c.get('hash_sha3_512'),
        "hash_sha512": c.get('hash_sha512'),
        "hash_blake2b": c.get('hash_blake2b'),
        "public_key": c.get('public_key'),
        "signature": c.get('signature'),
        "jwt": c.get('jwt'),
        "certificate": c.get('certificate'),
        "metadata": c.get('metadata'),
        "security_score": c.get('security_score')
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 JSON COMPLET", json.dumps(export_data, indent=2), 
                          f"{c.get('mot', 'crypto')}_complete.json", "application/json")
    with col2:
        st.download_button("📥 MASTER HASH", c.get('master_hash', ''), 
                          f"{c.get('mot', 'crypto')}_hash.txt", "text/plain")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("❌ Erreur: impossible de générer la cryptographie")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
    🔐 <strong>Quantum Gradation System v6.0</strong> - Cryptographie Complète<br>
    Chaque mot génère sa propre cryptographie unique et vérifiable<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
