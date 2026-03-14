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

# FUNÇÃO DE FOTOS (MANTIDA)
def exibir_foto_piloto(nome):
    if nome and nome != "" and nome != "Nenhum / Outro":
        nome_arquivo = nome.replace(" ", "%20") + ".png"
        url_foto = URL_BASE_FOTOS + nome_arquivo
        st.image(url_foto, width=80)

try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.png", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

# DADOS ORIGINAIS DO TXT
participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]
emails_autorizados = {"Alaerte Fleury": "alaertefleury@hotmail.com", "César Gaudie": "c3sargaudie@gmail.com", "Delvânia Belo": "del.gomes04@gmail.com", "Emilio Jacinto": "emiliopaja@gmail.com", "Fabrício Abe": "fabricio.fleury84@gmail.com", "Fausto Fleury": "faustofleury.perito@gmail.com", "Fernanda Fleury": "fefleury17@gmail.com", "Flávio Soares": "flaviosoaresparente@gmail.com", "Frederico Gaudie": "fredericofleury@gmail.com", "George Fleury": "gfleury@gmail.com", "Henrique Junqueira": "amtelegas@gmail.com", "Hilton Jacinto": "hiltonlpj2@hotmail.com", "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com", "Luciano (Medalha)": "luciano.pallada@terra.com.br", "Maikon Miranda": "maikonmiranda@gmail.com", "Myke Ribeiro": "mribeiro3088@gmail.com", "Rodolfo Brandão": "rodolfo.fleury@gmail.com", "Ronaldo Fleury": "ronaldofleury18@gmail.com", "Syllas Araújo": "sylaopoim@gmail.com", "Valério Bimbato": "bimbatovalerio2@gmail.com"}
equipes = {"Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"], "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"], "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"], "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"], "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"], "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"], "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"], "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"], "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"], "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]}
pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]
lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# FUNÇÕES DO GITHUB (RESTAURADAS DO TXT)
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
    payload = {"message": "Update", "content": encoded_content}
    if sha: payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(req) as response: return response.status in [200, 201]
    except: return False

def deletar_registro_github(arquivo, mascara_filtro):
    df_atual, sha = ler_dados(arquivo)
    if not df_atual.empty:
        df_final = df_atual[mascara_filtro]
        csv_content = df_final.to_csv(index=False)
        encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {"message": "Removendo registro", "content": encoded_content, "sha": sha}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
        try:
            with urllib.request.urlopen(req) as response: return response.status in [200, 201]
        except: return False
    return False

# PONTUAÇÃO (ORIGINAL)
def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    if val_p and val_p == val_g: return valor_pontos
    return 0

def calcular_pontos_sessao(palpite, gabarito):
    pontos = 0
    tipo = palpite.get('Tipo', '')
    if "Pole" in tipo: pontos += check_ponto(palpite, gabarito, 'Pole', 100)
    elif tipo == "Corrida Principal":
        valores = [150, 125, 100, 85, 70, 60, 50, 40, 25, 15]
        for i in range(1, 11): pontos += check_ponto(palpite, gabarito, f'P{i}', valores[i-1])
        pontos += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pontos += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pontos += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
    elif tipo == "Corrida Sprint":
        valores_s = [80, 70, 60, 50, 40, 30, 20, 10]
        for i in range(1, 9): pontos += check_ponto(palpite, gabarito, f'P{i}', valores_s[i-1])
    return pontos

