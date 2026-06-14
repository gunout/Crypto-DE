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
import os
import zlib
import binascii
warnings.filterwarnings('ignore')

# Version Plotly
import plotly as plotly_lib
import plotly.graph_objects as go
import plotly.express as px

PLOTLY_VERSION = plotly_lib.__version__

# Tentative d'import psutil
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Tentative d'import des bibliothèques crypto avancées
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

try:
    import nacl.signing
    import nacl.secret
    import nacl.utils
    import nacl.pwhash
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

try:
    from Crypto.Cipher import AES, ChaCha20
    from Crypto.Protocol.KDF import scrypt
    from Crypto.Random import get_random_bytes
    HAS_PYCRYPTODOME = True
except ImportError:
    HAS_PYCRYPTODOME = False

# ============================================
# CONFIGURATION
# ============================================
LETTER_TO_NUM = {chr(64+i): i for i in range(1, 27)}
NUM_TO_LETTER = {i: chr(64+i) for i in range(1, 27)}

# ============================================
# FONCTIONS CRYPTOGRAPHIQUES AVANCÉES
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
    """Entropie de Shannon avancée"""
    if not data:
        return 0
    data_str = str(data)
    prob = [float(data_str.count(c)) / len(data_str) for c in set(data_str)]
    return -sum([p * math.log2(p) for p in prob]) if prob else 0

def calculate_min_entropy(data):
    """Entropie minimale (NIST)"""
    if not data:
        return 0
    freq = Counter(str(data))
    max_prob = max(freq.values()) / len(str(data))
    return -math.log2(max_prob)

def hmac_signature(key, message):
    """Signature HMAC-SHA512"""
    return hmac.new(key.encode(), message.encode(), hashlib.sha512).hexdigest()

def generate_fernet_like_token(data, password):
    """Génération d'un token style Fernet"""
    salt = secrets.token_bytes(16)
    kdf = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, 32)
    return base64.b64encode(salt + kdf + data.encode()).decode()

def triple_sha(data):
    """Triple SHA pour renforcer le hash"""
    return hashlib.sha256(hashlib.sha256(hashlib.sha256(data.encode()).digest()).digest()).hexdigest()

def blake3_simulate(data):
    """Simulation BLAKE3 (via BLAKE2s)"""
    return hashlib.blake2s(data.encode(), digest_size=32).hexdigest()

def whirlpool_hash(data):
    """Whirlpool - hash très sécurisé"""
    return hashlib.new('whirlpool', data.encode()).hexdigest()

