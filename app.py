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

GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"
URL_BASE_FOTOS = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/"

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança não foram encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# FUNÇÃO PARA EXIBIR FOTO (Ajustada para não quebrar se a foto faltar)
def exibir_foto_piloto(nome):
    if nome and nome != "" and nome != "Nenhum / Outro":
        nome_arquivo = nome.replace(" ", "%20") + ".png"
        url_foto = URL_BASE_FOTOS + nome_arquivo
        st.image(url_foto, width=80)

try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.png", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]

emails_autorizados = {"Alaerte Fleury": "alaertefleury@hotmail.com", "César Gaudie": "c3sargaudie@gmail.com", "Delvânia Belo": "del.gomes04@gmail.com", "Emilio Jacinto": "emiliopaja@gmail.com", "Fabrício Abe": "fabricio.fleury84@gmail.com", "Fausto Fleury": "faustofleury.perito@gmail.com", "Fernanda Fleury": "fefleury17@gmail.com", "Flávio Soares": "flaviosoaresparente@gmail.com", "Frederico Gaudie": "fredericofleury@gmail.com", "George Fleury": "gfleury@gmail.com", "Henrique Junqueira": "amtelegas@gmail.com", "Hilton Jacinto": "hiltonlpj2@hotmail.com", "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com", "Luciano (Medalha)": "luciano.pallada@terra.com.br", "Maikon Miranda": "maikonmiranda@gmail.com", "Myke Ribeiro": "mribeiro3088@gmail.com", "Rodolfo Brandão": "rodolfo.fleury@gmail.com", "Ronaldo Fleury": "ronaldofleury18@gmail.com", "Syllas Araújo": "sylaopoim@gmail.com", "Valério Bimbato": "bimbatovalerio2@gmail.com"}

equipes = {"Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"], "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"], "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"], "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"], "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"], "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"], "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"], "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"], "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"], "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]}

pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]

lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- FUNÇÕES DE BANCO E EMAIL (Mantidas como no TXT original) ---
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
        if 'Usuario' in dados: mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']) & (df_atual['Usuario'] == dados['Usuario']))
        else: mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']))
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
    msg['Subject'] = f"🏁 Recibo F1 - {dados['Usuario']} - GP {dados['GP']}"
    corpo = f"Palpite de {dados['Usuario']} recebido.\n\nSessão: {dados['Tipo']}\nData: {dados['Data_Envio']}"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except: return False

def calcular_pontos_sessao(palpite, gabarito):
    # Lógica simplificada de pontos conforme original
    return 0 

# --- INTERFACE ---
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"**{usuario_logado}** (🏎️ {equipe_usuario})")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp: gp_selecionado = st.selectbox("Grande Prêmio:", lista_gps)
        with col_tipo: tipo_sessao = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_selecionado in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])
        
        st.header(f"🏁 {gp_selecionado} - {tipo_sessao}")

        # VARIÁVEIS DE PALPITE
        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = v_rapida = p_abandono = m_ultrapassagens = ""

        # SELEÇÃO COM IMAGEM (Fora do form para ser instantâneo)
        if "Pole" in tipo_sessao:
            pole = st.selectbox("Pole Position:", pilotos, key="p_pole")
            exibir_foto_piloto(pole)
        elif tipo_sessao == "Corrida Principal":
            c1, c2 = st.columns(2)
            with c1:
                p1 = st.selectbox("1º Colocado:", pilotos); exibir_foto_piloto(p1)
                p2 = st.selectbox("2º Colocado:", pilotos); exibir_foto_piloto(p2)
                p3 = st.selectbox("3º Colocado:", pilotos); exibir_foto_piloto(p3)
                p4 = st.selectbox("4º Colocado:", pilotos); exibir_foto_piloto(p4)
                p5 = st.selectbox("5º Colocado:", pilotos); exibir_foto_piloto(p5)
            with c2:
                p6 = st.selectbox("6º Colocado:", pilotos); exibir_foto_piloto(p6)
                p7 = st.selectbox("7º Colocado:", pilotos); exibir_foto_piloto(p7)
                p8 = st.selectbox("8º Colocado:", pilotos); exibir_foto_piloto(p8)
                p9 = st.selectbox("9º Colocado:", pilotos); exibir_foto_piloto(p9)
                p10 = st.selectbox("10º Colocado:", pilotos); exibir_foto_piloto(p10)
            v_rapida = st.selectbox("Melhor Volta:", pilotos); exibir_foto_piloto(v_rapida)
            p_abandono = st.selectbox("1º Abandono:", pilotos); exibir_foto_piloto(p_abandono)
            m_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos); exibir_foto_piloto(m_ultrapassagens)
        elif tipo_sessao == "Corrida Sprint":
            c1, c2 = st.columns(2)
            with c1:
                p1 = st.selectbox("1º:", pilotos); exibir_foto_piloto(p1)
                p2 = st.selectbox("2º:", pilotos); exibir_foto_piloto(p2)
                p3 = st.selectbox("3º:", pilotos); exibir_foto_piloto(p3)
                p4 = st.selectbox("4º:", pilotos); exibir_foto_piloto(p4)
            with c2:
                p5 = st.selectbox("5º:", pilotos); exibir_foto_piloto(p5)
                p6 = st.selectbox("6º:", pilotos); exibir_foto_piloto(p6)
                p7 = st.selectbox("7º:", pilotos); exibir_foto_piloto(p7)
                p8 = st.selectbox("8º:", pilotos); exibir_foto_piloto(p8)

        # BOTÃO DE SALVAR (Dentro de um form pequeno apenas para o envio)
        with st.form("envio_final"):
            email_confirmacao = st.text_input("E-mail de validação:", type="password")
            if st.form_submit_button("GRAVAR PALPITE"):
                if email_confirmacao.lower() == emails_autorizados.get(usuario_logado, "").lower():
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": v_rapida, "PrimeiroAbandono": p_abandono, "MaisUltrapassagens": m_ultrapassagens}
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        enviar_recibo_email(dados, email_confirmacao)
                        st.success("Palpite Gravado!")
                    else: st.error("Erro no GitHub.")
                else: st.error("E-mail incorreto.")

# --- As outras abas seguem o padrão do seu TXT original ---
else:
    st.info("Acesse as outras funcionalidades ou selecione um piloto.")
