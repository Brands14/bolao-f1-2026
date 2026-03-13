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
    msg = smtplib.email.mime.multipart.MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo F1 - {dados['Usuario']} - GP {dados['GP']}"
    corpo = f"Seu palpite para {dados['GP']} foi recebido com sucesso!\nBoa sorte!"
    msg.attach(smtplib.email.mime.text.MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except: return False

# --- LISTAS DO CAMPEONATO ---
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
        c_gp, c_ses = st.columns(2)
        with c_gp: gp_sel = st.selectbox("GP:", lista_gps)
        opcoes = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_sel in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
        with c_ses: tipo_sel = st.selectbox("Sessão:", opcoes)

        st.divider()

        # --- VARIÁVEIS DE PALPITE ---
        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
        vr = ab = ut = ""

        if "Pole" in tipo_sel:
            col_sel, col_img = st.columns([3, 1])
            with col_sel:
                pole = st.selectbox("Quem será o Pole?", pilotos, key="pole_box")
            with col_img:
                mostrar_perfil(pole)
            
            with st.form("confirm_pole"):
                email_c = st.text_input("Confirme seu E-mail:", type="password")
                if st.form_submit_button("GRAVAR POLE 💾"):
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp_sel, "Tipo": tipo_sel, "Usuario": usuario, "Pole": pole}
                    if guardar_dados(dados, ARQUIVO_DADOS): st.success("Gravado!")
                    else: st.error("Erro!")

        elif tipo_sel == "Corrida Principal":
            st.subheader("🏆 Pódio (Atualização Instantânea)")
            
            # P1
            c1, c2 = st.columns([3, 1])
            with c1: p1 = st.selectbox("1º Colocado (Vencedor):", pilotos, key="p1_box")
            with c2: mostrar_perfil(p1)
            
            # P2 e P3 lado a lado
            col_a, col_img_a, col_b, col_img_b = st.columns([2, 1, 2, 1])
            with col_a: p2 = st.selectbox("2º Colocado:", pilotos, key="p2_box")
            with col_img_a: mostrar_perfil(p2)
            with col_b: p3 = st.selectbox("3º Colocado:", pilotos, key="p3_box")
            with col_img_b: mostrar_perfil(p3)

            with st.form("confirm_corrida"):
                st.subheader("🏁 Top 10 e VAR")
                ca, cb = st.columns(2)
                with ca:
                    p4 = st.selectbox("4º Colocado:", pilotos)
                    p5 = st.selectbox("5º Colocado:", pilotos)
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                with cb:
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    p9 = st.selectbox("9º Colocado:", pilotos)
                    p10 = st.selectbox("10º Colocado:", pilotos)
                    vr = st.selectbox("Melhor Volta:", pilotos)
                
                ab = st.selectbox("1º Abandono:", pilotos)
                ut = st.selectbox("Mais Ultrapassagens:", pilotos)
                
                email_c = st.text_input("E-mail para validação:", type="password")
                if st.form_submit_button("SALVAR TODOS OS PALPITES 🚀"):
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_sel, "Tipo": tipo_sel, "Usuario": usuario,
                        "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, 
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": vr, "PrimeiroAbandono": ab, "MaisUltrapassagens": ut
                    }
                    if guardar_dados(dados, ARQUIVO_DADOS): st.success("🏁 Palpites salvos no sistema!")
                    else: st.error("Erro ao salvar.")

# --- OUTRAS SEÇÕES ---
elif menu == "Meus Palpites":
    st.header("🕵️ Histórico")
    u_h = st.selectbox("Usuário:", [""] + participantes)
    if u_h:
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty: st.dataframe(df[df['Usuario'] == u_h])

elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha Admin:", type="password")
    if senha == "fleury1475":
        st.write("🔧 Painel de Controle Ativo")
        if st.button("Debug: Listar Fotos"):
            url_api = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/fotos"
            req = urllib.request.Request(url_api, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            with urllib.request.urlopen(req) as response:
                arqs = json.loads(response.read().decode())
                for a in arqs: st.text(a['name'])
