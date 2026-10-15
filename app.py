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

# 1. Configurações Iniciais da Página
st.set_page_config(
    page_title="Bolão F1 2026 — Premium Edition",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🚨 Configurações do Repositório do GitHub
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Puxa as chaves de acesso
try:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = os.environ.get("SENHA_EMAIL") or st.secrets["SENHA_EMAIL"]
except:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    SENHA_EMAIL = os.environ.get("SENHA_EMAIL")

if not GITHUB_TOKEN:
    st.error("Erro Crítico: A variável GITHUB_TOKEN não foi encontrada nas configurações de ambiente.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"
ARQUIVO_HISTORICO = "historico_alteracoes_2026.csv"

# URL do seu vídeo hospedado diretamente no seu GitHub
URL_VIDEO_GITHUB = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/f1_bg.mp4"

# --- CSS CUSTOMIZADO COM VÍDEO EXPANDIDO E MAIS CLARO ---
st.markdown(f"""
<style>
    /* Estilização Geral F1 Dark */
    .stApp {{
        background-color: #0E0E10;
        color: #F3F4F6;
    }}
    
    /* Hero Container com Vídeo de Fundo Ajustado */
    .hero-container {{
        position: relative;
        width: 100%;
        height: 380px; /* Altura maior */
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 25px;
        border: 1px solid #252525;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        background: #151515;
    }}
    .hero-video {{
        position: absolute;
        top: 50%;
        left: 50%;
        min-width: 100%;
        min-height: 100%;
        width: auto;
        height: auto;
        z-index: 0;
        transform: translate(-50%, -50%);
        object-fit: cover;
        filter: brightness(0.85) contrast(1.05); /* Vídeo mais claro */
    }}
    .hero-overlay {{
        position: relative;
        z-index: 1;
        padding: 45px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        height: 100%;
        background: linear-gradient(180deg, rgba(14,14,16,0.1) 0%, rgba(14,14,16,0.85) 100%);
    }}
    .hero-title {{
        font-size: 3.2rem;
        font-weight: 900;
        letter-spacing: -1px;
        color: #FFFFFF;
        margin: 0;
        text-transform: uppercase;
        text-shadow: 0 4px 12px rgba(0,0,0,0.8);
    }}
    .hero-subtitle {{
        color: #E10600;
        font-size: 1.3rem;
        font-weight: 800;
        margin-top: 5px;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.8);
    }}
    
    /* Customização das Abas */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: #151515;
        padding: 8px;
        border-radius: 14px;
        border: 1px solid #252525;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 45px;
        border-radius: 10px;
        color: #9CA3AF;
        font-weight: 600;
        border: none;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #E10600 !important;
        color: #FFFFFF !important;
    }}
    
    /* Inputs e Botões */
    div[data-baseweb="select"] > div {{
        background-color: #151515 !important;
        border-color: #252525 !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
    }}
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease-in-out !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(225, 6, 0, 0.4);
    }}
</style>

<div class="hero-container">
    <video autoplay loop muted playsinline class="hero-video">
        <source src="{URL_VIDEO_GITHUB}" type="video/mp4">
    </video>
    <div class="hero-overlay">
        <h1 class="hero-title">BOLÃO F1 2026</h1>
        <div class="hero-subtitle">🏁 Campeonato Oficial de Palpites</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Dados e Estruturas Base
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
    "Equipe 2º Myke e César": ["Myke Ribeiro", "César Gaudie"],
    "Equipe 3º Luciano e Ronaldo": ["Luciano (Medalha)", "Ronaldo Fleury"],
    "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"],
    "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"],
    "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"],
    "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"],
    "Equipe 8º Delvânia Belo e Maikon": ["Delvânia Belo", "Maikon Miranda"],
    "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"],
    "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]
}

pilotos = [
    "", 
    "Max Verstappen", "Yuki Tsunoda", "Isack Hadjar",
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
    "Austrália", "China", "Japão", "Miami", "Canadá", "Mônaco", 
    "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", 
    "Holanda", "Itália", "Madrid", "Azerbaijão", 
    "Bahrein (Malásia / Sepang)", 
    "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# 3. Motor de Dados GitHub API
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

def registrar_historico(usuario, gp, tipo, acao):
    agora_br = datetime.now(fuso_br)
    log_entry = {
        "Data_Hora": agora_br.strftime('%d/%m/%Y %H:%M:%S'),
        "Usuario": usuario,
        "GP": gp,
        "Tipo": tipo,
        "Mensagem": f"O participante {usuario} {acao} seu palpite no GP de {gp} ({tipo}) às {agora_br.strftime('%H:%M:%S')} de {agora_br.strftime('%d/%m/%Y')}."
    }
    
    df_hist, sha_hist = ler_dados(ARQUIVO_HISTORICO)
    df_novo_hist = pd.DataFrame([log_entry])
    df_final_hist = pd.concat([df_hist, df_novo_hist], ignore_index=True) if not df_hist.empty else df_novo_hist
    
    conteudo_csv = df_final_hist.to_csv(index=False)
    conteudo_b64 = base64.b64encode(conteudo_csv.encode()).decode()
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{ARQUIVO_HISTORICO}"
    payload = {
        "message": f"Log de histórico: {usuario} - {gp}",
        "content": conteudo_b64,
        "sha": sha_hist if sha_hist else None
    }
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "BolaoF1-App"
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method='PUT')
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Erro ao salvar log de historico: {e}")

def guardar_dados(novos_dados, nome_arquivo, eh_edicao_admin=False):
    df_atual, sha = ler_dados(nome_arquivo)
    df_novo = pd.DataFrame([novos_dados])
    
    if not df_atual.empty:
        if "Usuario" in novos_dados:
            condicao_existente = (
                (df_atual['Usuario'] == novos_dados['Usuario']) & 
                (df_atual['GP'] == novos_dados['GP']) & 
                (df_atual['Tipo'] == novos_dados['Tipo'])
            )
            eh_alteracao = df_atual[condicao_existente].shape[0] > 0
            df_atual = df_atual[~condicao_existente]
        else:
            condicao_existente = (
                (df_atual['GP'] == novos_dados['GP']) & 
                (df_atual['Tipo'] == novos_dados['Tipo'])
            )
            eh_alteracao = False
            df_atual = df_atual[~condicao_existente]

        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo
        eh_alteracao = False

    conteudo_csv = df_final.to_csv(index=False)
    conteudo_b64 = base64.b64encode(conteudo_csv.encode()).decode()
    
    if "Usuario" in novos_dados:
        msg_log = f"Atualizado palpite: {novos_dados['Usuario']} - {novos_dados['GP']} ({novos_dados['Tipo']})"
        acao_log = "alterou (pelo Admin)" if eh_edicao_admin else ("alterou" if eh_alteracao else "enviou")
        registrar_historico(novos_dados['Usuario'], novos_dados['GP'], novos_dados['Tipo'], acao_log)
    else:
        msg_log = f"Atualizado Gabarito: {novos_dados.get('GP', 'Oficial')} ({novos_dados.get('Tipo', '')})"
    
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"
    payload = {
        "message": msg_log,
        "content": conteudo_b64,
        "sha": sha if sha else None
    }
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "BolaoF1-App"
    }
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
        with urllib.request.urlopen(req, timeout=15) as response:
            return True
    except Exception as e:
        st.error(f"Erro ao salvar dados no GitHub: {e}")
        return False

def deletar_registro_github(arquivo, mascara_filtro):
    df_atual, sha = ler_dados(arquivo)
    if not df_atual.empty:
        df_final = df_atual[mascara_filtro]
        csv_content = df_final.to_csv(index=False)
        encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {
            "message": f"Removendo registro: {arquivo}",
            "content": encoded_content,
            "sha": sha
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }, method="PUT")
        try:
            with urllib.request.urlopen(req) as response:
                return response.status in [200, 201]
        except:
            return False
    return False

def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    
    corpo = f"""
    Olá {dados['Usuario']},
    
    Seu palpite foi registrado/atualizado com sucesso no Bolão F1 2026!
    
    --- REGISTRO OFICIAL ---
    Grande Prêmio: {dados['GP']}
    Sessão: {dados['Tipo']}
    Data/Hora do Envio: {dados['Data_Envio']}
    
    --- DETALHES DO SEU PALPITE ---
    """
    if "Pole" in dados['Tipo']:
        corpo += f"Pole Position: {dados.get('Pole', '')}\n"
    elif "Corrida Principal" == dados['Tipo']:
        corpo += f"1º Colocado: {dados.get('P1', '')}\n2º Colocado: {dados.get('P2', '')}\n3º Colocado: {dados.get('P3', '')}\n"
        corpo += f"4º Colocado: {dados.get('P4', '')}\n5º Colocado: {dados.get('P5', '')}\n6º Colocado: {dados.get('P6', '')}\n"
        corpo += f"7º Colocado: {dados.get('P7', '')}\n8º Colocado: {dados.get('P8', '')}\n9º Colocado: {dados.get('P9', '')}\n10º Colocado: {dados.get('P10', '')}\n"
        corpo += f"\nMelhor Volta: {dados.get('VoltaRapida', '')}\n1º Abandono: {dados.get('PrimeiroAbandono', '')}\nMais Ultrapassagens: {dados.get('MaisUltrapassagens', '')}\n"
    elif "Corrida Sprint" == dados['Tipo']:
        corpo += f"1º Colocado: {dados.get('P1', '')}\n2º Colocado: {dados.get('P2', '')}\n3º Colocado: {dados.get('P3', '')}\n4º Colocado: {dados.get('P4', '')}\n"
        corpo += f"5º Colocado: {dados.get('P5', '')}\n6º Colocado: {dados.get('P6', '')}\n7º Colocado: {dados.get('P7', '')}\n8º Colocado: {dados.get('P8', '')}\n"
        
    corpo += "\n\nDireção de Prova — Bolão F1 2026"
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# 4. Cálculo da Pontuação
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
        pontos += check_ponto(palpite, gabarito, 'P1', 150)
        pontos += check_ponto(palpite, gabarito, 'P2', 125)
        pontos += check_ponto(palpite, gabarito, 'P3', 100)
        pontos += check_ponto(palpite, gabarito, 'P4', 85)
        pontos += check_ponto(palpite, gabarito, 'P5', 70)
        pontos += check_ponto(palpite, gabarito, 'P6', 60)
        pontos += check_ponto(palpite, gabarito, 'P7', 50)
        pontos += check_ponto(palpite, gabarito, 'P8', 40)
        pontos += check_ponto(palpite, gabarito, 'P9', 25)
        pontos += check_ponto(palpite, gabarito, 'P10', 15)
        pontos += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pontos += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pontos += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
        
        top10_p = [str(palpite.get(f'P{i}', '')).strip() for i in range(1, 11)]
        top10_g = [str(gabarito.get(f'P{i}', '')).strip() for i in range(1, 11)]
        if all(top10_p) and all(top10_g):
            if top10_p == top10_g: pontos += 600
            elif top10_p[:5] == top10_g[:5]: pontos += 450
            elif top10_p[:3] == top10_g[:3]: pontos += 300
    elif tipo == "Corrida Sprint":
        pontos += check_ponto(palpite, gabarito, 'P1', 80)
        pontos += check_ponto(palpite, gabarito, 'P2', 70)
        pontos += check_ponto(palpite, gabarito, 'P3', 60)
        pontos += check_ponto(palpite, gabarito, 'P4', 50)
        pontos += check_ponto(palpite, gabarito, 'P5', 40)
        pontos += check_ponto(palpite, gabarito, 'P6', 30)
        pontos += check_ponto(palpite, gabarito, 'P7', 20)
        pontos += check_ponto(palpite, gabarito, 'P8', 10)
        
    return pontos

def exibir_foto_piloto(nome):
    if nome and nome != "" and nome != "Nenhum / Outro":
        nome_arquivo = nome.replace(" ", "%20") + ".png"
        url_foto = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome_arquivo}"
        st.image(url_foto, width=80)

def index_piloto(val):
    val_str = str(val).strip() if pd.notna(val) else ""
    return pilotos.index(val_str) if val_str in pilotos else 0

# 5. Navegação Lateral
st.sidebar.markdown("## 🏎️ Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        
        st.markdown(f"### 🏎️ Piloto: **{usuario_logado}** | <span style='color:#E10600'>{equipe_usuario}</span>", unsafe_allow_html=True)

        col_gp, col_tipo = st.columns(2)
        with col_gp:
            df_gabaritos, _ = ler_dados(ARQUIVO_GABARITOS)
            gps_ja_realizados = df_gabaritos['GP'].unique().tolist() if not df_gabaritos.empty else []
            lista_gps_disponiveis = [gp for gp in lista_gps if gp not in gps_ja_realizados]
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps_disponiveis)

        with col_tipo:
            sessao_opcoes = ["Classificação Principal (Pole)", "Corrida Principal"]
            if gp_selecionado in sprint_gps:
                sessao_opcoes = ["Qualy Sprint (Pole)", "Corrida Sprint", "Classificação Principal (Pole)", "Corrida Principal"]
            tipo_sessao = st.selectbox("Selecione a Sessão:", sessao_opcoes)

        # Carrega palpite anterior se existir
        df_dados, _ = ler_dados(ARQUIVO_DADOS)
        palpite_existente = {}
        if not df_dados.empty:
            match = df_dados[
                (df_dados['Usuario'] == usuario_logado) & 
                (df_dados['GP'] == gp_selecionado) & 
                (df_dados['Tipo'] == tipo_sessao)
            ]
            if not match.empty:
                palpite_existente = match.iloc[-1].to_dict()
                st.info("ℹ️ **Você já enviou um palpite para esta sessão.** Os campos foram preenchidos com suas escolhas atuais. Altere o que quiser e grave novamente.")

        st.divider()
        st.header(f"🏁 {gp_selecionado} — {tipo_sessao}")

        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
        v_rapida = p_abandono = m_ultrapassagens = ""

        if "Pole" in tipo_sessao:
            pole = st.selectbox("Selecione o Pole Position:", pilotos, index=index_piloto(palpite_existente.get('Pole', '')), key="sel_pole")
            exibir_foto_piloto(pole)

        elif tipo_sessao == "Corrida Principal":
            c1, c2 = st.columns(2)
            with c1:
                p1 = st.selectbox("1º Colocado (Vencedor):", pilotos, index=index_piloto(palpite_existente.get('P1', '')), key="p1"); exibir_foto_piloto(p1)
                p2 = st.selectbox("2º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P2', '')), key="p2"); exibir_foto_piloto(p2)
                p3 = st.selectbox("3º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P3', '')), key="p3"); exibir_foto_piloto(p3)
                p4 = st.selectbox("4º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P4', '')), key="p4"); exibir_foto_piloto(p4)
                p5 = st.selectbox("5º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P5', '')), key="p5"); exibir_foto_piloto(p5)
            with c2:
                p6 = st.selectbox("6º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P6', '')), key="p6"); exibir_foto_piloto(p6)
                p7 = st.selectbox("7º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P7', '')), key="p7"); exibir_foto_piloto(p7)
                p8 = st.selectbox("8º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P8', '')), key="p8"); exibir_foto_piloto(p8)
                p9 = st.selectbox("9º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P9', '')), key="p9"); exibir_foto_piloto(p9)
                p10 = st.selectbox("10º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P10', '')), key="p10"); exibir_foto_piloto(p10)
            
            st.divider()
            mv_col, ab_col, mu_col = st.columns(3)
            with mv_col:
                v_rapida = st.selectbox("Melhor Volta:", pilotos, index=index_piloto(palpite_existente.get('VoltaRapida', '')), key="vr"); exibir_foto_piloto(v_rapida)
            with ab_col:
                p_abandono = st.selectbox("1º Abandono:", pilotos, index=index_piloto(palpite_existente.get('PrimeiroAbandono', '')), key="ab"); exibir_foto_piloto(p_abandono)
            with mu_col:
                m_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos, index=index_piloto(palpite_existente.get('MaisUltrapassagens', '')), key="mu"); exibir_foto_piloto(m_ultrapassagens)

        elif tipo_sessao == "Corrida Sprint":
            c1, c2 = st.columns(2)
            with c1:
                p1 = st.selectbox("1º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P1', '')), key="s1"); exibir_foto_piloto(p1)
                p2 = st.selectbox("2º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P2', '')), key="s2"); exibir_foto_piloto(p2)
                p3 = st.selectbox("3º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P3', '')), key="s3"); exibir_foto_piloto(p3)
                p4 = st.selectbox("4º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P4', '')), key="s4"); exibir_foto_piloto(p4)
            with c2:
                p5 = st.selectbox("5º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P5', '')), key="s5"); exibir_foto_piloto(p5)
                p6 = st.selectbox("6º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P6', '')), key="s6"); exibir_foto_piloto(p6)
                p7 = st.selectbox("7º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P7', '')), key="s7"); exibir_foto_piloto(p7)
                p8 = st.selectbox("8º Colocado:", pilotos, index=index_piloto(palpite_existente.get('P8', '')), key="s8"); exibir_foto_piloto(p8)

        with st.form("confirmar_palpite"):
            st.write("---")
            email_confirmacao = st.text_input("Confirme seu e-mail cadastrado para validar o envio:", type="password")
            
            if st.form_submit_button("GRAVAR MEU PALPITE FINAL 🏎️"):
                if email_confirmacao.lower() == emails_autorizados.get(usuario_logado, "").lower():
                    dados_palpite = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_selecionado,
                        "Tipo": tipo_sessao,
                        "Usuario": usuario_logado,
                        "Equipe": equipe_usuario,
                        "Pole": pole,
                        "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": v_rapida,
                        "PrimeiroAbandono": p_abandono,
                        "MaisUltrapassagens": m_ultrapassagens
                    }
                    if guardar_dados(dados_palpite, ARQUIVO_DADOS):
                        enviar_recibo_email(dados_palpite, email_confirmacao)
                        st.toast(f'Palpite Registrado com Sucesso! Acelera, {usuario_logado}! 🏎️💨', icon='🏁')
                        st.success(f"🏁 Maravilha, {usuario_logado}! Seu palpite para o GP de {gp_selecionado} foi gravado/atualizado.")
                    else:
                        st.error("Erro técnico ao conectar ao servidor. Tente novamente.")
                else:
                    st.error("E-mail não confere com o cadastrado para este participante.")

# --- ÁREA: MEUS PALPITES ---
elif menu == "Meus Palpites":
    st.header("🕵️ Meu Histórico de Palpites")
    usuario_consulta = st.selectbox("Selecione o seu nome:", [""] + participantes)
    
    if usuario_consulta:
        email_consulta = st.text_input("Digite o seu E-mail cadastrado para abrir o cofre:", type="password")
        if st.button("Buscar Meus Palpites 🔍"):
            if email_consulta.strip().lower() == emails_autorizados.get(usuario_consulta, "").strip().lower():
                df_todos, _ = ler_dados(ARQUIVO_DADOS)
                if not df_todos.empty:
                    meus_dados = df_todos[df_todos['Usuario'] == usuario_consulta]
                    if not meus_dados.empty:
                        st.success("Histórico localizado!")
                        meus_dados_ultimos = meus_dados.drop_duplicates(subset=['GP', 'Tipo'], keep='last')
                        st.dataframe(meus_dados_ultimos.drop(columns=['Usuario', 'Equipe']), use_container_width=True)
                    else:
                        st.warning("Nenhum palpite enviado ainda.")
                else:
                    st.info("Banco de dados vazio.")
            else:
                st.error("Acesso negado: E-mail incorreto.")

# --- ÁREA: CLASSIFICAÇÕES ---
elif menu == "Classificações":
    st.header("🏆 Classificação Geral do Campeonato")
    df_palpites, _ = ler_dados(ARQUIVO_DADOS)
    df_gabaritos, _ = ler_dados(ARQUIVO_GABARITOS)
    
    if not df_palpites.empty and not df_gabaritos.empty:
        df_palpites_validos = df_palpites.drop_duplicates(subset=['Usuario', 'GP', 'Tipo'], keep='last')
        resultados = []
        for _, row_p in df_palpites_validos.iterrows():
            gp = row_p.get('GP', '')
            tipo = row_p.get('Tipo', '')
            usuario = row_p['Usuario']
            equipe_atual = next((eq for eq, membros in equipes.items() if usuario in membros), "Sem Equipe")
            
            gabarito_match = df_gabaritos[(df_gabaritos['GP'] == gp) & (df_gabaritos['Tipo'] == tipo)]
            if not gabarito_match.empty:
                pontos = calcular_pontos_sessao(row_p, gabarito_match.iloc[-1])
                resultados.append({"Usuario": usuario, "Equipe": equipe_atual, "Pontos": pontos, "GP": gp})
        
        if resultados:
            df_res = pd.DataFrame(resultados)
            filtro_gp = st.selectbox("Visualizar Por GP:", ["Geral (Campeonato Completo)"] + lista_gps)
            if filtro_gp != "Geral (Campeonato Completo)":
                df_res = df_res[df_res["GP"] == filtro_gp]
            
            if not df_res.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 👤 Mundial de Pilotos")
                    rk_pilotos = df_res.groupby('Usuario')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                    rk_pilotos.index = range(1, len(rk_pilotos) + 1)
                    st.dataframe(rk_pilotos, use_container_width=True)
                with col2:
                    st.markdown("### 🏎️ Mundial de Construtores")
                    rk_equipes = df_res.groupby('Equipe')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                    rk_equipes.index = range(1, len(rk_equipes) + 1)
                    st.dataframe(rk_equipes, use_container_width=True)

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha do Diretor de Prova:", type="password")
    
    if senha == "fleury1475":
        st.warning("⚠ PAINEL DE CONTROLE ADMINISTRATIVO — ACESSO RESTRITO")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🛡️ Auditoria & Edição", 
            "📜 Log Auditável",
            "🚩 Gabarito & Pontuação", 
            "📋 Gabaritos Salvos", 
            "🗑️ Limpeza de Dados"
        ])
        
        # TAB 1: AUDITORIA E EDIÇÃO
        with tab1:
            st.subheader("🛡️ Gerenciador Direto de Palpites")
            df_aud, _ = ler_dados(ARQUIVO_DADOS)
            if not df_aud.empty:
                df_aud_limpo = df_aud.drop_duplicates(subset=['Usuario', 'GP', 'Tipo'], keep='last')
                flt_gp_aud = st.selectbox("Filtrar Auditoria por GP:", ["Todos os GPs"] + lista_gps)
                df_view_aud = df_aud_limpo if flt_gp_aud == "Todos os GPs" else df_aud_limpo[df_aud_limpo["GP"] == flt_gp_aud]
                st.dataframe(df_view_aud, use_container_width=True)
                
                st.divider()
                st.subheader("🛠️ Editar Palpite de Participante")
                c_usr, c_gp, c_ses = st.columns(3)
                with c_usr: u_edit = st.selectbox("Participante:", [""] + participantes, key="adm_u")
                with c_gp: g_edit = st.selectbox("GP:", lista_gps, key="adm_g")
                with c_ses:
                    opts_s = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if g_edit in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
                    s_edit = st.selectbox("Sessão:", opts_s, key="adm_s")
                
                if u_edit != "":
                    match_e = df_aud_limpo[(df_aud_limpo['Usuario'] == u_edit) & (df_aud_limpo['GP'] == g_edit) & (df_aud_limpo['Tipo'] == s_edit)]
                    p_exist = match_e.iloc[-1].to_dict() if not match_e.empty else {}
                    eq_u = next((eq for eq, me in equipes.items() if u_edit in me), "Sem Equipe")
                    
                    with st.form("f_adm_edit"):
                        st.markdown(f"**Modificando:** {u_edit} | {g_edit} ({s_edit})")
                        pole_e = p1_e = p2_e = p3_e = p4_e = p5_e = p6_e = p7_e = p8_e = p9_e = p10_e = ""
                        vr_e = ab_e = mu_e = ""
                        
                        if "Pole" in s_edit:
                            pole_e = st.selectbox("Pole Position:", pilotos, index=index_piloto(p_exist.get('Pole', '')))
                        elif s_edit == "Corrida Principal":
                            col1_e, col2_e = st.columns(2)
                            with col1_e:
                                p1_e = st.selectbox("1º Colocado:", pilotos, index=index_piloto(p_exist.get('P1', '')))
                                p2_e = st.selectbox("2º Colocado:", pilotos, index=index_piloto(p_exist.get('P2', '')))
                                p3_e = st.selectbox("3º Colocado:", pilotos, index=index_piloto(p_exist.get('P3', '')))
                                p4_e = st.selectbox("4º Colocado:", pilotos, index=index_piloto(p_exist.get('P4', '')))
                                p5_e = st.selectbox("5º Colocado:", pilotos, index=index_piloto(p_exist.get('P5', '')))
                            with col2_e:
                                p6_e = st.selectbox("6º Colocado:", pilotos, index=index_piloto(p_exist.get('P6', '')))
                                p7_e = st.selectbox("7º Colocado:", pilotos, index=index_piloto(p_exist.get('P7', '')))
                                p8_e = st.selectbox("8º Colocado:", pilotos, index=index_piloto(p_exist.get('P8', '')))
                                p9_e = st.selectbox("9º Colocado:", pilotos, index=index_piloto(p_exist.get('P9', '')))
                                p10_e = st.selectbox("10º Colocado:", pilotos, index=index_piloto(p_exist.get('P10', '')))
                            c3_e, c4_e, c5_e = st.columns(3)
                            with c3_e: vr_e = st.selectbox("Melhor Volta:", pilotos, index=index_piloto(p_exist.get('VoltaRapida', '')))
                            with c4_e: ab_e = st.selectbox("1º Abandono:", pilotos, index=index_piloto(p_exist.get('PrimeiroAbandono', '')))
                            with c5_e: mu_e = st.selectbox("Mais Ultrapassagens:", pilotos, index=index_piloto(p_exist.get('MaisUltrapassagens', '')))
                        
                        if st.form_submit_button("Salvar Alteração do Admin 🛠️"):
                            dados_e = {
                                "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S') + " (Admin)",
                                "GP": g_edit, "Tipo": s_edit, "Usuario": u_edit, "Equipe": eq_u,
                                "Pole": pole_e, "P1": p1_e, "P2": p2_e, "P
