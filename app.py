import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import time
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

# Puxa as chaves mestras do painel do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas nas configurações do Streamlit.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- LOGO (VERSÃO COMPATÍVEL COM VERSÃO 1.31.0) ---
def mostrar_logo():
    url_logo = "https://raw.githubusercontent.com/Brands14/bolao-f1-2026/main/logo.png"
    st.sidebar.image(url_logo, width=200)

# 2. Dados Fixos da Temporada
lista_gps = [
    "Bahrein", "Arábia Saudita", "Austrália", "China", "Japão", "Miami",
    "Emília-Romanha", "Mônaco", "Espanha", "Canadá", "Áustria", "Reino Unido",
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura",
    "Estados Unidos", "Cidade do México", "São Paulo", "Las Vegas", "Catar", "Abu Dhabi"
]

cronograma_gps = {
    "Bahrein": datetime(2026, 3, 2, 12, 0),
    "Arábia Saudita": datetime(2026, 3, 9, 14, 0),
    "Austrália": datetime(2026, 3, 16, 1, 0),
    "China": datetime(2026, 3, 23, 4, 0),
    "Japão": datetime(2026, 4, 6, 2, 0),
    "Miami": datetime(2026, 5, 4, 16, 30),
    "Emília-Romanha": datetime(2026, 5, 18, 10, 0),
    "Mônaco": datetime(2026, 5, 25, 10, 0),
    "Espanha": datetime(2026, 6, 1, 10, 0),
    "Canadá": datetime(2026, 6, 15, 15, 0),
    "Áustria": datetime(2026, 6, 29, 10, 0),
    "Reino Unido": datetime(2026, 7, 6, 11, 0),
    "Bélgica": datetime(2026, 7, 27, 10, 0),
    "Hungria": datetime(2026, 8, 3, 10, 0),
    "Holanda": datetime(2026, 8, 24, 10, 0),
    "Itália": datetime(2026, 8, 31, 10, 0),
    "Azerbaijão": datetime(2026, 9, 21, 8, 0),
    "Singapura": datetime(2026, 10, 5, 9, 0),
    "Estados Unidos": datetime(2026, 10, 19, 16, 0),
    "Cidade do México": datetime(2026, 10, 26, 16, 0),
    "São Paulo": datetime(2026, 11, 9, 14, 0),
    "Las Vegas": datetime(2026, 11, 23, 3, 0),
    "Catar": datetime(2026, 11, 30, 14, 0),
    "Abu Dhabi": datetime(2026, 12, 7, 11, 0)
}

lista_pilotos = [
    "Max Verstappen", "Sergio Pérez", "Lewis Hamilton", "George Russell",
    "Charles Leclerc", "Carlos Sainz", "Lando Norris", "Oscar Piastri",
    "Fernando Alonso", "Lance Stroll", "Pierre Gasly", "Esteban Ocon",
    "Alex Albon", "Logan Sargeant", "Yuki Tsunoda", "Daniel Ricciardo",
    "Valtteri Bottas", "Guanyu Zhou", "Nico Hulkenberg", "Kevin Magnussen"
]

equipes = {
    "Red Bull": ["Max Verstappen", "Sergio Pérez"],
    "Mercedes": ["Lewis Hamilton", "George Russell"],
    "Ferrari": ["Charles Leclerc", "Carlos Sainz"],
    "McLaren": ["Lando Norris", "Oscar Piastri"],
    "Aston Martin": ["Fernando Alonso", "Lance Stroll"],
    "Alpine": ["Pierre Gasly", "Esteban Ocon"],
    "Williams": ["Alex Albon", "Logan Sargeant"],
    "RB": ["Yuki Tsunoda", "Daniel Ricciardo"],
    "Sauber": ["Valtteri Bottas", "Guanyu Zhou"],
    "Haas": ["Nico Hulkenberg", "Kevin Magnussen"]
}

