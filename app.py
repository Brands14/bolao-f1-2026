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

# 🚨 CONFIGURAÇÕES GITHUB
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Puxa as chaves mestras do painel do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO MESTRA PARA CARREGAR IMAGENS DO GITHUB (FOTOS E LOGO) ---
def carregar_imagem_github(caminho_arquivo):
    """Busca imagem no GitHub via API e retorna em Base64 para o Streamlit"""
    nome_url = caminho_arquivo.replace(" ", "%20")
    url_api = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_url}"
    try:
        req = urllib.request.Request(url_api, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['content'].replace('\n', '')
    except:
        return None

def mostrar_perfil(nome_piloto, largura=120):
    if nome_piloto and nome_piloto not in ["", "Nenhum / Outro"]:
        img_b64 = carregar_imagem_github(f"fotos/{nome_piloto}.png")
        if img_b64:
            st.markdown(
                f'<div style="text-align: center;">'
                f'<img src="data:image/png;base64,{img_b64}" width="{largura}" style="border-radius:10px; border:2px solid #555; box-shadow: 3px 3px 10px rgba(0,0,0,0.3);">'
                f'<p style="margin-top:5px; font-weight:bold; font-size:14px;">{nome_piloto}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.write(f"🏎️ {nome_piloto}")
    else:
        st.write("🏎️")

# --- EXIBIÇÃO DO LOGO ---
logo_b64 = carregar_imagem_github("WhatsApp Image 2026-02-24 at 16.12.18.png")
if logo_b64:
    st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;">', unsafe_allow_html=True)
else:
    st.title("🏁 Palpites F1 2026")

# --- LISTAS E DICIONÁRIOS (SEU CÓDIGO ORIGINAL) ---
participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]

emails_autorizados = {
    "Alaerte Fleury": "alaertefleury@hotmail.com", "César Gaudie": "c3sargaudie@gmail.com", "Delvânia Belo": "del.gomes04@gmail.com", "Emilio Jacinto": "emiliopaja@gmail.com", "Fabrício Abe": "fabricio.fleury84@gmail.com", "Fausto Fleury": "faustofleury.perito@gmail.com", "Fernanda Fleury": "fefleury17@gmail.com", "Flávio Soares": "flaviosoaresparente@gmail.com", "Frederico Gaudie": "fredericofleury@gmail.com", "George Fleury": "gfleury@gmail.com", "Henrique Junqueira": "amtelegas@gmail.com", "Hilton Jacinto": "hiltonlpj2@hotmail.com", "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com", "Luciano (Medalha)": "luciano.pallada@terra.com.br", "Maikon Miranda": "maikonmiranda@gmail.com", "Myke Ribeiro": "mribeiro3088@gmail.com", "Rodolfo Brandão": "rodolfo.fleury@gmail.com", "Ronaldo Fleury": "ronaldofleury18@gmail.com", "Syllas Araújo": "sylaopoim@gmail.com", "Valério Bimbato": "bimbatovalerio2@gmail.com"
}

equipes = {
    "Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"], "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"], "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"], "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"], "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"], "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"], "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"], "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"], "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"], "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]
}

pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]

lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- BANCO DE DADOS (GitHub API) ---
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
    corpo = f"Olá {dados['Usuario']},\nSeu palpite foi registrado com sucesso!\nGP: {dados['GP']}\nSessão: {dados['Tipo']}"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except: return False

# --- LÓGICA DE NAVEGAÇÃO ---
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((e for e, m in equipes.items() if usuario_logado in m), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp: gp_sel = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
        with col_tipo: tipo_sel = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_sel in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])

        st.header(f"🏁 GP: {gp_sel} - {tipo_sel}")
        
        # --- CAMPOS FORA DO FORM PARA ATUALIZAR FOTO NA HORA ---
        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
        vr = ab = ut = ""

        if "Pole" in tipo_sel:
            c1, c2 = st.columns([3, 1])
            with c1: pole = st.selectbox("Pole Position:", pilotos, key="p_sel")
            with c2: mostrar_perfil(pole)
        
        elif tipo_sel == "Corrida Principal":
            # Pódio com fotos
            cp1, cp2, cp3 = st.columns(3)
            with cp1: 
                p1 = st.selectbox("1º Colocado:", pilotos, key="p1_sel")
                mostrar_perfil(p1)
            with cp2:
                p2 = st.selectbox("2º Colocado:", pilotos, key="p2_sel")
                mostrar_perfil(p2)
            with cp3:
                p3 = st.selectbox("3º Colocado:", pilotos, key="p3_sel")
                mostrar_perfil(p3)
            
            # Outros campos dentro de colunas
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                p4 = st.selectbox("4º Colocado:", pilotos)
                p5 = st.selectbox("5º Colocado:", pilotos)
                p6 = st.selectbox("6º Colocado:", pilotos)
                p7 = st.selectbox("7º Colocado:", pilotos)
            with col2:
                p8 = st.selectbox("8º Colocado:", pilotos)
                p9 = st.selectbox("9º Colocado:", pilotos)
                p10 = st.selectbox("10º Colocado:", pilotos)
                vr = st.selectbox("Melhor Volta:", pilotos)
                ab = st.selectbox("1º Abandono:", pilotos)
                ut = st.selectbox("Mais Ultrapassagens:", pilotos)

        # --- FORMULÁRIO APENAS PARA O BOTÃO DE SALVAR ---
        with st.form("confirmar_envio"):
            st.markdown("🔒 **Assinatura de Segurança**")
            email_confirm = st.text_input("Digite o seu E-mail cadastrado:", type="password")
            if st.form_submit_button("GRAVAR PALPITE PERMANENTE 🏁"):
                email_correto = emails_autorizados.get(usuario_logado, "").strip().lower()
                if email_confirm.strip().lower() == email_correto:
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_sel, "Tipo": tipo_sel, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": vr, "PrimeiroAbandono": ab, "MaisUltrapassagens": ut
                    }
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        enviar_recibo_email(dados, email_correto)
                        st.success("✅ Palpite Salvo e Recibo Enviado!")
                    else: st.error("Erro ao salvar no GitHub.")
                else: st.error("E-mail incorreto!")

# Mantenha as outras seções (Meus Palpites, Classificações, Administrador) como estão no seu original...
elif menu == "Meus Palpites":
    st.header("🕵️ Meu Histórico")
    # ... (seu código de histórico)

elif menu == "Classificações":
    st.header("🏆 Classificação Geral")
    # ... (seu código de classificação)

elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha Admin:", type="password")
    if senha == "fleury1475":
        st.write("Modo Diretor de Prova")
        # ... (seu código de admin)
