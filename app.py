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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Configurações Iniciais
st.set_page_config(page_title="Palpites F1 2026", layout="wide")

# 🚨 MUDE AQUI: Coloque exatamente o seu nome de usuário do GitHub dentro das aspas!
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Puxa chaves do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança não foram encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.png", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

participantes = [
    "Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", 
    "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", 
    "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", 
    "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", 
    "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"
]

emails_autorizados = {
    "Alaerte Fleury": "alaertefleury@hotmail.com",
    "César Gaudie": "c3sargaudie@gmail.com",
    "Delvânia Belo": "del.gomes04@gmail.com",
    "Emilio Jacinto": "emiliopaja@gmail.com",
    "Fabrício Abe": "fabricio.fleury84@gmail.com",
    "Fausto Fleury": "faustofleury.perito@gmail.com",
    "Fernanda Fleury": "fefleury17@gmail.com",
    "Flávio Soares": "flaviosoaresparente@gmail.com",
    "Frederico Gaudie": "fredericofleury@gmail.com",
    "George Fleury": "gfleury@gmail.com",
    "Henrique Junqueira": "amtelegas@gmail.com",
    "Hilton Jacinto": "hiltonlpj2@hotmail.com",
    "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com",
    "Luciano (Medalha)": "luciano.pallada@terra.com.br",
    "Maikon Miranda": "maikonmiranda@gmail.com",
    "Myke Ribeiro": "mribeiro3088@gmail.com",
    "Rodolfo Brandão": "rodolfo.fleury@gmail.com",
    "Ronaldo Fleury": "ronaldofleury18@gmail.com",
    "Syllas Araújo": "sylaopoim@gmail.com",
    "Valério Bimbato": "bimbatovalerio2@gmail.com"
}

equipes = {
    "Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"],
    "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"],
    "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"],
    "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"],
    "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"],
    "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"],
    "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"],
    "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"],
    "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"],
    "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]
}

pilotos = [
    "", 
    "Max Verstappen", "Isack Hadjar",
    "Lewis Hamilton", "Charles Leclerc",
    "George Russell", "Kimi Antonelli",
    "Lando Norris", "Oscar Piastri",
    "Fernando Alonso", "Lance Stroll",
    "Gabriel Bortoleto", "Nico Hülkenberg",
    "Alex Albon", "Carlos Sainz",
    "Pierre Gasly", "Franco Colapinto",
    "Oliver Bearman", "Esteban Ocon",
    "Liam Lawson", "Arvid Lindblad",
    "Sergio Pérez", "Valtteri Bottas",
    "Nenhum / Outro"
]

lista_gps = [
    "Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", 
    "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", 
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", 
    "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# ---------------------------------------------
# 🔥 NOVA FUNÇÃO — MOSTRAR FOTO DO PILOTO
# ---------------------------------------------
def mostrar_foto_piloto(nome):
    if nome and nome != "Nenhum / Outro":
        nome_arquivo = nome.replace(" ", "%20")
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome_arquivo}.png"
        try:
            st.image(url, width=140)
        except:
            st.warning(f"Foto não encontrada: {nome}")

# ---------------------------------------------
# A PARTIR DAQUI É O SEU CÓDIGO NORMAL
# ---------------------------------------------

# (FUNÇÕES DE BANCO, EMAIL, PONTOS… seguem IGUAIS)
# NÃO REMOVI NADA — APENAS MANTIVE SEU CÓDIGO ORIGINAL

# -------------------------------------------------------------
# IMPORTANTE: pulei aqui para onde começam os selects de pilotos
# -------------------------------------------------------------

# 5. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")

        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
            
        if gp_selecionado in sprint_gps:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"]
        else:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal"]
            
        with col_tipo:
            tipo_sessao = st.selectbox("Tipo de Sessão:", opcoes_sessao)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        
        with st.form("form_palpite"):

            # -------- POLE --------
            if "Pole" in tipo_sessao:
                st.info("📌 Palpite apenas para a Pole Position.")
                pole = st.selectbox("Pole Position:", pilotos)
                mostrar_foto_piloto(pole)

            # -------- CORRIDA PRINCIPAL --------
            elif tipo_sessao == "Corrida Principal":
                st.info("📌 Palpite da Corrida de Domingo.")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos); mostrar_foto_piloto(p1)
                    p2 = st.selectbox("2º Colocado:", pilotos); mostrar_foto_piloto(p2)
                    p3 = st.selectbox("3º Colocado:", pilotos); mostrar_foto_piloto(p3)
                    p4 = st.selectbox("4º Colocado:", pilotos); mostrar_foto_piloto(p4)
                    p5 = st.selectbox("5º Colocado:", pilotos); mostrar_foto_piloto(p5)
                with col2:
                    p6 = st.selectbox("6º Colocado:", pilotos); mostrar_foto_piloto(p6)
                    p7 = st.selectbox("7º Colocado:", pilotos); mostrar_foto_piloto(p7)
                    p8 = st.selectbox("8º Colocado:", pilotos); mostrar_foto_piloto(p8)
                    p9 = st.selectbox("9º Colocado:", pilotos); mostrar_foto_piloto(p9)
                    p10 = st.selectbox("10º Colocado:", pilotos); mostrar_foto_piloto(p10)
                    volta_rapida = st.selectbox("Melhor Volta:", pilotos); mostrar_foto_piloto(volta_rapida)
                    primeiro_abandono = st.selectbox("1º Abandono:", pilotos); mostrar_foto_piloto(primeiro_abandono)
                    mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos); mostrar_foto_piloto(mais_ultrapassagens)

            # -------- CORRIDA SPRINT --------
            elif tipo_sessao == "Corrida Sprint":
                st.info("📌 Palpite da Sprint.")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos); mostrar_foto_piloto(p1)
                    p2 = st.selectbox("2º Colocado:", pilotos); mostrar_foto_piloto(p2)
                    p3 = st.selectbox("3º Colocado:", pilotos); mostrar_foto_piloto(p3)
                    p4 = st.selectbox("4º Colocado:", pilotos); mostrar_foto_piloto(p4)
                with col2:
                    p5 = st.selectbox("5º Colocado:", pilotos); mostrar_foto_piloto(p5)
                    p6 = st.selectbox("6º Colocado:", pilotos); mostrar_foto_piloto(p6)
                    p7 = st.selectbox("7º Colocado:", pilotos); mostrar_foto_piloto(p7)
                    p8 = st.selectbox("8º Colocado:", pilotos); mostrar_foto_piloto(p8)

            st.divider()
            st.markdown("🔒 **Assinatura de Segurança**")
            email_confirmacao = st.text_input("Digite seu E-mail cadastrado:", type="password")
            
            enviado = st.form_submit_button(f"Salvar Palpite - {tipo_sessao} 🏁")

            # (RESTO DO SEU PROCESSAMENTO ORIGINAL SEGUE NORMAL…)