participantes = [
    "Adriano", "Brands", "Bruno", "Cadu", "Cesar", "Danilo", "Digo", "Diogo", 
    "Fábio", "Fagner", "Felipe", "Flávio", "Igor", "Junior", "Léo", "Lucas", 
    "Maikon", "Marcelo", "Mário", "Mateus", "Maurício", "Murilo", "Neto", 
    "Paulinho", "Rafael", "Renan", "Ricardo", "Robson", "Rodrigo", "Sandro", 
    "Thiago", "Tiago", "Victor", "Vitor", "Willian"
]

# 3. Funções de Integração com GitHub
def ler_dados(nome_arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
            return df, data['sha']
    except urllib.error.HTTPError as e:
        return pd.DataFrame(), None

def salvar_palpite_github(nome_arquivo, novos_dados):
    df_atual, sha = ler_dados(nome_arquivo)
    df_novo = pd.DataFrame([novos_dados])
    
    if not df_atual.empty:
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    conteudo_csv = df_final.to_csv(index=False)
    conteudo_b64 = base64.b64encode(conteudo_csv.encode()).decode()
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    payload = {
        "message": f"Novo palpite: {novos_dados['Usuario']} - {novos_dados['GP']}",
        "content": conteudo_b64,
        "sha": sha if sha else None
    }
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
        with urllib.request.urlopen(req) as response:
            return True
    except:
        return False

def deletar_registro_github(nome_arquivo, mascara):
    df_atual, sha = ler_dados(nome_arquivo)
    if df_atual.empty or not sha:
        return False
    
    df_final = df_atual[mascara]
    conteudo_csv = df_final.to_csv(index=False)
    conteudo_b64 = base64.b64encode(conteudo_csv.encode()).decode()
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    payload = {
        "message": "Registro removido pelo Admin",
        "content": conteudo_b64,
        "sha": sha
    }
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
        with urllib.request.urlopen(req) as response:
            return True
    except:
        return False

# 4. Lógica de Pontuação
def calcular_pontos(palpite, gabarito):
    pontos = 0
    # Acerto exato (10 pontos)
    for i in range(1, 9):
        if palpite[f'P{i}'] == gabarito[f'P{i}']:
            pontos += 10
    
    # Volta Rápida (5 pontos)
    if str(palpite.get('V_Rapida', '')) == str(gabarito.get('V_Rapida', '')) and palpite.get('V_Rapida', '') != 'N/A':
        pontos += 5
        
    return pontos

# 5. INTERFACE (App Principal)
def main():
    mostrar_logo()
    st.sidebar.title("🏁 Bolão F1 2026")
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "Enviar Palpite", "📊 Dashboard", "⚙️ Admin"])

    if menu == "🏠 Início":
        st.title("Bem-vindo ao Bolão F1 2026!")
        st.markdown("""
        ### Como funciona:
        1. **Escolha seu nome** na barra lateral.
        2. **Selecione o GP** e a sessão desejada.
        3. **Preencha seu palpite** do 1º ao 8º lugar.
        4. **Pontuação:**
            - **10 pontos** por acerto de posição exata.
            - **5 pontos** por acerto da Volta Rápida (apenas na Corrida Principal).
        """)
        st.info("Os palpites fecham automaticamente 30 minutos antes do horário oficial de cada sessão.")

    # --- ÁREA: ENVIAR PALPITE ---
    if menu == "Enviar Palpite":
        usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
        
        if usuario_logado:
            equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
            st.header(f"🏎️ Palpite de {usuario_logado} ({equipe_usuario})")

            # --- FILTRO PARA OCULTAR O QUE JÁ PASSOU ---
            fuso_sp = pytz.timezone("America/Sao_Paulo")
            hoje = datetime.now(fuso_sp).date()
            gps_disponiveis = [gp for gp in lista_gps if cronograma_gps[gp].date() >= hoje]
            
            if not gps_disponiveis:
                gps_disponiveis = [lista_gps[-1]]

            col1, col2 = st.columns(2)
            with col1:
                gp_escolhido = st.selectbox("Selecione o Grande Prêmio:", gps_disponiveis)
            with col2:
                sessao = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"])

            agora = datetime.now(fuso_sp)
            limite = cronograma_gps[gp_escolhido].replace(tzinfo=fuso_sp)
            restante = (limite - agora).total_seconds()
            
            if restante < 1800:
                st.error(f"❌ Prazo encerrado para {gp_escolhido}!")
            else:
                st.info(f"⏳ Prazo até: {limite.strftime('%d/%m %H:%M')}")
                
                with st.form("form_palpite"):
                    st.subheader("Escolha seus pilotos (P1 ao P8):")
                    c1, c2, c3, c4 = st.columns(4)
                    p1 = c1.selectbox("🥇 1º Lugar", lista_pilotos, key="p1")
                    p2 = c2.selectbox("🥈 2º Lugar", lista_pilotos, key="p2")
                    p3 = c3.selectbox("🥉 3º Lugar", lista_pilotos, key="p3")
                    p4 = c4.selectbox("4º Lugar", lista_pilotos, key="p4")
                    
                    c5, c6, c7, c8 = st.columns(4)
                    p5 = c5.selectbox("5º Lugar", lista_pilotos, key="p5")
                    p6 = c6.selectbox("6º Lugar", lista_pilotos, key="p6")
                    p7 = c7.selectbox("7º Lugar", lista_pilotos, key="p7")
                    p8 = c8.selectbox("8º Lugar", lista_pilotos, key="p8")
                    
                    v_rapida = st.selectbox("⏱️ Volta Rápida:", ["N/A"] + lista_pilotos)
                    submit = st.form_submit_button("ENVIAR PALPITE")
                    
                    if submit:
                        dados_palpite = {
                            "GP": gp_escolhido, "Tipo": sessao, "Usuario": usuario_logado,
                            "Equipe": equipe_usuario, "P1": p1, "P2": p2, "P3": p3, "P4": p4,
                            "P5": p5, "P6": p6, "P7": p7, "P8": p8,
                            "V_Rapida": v_rapida, "Timestamp": agora.strftime("%d/%m/%Y %H:%M:%S")
                        }
                        if salvar_palpite_github(ARQUIVO_DADOS, dados_palpite):
                            st.success(f"✅ Palpite enviado!")
                            st.balloons()
                            import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import time
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

