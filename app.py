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

# 🚨 CONFIGURAÇÕES DO GITHUB
GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Ajuste no link RAW para garantir acesso à pasta /fotos/ na branch main
URL_BASE_FOTOS = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/"

# Puxa as chaves mestras do painel do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas nas configurações do Streamlit.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO DE EXIBIÇÃO DE FOTOS ---
def exibir_foto_piloto(nome):
    if nome and nome != "" and nome != "Nenhum / Outro":
        # Formata o nome exatamente como o arquivo (ex: Max Verstappen.png)
        # O .replace(" ", "%20") é vital para links web
        nome_arquivo = nome.replace(" ", "%20") + ".png"
        url_foto = URL_BASE_FOTOS + nome_arquivo
        
        # Tentamos exibir. Se o link estiver quebrado, ele não trava o app.
        st.image(url_foto, width=90)

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

# DICIONÁRIO DE SEGURANÇA
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

def deletar_registro_github(arquivo, mascara_filtro):
    df_atual, sha = ler_dados(arquivo)
    if not df_atual.empty:
        df_final = df_atual[mascara_filtro]
        csv_content = df_final.to_csv(index=False)
        encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {
            "message": f"Removendo registro no banco: {arquivo}",
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

# 3. Disparador de E-mails (Mantido original)
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
        
    corpo += "\n\nEste é um e-mail automático. Em caso de dúvidas, procure a Direção de Prova (Fabrício ou Rodolfo)."
    
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

# 4. Matemática das Sessões (Mantido original)
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

# 5. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
            
        if gp_selecionado in sprint_gps:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"]
        else:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal"]
            
        with col_tipo:
            tipo_sessao = st.selectbox("Tipo de Sessão (Selecione a fase atual):", opcoes_sessao)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        
        with st.form("form_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            volta_rapida = primeiro_abandono = mais_ultrapassagens = ""
            
            if "Pole" in tipo_sessao:
                st.info("📌 Palpite apenas para a Pole Position desta sessão.")
                pole = st.selectbox("Pole Position:", pilotos)
                exibir_foto_piloto(pole)
                
            elif tipo_sessao == "Corrida Principal":
                st.info("📌 Palpite para a Corrida de Domingo.")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos); exibir_foto_piloto(p1)
                    p2 = st.selectbox("2º Colocado:", pilotos); exibir_foto_piloto(p2)
                    p3 = st.selectbox("3º Colocado:", pilotos); exibir_foto_piloto(p3)
                    p4 = st.selectbox("4º Colocado:", pilotos); exibir_foto_piloto(p4)
                    p5 = st.selectbox("5º Colocado:", pilotos); exibir_foto_piloto(p5)
                with col2:
                    p6 = st.selectbox("6º Colocado:", pilotos); exibir_foto_piloto(p6)
                    p7 = st.selectbox("7º Colocado:", pilotos); exibir_foto_piloto(p7)
                    p8 = st.selectbox("8º Colocado:", pilotos); exibir_foto_piloto(p8)
                    p9 = st.selectbox("9º Colocado:", pilotos); exibir_foto_piloto(p9)
                    p10 = st.selectbox("10º Colocado:", pilotos); exibir_foto_piloto(p10)
                    volta_rapida = st.selectbox("Melhor Volta:", pilotos); exibir_foto_piloto(volta_rapida)
                    primeiro_abandono = st.selectbox("1º Abandono:", pilotos); exibir_foto_piloto(primeiro_abandono)
                    mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos); exibir_foto_piloto(mais_ultrapassagens)
                    
            elif tipo_sessao == "Corrida Sprint":
                st.info("📌 Palpite para a Corrida Sprint (Top 8).")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos); exibir_foto_piloto(p1)
                    p2 = st.selectbox("2º Colocado:", pilotos); exibir_foto_piloto(p2)
                    p3 = st.selectbox("3º Colocado:", pilotos); exibir_foto_piloto(p3)
                    p4 = st.selectbox("4º Colocado:", pilotos); exibir_foto_piloto(p4)
                with col2:
                    p5 = st.selectbox("5º Colocado:", pilotos); exibir_foto_piloto(p5)
                    p6 = st.selectbox("6º Colocado:", pilotos); exibir_foto_piloto(p6)
                    p7 = st.selectbox("7º Colocado:", pilotos); exibir_foto_piloto(p7)
                    p8 = st.selectbox("8º Colocado:", pilotos); exibir_foto_piloto(p8)

            st.divider()
            st.markdown("🔒 **Assinatura de Segurança**")
            email_confirmacao = st.text_input("Digite o seu E-mail cadastrado para validar o palpite:", type="password")
            
            enviado = st.form_submit_button(f"Salvar Palpite - {tipo_sessao} 🏁")
            
            if enviado:
                email_correto = emails_autorizados.get(usuario_logado, "").strip().lower()
                email_digitado = email_confirmacao.strip().lower()
                
                if email_digitado == email_correto and email_correto != "":
                    st.info("Gravando permanentemente no cofre do GitHub e gerando recibos... Aguarde!")
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                    }
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        email_enviado = enviar_recibo_email(dados, email_correto)
                        if email_enviado:
                            st.success(f"Palpite de {tipo_sessao} salvo! Recibo enviado para o seu e-mail.")
                        else:
                            st.warning(f"Palpite salvo no banco com sucesso, mas houve uma falha ao enviar o recibo por e-mail.")
                    else:
                        st.error("Falha ao salvar no banco permanente. Fale com a Direção de Prova.")
                else:
                    st.error("🚫 Acesso Negado: E-mail incorreto.")

    else:
        st.info("Selecione o seu nome no menu lateral para começar.")

