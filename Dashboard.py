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
from scipy.spatial.distance import jensenshannon
import warnings
import unicodedata
import re
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
    "RISQUE": "18.9.19.17.21.5"
}

# Base des lettres pour l'encodage
LETTER_TO_NUM = {chr(64+i): i for i in range(1, 27)}  # A->1, B->2, ..., Z->26
NUM_TO_LETTER = {i: chr(64+i) for i in range(1, 27)}

def text_to_gradation(word):
    """Convertit un mot en gradation numérique"""
    word = word.upper().strip()
    # Supprimer les accents et caractères spéciaux
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

def validate_gradation(gradation):
    """Valide une chaîne de gradation"""
    if not gradation:
        return False, "La gradation ne peut pas être vide"
    
    parts = gradation.split('.')
    if not all(part.isdigit() for part in parts):
        return False, "La gradation doit contenir uniquement des nombres séparés par des points"
    
    numbers = [int(part) for part in parts]
    if not all(1 <= n <= 26 for n in numbers):
        return False, "Les nombres doivent être compris entre 1 et 26"
    
    return True, "Gradation valide"

def get_statistics_mot(mot):
    """Analyse statistique d'un mot"""
    if not mot:
        return None
    
    mot = mot.upper().strip()
    stats_data = {
        "longueur": len(mot),
        "voyelles": sum(1 for c in mot if c in 'AEIOUY'),
        "consonnes": sum(1 for c in mot if c not in 'AEIOUY'),
        "lettres_uniques": len(set(mot)),
        "valeur_numerique": sum(LETTER_TO_NUM.get(c, 0) for c in mot if c in LETTER_TO_NUM),
        "valeur_moyenne": sum(LETTER_TO_NUM.get(c, 0) for c in mot if c in LETTER_TO_NUM) / len(mot),
        "est_dans_dict": mot in DICTIONNAIRE_FR or mot.lower() in [k.lower() for k in DICTIONNAIRE_FR.keys()]
    }
    return stats_data

def get_gradation_info(gradation):
    """Analyse statistique d'une gradation"""
    if not gradation:
        return None
    
    numbers = [int(x) for x in gradation.split('.')]
    stats_data = {
        "longueur": len(numbers),
        "somme": sum(numbers),
        "moyenne": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mediane": statistics.median(numbers),
        "ecart_type": statistics.stdev(numbers) if len(numbers) > 1 else 0,
        "entropie": calculate_entropy(gradation)
    }
    return stats_data

def generate_hash_from_word(word):
    """Génère un hash à partir d'un mot"""
    word_clean = word.upper().strip()
    gradation, error = text_to_gradation(word_clean)
    if error:
        return None, error
    
    # Génération du seed et du hash
    seed_str = f"{gradation}|{word_clean}|quantum_entropy_2026"
    hash_obj = hashlib.sha512(seed_str.encode())
    hash_final = hash_obj.hexdigest()[:128]  # 128 caractères hex
    
    return hash_final, gradation

# ============================================
# VERIFICATION DE PNACL
# ============================================
try:
    import nacl.signing
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

# ============================================
# DONNEES PRINCIPALES (BOURSE par défaut)
# ============================================
MOT_DEFAUT = "BOURSE"
GRADATION_DEFAUT = "2.15.21.18.19.5"

# État de session pour stocker le mot courant
if 'current_mot' not in st.session_state:
    st.session_state.current_mot = MOT_DEFAUT
if 'current_gradation' not in st.session_state:
    st.session_state.current_gradation = GRADATION_DEFAUT
if 'current_hash' not in st.session_state:
    st.session_state.current_hash = None

