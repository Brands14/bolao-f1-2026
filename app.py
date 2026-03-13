import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import urllib.request
import urllib.error
import json
import base64
import io
import smtplib
import requests  # Adicionado para baixar as imagens
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Configurações Iniciais
st.set_page_config(page_title="Palpites F1 2026", layout="wide")

# 🚨 CONFIGURAÇÕES GITHUB
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Verificação de Segurança (Secrets do Streamlit)
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Chaves de segurança (secrets) não encontradas no Streamlit Cloud.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO MESTRA PARA EXIBIR FOTOS (VIA BASE64) ---
def mostrar_perfil(nome_piloto):
    if nome_piloto and nome_piloto not in ["", "Nenhum / Outro"]:
        nome_url = nome_piloto.replace(" ", "%20")
        # Link RAW do seu repositório
        url_foto = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome_url}.png"
        
        try:
            # O servidor baixa a imagem usando o seu Token
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url_foto, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Converte para Base64 para evitar bloqueios de navegador
                img_b64 = base64.b64encode(response.content).decode()
                st.markdown(
                    f'<img src="data:image/png;base64,{img_b64}" width="130" style="border-radius:10px; border: 2px solid #333; box-shadow: 3px 3px 10px rgba(0,0,0,0.3);">',
                    unsafe_allow_html=True
                )
            else:
                st.caption(f"🏁 (Foto não encontrada)")
        except:
            st.caption("⚠️ Erro de conexão")
    else:
        st.write("🏎️")

# --- FUNÇÕES DE BANCO DE DADOS (GitHub) ---
def ler_dados(arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    req = urllib.request.Request(url, headers={"Authorization": f"