# --- ABAS MEUS PALPITES, CLASSIFICAÇÕES E ADMINISTRADOR (MANTIDAS 100% IGUAIS) ---
elif menu == "Meus Palpites":
    usuario_logado = st.sidebar.selectbox("Ver palpites de quem?", [""] + participantes)
    if usuario_logado:
        st.header(f"📋 Histórico de: {usuario_logado}")
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty:
            meus_votos = df[df['Usuario'] == usuario_logado].sort_values(by="GP")
            if not meus_votos.empty:
                st.dataframe(meus_votos)
            else:
                st.info("Você ainda não enviou nenhum palpite.")
        else:
            st.info("O banco de dados está vazio.")

elif menu == "Classificações":
    st.header("🏆 Classificação Geral")
    df_palpites, _ = ler_dados(ARQUIVO_DADOS)
    df_gabaritos, _ = ler_dados(ARQUIVO_GABARITOS)
    
    if not df_palpites.empty and not df_gabaritos.empty:
        pontuacoes = []
        for index, palpite in df_palpites.iterrows():
            gabarito = df_gabaritos[(df_gabaritos['GP'] == palpite['GP']) & (df_gabaritos['Tipo'] == palpite['Tipo'])]
            if not gabarito.empty:
                pts = calcular_pontos_sessao(palpite, gabarito.iloc[0])
                pontuacoes.append({"Usuario": palpite['Usuario'], "Equipe": palpite['Equipe'], "Pontos": pts})
        
        if pontuacoes:
            ranking = pd.DataFrame(pontuacoes).groupby(['Usuario', 'Equipe']).sum().sort_values(by=\"Pontos\", ascending=False).reset_index()
            st.table(ranking)
            
            st.header("👥 Classificação por Equipes")
            ranking_equipes = ranking.groupby('Equipe').sum().sort_values(by=\"Pontos\", ascending=False).reset_index()
            st.table(ranking_equipes)
        else:
            st.info("Aguardando resultados oficiais para calcular a pontuação.")
    else:
        st.info("Os resultados ainda não foram lançados pela Direção de Prova.")

elif menu == "Administrador":
    st.header("🔐 Painel do Comissário")
    senha_adm = st.text_input("Senha de Acesso:", type="password")
    
    if senha_adm == "f12026":
        st.success("Acesso Liberado!")
        
        aba_adm1, aba_adm2 = st.tabs(["Lançar Gabarito (Resultados)", "Limpeza de Dados"])
        
        with aba_adm1:
            st.subheader("🏁 Lançar Resultado Oficial")
            gp_res = st.selectbox("GP do Resultado:", lista_gps, key="gp_res")
            tipo_res = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key="tipo_res")
            
            with st.form("form_gabarito"):
                g_pole = g_p1 = g_p2 = g_p3 = g_p4 = g_p5 = g_p6 = g_p7 = g_p8 = g_p9 = g_p10 = ""
                g_mv = g_ab = g_mu = ""
                
                if "Pole" in tipo_res:
                    g_pole = st.selectbox("Pole Position Oficial:", pilotos)
                elif tipo_res == "Corrida Principal":
                    col1, col2 = st.columns(2)
                    with col1:
                        g_p1 = st.selectbox("1º", pilotos); g_p2 = st.selectbox("2º", pilotos); g_p3 = st.selectbox("3º", pilotos); g_p4 = st.selectbox("4º", pilotos); g_p5 = st.selectbox("5º", pilotos)
                    with col2:
                        g_p6 = st.selectbox("6º", pilotos); g_p7 = st.selectbox("7º", pilotos); g_p8 = st.selectbox("8º", pilotos); g_p9 = st.selectbox("9º", pilotos); g_p10 = st.selectbox("10º", pilotos)
                        g_mv = st.selectbox("Melhor Volta:", pilotos); g_ab = st.selectbox("1º Abandono:", pilotos); g_mu = st.selectbox("Mais Ultrapassagens:", pilotos)
                elif tipo_res == "Corrida Sprint":
                    col1, col2 = st.columns(2)
                    with col1:
                        g_p1 = st.selectbox("1º", pilotos); g_p2 = st.selectbox("2º", pilotos); g_p3 = st.selectbox("3º", pilotos); g_p4 = st.selectbox("4º", pilotos)
                    with col2:
                        g_p5 = st.selectbox("5º", pilotos); g_p6 = st.selectbox("6º", pilotos); g_p7 = st.selectbox("7º", pilotos); g_p8 = st.selectbox("8º", pilotos)
                
                if st.form_submit_button("SALVAR RESULTADO OFICIAL"):
                    gabarito_dados = {
                        "GP": gp_res, "Tipo": tipo_res, "Pole": g_pole, "P1": g_p1, "P2": g_p2, "P3": g_p3, "P4": g_p4, "P5": g_p5,
                        "P6": g_p6, "P7": g_p7, "P8": g_p8, "P9": g_p9, "P10": g_p10, "VoltaRapida": g_mv, "PrimeiroAbandono": g_ab, "MaisUltrapassagens": g_mu
                    }
                    if guardar_dados(gabarito_dados, ARQUIVO_GABARITOS):
                        st.success("Resultado oficial gravado!")
                    else:
                        st.error("Erro ao gravar gabarito.")
        
        with aba_adm2:
            st.header("🗑️ Apagar Registros")
            df_limpeza, _ = ler_dados(ARQUIVO_DADOS)
            if not df_limpeza.empty:
                col_del_gp, col_del_sessao = st.columns(2)
                with col_del_gp: gp_del = st.selectbox("GP para excluir:", lista_gps, key=\"del_gp\")
                with col_del_sessao: sessao_del = st.selectbox("Sessão para excluir:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key=\"del_sessao\")
                
                palpites_filtrados = df_limpeza[(df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del)]
                
                if not palpites_filtrados.empty:
                    user_del = st.selectbox("Selecione o usuário para APAGAR o palpite:", [""] + sorted(palpites_filtrados['Usuario'].tolist()), key=\"del_user\")
                    if user_del != "":
                        if st.button(f"CONFIRMAR EXCLUSÃO DE {user_del}", type=\"primary\"):
                            mascara = ~((df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del) & (df_limpeza['Usuario'] == user_del))
                            if deletar_registro_github(ARQUIVO_DADOS, mascara):
                                st.success("Palpite removido com sucesso!")
                                st.rerun()