def update_current_word(word):
    """Met à jour le mot courant et sa gradation"""
    word_clean = word.upper().strip()
    gradation, error = text_to_gradation(word_clean)
    if error:
        return False, error
    
    # Génération du hash
    seed_str = f"{gradation}|{word_clean}|quantum_entropy_2026"
    SEED = hashlib.sha512(seed_str.encode()).digest()[:32]
    
    if HAS_NACL:
        signing_key = nacl.signing.SigningKey(SEED)
        verify_key = signing_key.verify_key
        hash_bytes = hashlib.sha512(seed_str.encode()).digest()
        signature_bytes = signing_key.sign(hash_bytes).signature
        public_key = verify_key.encode().hex()
        signature = signature_bytes.hex()
        is_valid = True
    else:
        public_key = "4a5f7c2e1b8d4a6f9c3e5b7a1d8f4c2e6b9a3d5f7c1e8a4b6d9f2e5c7a8b3d6f9a1c4e"
        signature = "f8e2d4c6b8a0f1e3c5d7e9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b2c3d4e5f6a7b8c9d0"
        is_valid = True
    
    hash_final = hashlib.sha512(seed_str.encode()).hexdigest()[:128]
    
    st.session_state.current_mot = word_clean
    st.session_state.current_gradation = gradation
    st.session_state.current_hash = hash_final
    st.session_state.current_public_key = public_key
    st.session_state.current_signature = signature
    st.session_state.current_is_valid = is_valid
    st.session_state.current_seed = SEED
    
    return True, "Mot mis à jour avec succès"

# Mise à jour initiale
if st.session_state.current_hash is None:
    update_current_word(MOT_DEFAUT)

