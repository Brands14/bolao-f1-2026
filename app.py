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

# Configurações do GitHub
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

# --- NOVA FUNÇÃO: EXIBIR FOTO DO PILOTO ---
def exibir_foto_piloto(nome_piloto):
    """Exibe a foto do piloto buscada diretamente do repositório GitHub."""
    if nome_piloto and nome_piloto not in ["", "Nenhum / Outro"]:
        # Ajuste a extensão (.png ou .jpg) conforme seus arquivos
        url_foto = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome_piloto}.png"
        
        # Tenta exibir a imagem. Se não encontrar, mostra um ícone padrão.
        try:
            st.image(url_foto, width=120)
        except:
            st.caption("📸 Foto indisponível")

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
    "Alaerte Fleury": "alaertefleury@hotmail.com", "César Gaudie": "c3sargaudie@gmail.com",
    "Delvânia Belo": "del.gomes04@gmail.com", "Emilio Jacinto": "emiliopaja@gmail.com",
    "Fabrício Abe": "fabricio.fleury84@gmail.com", "Fausto Fleury": "faustofleury.perito@gmail.com",
    "Fernanda Fleury": "fefleury17@gmail.com", "Flávio Soares": "flaviosoaresparente@gmail.com",
    "Frederico Gaudie": "fredericofleury@gmail.com", "George Fleury": "gfleury@gmail.com",
    "Henrique Junqueira": "amtelegas@gmail.com", "Hilton Jacinto": "hiltonlpj2@hotmail.com",
    "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com", "Luciano (Medalha)": "luciano.pallada@terra.com.br",
    "Maikon Miranda": "maikonmiranda@gmail.com", "Myke Ribeiro": "mribeiro3088@gmail.com",
    "Rodolfo Brandão": "rodolfo.fleury@gmail.com", "Ronaldo Fleury": "ronaldofleury18@gmail.com",
    "Syllas Araújo": "sylaopoim@gmail.com", "Valério Bimbato": "bimbatovalerio2@gmail.com"
}

pilotos = [
    "", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc",
    "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri",
    "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg",
    "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto",
    "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad",
    "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"
]

lista_gps = [
    "Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", 
    "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", 
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", 
    "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# 2. Funções de Banco de Dados (GitHub API)
def ler_dados(arquivo):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            return pd.read_csv(io.StringIO(content)), data['sha']
    except:
        return pd.DataFrame(), None

def salvar_dados_github(arquivo, df):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    _, sha = ler_dados(arquivo)
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode()).decode()
    payload = {"message": f"Update {arquivo}", "content": encoded_content}
    if sha: payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method='PUT')
    try:
        with urllib.request.urlopen(req) as response: return True
    except: return False

# 3. Interface Principal
menu = st.sidebar.selectbox("Menu", ["Palpites", "Resultados e Classificação", "Gabarito (Admin)"])

if menu == "Palpites":
    st.header("🏁 Registre seu Palpite")
    
    col_u, col_g, col_s = st.columns(3)
    with col_u: user = st.selectbox("Selecione seu Nome:", [""] + participantes)
    with col_g: gp = st.selectbox("Grande Prêmio:", lista_gps)
    
    opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal"]
    if gp in sprint_gps:
        opcoes_sessao += ["Qualy Sprint (Pole)", "Corrida Sprint"]
    with col_s: sessao = st.selectbox("Sessão:", opcoes_sessao)

    st.divider()
    
    col_p, col_v = st.columns(2)
    with col_p:
        pole = st.selectbox("Quem será o Pole Position?", pilotos)
        exibir_foto_piloto(pole) # FOTO DO POLE
        
    with col_v:
        vencedor = st.selectbox("Quem vencerá a corrida?", pilotos)
        exibir_foto_piloto(vencedor) # FOTO DO VENCEDOR

    if st.button("Enviar Palpite"):
        if user == "" or pole == "" or vencedor == "":
            st.warning("Preencha todos os campos!")
        else:
            df, _ = ler_dados(ARQUIVO_DADOS)
            novo_palpite = pd.DataFrame([{
                "Data": datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M"),
                "Usuario": user, "GP": gp, "Tipo": sessao, "Pole": pole, "Vencedor": vencedor
            }])
            df = pd.concat([df, novo_palpite], ignore_index=True)
            if salvar_dados_github(ARQUIVO_DADOS, df):
                st.success(f"Palpite de {user} enviado com sucesso!")

