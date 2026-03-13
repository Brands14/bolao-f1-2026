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

# 1. Configurações Iniciais
st.set_page_config(page_title="Palpites F1 2026", layout="wide")

# 🚨 CONFIGURAÇÕES GITHUB
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Chaves de segurança não encontradas no Streamlit Cloud.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO PARA EXIBIR FOTOS VIA API DO GITHUB (BASE64) ---
def mostrar_perfil(nome_piloto):
    if nome_piloto and nome_piloto not in ["", "Nenhum / Outro"]:
        nome_url = f"{nome_piloto}.png".replace(" ", "%20")
        url_api = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/fotos/{nome_url}"
        
        try:
            req = urllib.request.Request(url_api, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                img_b64 = data['content'].replace('\n', '') 
                st.markdown(
                    f'<img src="data:image/png;base64,{img_b64}" width="130" style="border-radius:10px; border: 2px solid #555; box-shadow: 3px 3px 10px rgba(0,0,0,0.3);">',
                    unsafe_allow_html=True
                )
        except:
            st.write("🏎️") # Mostra ícone se a foto não existir
    else:
        st.write("🏎️")

# --- FUNÇÕES DE BANCO DE DADOS (GitHub) ---
def ler_dados(arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    req = urllib.request.Request(url, headers={"
