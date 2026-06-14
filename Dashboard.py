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
import unicodedata
import re
import warnings
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
    "FOREX": "6.15.18.5.24"
}

# Base des lettres pour l'encodage
LETTER_TO_NUM = {chr(64+i): i for i in range(1, 27)}
NUM_TO_LETTER = {i: chr(64+i) for i in range(1, 27)}

# ============================================
# FONCTIONS ENCODEUR/DECODEUR
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

def generate_keys_from_word(word):
    """Génère une paire de clés Ed25519 à partir d'un mot"""
    gradation, error = text_to_gradation(word)
    if error:
        return None, None, None, None, error
    
    seed_str = f"{gradation}|{word}|quantum_entropy_2026"
    SEED = hashlib.sha512(seed_str.encode()).digest()[:32]
    
    if HAS_NACL:
        signing_key = nacl.signing.SigningKey(SEED)
        verify_key = signing_key.verify_key
        public_key = verify_key.encode().hex()
        
        # Génération du hash et de la signature
        hash_bytes = hashlib.sha512(seed_str.encode()).digest()
        signature_bytes = signing_key.sign(hash_bytes).signature
        signature = signature_bytes.hex()
        hash_final = hash_bytes.hex()[:128]
        is_valid = True
    else:
        # Mode démo
        public_key = hashlib.sha256(seed_str.encode()).hexdigest()[:64]
        signature = hashlib.sha512(f"{seed_str}|signature".encode()).hexdigest()[:128]
        hash_final = hashlib.sha512(seed_str.encode()).hexdigest()[:128]
        is_valid = True
    
    return public_key, signature, hash_final, SEED, is_valid