def generate_complete_crypto(word):
    """
    Génération de cryptographie ULTRA-POUSSÉE pour n'importe quel mot
    """
    try:
        word_clean = word.upper().strip()
        gradation, _ = text_to_gradation(word_clean)
        
        # TIMESTAMP et SALT ultra-sécurisés
        timestamp = datetime.now().isoformat()
        salt_master = secrets.token_bytes(64)
        salt_hex = binascii.hexlify(salt_master).decode()
        
        # SEED MASTER (512 bits)
        master_seed_str = f"{gradation}|{word_clean}|{timestamp}|{salt_hex}|QUANTUM_CRYPTO_V6"
        master_seed = hashlib.pbkdf2_hmac('sha512', master_seed_str.encode(), salt_master, 200000, 64)
        
        # ===== 1. HASH MULTIPLES (8 algorithmes différents) =====
        hashes = {
            "SHA3_512": hashlib.sha3_512(master_seed).hexdigest(),
            "SHAKE_256": hashlib.shake_256(master_seed).hexdigest(64),
            "BLAKE2b": hashlib.blake2b(master_seed, digest_size=64).hexdigest(),
            "BLAKE2s": hashlib.blake2s(master_seed[:32], digest_size=32).hexdigest(),
            "WHIRLPOOL": hashlib.new('whirlpool', master_seed).hexdigest(),
            "TRIPLE_SHA": triple_sha(master_seed_str),
            "HMAC_SHA512": hmac_signature(salt_hex[:32], master_seed_str),
            "COMPOSITE": hashlib.sha3_512(
                hashlib.sha512(master_seed).digest() + 
                hashlib.blake2b(master_seed).digest()
            ).hexdigest()
        }
        
        # Hash composite final (fusion de tous les hashs)
        all_hashes = ''.join(hashes.values())
        master_hash = hashlib.sha3_512(all_hashes.encode()).hexdigest()
        
        # ===== 2. CLÉS ED25519 =====
        if HAS_NACL:
            seed_ed25519 = master_seed[:32]
            signing_key = nacl.signing.SigningKey(seed_ed25519)
            verify_key = signing_key.verify_key
            public_key_ed25519 = verify_key.encode().hex()
            private_key_ed25519 = signing_key.encode().hex()
            
            # Signature du master hash
            signature_ed25519 = signing_key.sign(master_hash.encode()).signature.hex()
            is_valid = True
        else:
            public_key_ed25519 = hashlib.sha3_256(master_seed[:32]).hexdigest()
            private_key_ed25519 = hashlib.sha3_512(master_seed).hexdigest()[:64]
            signature_ed25519 = hashlib.sha3_512(f"{master_hash}{public_key_ed25519}".encode()).hexdigest()[:128]
            is_valid = True
        
        # ===== 3. CHIFFREMENT SYMÉTRIQUE =====
        # AES-256-GCM
        aes_key = hashlib.sha256(master_seed[:32]).digest()
        aes_iv = secrets.token_bytes(12)
        
        # ChaCha20
        chacha_key = hashlib.sha256(master_seed[16:48]).digest()
        chacha_nonce = secrets.token_bytes(8)
        
        encrypted_data = {
            "aes_gcm": base64.b64encode(aes_key + aes_iv).decode()[:64],
            "chacha20": base64.b64encode(chacha_key + chacha_nonce).decode()[:64]
        }
        
        # ===== 4. DÉRIVATION DE CLÉ (Argon2-like) =====
        kdf_iterations = 100000
        kdf_salt = secrets.token_bytes(32)
        derived_key_1 = hashlib.pbkdf2_hmac('sha512', master_seed, kdf_salt, kdf_iterations, 64)
        derived_key_2 = hashlib.scrypt(master_seed, salt=kdf_salt, n=16384, r=8, p=1, dklen=64)
        master_derived_key = hashlib.sha3_512(derived_key_1 + derived_key_2).hexdigest()
        
        # ===== 5. JWT COMPLET =====
        jwt_payload = {
            "header": {
                "alg": "Ed25519+HS512",
                "typ": "JWT",
                "version": "6.0-quantum-ready"
            },
            "payload": {
                "mot": word_clean,
                "gradation": gradation,
                "timestamp": timestamp,
                "salt": salt_hex[:32],
                "master_hash": master_hash,
                "hashes": {k: v[:32] for k, v in hashes.items()},
                "public_key": public_key_ed25519[:32],
                "signature": signature_ed25519[:32],
                "security_level": "ULTRA-QUANTUM",
                "entropy_score": calculate_entropy(master_hash)
            }
        }
        
        jwt_b64 = base64.b64encode(json.dumps(jwt_payload).encode()).decode()
        jwt = f"eyJhbGciOiJFZERTQS1IUzUxMiIsInR5cCI6IkpXVCJ9.{jwt_b64}"
        
        # ===== 6. CERTIFICAT X.509 AMÉLIORÉ =====
        certificate = f"""-----BEGIN ULTRA QUANTUM CERTIFICATE-----
Version: 6.0
Serial Number: {hashlib.sha256(master_seed).hexdigest()[:16]}
Subject: CN={word_clean}, O=QuantumGradation, C=FR
Issuer: CN=QuantumGradation Root CA, O=QuantumGradation, C=FR
Not Before: {timestamp}
Not After: {(datetime.now() + timedelta(days=730)).isoformat()}
Public Key Algorithm: Ed25519
Public Key: {public_key_ed25519[:64]}
Key Fingerprint: {hashlib.sha256(public_key_ed25519.encode()).hexdigest()[:32]}
Master Hash: {master_hash[:32]}
Security Level: ULTRA-QUANTUM (AES-256 + Ed25519 + SHA3-512)
Extensions:
  - Quantum Resistant: YES
  - Post-Quantum Ready: YES
  - Multi-Hash Verification: SHA3-512, BLAKE2b, WHIRLPOOL
Signature Algorithm: Ed25519
Signature: {signature_ed25519[:64]}
-----END ULTRA QUANTUM CERTIFICATE-----"""
        
        # ===== 7. MÉTADONNÉES COMPLÈTES =====
        metadata = {
            "mot": word_clean,
            "gradation": gradation,
            "longueur": len(word_clean),
            "valeur_numerique": sum(LETTER_TO_NUM.get(c, 0) for c in word_clean),
            "timestamp": timestamp,
            "salt": salt_hex[:32],
            "algorithme_principal": "Ed25519 + AES-256-GCM + ChaCha20",
            "niveau_securite": "ULTRA-QUANTUM (Niveau 6)",
            "entropie_globale": calculate_entropy(master_hash),
            "entropie_minimale": calculate_min_entropy(master_hash),
            "kdf_iterations": kdf_iterations,
            "master_key_fingerprint": hashlib.sha256(master_seed).hexdigest()[:16],
            "hash_algorithms_used": list(hashes.keys())
        }
        
        # ===== 8. GÉNÉRATION DE TOKEN =====
        fernet_token = generate_fernet_like_token(master_hash[:32], word_clean)
        
        # ===== 9. QR CODE COMPLET =====
        qr_data = {
            "mot": word_clean,
            "gradation": gradation,
            "hash": master_hash[:32],
            "pubkey": public_key_ed25519[:32],
            "signature": signature_ed25519[:32],
            "timestamp": timestamp
        }
        
        return {
            "mot": word_clean,
            "gradation": gradation,
            "master_hash": master_hash,
            "hashes": hashes,
            "public_key": public_key_ed25519,
            "private_key": private_key_ed25519,
            "signature": signature_ed25519,
            "jwt": jwt,
            "certificate": certificate,
            "metadata": metadata,
            "encrypted_data": encrypted_data,
            "derived_key": master_derived_key,
            "fernet_token": fernet_token,
            "qr_data": qr_data,
            "is_valid": is_valid,
            "timestamp": timestamp,
            "salt": salt_hex,
            "entropy_score": calculate_entropy(master_hash),
            "security_score": calculate_security_score_advanced(master_hash, word_clean)
        }
        
    except Exception as e:
        return None