# Puxa as chaves mestras do painel do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas nas configurações do Streamlit.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- LOGO (VERSÃO COMPATÍVEL COM VERSÃO 1.31.0) ---
def mostrar_logo():
    url_logo = "https://raw.githubusercontent.com/Brands14/bolao-f1-2026/main/logo.png"
    st.sidebar.image(url_logo, width=200)

# 2. Dados Fixos da Temporada
lista_gps = [
    "Bahrein", "Arábia Saudita", "Austrália", "China", "Japão", "Miami",
    "Emília-Romanha", "Mônaco", "Espanha", "Canadá", "Áustria", "Reino Unido",
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura",
    "Estados Unidos", "Cidade do México", "São Paulo", "Las Vegas", "Catar", "Abu Dhabi"
]

cronograma_gps = {
    "Bahrein": datetime(2026, 3, 2, 12, 0),
    "Arábia Saudita": datetime(2026, 3, 9, 14, 0),
    "Austrália": datetime(2026, 3, 16, 1, 0),
    "China": datetime(2026, 3, 23, 4, 0),
    "Japão": datetime(2026, 4, 6, 2, 0),
    "Miami": datetime(2026, 5, 4, 16, 30),
    "Emília-Romanha": datetime(2026, 5, 18, 10, 0),
    "Mônaco": datetime(2026, 5, 25, 10, 0),
    "Espanha": datetime(2026, 6, 1, 10, 0),
    "Canadá": datetime(2026, 6, 15, 15, 0),
    "Áustria": datetime(2026, 6, 29, 10, 0),
    "Reino Unido": datetime(2026, 7, 6, 11, 0),
    "Bélgica": datetime(2026, 7, 27, 10, 0),
    "Hungria": datetime(2026, 8, 3, 10, 0),
    "Holanda": datetime(2026, 8, 24, 10, 0),
    "Itália": datetime(2026, 8, 31, 10, 0),
    "Azerbaijão": datetime(2026, 9, 21, 8, 0),
    "Singapura": datetime(2026, 10, 5, 9, 0),
    "Estados Unidos": datetime(2026, 10, 19, 16, 0),
    "Cidade do México": datetime(2026, 10, 26, 16, 0),
    "São Paulo": datetime(2026, 11, 9, 14, 0),
    "Las Vegas": datetime(2026, 11, 23, 3, 0),
    "Catar": datetime(2026, 11, 30, 14, 0),
    "Abu Dhabi": datetime(2026, 12, 7, 11, 0)
}

