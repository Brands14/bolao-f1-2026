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
        nome_arquivo = f"{nome_piloto}.png"
        # Usamos a API de conteúdos do GitHub (a mesma que lê o seu CSV)
        url_api = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/fotos/{nome_arquivo}"
        
        try:
            req = urllib.request.Request(url_api, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                # O GitHub já entrega a imagem em Base64 nativamente pela API!
                img_b64 = data['content'].replace('\n', '') 
                
                st.markdown(
                    f'<img src="data:image/png;base64,{img_b64}" width="130" style="border-radius:10px; border: 2px solid #555;">',
                    unsafe_allow_html=True
                )
        except Exception as e:
            # Se não encontrar a foto, mostra apenas o ícone para não travar o app
            st.write("🏎️") 
    else:
        st.write("🏎️")

# --- FUNÇÕES DE BANCO DE DADOS (GitHub) ---
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

def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo F1 - {dados['Usuario']} - GP {dados['GP']}"
    corpo = f"Olá {dados['Usuario']},\nSeu palpite para {dados['GP']} foi recebido.\nBoa sorte!"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except: return False

# --- DADOS DO CAMPEONATO ---
participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]
equipes = {"Equipe 1": ["Fabrício Abe", "Fausto Fleury"], "Equipe 2": ["Myke Ribeiro", "Luciano (Medalha)"], "Equipe 3": ["César Gaudie", "Ronaldo Fleury"], "Equipe 4": ["Valério Bimbato", "Syllas Araújo"], "Equipe 5": ["Frederico Gaudie", "Emilio Jacinto"], "Equipe 6": ["Fernanda Fleury", "Henrique Junqueira"], "Equipe 7": ["Jaime Gabriel", "Hilton Jacinto"], "Equipe 8": ["Delvânia Belo", "Maikon Miranda"], "Equipe 9": ["Alaerte Fleury", "Flávio Soares"], "Equipe 10": ["Rodolfo Brandão", "George Fleury"]}
pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]
lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- INTERFACE ---
st.sidebar.title("🏎️ F1 Bolão 2026")
menu = st.sidebar.radio("Navegação:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    st.header("📝 Formulário de Palpites")
    usuario = st.sidebar.selectbox("Selecione seu nome:", [""] + participantes)
    
    if usuario:
        col_gp, col_sessao = st.columns(2)
        with col_gp: gp_sel = st.selectbox("GP:", lista_gps)
        opcoes = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_sel in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
        with col_sessao: tipo_sel = st.selectbox("Sessão:", opcoes)

        with st.form("meu_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            vr = ab = ut = ""

            if "Pole" in tipo_sel:
                c1, c2 = st.columns([3, 1])
                with c1: pole = st.selectbox("Pole Position:", pilotos)
                with c2: mostrar_perfil(pole)
            
            elif tipo_sel == "Corrida Principal":
                st.subheader("🏆 Pódio")
                c1, c2 = st.columns([3, 1])
                with c1: p1 = st.selectbox("1º Colocado:", pilotos)
                with c2: mostrar_perfil(p1)
                
                col_a, col_b = st.columns(2)
                with col_a: 
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    mostrar_perfil(p2)
                with col_b: 
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    mostrar_perfil(p3)

                st.divider()
                st.subheader("🏁 Top 10 e VAR")
                ca, cb = st.columns(2)
                with ca:
                    p4, p5, p6, p7 = [st.selectbox(f"{i}º:", pilotos) for i in range(4, 8)]
                with cb:
                    p8, p9, p10 = [st.selectbox(f"{i}º:", pilotos) for i in range(8, 11)]
                    vr = st.selectbox("Melhor Volta:", pilotos)
                
                ab = st.selectbox("1º Abandono:", pilotos)
                ut = st.selectbox("Mais Ultrapassagens:", pilotos)

            elif tipo_sel == "Corrida Sprint":
                c1, c2 = st.columns([3, 1])
                with c1: p1 = st.selectbox("Vencedor Sprint:", pilotos)
                with c2: mostrar_perfil(p1)
                p2, p3, p4, p5, p6, p7, p8 = [st.selectbox(f"{i}º:", pilotos) for i in range(2, 9)]

            email_confirm = st.text_input("Seu e-mail cadastrado:", type="password")
            if st.form_submit_button("Salvar Palpite 💾"):
                if email_confirm:
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_sel, "Tipo": tipo_sel, "Usuario": usuario,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, 
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": vr, "PrimeiroAbandono": ab, "MaisUltrapassagens": ut
                    }
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        st.success("✅ Palpite enviado com sucesso!")
                        enviar_recibo_email(dados, email_confirm)
                    else: st.error("❌ Erro ao gravar no GitHub.")

elif menu == "Meus Palpites":
    st.header("🕵️ Histórico")
    u_h = st.selectbox("Usuário:", [""] + participantes)
    if u_h:
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty:
            st.dataframe(df[df['Usuario'] == u_h])

elif menu == "Classificações":
    st.header("🏆 Dashboard de Pontos")
    st.info("Gráficos de desempenho em desenvolvimento para amanhã!")

elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha:", type="password")
    if senha == "fleury1475":
        st.write("Modo Admin Ativo")