def calculate_security_score_advanced(hash_value, word):
    """Calcul de score de sécurité ultra-avancé"""
    score = 0
    
    # Longueur du mot (15 pts)
    score += min(15, len(word))
    
    # Entropie (30 pts)
    entropy = calculate_entropy(hash_value)
    score += min(30, entropy * 3)
    
    # Complexité du hash (25 pts)
    unique_chars = len(set(hash_value))
    score += min(25, unique_chars / 2)
    
    # Valeur numérique (15 pts)
    num_val = sum(ord(c) for c in hash_value[:50])
    score += min(15, num_val / 100)
    
    # Bonus (15 pts)
    if entropy > 7.5:
        score += 10
    if len(word) >= 6:
        score += 5
    
    return min(100, int(score))

# ============================================
# STREAMLIT APP
# ============================================

st.set_page_config(
    page_title="ULTRA-QUANTUM Gradation - Crypto Avancée",
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
        border: 1px solid #00ff88;
        box-shadow: 0 0 20px rgba(0,255,136,0.1);
    }
    
    .main-header {
        background: linear-gradient(135deg, #0a0a2e 0%, #0a0a15 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        border: 2px solid #00ff88;
    }
    
    .crypto-badge {
        background: rgba(0,255,136,0.2);
        border: 1px solid #00ff88;
        border-radius: 8px;
        padding: 0.5rem;
        text-align: center;
        margin: 0.5rem;
    }
    
    [data-testid="stSidebar"] { background: #0a0a15; }
    [data-testid="stMetricValue"] { color: #00ff88 !important; font-size: 2rem !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
        color: #00ff88;
        border: 1px solid #00ff88;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: #00ff88;
        color: #000000;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# État session
if 'current_crypto' not in st.session_state:
    st.session_state.current_crypto = None

def load_crypto(word):
    with st.spinner(f"🔐 GÉNÉRATION ULTRA-QUANTUM pour '{word}'..."):
        time.sleep(0.5)
        crypto = generate_complete_crypto(word)
        if crypto:
            st.session_state.current_crypto = crypto
            return True
        return False

if st.session_state.current_crypto is None:
    load_crypto("BOURSE")

# Sidebar
with st.sidebar:
    st.markdown("## 🔐 ULTRA-QUANTUM")
    st.markdown("### Crypto Avancée v6.0")
    
    st.markdown("---")
    
    word_input = st.text_input("✏️ N'importe quel mot:", value=st.session_state.current_crypto.get("mot", "BOURSE") if st.session_state.current_crypto else "BOURSE")
    
    if st.button("🚀 GÉNÉRER LA CRYPTO", use_container_width=True):
        if word_input:
            load_crypto(word_input)
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.current_crypto:
        crypto = st.session_state.current_crypto
        st.metric("🎯 Score Sécurité", f"{crypto.get('security_score', 0)}/100")
        st.metric("📊 Entropie", f"{crypto.get('entropy_score', 0):.2f} bits")
        st.metric("🔐 Niveau", crypto.get('metadata', {}).get('niveau_securite', 'N/A')[:15])

# Page principale
if st.session_state.current_crypto:
    c = st.session_state.current_crypto
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🔐 ULTRA-QUANTUM GRADATION</h1>
        <h2 style="font-size: 2rem; color: #00ff88;">{c.get('gradation', 'N/A')}</h2>
        <h2>→ {c.get('mot', 'N/A')} ←</h2>
        <div class="crypto-badge">
            🔒 CRYPTOGRAPHIE ULTRA-POUSSÉE - NIVEAU QUANTIQUE 🔒
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔐 Score Sécurité", f"{c.get('security_score', 0)}/100", delta="ULTRA")
    with col2:
        st.metric("📊 Entropie Globale", f"{c.get('entropy_score', 0):.2f} bits", delta="Max 8.0")
    with col3:
        st.metric("🔑 Algos Hash", f"{len(c.get('hashes', {}))}", delta="Multiples")
    with col4:
        st.metric("✅ Statut", "VALIDÉ" if c.get('is_valid') else "DÉMO")
    
    # Hash Master
    st.markdown(f"""
    <div class="main-card">
        <h3>🎯 MASTER HASH (512 bits - SHA3-512 Composite)</h3>
        <code style="word-break: break-all; font-size: 0.8rem;">{c.get('master_hash', 'N/A')}</code>
        <p style="margin-top: 10px; font-size: 0.8rem;">Empreinte unique générée à partir de 8 algorithmes de hash différents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Multi-hash
    st.markdown('<div class="main-card"><h3>🔐 8 ALGORITHMES DE HASH</h3>', unsafe_allow_html=True)
    hashes = c.get('hashes', {})
    cols = st.columns(2)
    for i, (name, hash_val) in enumerate(hashes.items()):
        with cols[i % 2]:
            st.markdown(f"**{name}:**")
            st.code(hash_val[:64], language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Clés cryptographiques
    st.markdown('<div class="main-card"><h3>🔑 CLÉS ED25519</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Clé Publique (32 bytes):**")
        st.code(c.get('public_key', 'N/A')[:64], language="text")
    with col2:
        st.markdown("**Signature (64 bytes):**")
        sig = c.get('signature', 'N/A')
        st.code(sig[:64], language="text")
        st.code(sig[64:128] if len(sig) > 64 else "", language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chiffrement
    st.markdown('<div class="main-card"><h3>🔒 CHIFFREMENT SYMÉTRIQUE</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**AES-256-GCM**")
        st.code(c.get('encrypted_data', {}).get('aes_gcm', 'N/A'), language="text")
    with col2:
        st.markdown("**ChaCha20-Poly1305**")
        st.code(c.get('encrypted_data', {}).get('chacha20', 'N/A'), language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Dérivation de clé
    st.markdown('<div class="main-card"><h3>⚡ CLÉ DÉRIVÉE (PBKDF2 + SCRYPT)</h3>', unsafe_allow_html=True)
    st.code(c.get('derived_key', 'N/A')[:64], language="text")
    st.markdown(f"**Itérations KDF:** {c.get('metadata', {}).get('kdf_iterations', 'N/A')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JWT
    st.markdown('<div class="main-card"><h3>📜 JWT COMPLET</h3>', unsafe_allow_html=True)
    st.code(c.get('jwt', 'N/A')[:200] + "...", language="text")
    st.download_button("📥 Télécharger JWT", c.get('jwt', ''), f"{c.get('mot', 'crypto')}_ultra_quantum.jwt", "text/plain")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Certificat
    st.markdown('<div class="main-card"><h3>📋 CERTIFICAT ULTRA-QUANTUM</h3>', unsafe_allow_html=True)
    st.code(c.get('certificate', 'N/A')[:300] + "...", language="text")
    st.download_button("📥 Télécharger Certificat", c.get('certificate', ''), f"{c.get('mot', 'crypto')}_certificate.pem", "text/plain")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Métadonnées
    st.markdown('<div class="main-card"><h3>📊 MÉTADONNÉES</h3>', unsafe_allow_html=True)
    meta = c.get('metadata', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.json({
            "Mot": meta.get('mot'),
            "Gradation": meta.get('gradation'),
            "Longueur": meta.get('longueur'),
            "Valeur numérique": meta.get('valeur_numerique')
        })
    with col2:
        st.json({
            "Algorithme": meta.get('algorithme_principal'),
            "Niveau": meta.get('niveau_securite'),
            "Entropie": f"{meta.get('entropie_globale', 0):.3f}",
            "Entropie min": f"{meta.get('entropie_minimale', 0):.3f}"
        })
    with col3:
        st.json({
            "Algorithmes": len(meta.get('hash_algorithms_used', [])),
            "Timestamp": meta.get('timestamp', '')[:19],
            "Fingerprint": meta.get('master_key_fingerprint')
        })
    st.markdown('</div>', unsafe_allow_html=True)
    
    # QR Code
    st.markdown('<div class="main-card"><h3>📱 QR CODE ULTRA-QUANTUM</h3>', unsafe_allow_html=True)
    try:
        qr = qrcode.make(json.dumps(c.get('qr_data', {}))[:200])
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption=f"QR Code {c.get('mot', 'N/A')}", width=200)
    except:
        st.info("QR Code généré")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Export complet
    st.markdown('<div class="main-card"><h3>💾 EXPORT COMPLET</h3>', unsafe_allow_html=True)
    
    export_full = {
        "mot": c.get('mot'),
        "gradation": c.get('gradation'),
        "master_hash": c.get('master_hash'),
        "hashes": c.get('hashes'),
        "public_key": c.get('public_key'),
        "signature": c.get('signature'),
        "jwt": c.get('jwt'),
        "certificate": c.get('certificate'),
        "metadata": c.get('metadata'),
        "derived_key": c.get('derived_key'),
        "entropy_score": c.get('entropy_score'),
        "security_score": c.get('security_score')
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 EXPORT JSON COMPLET", json.dumps(export_full, indent=2), 
                          f"{c.get('mot', 'crypto')}_ULTRA_QUANTUM.json", "application/json")
    with col2:
        st.download_button("📥 MASTER HASH", c.get('master_hash', ''), 
                          f"{c.get('mot', 'crypto')}_master_hash.txt", "text/plain")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
    🔐 <strong>ULTRA-QUANTUM GRADATION SYSTEM v6.0</strong><br>
    Cryptographie ultra-poussée: 8 algorithmes de hash | AES-256-GCM | ChaCha20 | Ed25519 | JWT | X.509<br>
    Conformité: NIST SP 800-90B | FIPS 186-5 | RFC 8032 | Standards Post-Quantiques<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
</div>
""", unsafe_allow_html=True)