lista_pilotos = [
    "Max Verstappen", "Sergio Pérez", "Lewis Hamilton", "George Russell",
    "Charles Leclerc", "Carlos Sainz", "Lando Norris", "Oscar Piastri",
    "Fernando Alonso", "Lance Stroll", "Pierre Gasly", "Esteban Ocon",
    "Alex Albon", "Logan Sargeant", "Yuki Tsunoda", "Daniel Ricciardo",
    "Valtteri Bottas", "Guanyu Zhou", "Nico Hulkenberg", "Kevin Magnussen"
]

equipes = {
    "Red Bull": ["Max Verstappen", "Sergio Pérez"],
    "Mercedes": ["Lewis Hamilton", "George Russell"],
    "Ferrari": ["Charles Leclerc", "Carlos Sainz"],
    "McLaren": ["Lando Norris", "Oscar Piastri"],
    "Aston Martin": ["Fernando Alonso", "Lance Stroll"],
    "Alpine": ["Pierre Gasly", "Esteban Ocon"],
    "Williams": ["Alex Albon", "Logan Sargeant"],
    "RB": ["Yuki Tsunoda", "Daniel Ricciardo"],
    "Sauber": ["Valtteri Bottas", "Guanyu Zhou"],
    "Haas": ["Nico Hulkenberg", "Kevin Magnussen"]
}

participantes = [
    "Adriano", "Brands", "Bruno", "Cadu", "Cesar", "Danilo", "Digo", "Diogo", 
    "Fábio", "Fagner", "Felipe", "Flávio", "Igor", "Junior", "Léo", "Lucas", 
    "Maikon", "Marcelo", "Mário", "Mateus", "Maurício", "Murilo", "Neto", 
    "Paulinho", "Rafael", "Renan", "Ricardo", "Robson", "Rodrigo", "Sandro", 
    "Thiago", "Tiago", "Victor", "Vitor", "Willian"
]

