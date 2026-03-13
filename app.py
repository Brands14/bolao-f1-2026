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

# Verificação de Segurança
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Chaves de segurança (secrets) não encontradas no Streamlit Cloud.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO PARA EXIBIR FOTOS DO SEU GITHUB ---
def mostrar_perfil(nome_piloto):
    if nome_piloto and nome_piloto not in ["", "Nenhum / Outro"]:
        # Formata o nome para a URL
        nome_url = nome_piloto.replace(" ", "%20")
        
        # Adicionamos um parâmetro aleatório no final (?v=1) para evitar problemas de cache
        url_foto = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome_url}.png?v=1"
        
        # Usamos o st.markdown para renderizar a imagem caso o st.image falhe
        st.markdown(
            f"""
            <img src="{url_foto}" width="120" style="border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);">
            """, 
            unsafe_allow_html=True
        )
    else:
        st.info("Aguardando piloto...")

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

def deletar_registro_github(arquivo, mascara_filtro):
    df_atual, sha = ler_dados(arquivo)
    if not df_atual.empty:
        df_final = df_atual[mascara_filtro]
        csv_content = df_final.to_csv(index=False)
        encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {"message": "Delete record", "content": encoded_content, "sha": sha}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
        try:
            with urllib.request.urlopen(req) as response: return response.status in [200, 201]
        except: return False
    return False

# --- EMAIL E CÁLCULOS ---
def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo F1 - {dados['Usuario']} - GP {dados['GP']}"
    corpo = f"Olá {dados['Usuario']},\nSeu palpite para {dados['GP']} ({dados['Tipo']}) foi recebido em {dados['Data_Envio']}.\nBoa sorte!"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except: return False

def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    return valor_pontos if val_p and val_p == val_g else 0

def calcular_pontos_sessao(palpite, gabarito):
    pontos = 0
    tipo = palpite.get('Tipo', '')
    if "Pole" in tipo: pontos += check_ponto(palpite, gabarito, 'Pole', 100)
    elif tipo == "Corrida Principal":
        pts = [0, 150, 125, 100, 85, 70, 60, 50, 40, 25, 15]
        for i in range(1, 11): 
            pontos += check_ponto(palpite, gabarito, f'P{i}', pts[i])
        pontos += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pontos += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pontos += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
    elif tipo == "Corrida Sprint":
        pts_s = [0, 80, 70, 60, 50, 40, 30, 20, 10]
        for i in range(1, 9):
            pontos += check_ponto(palpite, gabarito, f'P{i}', pts_s[i])
    return pontos

# --- DADOS ESTÁTICOS ---
participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]
emails_autorizados = {p: f"email_{p.lower().replace(' ', '')}@teste.com" for p in participantes} # Ajuste conforme sua lista real

equipes = {"Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"], "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"], "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"], "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"], "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"], "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"], "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"], "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"], "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"], "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]}
pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]
lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- INTERFACE ---
st.sidebar.header("🏁 Bolão F1 2026")
menu = st.sidebar.radio("Navegação:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    st.header("📝 Enviar Novo Palpite")
    usuario_logado = st.sidebar.selectbox("Selecione seu nome:", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((e for e, m in equipes.items() if usuario_logado in m), "Sem Equipe")
        st.info(f"Piloto: **{usuario_logado}** | 🏎️ Equipe: **{equipe_usuario}**")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp: gp_sel = st.selectbox("Grande Prêmio:", lista_gps)
        opcoes = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_sel in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
        with col_tipo: tipo_sel = st.selectbox("Sessão:", opcoes)

        with st.form("form_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            vr = abandono = ultrapassagem = ""
            
            if "Pole" in tipo_sel:
                c1, c2 = st.columns([3, 1])
                with c1: pole = st.selectbox("Quem será o Pole?", pilotos)
                with c2: mostrar_perfil(pole)
            
            elif tipo_sel == "Corrida Principal":
                st.subheader("🏆 Pódio e Destaques")
                c1, c2 = st.columns([3, 1])
                with c1: p1 = st.selectbox("1º Colocado (Vencedor):", pilotos)
                with c2: mostrar_perfil(p1)
                
                col_a, col_b = st.columns(2)
                with col_a: 
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    mostrar_perfil(p2)
                with col_b: 
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    mostrar_perfil(p3)

                st.divider()
                st.subheader("🏁 Top 10 e Extras")
                ca, cb = st.columns(2)
                with ca:
                    p4, p5, p6, p7 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(4, 8)]
                with cb:
                    p8, p9, p10 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(8, 11)]
                    vr = st.selectbox("Melhor Volta:", pilotos)

                st.divider()
                abandono = st.selectbox("Quem abandona primeiro?", pilotos)
                ultrapassagem = st.selectbox("Quem fará mais ultrapassagens?", pilotos)

            elif tipo_sel == "Corrida Sprint":
                c1, c2 = st.columns([3, 1])
                with c1: p1 = st.selectbox("Vencedor Sprint:", pilotos)
                with c2: mostrar_perfil(p1)
                p2, p3, p4, p5, p6, p7, p8 = [st.selectbox(f"{i}º Colocado:", pilotos) for i in range(2, 9)]

            st.divider()
            email_valida = st.text_input("Confirme seu E-mail cadastrado:", type="password")
            
            if st.form_submit_button("GRAVAR PALPITE NO GITHUB 🚀"):
                # Validação simples de email (ajuste conforme sua lógica real)
                if email_valida.strip().lower(): 
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_sel, "Tipo": tipo_sel, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, 
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": vr, "PrimeiroAbandono": abandono, "MaisUltrapassagens": ultrapassagem
                    }
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        st.success(f"✅ Sucesso! Palpite para o GP de {gp_sel} foi salvo.")
                        enviar_recibo_email(dados, email_valida)
                    else: st.error("Erro ao salvar no GitHub.")
                else: st.error("Email inválido.")

elif menu == "Meus Palpites":
    st.header("🕵️ Histórico de Palpites")
    u_c = st.selectbox("Selecione seu nome:", [""] + participantes)
    if u_c:
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty:
            meus_dados = df[df['Usuario'] == u_c]
