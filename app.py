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
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas nas configurações do Streamlit.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- ALTERAÇÃO NO ESQUEMA DE IMAGEM (LOGO) ---
# Tenta carregar a imagem. Se falhar, usa um título reserva para não sumir com as opções.
try:
    # Substitua a URL abaixo pelo link real da sua imagem se ela estiver no GitHub ou Imgur
    logo_url = "https://raw.githubusercontent.com/Brands14/bolao-f1-2026/main/logo_f1.png" 
    st.image(logo_url, use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

# --- DADOS DO CAMPEONATO ---
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

pilotos = [
    "", 
    "Max Verstappen", "Isack Hadjar",
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
    "Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", 
    "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", 
    "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", 
    "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"
]

sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# 2. Motor de Banco de Dados Permanente (GitHub API)
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

def guardar_dados(dados, arquivo):
    df_atual, sha = ler_dados(arquivo)
    df_novo = pd.DataFrame([dados])

    if not df_atual.empty:
        if 'Usuario' in dados:
            mascara = ~((df_atual['GP'] == dados['GP']) & 
                        (df_atual['Tipo'] == dados['Tipo']) & 
                        (df_atual['Usuario'] == dados['Usuario']))
        else:
            mascara = ~((df_atual['GP'] == dados['GP']) & 
                        (df_atual['Tipo'] == dados['Tipo']))
            
        df_atual = df_atual[mascara]
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    csv_content = df_final.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    payload = {
        "message": f"Atualizando registro no banco: {arquivo}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json"
    }, method="PUT")

    try:
        with urllib.request.urlopen(req) as response:
            return response.status in [200, 201]
    except urllib.error.HTTPError as e:
        st.error(f"Erro na nuvem: {e}")
        return False

# 3. Disparador de E-mails
def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    
    corpo = f"""
    Olá {dados['Usuario']},
    
    Seu palpite foi registrado com sucesso pelo VAR do nosso sistema!
    Abaixo está a cópia oficial do seu envio.
    
    --- DETALHES DO REGISTRO ---
    Grande Prêmio: {dados['GP']}
    Sessão: {dados['Tipo']}
    Data e Hora Exata do Envio: {dados['Data_Envio']}
    
    --- SEU PALPITE ---
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
        
    corpo += "\n\nEste é um e-mail automático. Em caso de dúvidas, procure a Direção de Prova."
    
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except:
        return False

# 4. Matemática das Sessões
def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    if val_p and val_p == val_g:
        return valor_pontos
    return 0

def calcular_pontos_sessao(palpite, gabarito):
    pontos = 0
    tipo = palpite.get('Tipo', '')
    if "Classificação" in tipo or "Qualy Sprint" in tipo:
        pontos += check_ponto(palpite, gabarito, 'Pole', 100)
    elif tipo == "Corrida Principal":
        for i in range(1, 11):
            pts = [150, 125, 100, 85, 70, 60, 50, 40, 25, 15]
            pontos += check_ponto(palpite, gabarito, f'P{i}', pts[i-1])
        pontos += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pontos += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pontos += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
    elif tipo == "Corrida Sprint":
        for i in range(1, 9):
            pts = [80, 70, 60, 50, 40, 30, 20, 10]
            pontos += check_ponto(palpite, gabarito, f'P{i}', pts[i-1])
    return pontos

# 5. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    if usuario_logado:
        equipe_usuario = next((eq for eq, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        col_gp, col_tipo = st.columns(2)
        with col_gp: gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
        opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_selecionado in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
        with col_tipo: tipo_sessao = st.selectbox("Tipo de Sessão:", opcoes_sessao)
        
        with st.form("form_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            vr = pa = mu = ""
            if "Pole" in tipo_sessao:
                pole = st.selectbox("Pole Position:", pilotos)
            elif tipo_sessao == "Corrida Principal":
                c1, c2 = st.columns(2)
                with c1: p1, p2, p3, p4, p5 = [st.selectbox(f"{i}º Colocado:", pilotos, key=f"p{i}") for i in range(1, 6)]
                with c2: p6, p7, p8, p9, p10 = [st.selectbox(f"{i}º Colocado:", pilotos, key=f"p{i}") for i in range(6, 11)]
                vr = st.selectbox("Melhor Volta:", pilotos)
                pa = st.selectbox("1º Abandono:", pilotos)
                mu = st.selectbox("Mais Ultrapassagens:", pilotos)
            elif tipo_sessao == "Corrida Sprint":
                c1, c2 = st.columns(2)
                with c1: p1, p2, p3, p4 = [st.selectbox(f"{i}º Colocado:", pilotos, key=f"s{i}") for i in range(1, 5)]
                with c2: p5, p6, p7, p8 = [st.selectbox(f"{i}º Colocado:", pilotos, key=f"s{i}") for i in range(5, 9)]
            
            email_confirmacao = st.text_input("E-mail para validar:", type="password")
            if st.form_submit_button("Salvar Palpite 🏁"):
                if email_confirmacao.strip().lower() == emails_autorizados.get(usuario_logado, "").lower():
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": vr, "PrimeiroAbandono": pa, "MaisUltrapassagens": mu}
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        enviar_recibo_email(dados, email_confirmacao)
                        st.success("Palpite registrado!")
                    else: st.error("Erro ao salvar.")
                else: st.error("E-mail incorreto.")
    else: st.info("Selecione seu nome na lateral.")

elif menu == "Meus Palpites":
    st.header("🕵️ Meus Palpites")
    usuario_consulta = st.selectbox("Nome:", [""] + participantes)
    email_consulta = st.text_input("E-mail:", type="password")
    if st.button("Buscar"):
        if email_consulta.strip().lower() == emails_autorizados.get(usuario_consulta, "").lower():
            df, _ = ler_dados(ARQUIVO_DADOS)
            if not df.empty:
                st.dataframe(df[df['Usuario'] == usuario_consulta])
        else: st.error("Acesso negado.")

elif menu == "Classificações":
    st.header("🏆 Classificações")
    df_p, _ = ler_dados(ARQUIVO_DADOS)
    df_g, _ = ler_dados(ARQUIVO_GABARITOS)
    if not df_p.empty and not df_g.empty:
        # Lógica de cálculo simplificada para exibição
        st.write("Resultados processados...")
        st.dataframe(df_p) # Exemplo básico
    else: st.info("Aguardando gabaritos oficiais.")

elif menu == "Administrador":
    st.header("🛠️ Área do Admin")
    senha_adm = st.text_input("Senha de Admin:", type="password")
    if senha_adm == "f12026":
        st.write("Bem-vindo, Chefe de Equipe.")
        # Adicionar aqui funções de inserção de gabarito se desejar