# MENU
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ABA 1: ENVIAR (BLINDADA) ---
if menu == "Enviar Palpite":
    user = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    if user:
        equipe = next((eq for eq, m em equipes.items() if user em m), "Sem Equipe")
        st.write(f"**{user}** ({equipe})")
        c1, c2 = st.columns(2)
        with c1: gp = st.selectbox("GP:", lista_gps)
        with c2: tp = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp em sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])
        
        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = vr = ab = mu = ""
        if "Pole" em tp:
            pole = st.selectbox("Pole Position:", pilotos); exibir_foto_piloto(pole)
        elif tp == "Corrida Principal":
            col_a, col_b = st.columns(2)
            with col_a:
                p1 = st.selectbox("1º Colocado:", pilotos); exibir_foto_piloto(p1)
                p2 = st.selectbox("2º Colocado:", pilotos); exibir_foto_piloto(p2)
                p3 = st.selectbox("3º Colocado:", pilotos); exibir_foto_piloto(p3)
                p4 = st.selectbox("4º Colocado:", pilotos); exibir_foto_piloto(p4)
                p5 = st.selectbox("5º Colocado:", pilotos); exibir_foto_piloto(p5)
            with col_b:
                p6 = st.selectbox("6º Colocado:", pilotos); exibir_foto_piloto(p6)
                p7 = st.selectbox("7º Colocado:", pilotos); exibir_foto_piloto(p7)
                p8 = st.selectbox("8º Colocado:", pilotos); exibir_foto_piloto(p8)
                p9 = st.selectbox("9º Colocado:", pilotos); exibir_foto_piloto(p9)
                p10 = st.selectbox("10º Colocado:", pilotos); exibir_foto_piloto(p10)
            vr = st.selectbox("Volta Rápida:", pilotos); exibir_foto_piloto(vr)
            ab = st.selectbox("Abandono:", pilotos); exibir_foto_piloto(ab)
            mu = st.selectbox("Ultrapassagens:", pilotos); exibir_foto_piloto(mu)
        # (Outras sessões seguem a mesma lógica de exibir_foto_piloto abaixo do selectbox)

        with st.form("f_envio"):
            email = st.text_input("E-mail:", type="password")
            if st.form_submit_button("GRAVAR"):
                if email.lower() == emails_autorizados.get(user, "").lower():
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp, "Tipo": tp, "Usuario": user, "Equipe": equipe, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": vr, "PrimeiroAbandono": ab, "MaisUltrapassagens": mu}
                    if guardar_dados(dados, ARQUIVO_DADOS): st.success("Gravado!")
                    else: st.error("Erro no GitHub.")
                else: st.error("Erro de e-mail.")

# --- ABA 2: MEUS PALPITES (RESTAURADA) ---
elif menu == "Meus Palpites":
    user_view = st.sidebar.selectbox("Ver palpites de:", [""] + participantes)
    if user_view:
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty:
            df_filtro = df[df['Usuario'] == user_view].sort_values(by="GP")
            st.dataframe(df_filtro)
        else: st.info("Sem dados.")

# --- ABA 3: CLASSIFICAÇÕES (RESTAURADA) ---
elif menu == "Classificações":
    tab1, tab2 = st.tabs(["🏆 Geral", "📍 Por Etapa"])
    df_p, _ = ler_dados(ARQUIVO_DADOS)
    df_g, _ = ler_dados(ARQUIVO_GABARITOS)
    if not df_p.empty and not df_g.empty:
        lista_pts = []
        for _, p em df_p.iterrows():
            g = df_g[(df_g['GP'] == p['GP']) & (df_g['Tipo'] == p['Tipo'])]
            if not g.empty:
                lista_pts.append({"GP": p['GP'], "Usuario": p['Usuario'], "Equipe": p['Equipe'], "Pontos": calcular_pontos_sessao(p, g.iloc[0])})
        df_rank = pd.DataFrame(lista_pts)
        with tab1:
            st.table(df_rank.groupby(['Usuario', 'Equipe']).sum().sort_values(by="Pontos", ascending=False).reset_index())
        with tab2:
            gp_escolha = st.selectbox("GP:", lista_gps)
            st.table(df_rank[df_rank['GP'] == gp_escolha].groupby('Usuario').sum().sort_values(by="Pontos", ascending=False).reset_index())

# --- ABA 4: ADMINISTRADOR (RESTAURADA INTEGRALMENTE) ---
elif menu == "Administrador":
    if st.text_input("Senha:", type="password") == "f12026":
        st.success("Acesso ok.")
        a1, a2 = st.tabs(["Lançar Resultados", "Limpeza"])
        with a1:
            with st.form("f_gab"):
                gp_r = st.selectbox("GP:", lista_gps)
                tp_r = st.selectbox("Tipo:", ["Classificação Principal (Pole)", "Corrida Principal"])
                g_pole = st.selectbox("Pole Oficial:", pilotos)
                if st.form_submit_button("Salvar Gabarito"):
                    if guardar_dados({"GP": gp_r, "Tipo": tp_r, "Pole": g_pole}, ARQUIVO_GABARITOS): st.success("OK")
        with a2:
            df_l, _ = ler_dados(ARQUIVO_DADOS)
            if not df_l.empty:
                u_del = st.selectbox("Usuário para apagar:", df_l['Usuario'].unique())
                if st.button("Confirmar Exclusão"):
                    if deletar_registro_github(ARQUIVO_DADOS, df_l['Usuario'] != u_del): st.rerun()