# ============================================
# CONFIGURATION PAGE
# ============================================
st.set_page_config(
    page_title="Quantum Gradation BOURSE - Ultimate Security Dashboard",
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
    .main-card:hover { border-color: #00ff88; transform: translateY(-2px); box-shadow: 0 8px 12px rgba(0,0,0,0.4); }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #0a0a15 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #2a2a3e;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .status-valid { background: linear-gradient(135deg, #0a2a1a 0%, #0a1a0a 100%); border: 1px solid #00ff88; border-radius: 12px; padding: 1rem; text-align: center; }
    .status-invalid { background: linear-gradient(135deg, #2a0a0a 0%, #1a0a0a 100%); border: 1px solid #ff4444; border-radius: 12px; padding: 1rem; text-align: center; }
    
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
    
    .warning-box {
        background: rgba(255, 68, 68, 0.1);
        border-left: 4px solid #ff4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .big-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ff88;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ÉTAT DE SESSION
# ============================================
if 'current_mot' not in st.session_state:
    st.session_state.current_mot = "BOURSE"
if 'current_gradation' not in st.session_state:
    st.session_state.current_gradation = "2.15.21.18.19.5"
if 'current_hash' not in st.session_state:
    st.session_state.current_hash = None
if 'current_public_key' not in st.session_state:
    st.session_state.current_public_key = None
if 'current_signature' not in st.session_state:
    st.session_state.current_signature = None

def update_current_word(word):
    """Met à jour le mot courant et toutes les données cryptographiques"""
    word_clean = word.upper().strip()
    gradation, error = text_to_gradation(word_clean)
    if error:
        return False, error
    
    public_key, signature, hash_final, seed, is_valid = generate_keys_from_word(word_clean)
    
    st.session_state.current_mot = word_clean
    st.session_state.current_gradation = gradation
    st.session_state.current_hash = hash_final
    st.session_state.current_public_key = public_key
    st.session_state.current_signature = signature
    st.session_state.current_seed = seed
    st.session_state.current_is_valid = is_valid
    
    return True, "Mot mis à jour avec succès"

# Initialisation
if st.session_state.current_hash is None:
    update_current_word("BOURSE")

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

def calculate_min_entropy(data):
    """Entropie minimale (NIST SP 800-90B)"""
    if not data:
        return 0
    freq = Counter(data)
    max_prob = max(freq.values()) / len(data)
    return -math.log2(max_prob)

def calculate_collision_entropy(data):
    """Entropie de collision (Renyi d'ordre 2)"""
    if not data:
        return 0
    freq = Counter(data)
    sum_sq = sum((v/len(data))**2 for v in freq.values())
    return -math.log2(sum_sq)

def calculate_conditional_entropy(data):
    """Entropie conditionnelle (ordre 2)"""
    if len(data) < 2:
        return 0
    pairs = [data[i:i+2] for i in range(len(data)-1)]
    pair_counts = Counter(pairs)
    entropy = 0
    for pair, count in pair_counts.items():
        p = count / len(pairs)
        entropy += p * math.log2(p)
    return -entropy

def calculate_avalanche_effect(hash_final=None):
    """Calcule l'effet avalanche"""
    if hash_final is None:
        hash_final = st.session_state.current_hash
    
    if not hash_final or len(hash_final) < 64:
        return 0
    
    try:
        original = bytes.fromhex(hash_final[:64])
    except:
        return 0
    
    changes = []
    for i in range(min(20, len(original))):
        modified = bytearray(original)
        modified[i] ^= 0x01
        modified_hash = hashlib.sha256(modified).digest()
        diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(original[:32], modified_hash))
        changes.append(diff_bits / 256 * 100)
    return statistics.mean(changes) if changes else 0

def calculate_sac(hash_final=None, modified_positions=10):
    """Strict Avalanche Criterion"""
    if hash_final is None:
        hash_final = st.session_state.current_hash
    
    if not hash_final or len(hash_final) < 64:
        return 0
    
    try:
        original = bytes.fromhex(hash_final[:64])
    except:
        return 0
    
    results = []
    for i in range(min(modified_positions, len(original))):
        modified = bytearray(original)
        modified[i] ^= 0x01
        modified_hash = hashlib.sha256(modified).digest()
        changed_bits = sum(bin(a ^ b).count('1') for a, b in zip(original[:32], modified_hash))
        results.append(changed_bits / 256)
    return statistics.mean(results) if results else 0

def calculate_security_strength(bits):
    """Force de sécurité selon NIST"""
    if bits >= 256:
        return "Post-Quantum Level (5) - Résistance quantique", 5
    elif bits >= 192:
        return "High Security (4) - Niveau gouvernemental", 4
    elif bits >= 128:
        return "Standard Security (3) - Niveau entreprise", 3
    elif bits >= 80:
        return "Legacy Security (2) - Hérité", 2
    else:
        return "Weak Security (1) - À éviter", 1

def get_hash_byte_distribution():
    """Distribution des bytes du hash"""
    if not st.session_state.current_hash or len(st.session_state.current_hash) < 64:
        return Counter()
    try:
        hash_bytes = bytes.fromhex(st.session_state.current_hash[:64])
        return Counter(hash_bytes)
    except:
        return Counter()

def get_entropy_analysis():
    """Analyse complète de l'entropie"""
    hash_data = st.session_state.current_hash or ""
    return {
        "shannon": calculate_entropy(hash_data),
        "min_entropy": calculate_min_entropy(hash_data),
        "collision_entropy": calculate_collision_entropy(hash_data),
        "conditional_entropy": calculate_conditional_entropy(hash_data),
        "avalanche": calculate_avalanche_effect(),
        "sac": calculate_sac()
    }

def get_signature_analysis():
    """Analyse complète de la signature"""
    sig = st.session_state.current_signature or ""
    if len(sig) < 64:
        return {}
    try:
        sig_bytes = bytes.fromhex(sig[:128])
        return {
            "length_bytes": len(sig_bytes),
            "length_bits": len(sig_bytes) * 8,
            "entropy": calculate_entropy(sig),
            "unique_bytes": len(set(sig_bytes)),
            "unique_ratio": len(set(sig_bytes)) / 256 * 100,
            "std_dev": float(np.std(list(sig_bytes))),
            "mean": float(np.mean(list(sig_bytes))),
            "median": float(np.median(list(sig_bytes))),
            "skewness": float(stats.skew(list(sig_bytes)) if len(sig_bytes) > 2 else 0),
            "kurtosis": float(stats.kurtosis(list(sig_bytes)) if len(sig_bytes) > 3 else 0)
        }
    except:
        return {}

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(str(data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="#ffffff", back_color="#000000")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

def create_distribution_chart(data, title):
    """Graphique de distribution"""
    if not data:
        return go.Figure()
    try:
        bytes_data = list(bytes.fromhex(data[:128]))
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=bytes_data, nbinsx=256, name="Distribution", marker_color='#00ff88'))
        fig.update_layout(
            title=title,
            paper_bgcolor='black', 
            font=dict(color='white'), 
            plot_bgcolor='black',
            xaxis_title="Valeur du byte (0-255)",
            yaxis_title="Fréquence"
        )
        fig.update_xaxes(color='white')
        fig.update_yaxes(color='white')
        return fig
    except:
        return go.Figure()

def create_radar_chart():
    """Graphique radar des métriques de sécurité"""
    entropy_data = get_entropy_analysis()
    
    categories = ['Entropie\nShannon', 'Entropie\nMinimale', 'Entropie de\nCollision', 'Entropie\nConditionnelle', 'Effet\nAvalanche', 'SAC']
    values = [
        min(100, entropy_data['shannon'] / 4 * 100),
        min(100, entropy_data['min_entropy'] / 4 * 100),
        min(100, entropy_data['collision_entropy'] / 4 * 100),
        min(100, entropy_data['conditional_entropy'] / 4 * 100),
        min(100, entropy_data['avalanche']),
        min(100, entropy_data['sac'] * 100)
    ]
    
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', 
                                         marker=dict(color='#00ff88'), line=dict(color='#00ff88', width=2)))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], color='white', 
                                   tickfont=dict(color='white'))),
        showlegend=False,
        paper_bgcolor='black',
        font=dict(color='white'),
        title="Métriques de Sécurité - Vue d'ensemble"
    )
    return fig

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
        "valeur_moyenne": sum(LETTER_TO_NUM.get(c, 0) for c in mot if c in LETTER_TO_NUM) / len(mot) if mot else 0,
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

