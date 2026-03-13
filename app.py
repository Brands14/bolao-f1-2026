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

GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Chaves de segurança não encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO DE DIAGNÓSTICO E EXIBIÇÃO ---
def mostrar_perfil(nome_piloto):
    if nome_piloto and nome_piloto not in ["", "Nenhum / Outro"]:
        # Tenta buscar o arquivo exato
        nome_arquivo = f"{nome_piloto}.png"
        nome_url = nome_arquivo.replace(" ", "%20")
        url_api = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/fotos/{nome_url}"
        
        try:
            req = urllib.request.Request(url_api, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                img_b64 = data['content'].replace('\n', '') 
                st.markdown(f'<img src="data:image/png;base64,{img_b64}" width="130" style="border-radius:10px; border:2px solid #555;">', unsafe_allow_html=True)
        except Exception as e:
            # Se der erro, vamos mostrar o que aconteceu para debugar
            st.write(f"⚠️ Erro ao buscar: {nome_piloto}.png")
            st.caption("Verifique se o nome do arquivo no GitHub está idêntico.")
    else:
        st.write("🏎️")

# --- FUNÇÕES DE BANCO DE DADOS ---
def ler_dados(arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content)), data['sha']
    except: return pd.DataFrame(), None

def guardar_dados(dados, arquivo):
    df_atual, sha = ler_dados(arquivo)
    df_novo = pd.DataFrame([dados])
    if not df_atual.empty:
        if 'Usuario' in dados:
            mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']) & (df_atual['Usuario'] == dados['Usuario']))
        else:
            mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']))
        df_atual = df_atual[mascara]
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else: df_final = df_novo
    csv_content = df_final.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    payload = {"message": f"Update {arquivo}", "content": encoded_content}
    if sha: payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(req) as response: return response.status in [200, 201]
    except: return False

# --- LISTAS ---
participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]
pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]
lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- INTERFACE ---
st.sidebar.title("🏎️ F1 Bolão 2026")
menu = st.sidebar.radio("Navegação:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    st.header("📝 Novo Palpite")
    usuario = st.sidebar.selectbox("Selecione seu nome:", [""] + participantes)
    
    if usuario:
        gp_sel = st.selectbox("GP:", lista_gps)
        tipo_sel = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal"])

        with st.form("form_fotos"):
            if "Pole" in tipo_sel:
                c1, c2 = st.columns([3, 1])
                with c1: pole = st.selectbox("Pole Position:", pilotos)
                with c2: mostrar_perfil(pole)
            else:
                c1, c2 = st.columns([3, 1])
                with c1: p1 = st.selectbox("Vencedor:", pilotos)
                with c2: mostrar_perfil(p1)
            
            if st.form_submit_button("Apenas Testar Foto 📸"):
                st.info("Formulário atualizado.")

elif menu == "Administrador":
    # Adicionei uma ferramenta de debug aqui para você ver o que tem na pasta fotos
    if st.sidebar.text_input("Senha Admin:", type="password") == "fleury1475":
        st.subheader("Debug de Fotos")
        if st.button("Listar Arquivos na Pasta Fotos"):
            url_debug = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/fotos"
            req = urllib.request.Request(url_debug, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            try:
                with urllib.request.urlopen(req) as response:
                    arquivos = json.loads(response.read().decode())
                    for f in arquivos: st.write(f"- {f['name']}")
            except Exception as e: st.error(f"Erro: {e}")