# 3. Funções de Integração com GitHub
def ler_dados(nome_arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
            return df, data['sha']
    except urllib.error.HTTPError as e:
        return pd.DataFrame(), None

def salvar_palpite_github(nome_arquivo, novos_dados):
    df_atual, sha = ler_dados(nome_arquivo)
    df_novo = pd.DataFrame([novos_dados])
    
    if not df_atual.empty:
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    conteudo_csv = df_final.to_csv(index=False)
    conteudo_b64 = base64.b64encode(conteudo_csv.encode()).decode()
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    payload = {
        "message": f"Novo palpite: {novos_dados['Usuario']} - {novos_dados['GP']}",
        "content": conteudo_b64,
        "sha": sha if sha else None
    }
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
        with urllib.request.urlopen(req) as response:
            return True
    except:
        return False

def deletar_registro_github(nome_arquivo, mascara):
    df_atual, sha = ler_dados(nome_arquivo)
    if df_atual.empty or not sha:
        return False
    
    df_final = df_atual[mascara]
    conteudo_csv = df_final.to_csv(index=False)
    conteudo_b64 = base64.b64encode(conteudo_csv.encode()).decode()
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    payload = {
        "message": "Registro removido pelo Admin",
        "content": conteudo_b64,
        "sha": sha
    }
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
        with urllib.request.urlopen(req) as response:
            return True
    except:
        return False

# 4. Lógica de Pontuação
def calcular_pontos(palpite, gabarito):
    pontos = 0
    # Acerto exato (10 pontos)
    for i in range(1, 9):
        if palpite[f'P{i}'] == gabarito[f'P{i}']:
            pontos += 10
    
    # Volta Rápida (5 pontos)
    if str(palpite.get('V_Rapida', '')) == str(gabarito.get('V_Rapida', '')) and palpite.get('V_Rapida', '') != 'N/A':
        pontos += 5
        
    return pontos

# 5. INTERFACE (App Principal)
def main():
    mostrar_logo()
    st.sidebar.title("🏁 Bolão F1 2026")
    menu = st.sidebar.radio("Navegação:", ["🏠 Início", "Enviar Palpite", "📊 Dashboard", "⚙️ Admin"])

    if menu == "🏠 Início":
        st.title("Bem-vindo ao Bolão F1 2026!")
        st.markdown("""
        ### Como funciona:
        1. **Escolha seu nome** na barra lateral.
        2. **Selecione o GP** e a sessão desejada.
        3. **Preencha seu palpite** do 1º ao 8º lugar.
        4. **Pontuação:**
            - **10 pontos** por acerto de posição exata.
            - **5 pontos** por acerto da Volta Rápida (apenas na Corrida Principal).
        """)
        st.info("Os palpites fecham automaticamente 30 minutos antes do horário oficial de cada sessão.")

    # --- ÁREA: ENVIAR PALPITE ---
    if menu == "Enviar Palpite":
        usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
        
        if usuario_logado:
            equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
            st.header(f"🏎️ Palpite de {usuario_logado} ({equipe_usuario})")

            # --- FILTRO PARA OCULTAR O QUE JÁ PASSOU ---
            fuso_sp = pytz.timezone("America/Sao_Paulo")
            hoje = datetime.now(fuso_sp).date()
            gps_disponiveis = [gp for gp in lista_gps if cronograma_gps[gp].date() >= hoje]
            
            if not gps_disponiveis:
                gps_disponiveis = [lista_gps[-1]]

            col1, col2 = st.columns(2)
            with col1:
                gp_escolhido = st.selectbox("Selecione o Grande Prêmio:", gps_disponiveis)
            with col2:
                sessao = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"])

            agora = datetime.now(fuso_sp)
            limite = cronograma_gps[gp_escolhido].replace(tzinfo=fuso_sp)
            restante = (limite - agora).total_seconds()
            
            if restante < 1800:
                st.error(f"❌ Prazo encerrado para {gp_escolhido}!")
            else:
                st.info(f"⏳ Prazo até: {limite.strftime('%d/%m %H:%M')}")
                
                with st.form("form_palpite"):
                    st.subheader("Escolha seus pilotos (P1 ao P8):")
                    c1, c2, c3, c4 = st.columns(4)
                    p1 = c1.selectbox("🥇 1º Lugar", lista_pilotos, key="p1")
                    p2 = c2.selectbox("🥈 2º Lugar", lista_pilotos, key="p2")
                    p3 = c3.selectbox("🥉 3º Lugar", lista_pilotos, key="p3")
                    p4 = c4.selectbox("4º Lugar", lista_pilotos, key="p4")
                    
                    c5, c6, c7, c8 = st.columns(4)
                    p5 = c5.selectbox("5º Lugar", lista_pilotos, key="p5")
                    p6 = c6.selectbox("6º Lugar", lista_pilotos, key="p6")
                    p7 = c7.selectbox("7º Lugar", lista_pilotos, key="p7")
                    p8 = c8.selectbox("8º Lugar", lista_pilotos, key="p8")
                    
                    v_rapida = st.selectbox("⏱️ Volta Rápida:", ["N/A"] + lista_pilotos)
                    submit = st.form_submit_button("ENVIAR PALPITE")
                    
                    if submit:
                        dados_palpite = {
                            "GP": gp_escolhido, "Tipo": sessao, "Usuario": usuario_logado,
                            "Equipe": equipe_usuario, "P1": p1, "P2": p2, "P3": p3, "P4": p4,
                            "P5": p5, "P6": p6, "P7": p7, "P8": p8,
                            "V_Rapida": v_rapida, "Timestamp": agora.strftime("%d/%m/%Y %H:%M:%S")
                        }
                        if salvar_palpite_github(ARQUIVO_DADOS, dados_palpite):
                            st.success(f"✅ Palpite enviado!")
                            st.balloons()