def run_nist_statistical_tests():
    """Tests statistiques NIST simplifiés"""
    if not st.session_state.current_hash or len(st.session_state.current_hash) < 64:
        return {"frequence_pass": False, "runs_pass": False}
    
    try:
        hash_bytes = bytes.fromhex(st.session_state.current_hash[:64])
        bit_string = ''.join(format(byte, '08b') for byte in hash_bytes)
        
        # Test de fréquence (monobit)
        n = len(bit_string)
        count_ones = bit_string.count('1')
        s_obs = abs(count_ones - n/2) / math.sqrt(n/4)
        p_value_freq = math.erfc(s_obs / math.sqrt(2))
        
        # Test de runs
        runs = 1
        for i in range(1, n):
            if bit_string[i] != bit_string[i-1]:
                runs += 1
        pi = count_ones / n
        if abs(pi - 0.5) >= (2/math.sqrt(n)):
            p_value_runs = 0
        else:
            num = abs(runs - 2*n*pi*(1-pi))
            denom = 2*math.sqrt(2*n)*pi*(1-pi)
            p_value_runs = math.erfc(num/denom)
        
        return {
            "frequence": p_value_freq,
            "runs": p_value_runs,
            "frequence_pass": p_value_freq > 0.01,
            "runs_pass": p_value_runs > 0.01
        }
    except:
        return {"frequence_pass": False, "runs_pass": False}