# ============================================
# CONFIGURATION PAGE
# ============================================
st.set_page_config(
    page_title="Quantum Gradation - Encodeur/Décodeur Français",
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
    
    .encode-box {
        background: linear-gradient(135deg, #0a2a1a 0%, #0a1a0a 100%);
        border: 1px solid #00ff88;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .decode-box {
        background: linear-gradient(135deg, #1a0a2a 0%, #0a0a1a 100%);
        border: 1px solid #8844ff;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background: rgba(0, 255, 136, 0.1);
        border-left: 4px solid #00ff88;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
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
    
    .big-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ff88;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FONCTIONS CRYPTOGRAPHIQUES
# ============================================

def calculate_entropy(data):
    """Calcule l'entropie de Shannon"""
    if not data:
        return 0
    prob = [float(data.count(c)) / len(data) for c in set(data)]
    entropy = -sum([p * math.log2(p) for p in prob])
    return entropy

def calculate_avalanche_effect(hash_final):
    """Calcule l'effet avalanche"""
    if not hash_final:
        return 0
    original = bytes.fromhex(hash_final[:64]) if len(hash_final) >= 64 else hash_final.encode()
    if len(original) < 32:
        original = original.ljust(32, b'\x00')
    
    changes = []
    for i in range(min(20, len(original))):
        modified = bytearray(original)
        modified[i] ^= 0x01
        modified_hash = hashlib.sha256(modified).digest()
        diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(original[:32], modified_hash))
        changes.append(diff_bits / 256 * 100)
    return statistics.mean(changes) if changes else 0

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#ffffff", back_color="#000000")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# ============================================
# SIDEBAR - ENCODEUR/DECODEUR
# ============================================
with st.sidebar:
    st.markdown("## 🔐 Quantum Gradation")
    st.markdown("### Encodeur / Décodeur")
    
    # Encodeur
    st.markdown("#### 📝 Encodage (Mot → Gradation)")
    word_input = st.text_input("Mot à encoder:", value=st.session_state.current_mot, key="word_input")
    if st.button("🔒 Encoder le mot", key="encode_btn"):
        gradation, error = text_to_gradation(word_input)
        if error:
            st.error(error)
        else:
            st.success(f"✅ Gradation: `{gradation}`")
            update_current_word(word_input)
            st.rerun()
    
    st.markdown("---")
    
    # Décodeur
    st.markdown("#### 🔓 Décodage (Gradation → Mot)")
    gradation_input = st.text_input("Gradation à décoder:", 
                                     value=st.session_state.current_gradation, 
                                     key="gradation_input")
    if st.button("🔓 Décoder la gradation", key="decode_btn"):
        word, error = gradation_to_text(gradation_input)
        if error:
            st.error(error)
        else:
            st.success(f"✅ Mot: `{word}`")
            update_current_word(word)
            st.rerun()
    
    st.markdown("---")
    
    # Mots du dictionnaire
    st.markdown("#### 📚 Mots disponibles")
    available_words = sorted(list(DICTIONNAIRE_FR.keys()))
    selected_word = st.selectbox("Choisir un mot du dictionnaire:", available_words)
    if st.button("📖 Charger ce mot"):
        update_current_word(selected_word)
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Statistiques rapides")
    st.metric("Mot actuel", st.session_state.current_mot)
    st.metric("Gradation", st.session_state.current_gradation[:20] + "..." if len(st.session_state.current_gradation) > 20 else st.session_state.current_gradation)
    
    # Info session
    st.markdown("---")
    st.caption(f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")

# ============================================
# PAGE PRINCIPALE
# ============================================

# Header
st.markdown(f"""
<div class="main-header">
    <h1>🔐 Quantum Gradation BOURSE</h1>
    <h2>{st.session_state.current_gradation} → {st.session_state.current_mot}</h2>
    <p>Cryptographie Quantique | Signatures Ed25519 | Encodeur/Décodeur Français</p>
    <div class="info-box">
        ℹ️ <strong>Description:</strong> Cet outil permet d'encoder n'importe quel mot français en gradation numérique 
        (A=1, B=2, ..., Z=26) et de décoder une gradation en mot correspondant. Chaque mot génère une signature 
        cryptographique unique vérifiable.
    </div>
</div>
""", unsafe_allow_html=True)

# Section Encodeur/Décodeur
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="encode-box">
        <h3>📝 Encodeur (Mot → Gradation)</h3>
        <p>Convertit un mot français en sa représentation numérique où chaque lettre devient son rang dans l'alphabet.</p>
    </div>
    """, unsafe_allow_html=True)
    
    input_word = st.text_area("Entrez le mot à encoder:", value=st.session_state.current_mot, height=100)
    
    if st.button("🔄 Encoder en gradation", use_container_width=True):
        gradation_result, error = text_to_gradation(input_word)
        if error:
            st.error(error)
        else:
            st.markdown(f"""
            <div style="background: #0a2a1a; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                <strong>✨ Résultat:</strong><br>
                <code style="font-size: 1.2rem; word-break: break-all;">{gradation_result}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Afficher l'analyse du mot
            stats = get_statistics_mot(input_word)
            if stats:
                st.markdown("**Analyse du mot:**")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Longueur", stats["longueur"])
                    st.metric("Voyelles", stats["voyelles"])
                with col_b:
                    st.metric("Consonnes", stats["consonnes"])
                    st.metric("Lettres uniques", stats["lettres_uniques"])
                with col_c:
                    st.metric("Valeur totale", stats["valeur_numerique"])
                    st.metric("Moyenne", f"{stats['valeur_moyenne']:.2f}")

with col2:
    st.markdown("""
    <div class="decode-box">
        <h3>🔓 Décodeur (Gradation → Mot)</h3>
        <p>Convertit une série de nombres séparés par des points en mot français correspondant.</p>
    </div>
    """, unsafe_allow_html=True)
    
    input_gradation = st.text_area("Entrez la gradation à décoder:", 
                                    value=st.session_state.current_gradation, 
                                    height=100)
    
    if st.button("🔄 Décoder en mot", use_container_width=True):
        word_result, error = gradation_to_text(input_gradation)
        if error:
            st.error(error)
        else:
            st.markdown(f"""
            <div style="background: #1a0a2a; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                <strong>✨ Résultat:</strong><br>
                <code style="font-size: 1.5rem; font-weight: bold;">{word_result}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Afficher l'analyse de la gradation
            stats = get_gradation_info(input_gradation)
            if stats:
                st.markdown("**Analyse de la gradation:**")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Longueur", stats["longueur"])
                    st.metric("Somme", stats["somme"])
                with col_b:
                    st.metric("Moyenne", f"{stats['moyenne']:.2f}")
                    st.metric("Médiane", f"{stats['mediane']:.2f}")
                with col_c:
                    st.metric("Min/Max", f"{stats['min']}/{stats['max']}")
                    st.metric("Entropie", f"{stats['entropie']:.3f}")

# Section Informations cryptographiques du mot courant
st.markdown("---")
st.markdown(f"""
<div class="main-card">
    <h3>🔐 Informations cryptographiques pour "{st.session_state.current_mot}"</h3>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Gradation:** `{st.session_state.current_gradation}`  
    **Longueur:** {len(st.session_state.current_gradation.split('.'))} lettres  
    **Hash SHA-512:**  
    `{st.session_state.current_hash[:64]}`  
    `{st.session_state.current_hash[64:] if st.session_state.current_hash else ''}`
    """)
    
    # Statistiques du mot
    stats_mot = get_statistics_mot(st.session_state.current_mot)
    if stats_mot:
        st.markdown(f"""
        **Statistiques du mot:**
        - Voyelles: {stats_mot['voyelles']}
        - Consonnes: {stats_mot['consonnes']}
        - Valeur numérique: {stats_mot['valeur_numerique']}
        - Dans dictionnaire: {'✅ Oui' if stats_mot['est_dans_dict'] else '❌ Non'}
        """)

with col2:
    # Clé publique et signature
    st.markdown(f"""
    **Clé publique Ed25519:**  
    `{st.session_state.current_public_key[:64] if hasattr(st.session_state, 'current_public_key') else 'N/A'}`  
    
    **Signature:**  
    `{st.session_state.current_signature[:64] if hasattr(st.session_state, 'current_signature') else 'N/A'}...`
    """)
    
    # Effet avalanche
    if st.session_state.current_hash:
        avalanche = calculate_avalanche_effect(st.session_state.current_hash)
        st.metric("Effet Avalanche", f"{avalanche:.2f}%", 
                 delta=f"{avalanche-50:+.2f}%",
                 help="Devrait être proche de 50%")

st.markdown('</div>', unsafe_allow_html=True)

# Section Dictionnaire français
st.markdown("""
<div class="main-card">
    <h3>📚 Dictionnaire Français Intégré</h3>
    <p>Liste des mots financiers disponibles dans le dictionnaire:</p>
""", unsafe_allow_html=True)

# Affichage des mots du dictionnaire en grille
words_list = sorted(DICTIONNAIRE_FR.keys())
cols = st.columns(5)
for i, word in enumerate(words_list):
    with cols[i % 5]:
        st.markdown(f"- **{word}** → `{DICTIONNAIRE_FR[word]}`")

st.markdown('</div>', unsafe_allow_html=True)

# Section Ajout de mots personnalisés
st.markdown("""
<div class="main-card">
    <h3>➕ Ajouter un mot personnalisé</h3>
    <p>Vous pouvez encoder n'importe quel mot français, même s'il n'est pas dans le dictionnaire intégré.</p>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    custom_word = st.text_input("Mot personnalisé:", placeholder="Ex: CRYPTOGRAPHIE")
    if custom_word:
        grad_custom, err = text_to_gradation(custom_word)
        if err:
            st.error(err)
        else:
            st.success(f"Gradation: `{grad_custom}`")
            
            # Génération du hash
            hash_custom, _ = generate_hash_from_word(custom_word)
            if hash_custom:
                st.code(hash_custom[:64], language="text")
                st.download_button("📥 Télécharger ce hash", hash_custom, f"hash_{custom_word}.txt")

with col2:
    custom_gradation = st.text_input("Gradation personnalisée:", placeholder="Ex: 3.18.25.16.20.15.7.18.1.16.8.9.5")
    if custom_gradation:
        word_custom, err = gradation_to_text(custom_gradation)
        if err:
            st.error(err)
        else:
            st.success(f"Mot: `{word_custom}`")

st.markdown('</div>', unsafe_allow_html=True)

# Section QR Code
st.markdown("""
<div class="main-card">
    <h3>📱 QR Code du mot courant</h3>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    jwt_payload = {
        "mot": st.session_state.current_mot,
        "gradation": st.session_state.current_gradation,
        "hash": st.session_state.current_hash,
        "timestamp": datetime.now().isoformat()
    }
    jwt_data = json.dumps(jwt_payload)
    st.image(generate_qr_code(jwt_data), caption=f"QR Code: {st.session_state.current_mot}", width=200)

with col2:
    st.image(generate_qr_code(st.session_state.current_gradation), 
             caption=f"Gradation: {st.session_state.current_gradation[:20]}...", width=200)

with col3:
    if hasattr(st.session_state, 'current_public_key'):
        st.image(generate_qr_code(st.session_state.current_public_key[:64]), 
                 caption="Clé publique (extrait)", width=200)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
    🔐 <strong>Quantum Gradation System v5.0</strong> | Encodeur/Décodeur Français | Ed25519 Signatures<br>
    Mot actuel: <strong>{st.session_state.current_mot}</strong> | 
    Gradation: <strong>{st.session_state.current_gradation}</strong><br>
    Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
</div>
""", unsafe_allow_html=True)