elif menu == "Gabarito (Admin)":
    st.header("🏆 Atualizar Gabarito Oficial")
    senha = st.text_input("Senha de Admin:", type="password")
    
    if senha == "f12026":
        tab1, tab2 = st.tabs(["Lançar Gabarito", "Gerenciar Registros"])
        
        with tab1:
            col_g2, col_s2 = st.columns(2)
            with col_g2: gp_gab = st.selectbox("GP do Gabarito:", lista_gps, key="gp_gab")
            with col_s2: sessao_gab = st.selectbox("Sessão do Gabarito:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key="sessao_gab")
            
            col_p2, col_v2 = st.columns(2)
            with col_p2:
                pole_gab = st.selectbox("Pole Oficial:", pilotos, key="p_gab")
                exibir_foto_piloto(pole_gab)
            with col_v2:
                venc_gab = st.selectbox("Vencedor Oficial:", pilotos, key="v_gab")
                exibir_foto_piloto(venc_gab)
                
            if st.button("Salvar Gabarito"):
                df_g, _ = ler_dados(ARQUIVO_GABARITOS)
                novo_g = pd.DataFrame([{"GP": gp_gab, "Tipo": sessao_gab, "Pole": pole_gab, "Vencedor": venc_gab}])
                df_g = pd.concat([df_g, novo_g], ignore_index=True)
                if salvar_dados_github(ARQUIVO_GABARITOS, df_g):
                    st.success("Gabarito salvo!")
        
        with tab2:
            st.subheader("🗑️ Limpeza de Dados")
            if st.button("Apagar todos os Palpites"):
                if salvar_dados_github(ARQUIVO_DADOS, pd.DataFrame(columns=["Data","Usuario","GP","Tipo","Pole","Vencedor"])):
                    st.success("Tabela de palpites resetada!")

elif menu == "Resultados e Classificação":
    st.header("📊 Classificação e Resultados")
    
    df_p, _ = ler_dados(ARQUIVO_DADOS)
    df_g, _ = ler_dados(ARQUIVO_GABARITOS)
    
    if df_g.empty:
        st.info("Nenhum resultado oficial lançado ainda.")
    else:
        # Cálculo de Pontos Simples
        def calcular_pontos(row, gab):
            pts = 0
            if row['Pole'] == gab['Pole']: pts += 5
            if row['Vencedor'] == gab['Vencedor']: pts += 10
            return pts

        # Lógica de Classificação
        pontuacao = {p: 0 for p in participantes}
        for _, gab in df_g.iterrows():
            sessao_p = df_p[(df_p['GP'] == gab['GP']) & (df_p['Tipo'] == gab['Tipo'])]
            for _, palpite in sessao_p.iterrows():
                if palpite['Usuario'] in pontuacao:
                    pontuacao[palpite['Usuario']] += calcular_pontos(palpite, gab)
        
        classificacao = pd.DataFrame(list(pontuacao.items()), columns=['Participante', 'Pontos']).sort_values(by='Pontos', ascending=False)
        st.table(classificacao)
        
        st.divider()
        st.subheader("🔍 Conferir por GP")
        gp_ver = st.selectbox("Selecione o GP para ver as fotos dos vencedores:", lista_gps, key="ver_gp")
        
        res_gp = df_g[df_g['GP'] == gp_ver]
        if not res_gp.empty:
            for _, r in res_gp.iterrows():
                st.write(f"**Sessão: {r['Tipo']}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"Pole: {r['Pole']}")
                    exibir_foto_piloto(r['Pole'])
                with c2:
                    st.write(f"Vencedor: {r['Vencedor']}")
                    exibir_foto_piloto(r['Vencedor'])