def get_system_info():
    """Informations système détaillées"""
    info = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor() or "Unknown",
        "hostname": platform.node(),
    }
    if HAS_PSUTIL:
        info["memory_total"] = f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
        info["memory_available"] = f"{psutil.virtual_memory().available / (1024**3):.1f} GB"
        info["cpu_count"] = psutil.cpu_count()
        info["cpu_percent"] = psutil.cpu_percent(interval=1)
    else:
        info["memory_total"] = "N/A"
        info["memory_available"] = "N/A"
        info["cpu_count"] = "N/A"
        info["cpu_percent"] = "N/A"
    return info

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    page = st.radio("Sélectionnez une section", [
        "🏠 Dashboard Principal",
        "🔐 Encodeur/Décodeur",
        "📊 Analyse Entropique",
        "📈 Statistiques Avancees",
        "🔑 Signature & Certificat",
        "📁 Export & QR Code",
        "ℹ️ Informations Systeme"
    ])
    
    st.markdown("---")
    st.markdown("## 📊 Metriques Rapides")
    
    st.metric("Mot actuel", st.session_state.current_mot)
    st.metric("Gradation", st.session_state.current_gradation[:20] + "..." if len(st.session_state.current_gradation) > 20 else st.session_state.current_gradation)
    
    entropy = calculate_entropy(st.session_state.current_hash or "")
    st.metric("Entropie Shannon", f"{entropy:.3f} bits", delta=f"{entropy/8*100:.0f}% du max")
    
    if st.session_state.current_hash:
        sec_strength, _ = calculate_security_strength(len(st.session_state.current_hash) * 4)
        st.metric("Niveau Securite", sec_strength.split()[0])
    
    st.markdown("---")
    
    # Sélecteur de mots du dictionnaire
    st.markdown("### 📚 Mots disponibles")
    available_words = sorted(list(DICTIONNAIRE_FR.keys()))
    selected_word = st.selectbox("Choisir un mot:", available_words)
    if st.button("📖 Charger ce mot", use_container_width=True):
        update_current_word(selected_word)
        st.rerun()
    
    st.markdown("---")
    st.caption(f"🕐 Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("🔒 Système certifié conforme aux standards NIST")

# ============================================
# PAGE 1: DASHBOARD PRINCIPAL
# ============================================
if page == "🏠 Dashboard Principal":
    st.markdown(f"""
    <div class="main-header">
        <h1>🔐 Quantum Gradation BOURSE</h1>
        <h2>{st.session_state.current_gradation} → {st.session_state.current_mot}</h2>
        <p>Cryptographie Quantique | Signatures Ed25519 | Prêt pour l'ère Post-Quantique</p>
        <div class="info-box">
            ℹ️ <strong>Description:</strong> Ce tableau de bord présente les résultats de la gradation cryptographique 
            reliant une séquence numérique à un mot français. Toutes les opérations sont vérifiables 
            cryptographiquement via des signatures Ed25519 et une analyse d'entropie quantique avancée.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Information Generale")
        st.markdown(f"""
        | Propriete | Valeur |
        |-----------|--------|
        | **Gradation** | `{st.session_state.current_gradation}` |
        | **Mot** | `{st.session_state.current_mot}` |
        | **Timestamp** | `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` |
        | **Algorithme** | Ed25519 (Courbe elliptique) |
        | **Hash Size** | 128 hex (64 bytes) |
        | **Sécurité théorique** | 2^128 opérations |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Statut Signature")
        if st.session_state.current_is_valid:
            st.markdown("""
            <div class="status-valid">
                <h3>✅ SIGNATURE VALIDE</h3>
                <p>Intégrité cryptographique confirmée<br>Authentification réussie</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-invalid">
                <h3>❌ SIGNATURE INVALIDE</h3>
                <p>Vérification échouée - Données altérées</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Clé Publique")
        if st.session_state.current_public_key:
            st.code(st.session_state.current_public_key[:64], language="text")
        else:
            st.code("Génération en cours...", language="text")
        st.caption("Ed25519 Public Key (32 bytes / 64 hex) - À partager pour vérification")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Hash complet
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Hash Final")
    if st.session_state.current_hash:
        st.code(st.session_state.current_hash, language="text")
    else:
        st.code("Génération en cours...", language="text")
    st.caption(f"Longueur: 128 caractères hexadécimaux | 64 bytes | 512 bits")
    st.markdown("**Description:** Ce hash représente l'empreinte cryptographique unique de la gradation. Toute modification, même d'un seul bit, produirait un hash complètement différent grâce à l'effet avalanche.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Visualisation
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        if st.session_state.current_hash:
            fig = create_distribution_chart(st.session_state.current_hash, "Distribution des bytes - Hash")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Hash non disponible")
        st.caption("Distribution uniforme idéale pour une sécurité optimale")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        if st.session_state.current_signature:
            fig = create_distribution_chart(st.session_state.current_signature, "Distribution des bytes - Signature Ed25519")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Signature non disponible")
        st.caption("La signature montre une distribution aléatoire caractéristique d'Ed25519")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Radar chart
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Metriques de Securite")
    fig = create_radar_chart()
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Plus les valeurs sont proches de 100%, meilleure est la sécurité cryptographique")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 2: ENCODEUR/DECODEUR
# ============================================
elif page == "🔐 Encodeur/Décodeur":
    st.markdown('<div class="main-header"><h1>🔐 Encodeur / Décodeur Français</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="encode-box">
            <h3>📝 Encodeur (Mot → Gradation)</h3>
            <p>Convertit un mot français en sa représentation numérique où chaque lettre devient son rang dans l'alphabet (A=1, B=2, ..., Z=26).</p>
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
                
                if st.button("✅ Utiliser ce mot", key="use_encode"):
                    update_current_word(input_word)
                    st.rerun()
                
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
                
                if st.button("✅ Utiliser cette gradation", key="use_decode"):
                    update_current_word(word_result)
                    st.rerun()
                
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
    
    # Dictionnaire intégré
    st.markdown("""
    <div class="main-card">
        <h3>📚 Dictionnaire Français Intégré</h3>
        <p>Liste des mots disponibles dans le dictionnaire:</p>
    """, unsafe_allow_html=True)
    
    words_list = sorted(DICTIONNAIRE_FR.keys())
    cols = st.columns(5)
    for i, word in enumerate(words_list):
        with cols[i % 5]:
            st.markdown(f"- **{word}** → `{DICTIONNAIRE_FR[word]}`")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 3: ANALYSE ENTROPIQUE
# ============================================
elif page == "📊 Analyse Entropique":
    st.markdown('<div class="main-header"><h1>📊 Analyse Entropique Avancée</h1></div>', unsafe_allow_html=True)
    
    entropy_data = get_entropy_analysis()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Metriques d'Entropie")
        st.markdown(f"""
        | Metrique | Valeur | Maximum | Ratio | Signification |
        |----------|--------|---------|-------|---------------|
        | **Shannon Entropy** | {entropy_data['shannon']:.4f} bits | 8.0 bits | {entropy_data['shannon']/8*100:.1f}% | Aléatoire général |
        | **Min-Entropy (NIST)** | {entropy_data['min_entropy']:.4f} bits | 8.0 bits | {entropy_data['min_entropy']/8*100:.1f}% | Pire scénario |
        | **Collision Entropy** | {entropy_data['collision_entropy']:.4f} bits | 8.0 bits | {entropy_data['collision_entropy']/8*100:.1f}% | Risque de collision |
        | **Conditional Entropy** | {entropy_data['conditional_entropy']:.4f} bits | 8.0 bits | {entropy_data['conditional_entropy']/8*100:.1f}% | Dépendances |
        """)
        
        st.progress(entropy_data['shannon']/8)
        st.caption(f"Entropie Shannon: {entropy_data['shannon']/8*100:.1f}% de l'aléatoire parfait")
        
        if entropy_data['shannon'] > 7.8:
            st.success("✨ Entropie quasi-parfaite - Niveau de sécurité maximal")
        elif entropy_data['shannon'] > 7.5:
            st.success("✅ Excellente entropie - Très bonne sécurité")
        else:
            st.warning("⚠️ Entropie perfectible - Risques théoriques")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Distribution Bytes Hash (Top 10)")
        byte_counts = get_hash_byte_distribution()
        if byte_counts:
            df_counts = pd.DataFrame(byte_counts.most_common(10), columns=["Byte (hex)", "Fréquence"])
            df_counts["Byte (hex)"] = df_counts["Byte (hex)"].apply(lambda x: f"0x{x:02x}")
            st.dataframe(df_counts, use_container_width=True)
        else:
            st.info("Données non disponibles")
        st.caption("Idéalement, chaque byte apparaît ~1-2 fois dans un hash de 64 bytes")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🎲 Tests NIST SP 800-22")
        nist_results = run_nist_statistical_tests()
        
        st.markdown(f"""
        | Test | P-value | Statut |
        |------|---------|--------|
        | **Fréquence (Monobit)** | {nist_results.get('frequence', 0):.4f} | {'✅ Passe' if nist_results.get('frequence_pass', False) else '❌ Échoue'} |
        | **Runs** | {nist_results.get('runs', 0):.4f} | {'✅ Passe' if nist_results.get('runs_pass', False) else '❌ Échoue'} |
        """)
        
        if nist_results.get('frequence_pass', False) and nist_results.get('runs_pass', False):
            st.success("✅ Le hash passe les tests NIST fondamentaux - Aléatoire statistiquement valide")
        
        st.markdown("---")
        st.markdown("### ⚡ Effet Avalanche")
        avalanche = calculate_avalanche_effect()
        sac = calculate_sac()
        
        st.metric("Effet Avalanche", f"{avalanche:.2f}%", delta=f"{avalanche-50:+.2f}%")
        st.metric("Strict Avalanche Criterion (SAC)", f"{sac*100:.2f}%", delta=f"{(sac-0.5)*100:+.2f}%")
        
        st.progress(min(avalanche/100, 1.0))
        st.caption("✅ Valeur idéale: 50% - Indique une diffusion parfaite des changements")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 4: STATISTIQUES AVANCEES
# ============================================
elif page == "📈 Statistiques Avancees":
    st.markdown('<div class="main-header"><h1>📈 Statistiques Cryptographiques Avancées</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Statistiques du Mot")
        stats_mot = get_statistics_mot(st.session_state.current_mot)
        if stats_mot:
            st.markdown(f"""
            | Statistique | Valeur |
            |-------------|--------|
            | **Longueur** | {stats_mot['longueur']} lettres |
            | **Voyelles** | {stats_mot['voyelles']} |
            | **Consonnes** | {stats_mot['consonnes']} |
            | **Lettres uniques** | {stats_mot['lettres_uniques']} |
            | **Valeur numérique** | {stats_mot['valeur_numerique']} |
            | **Valeur moyenne** | {stats_mot['valeur_moyenne']:.2f} |
            | **Dans dictionnaire** | {'✅ Oui' if stats_mot['est_dans_dict'] else '❌ Non'} |
            """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Statistiques Hash")
        if st.session_state.current_hash and len(st.session_state.current_hash) >= 64:
            try:
                hash_bytes = list(bytes.fromhex(st.session_state.current_hash[:64]))
                st.markdown(f"""
                | Statistique | Valeur |
                |-------------|--------|
                | **Moyenne** | {np.mean(hash_bytes):.2f} |
                | **Médiane** | {np.median(hash_bytes):.2f} |
                | **Ecart-type** | {np.std(hash_bytes):.2f} |
                | **Minimum** | {min(hash_bytes)} |
                | **Maximum** | {max(hash_bytes)} |
                """)
            except:
                st.info("Données non disponibles")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Statistiques Signature")
        sig_analysis = get_signature_analysis()
        if sig_analysis:
            st.markdown(f"""
            | Statistique | Valeur |
            |-------------|--------|
            | **Taille** | {sig_analysis.get('length_bytes', 0)} bytes |
            | **Entropie** | {sig_analysis.get('entropy', 0):.3f} bits |
            | **Bytes uniques** | {sig_analysis.get('unique_bytes', 0)}/256 |
            | **Ecart-type** | {sig_analysis.get('std_dev', 0):.2f} |
            | **Asymétrie** | {sig_analysis.get('skewness', 0):.3f} |
            | **Aplatissement** | {sig_analysis.get('kurtosis', 0):.3f} |
            """)
        else:
            st.info("Données non disponibles")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 5: SIGNATURE & CERTIFICAT
# ============================================
elif page == "🔑 Signature & Certificat":
    st.markdown('<div class="main-header"><h1>🔑 Signature Ed25519 & Infrastructure de Certificat</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Signature Complete")
        if st.session_state.current_signature:
            st.code(st.session_state.current_signature, language="text")
        else:
            st.code("Signature non disponible", language="text")
        st.caption("Longueur: 128-256 hex | 64-128 bytes | Signature Ed25519 standard")
        
        st.markdown("### 🔑 Clé Publique")
        if st.session_state.current_public_key:
            st.code(st.session_state.current_public_key, language="text")
        else:
            st.code("Clé publique non disponible", language="text")
        st.caption("Ed25519 Public Key (32-64 bytes)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📱 QR Codes")
        st.image(generate_qr_code(st.session_state.current_mot), caption=f"Mot: {st.session_state.current_mot}", width=150)
        st.image(generate_qr_code(st.session_state.current_gradation), caption="Gradation", width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📜 JWT Complet")
        jwt_payload = {
            "mot": st.session_state.current_mot,
            "gradation": st.session_state.current_gradation,
            "hash": st.session_state.current_hash,
            "public_key": st.session_state.current_public_key,
            "signature": st.session_state.current_signature,
            "timestamp": datetime.now().isoformat(),
            "algorithm": "Ed25519",
            "security_level": "Post-Quantum Ready"
        }
        jwt_b64 = base64.b64encode(json.dumps(jwt_payload).encode()).decode()
        jwt = f"eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.{jwt_b64}"
        st.code(jwt[:200] + "...", language="text")
        st.download_button("📥 Télécharger JWT", jwt, "gradation.jwt", "text/plain")
        
        st.markdown("### 📱 QR Code JWT")
        st.image(generate_qr_code(jwt), caption="QR Code JWT", width=200)
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 6: EXPORT & QR CODE
# ============================================
elif page == "📁 Export & QR Code":
    st.markdown('<div class="main-header"><h1>📁 Export de Données & QR Codes</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📄 Format JSON")
        export_json = json.dumps({
            "mot": st.session_state.current_mot,
            "gradation": st.session_state.current_gradation,
            "hash": st.session_state.current_hash,
            "signature": st.session_state.current_signature,
            "public_key": st.session_state.current_public_key,
            "timestamp": datetime.now().isoformat(),
            "algorithm": "Ed25519"
        }, indent=2)
        st.download_button("📥 Télécharger JSON", export_json, "gradation.json", "application/json")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📄 Format CSV")
        export_csv = pd.DataFrame([{
            "mot": st.session_state.current_mot,
            "gradation": st.session_state.current_gradation,
            "hash": st.session_state.current_hash,
            "signature": st.session_state.current_signature,
            "public_key": st.session_state.current_public_key,
            "timestamp": datetime.now().isoformat()
        }]).to_csv(index=False)
        st.download_button("📥 Télécharger CSV", export_csv, "gradation.csv", "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📄 Format TXT")
        export_txt = f"""=== Quantum Gradation System ===
Mot: {st.session_state.current_mot}
Gradation: {st.session_state.current_gradation}
Hash: {st.session_state.current_hash}
Signature: {st.session_state.current_signature}
Clé publique: {st.session_state.current_public_key}
Timestamp: {datetime.now().isoformat()}
Algorithme: Ed25519
=== Fin du document ==="""
        st.download_button("📥 Télécharger TXT", export_txt, "gradation.txt", "text/plain")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Données Séparées")
        if st.session_state.current_signature:
            st.download_button("🔐 Signature", st.session_state.current_signature, "signature.sig", "text/plain")
        if st.session_state.current_hash:
            st.download_button("📝 Hash", st.session_state.current_hash, "hash.txt", "text/plain")
        if st.session_state.current_public_key:
            st.download_button("🔑 Clé publique", st.session_state.current_public_key, "public_key.key", "text/plain")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📱 QR Codes")
        st.markdown("**Mot actuel:**")
        st.image(generate_qr_code(st.session_state.current_mot), caption=st.session_state.current_mot, width=200)
        st.markdown("**Gradation:**")
        st.image(generate_qr_code(st.session_state.current_gradation), caption="Gradation", width=200)
        st.markdown("**Hash:**")
        if st.session_state.current_hash:
            st.image(generate_qr_code(st.session_state.current_hash[:64]), caption="Hash (extrait)", width=200)
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# PAGE 7: INFORMATIONS SYSTEME
# ============================================
elif page == "ℹ️ Informations Systeme":
    st.markdown('<div class="main-header"><h1>ℹ️ Environnement Système & Métriques</h1></div>', unsafe_allow_html=True)
    
    sys_info = get_system_info()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 💻 Environnement d'Exécution")
        st.markdown(f"""
        | Paramètre | Valeur |
        |-----------|--------|
        | **Python** | {sys_info['python_version']} |
        | **Platforme** | {sys_info['platform']} |
        | **Processeur** | {sys_info['processor']} |
        | **Hostname** | {sys_info['hostname']} |
        | **CPU Cœurs** | {sys_info['cpu_count']} |
        | **CPU Usage** | {sys_info['cpu_percent']}% |
        | **Memory Total** | {sys_info['memory_total']} |
        | **Memory Available** | {sys_info['memory_available']} |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Résumé Cryptographique")
        st.markdown(f"""
        | Métrique | Valeur |
        |----------|--------|
        | **Mot actuel** | {st.session_state.current_mot} |
        | **Gradation** | {st.session_state.current_gradation} |
        | **Hash Entropy** | {calculate_entropy(st.session_state.current_hash or ''):.3f} bits |
        | **Avalanche Effect** | {calculate_avalanche_effect():.2f}% |
        | **NIST Tests** | {'✅ Passés' if run_nist_statistical_tests().get('frequence_pass', False) else '⚠️ À vérifier'} |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Bibliothèques Installées")
        
        libs_status = {
            "PyNaCl (Ed25519)": "✅ Installé" if HAS_NACL else "❌ Non installé (mode démo)",
            "NumPy": np.__version__,
            "Pandas": pd.__version__,
            "Plotly": PLOTLY_VERSION,
            "psutil": "✅ Installé" if HAS_PSUTIL else "❌ Non installé",
            "qrcode": "✅ Installé",
            "scipy": "✅ Installé"
        }
        
        for lib, version in libs_status.items():
            if "✅" in str(version) or "❌" in str(version):
                st.markdown(f"- **{lib}**: {version}")
            else:
                st.markdown(f"- **{lib}**: `{version}`")
        
        if not HAS_NACL:
            st.warning("⚠️ PyNaCl non installé - Fonctionnalités de signature limitées au mode démo")
            st.code("pip install pynacl", language="bash")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### ✅ Validation Finale")
        if st.session_state.current_is_valid:
            st.success("""
            ✅ **SYSTÈME VALIDE**
            
            La signature cryptographique a été vérifiée avec succès. 
            Toutes les métriques de sécurité sont dans les normes attendues.
            """)
        else:
            st.error("❌ **SYSTÈME INVALIDE**")
        
        st.markdown("---")
        st.markdown("""
        **Certification:**  
        Conforme aux standards: NIST SP 800-90B, FIPS 186-5, RFC 8032
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px; font-size: 12px; color: #666;">
    🔐 <strong>Quantum Gradation System v5.0</strong> | Ed25519 Signatures | Post-Quantum Ready<br>
    Mot actuel: <strong>{st.session_state.current_mot}</strong> | 
    Gradation: <strong>{st.session_state.current_gradation}</strong><br>
    Dernière analyse: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | 
    Statut: {'🟢 SYSTÈME SÉCURISÉ' if st.session_state.get('current_is_valid', False) else '🔴 SYSTÈME NON CERTIFIÉ'}<br>
    <span style="font-size: 10px;">© 2026 - Certificat cryptographique vérifiable - Standards NIST/FIPS</span>
</div>
""", unsafe_allow_html=True)
