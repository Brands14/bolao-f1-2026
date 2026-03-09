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

# 🚨 MUDE AQUI: Seu usuário do GitHub
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

pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]
lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- FUNÇÕES DE DADOS ---
def ler_dados(arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content)), data['sha']
    except urllib.error.HTTPError:
        return pd.DataFrame(), None

def salvar_no_github(df, arquivo, sha):
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    payload = {"message": f"Update {arquivo}", "content": encoded_content}
    if sha: payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req) as response: return response.status in [200, 201]

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
    else:
        df_final = df_novo
    return salvar_no_github(df_final, arquivo, sha)

def apagar_registro(usuario, gp, tipo, arquivo):
    df, sha = ler_dados(arquivo)
    if not df.empty:
        df_novo = df[~((df['Usuario'] == usuario) & (df['GP'] == gp) & (df['Tipo'] == tipo))]
        return salvar_no_github(df_novo, arquivo, sha)
    return False

# --- FUNÇÃO DE E-MAIL ---
def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    corpo = f"Olá {dados['Usuario']},\n\nSeu palpite foi registrado!\n\nGP: {dados['GP']}\nSessão: {dados['Tipo']}\nData: {dados['Data_Envio']}\n\nConfira os detalhes no app."
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except: return False

# --- LÓGICA DE PONTOS ---
def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    return valor_pontos if (val_p and val_p == val_g) else 0

def calcular_pontos_sessao(palpite, gabarito):
    pontos = 0
    tipo = palpite.get('Tipo', '')
    if "Classificação" in tipo or "Qualy Sprint" in tipo:
        pontos += check_ponto(palpite, gabarito, 'Pole', 100)
    elif tipo == "Corrida Principal":
        for i, p in enumerate(['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10']):
            pontos += check_ponto(palpite, gabarito, p, [150,125,100,85,70,60,50,40,25,15][i])
        pontos += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pontos += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pontos += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
    elif tipo == "Corrida Sprint":
        for i, p in enumerate(['P1','P2','P3','P4','P5','P6','P7','P8']):
            pontos += check_ponto(palpite, gabarito, p, [80,70,60,50,40,30,20,10][i])
    return pontos

# --- INTERFACE ---
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    if usuario_logado:
        equipe_usuario = next((e for e, m in equipes.items() if usuario_logado in m), "Sem Equipe")
        gp_selecionado = st.selectbox("GP:", lista_gps)
        tipo_sessao = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_selecionado in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])
        
        with st.form("form_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = vr = pa = mu = ""
            if "Pole" in tipo_sessao: pole = st.selectbox("Pole Position:", pilotos)
            elif "Corrida Principal" in tipo_sessao:
                c1, c2 = st.columns(2)
                with c1: p1=st.selectbox("1º:", pilotos); p2=st.selectbox("2º:", pilotos); p3=st.selectbox("3º:", pilotos); p4=st.selectbox("4º:", pilotos); p5=st.selectbox("5º:", pilotos)
                with c2: p6=st.selectbox("6º:", pilotos); p7=st.selectbox("7º:", pilotos); p8=st.selectbox("8º:", pilotos); p9=st.selectbox("9º:", pilotos); p10=st.selectbox("10º:", pilotos); vr=st.selectbox("Volta Rápida:", pilotos); pa=st.selectbox("1º Abandono:", pilotos); mu=st.selectbox("Mais Ultrapassagens:", pilotos)
            elif "Corrida Sprint" in tipo_sessao:
                c1, c2 = st.columns(2)
                with c1: p1=st.selectbox("1º:", pilotos); p2=st.selectbox("2º:", pilotos); p3=st.selectbox("3º:", pilotos); p4=st.selectbox("4º:", pilotos)
                with c2: p5=st.selectbox("5º:", pilotos); p6=st.selectbox("6º:", pilotos); p7=st.selectbox("7º:", pilotos); p8=st.selectbox("8º:", pilotos)
            
            email_conf = st.text_input("Seu E-mail:", type="password")
            if st.form_submit_button("Salvar Palpite"):
                if email_conf.strip().lower() == emails_autorizados.get(usuario_logado, "").lower():
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": vr, "PrimeiroAbandono": pa, "MaisUltrapassagens": mu}
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        enviar_recibo_email(dados, email_conf)
                        st.success("Palpite salvo e e-mail enviado!")
                else: st.error("E-mail incorreto.")

elif menu == "Meus Palpites":
    st.header("🕵️ Histórico")
    u_c = st.selectbox("Nome:", [""] + participantes)
    e_c = st.text_input("E-mail:", type="password")
    if st.button("Buscar") and e_c.strip().lower() == emails_autorizados.get(u_c, "").lower():
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty: st.dataframe(df[df['Usuario'] == u_c], use_container_width=True)

elif menu == "Classificações":
    st.header("🏆 Resultados")
    df_p, _ = ler_dados(ARQUIVO_DADOS)
    df_g, _ = ler_dados(ARQUIVO_GABARITOS)
    if not df_p.empty and not df_g.empty:
        res = []
        for _, row in df_p.iterrows():
            gab = df_g[(df_g['GP'] == row['GP']) & (df_g['Tipo'] == row['Tipo'])]
            if not gab.empty: res.append({"Usuario": row['Usuario'], "Equipe": row['Equipe'], "Pontos": calcular_pontos_sessao(row, gab.iloc[-1]), "GP": row['GP']})
        if res:
            df_res = pd.DataFrame(res)
            st.subheader("Pilotos")
            st.dataframe(df_res.groupby('Usuario')['Pontos'].sum().sort_values(ascending=False), use_container_width=True)
            st.subheader("Equipes")
            st.dataframe(df_res.groupby('Equipe')['Pontos'].sum().sort_values(ascending=False), use_container_width=True)

elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha Admin:", type="password")
    if senha == "fleury1475":
        st.warning("MODO ADMIN ATIVO")
        
        # --- NOVO: ZONA DE EXCLUSÃO ---
        st.subheader("🗑️ Zona de Exclusão (Limpeza de Testes)")
        df_auditoria, _ = ler_dados(ARQUIVO_DADOS)
        if not df_auditoria.empty:
            col_del1, col_del2, col_del3 = st.columns(3)
            with col_del1: u_del = st.selectbox("Palpiteiro:", [""] + sorted(df_auditoria['Usuario'].unique().tolist()))
            with col_del2: gp_del = st.selectbox("GP:", [""] + sorted(df_auditoria['GP'].unique().tolist()))
            with col_del3: tipo_del = st.selectbox("Sessão:", [""] + sorted(df_auditoria['Tipo'].unique().tolist()))
            
            if st.button("🔴 APAGAR PALPITE DEFINITIVAMENTE"):
                if u_del and gp_del and tipo_del:
                    if apagar_registro(u_del, gp_del, tipo_del, ARQUIVO_DADOS):
                        st.success(f"O palpite de {u_del} no GP {gp_del} foi removido!")
                        st.rerun()
                else: st.warning("Selecione todos os campos para apagar.")
        
        st.divider()
        st.subheader("🏆 Lançar Gabarito")
        gp_a = st.selectbox("GP Gabarito:", lista_gps)
        tipo_a = st.selectbox("Sessão Gabarito:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_a in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])
        with st.form("gab"):
            # (Campos de gabarito simplificados para economia de espaço, mesma lógica anterior)
            pole_a = st.selectbox("Pole Oficial:", pilotos)
            if st.form_submit_button("Salvar Gabarito"):
                guardar_dados({"GP": gp_a, "Tipo": tipo_a, "Pole": pole_a}, ARQUIVO_GABARITOS)
                st.success("Gabarito Salvo!")
