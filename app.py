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

# Puxa as chaves mestras
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

# --- FUNÇÃO DE EXIBIÇÃO DE FOTOS ---
def exibir_foto_piloto(nome):
    if nome and nome != "" and nome != "Nenhum / Outro":
        nome_arquivo = nome.replace(" ", "%20") + ".png"
        url_foto = URL_BASE_FOTOS + nome_arquivo
        st.image(url_foto, width=85)

# Tenta carregar o logo
try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.png", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

# --- LISTAS E DICIONÁRIOS (EXATAMENTE DO TXT) ---
participantes = ["Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"]
emails_autorizados = {"Alaerte Fleury": "alaertefleury@hotmail.com", "César Gaudie": "c3sargaudie@gmail.com", "Delvânia Belo": "del.gomes04@gmail.com", "Emilio Jacinto": "emiliopaja@gmail.com", "Fabrício Abe": "fabricio.fleury84@gmail.com", "Fausto Fleury": "faustofleury.perito@gmail.com", "Fernanda Fleury": "fefleury17@gmail.com", "Flávio Soares": "flaviosoaresparente@gmail.com", "Frederico Gaudie": "fredericofleury@gmail.com", "George Fleury": "gfleury@gmail.com", "Henrique Junqueira": "amtelegas@gmail.com", "Hilton Jacinto": "hiltonlpj2@hotmail.com", "Jaime Gabriel": "jaimesofiltrosgyn@gmail.com", "Luciano (Medalha)": "luciano.pallada@terra.com.br", "Maikon Miranda": "maikonmiranda@gmail.com", "Myke Ribeiro": "mribeiro3088@gmail.com", "Rodolfo Brandão": "rodolfo.fleury@gmail.com", "Ronaldo Fleury": "ronaldofleury18@gmail.com", "Syllas Araújo": "sylaopoim@gmail.com", "Valério Bimbato": "bimbatovalerio2@gmail.com"}
equipes = {"Equipe 1º Fabrício e Fausto": ["Fabrício Abe", "Fausto Fleury"], "Equipe 2º Myke e Luciano": ["Myke Ribeiro", "Luciano (Medalha)"], "Equipe 3º César e Ronaldo": ["César Gaudie", "Ronaldo Fleury"], "Equipe 4º Valério e Syllas": ["Valério Bimbato", "Syllas Araújo"], "Equipe 5º Frederico e Emilio": ["Frederico Gaudie", "Emilio Jacinto"], "Equipe 6º Fernanda e Henrique": ["Fernanda Fleury", "Henrique Junqueira"], "Equipe 7º Jaime e Hilton": ["Jaime Gabriel", "Hilton Jacinto"], "Equipe 8º Delvânia e Maikon": ["Delvânia Belo", "Maikon Miranda"], "Equipe 9º Alaerte e Flávio": ["Alaerte Fleury", "Flávio Soares"], "Equipe 10º Rodolfo e George": ["Rodolfo Brandão", "George Fleury"]}
pilotos = ["", "Max Verstappen", "Isack Hadjar", "Lewis Hamilton", "Charles Leclerc", "George Russell", "Kimi Antonelli", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Lance Stroll", "Gabriel Bortoleto", "Nico Hülkenberg", "Alex Albon", "Carlos Sainz", "Pierre Gasly", "Franco Colapinto", "Oliver Bearman", "Esteban Ocon", "Liam Lawson", "Arvid Lindblad", "Sergio Pérez", "Valtteri Bottas", "Nenhum / Outro"]
lista_gps = ["Austrália", "China", "Japão", "Bahrein", "Arábia Saudita", "Miami", "Emília-Romanha", "Mônaco", "Canadá", "Espanha", "Áustria", "Reino Unido", "Bélgica", "Hungria", "Holanda", "Itália", "Azerbaijão", "Singapura", "EUA (Austin)", "México", "Brasil", "Las Vegas", "Catar", "Abu Dhabi"]
sprint_gps = ["China", "Miami", "Canadá", "Reino Unido", "Holanda", "Singapura"]
fuso_br = pytz.timezone('America/Sao_Paulo')

# 2. Motor GitHub (Original do TXT)
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
        if 'Usuario' in dados: mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']) & (df_atual['Usuario'] == dados['Usuario']))
        else: mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']))
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
        csv_content = df_final.to_csv(index=False); encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {"message": "Removendo registro", "content": encoded_content, "sha": sha}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
        try:
            with urllib.request.urlopen(req) as response: return response.status in [200, 201]
        except: return False
    return False

# --- E-MAIL E PONTUAÇÃO (Originais do TXT) ---
def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    msg = MIMEMultipart()
    msg['From'] = remetente; msg['To'] = ", ".join(destinatarios); msg['Subject'] = f"🏁 Recibo F1 - {dados['Usuario']} - {dados['GP']}"
    corpo = f"Palpite confirmado para {dados['Usuario']}.\nGP: {dados['GP']}\nSessão: {dados['Tipo']}"
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(remetente, SENHA_EMAIL)
        server.sendmail(remetente, destinatarios, msg.as_string()); server.quit()
        return True
    except: return False

def check_ponto(p, g, chave, pts):
    return pts if str(p.get(chave, '')).strip() == str(g.get(chave, '')).strip() and str(g.get(chave, '')) != "" else 0

def calcular_pontos_sessao(palpite, gabarito):
    pts = 0; tipo = palpite.get('Tipo', '')
    if "Pole" in tipo: pts += check_ponto(palpite, gabarito, 'Pole', 100)
    elif tipo == "Corrida Principal":
        for i in range(1, 11): pts += check_ponto(palpite, gabarito, f'P{i}', [150, 125, 100, 85, 70, 60, 50, 40, 25, 15][i-1])
        pts += check_ponto(palpite, gabarito, 'VoltaRapida', 75)
        pts += check_ponto(palpite, gabarito, 'PrimeiroAbandono', 200)
        pts += check_ponto(palpite, gabarito, 'MaisUltrapassagens', 75)
    elif tipo == "Corrida Sprint":
        for i in range(1, 9): pts += check_ponto(palpite, gabarito, f'P{i}', [80, 70, 60, 50, 40, 30, 20, 10][i-1])
    return pts

# --- MENU ---
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# 3. ABA ENVIAR PALPITE (BLINDADA COM FOTOS)
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    if usuario_logado:
        equipe_usuario = next((e for e, m in equipes.items() if usuario_logado in m), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        c1, c2 = st.columns(2)
        with c1: gp_sel = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
        with c2: tipo_sel = st.selectbox("Tipo de Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_sel in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])
        
        st.header(f"🏁 GP: {gp_sel} - {tipo_sel}")
        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = mv = ab = mu = ""

        # Campos de Seleção com Fotos Instantâneas
        if "Pole" in tipo_sel:
            pole = st.selectbox("Pole Position:", pilotos, key="p_pole"); exibir_foto_piloto(pole)
        elif tipo_sel == "Corrida Principal":
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
            mv = st.selectbox("Melhor Volta:", pilotos); exibir_foto_piloto(mv)
            ab = st.selectbox("1º Abandono:", pilotos); exibir_foto_piloto(ab)
            mu = st.selectbox("Mais Ultrapassagens:", pilotos); exibir_foto_piloto(mu)
        elif tipo_sel == "Corrida Sprint":
            col_a, col_b = st.columns(2)
            with col_a:
                p1 = st.selectbox("1º:", pilotos); exibir_foto_piloto(p1)
                p2 = st.selectbox("2º:", pilotos); exibir_foto_piloto(p2)
                p3 = st.selectbox("3º:", pilotos); exibir_foto_piloto(p3)
                p4 = st.selectbox("4º:", pilotos); exibir_foto_piloto(p4)
            with col_b:
                p5 = st.selectbox("5º:", pilotos); exibir_foto_piloto(p5)
                p6 = st.selectbox("6º:", pilotos); exibir_foto_piloto(p6)
                p7 = st.selectbox("7º:", pilotos); exibir_foto_piloto(p7)
                p8 = st.selectbox("8º:", pilotos); exibir_foto_piloto(p8)

        with st.form("form_final"):
            email_confirm = st.text_input("E-mail de validação:", type="password")
            if st.form_submit_button("GRAVAR PALPITE 🏁"):
                if email_confirm.lower() == emails_autorizados.get(usuario_logado, "").lower():
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp_sel, "Tipo": tipo_sel, "Usuario": usuario_logado, "Equipe": equipe_usuario, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": mv, "PrimeiroAbandono": ab, "MaisUltrapassagens": mu}
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        enviar_recibo_email(dados, email_confirm)
                        st.success("Palpite salvo e recibo enviado!")
                    else: st.error("Erro ao gravar no GitHub.")
                else: st.error("E-mail incorreto.")

# 4. ABA MEUS PALPITES (CORRIGIDO ERRO DE GP)
elif menu == "Meus Palpites":
    usuario_logado = st.sidebar.selectbox("Ver de quem?", [""] + participantes)
    if usuario_logado:
        st.header(f"📋 Histórico de: {usuario_logado}")
        df, _ = ler_dados(ARQUIVO_DADOS)
        if not df.empty:
            # Filtro seguro para evitar erro de coluna ausente
            if 'Usuario' in df.columns:
                meus_votos = df[df['Usuario'] == usuario_logado]
                if not meus_votos.empty:
                    st.dataframe(meus_votos)
                else: st.info("Nenhum palpite para este usuário.")
            else: st.error("Arquivo de dados formatado incorretamente.")
        else: st.info("Banco de dados vazio.")

# 5. ABA CLASSIFICAÇÕES (GERAL + POR ETAPA)
elif menu == "Classificações":
    tab_geral, tab_etapa = st.tabs(["🏆 Classificação Geral", "📍 Classificação por Etapa"])
    df_p, _ = ler_dados(ARQUIVO_DADOS)
    df_g, _ = ler_dados(ARQUIVO_GABARITOS)
    
    if not df_p.empty and not df_g.empty:
        pontos_lista = []
        for _, p in df_p.iterrows():
            g = df_g[(df_g['GP'] == p['GP']) & (df_g['Tipo'] == p['Tipo'])]
            if not g.empty:
                pts = calcular_pontos_sessao(p, g.iloc[0])
                pontos_lista.append({"GP": p['GP'], "Usuario": p['Usuario'], "Equipe": p['Equipe'], "Pontos": pts})
        
        df_final = pd.DataFrame(pontos_lista)
        
        with tab_geral:
            rank = df_final.groupby(['Usuario', 'Equipe']).sum().sort_values(by="Pontos", ascending=False).reset_index()
            st.table(rank)
            st.header("👥 Por Equipes")
            st.table(rank.groupby('Equipe').sum().sort_values(by="Pontos", ascending=False).reset_index())
            
        with tab_etapa:
            gp_escolhido = st.selectbox("Ver pontuação de qual GP?", lista_gps)
            etapa_df = df_final[df_final['GP'] == gp_escolhido]
            if not etapa_df.empty:
                st.table(etapa_df.groupby('Usuario').sum().sort_values(by="Pontos", ascending=False).reset_index())
            else: st.info("Nenhum ponto registrado para este GP ainda.")
    else: st.info("Resultados não disponíveis.")

# 6. ABA ADMINISTRADOR (FUNCIONANDO COM SENHA)
elif menu == "Administrador":
    st.header("🔐 Painel do Comissário")
    senha = st.text_input("Senha de Acesso:", type="password")
    if senha == "f12026":
        st.success("Acesso Liberado!")
        a1, a2 = st.tabs(["Lançar Resultados", "Limpeza"])
        with a1:
            gp_r = st.selectbox("GP do Resultado:", lista_gps, key="gp_r")
            tp_r = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key="tp_r")
            with st.form("gab_form"):
                g_pole = st.selectbox("Pole Oficial:", pilotos)
                if st.form_submit_button("GRAVAR RESULTADO OFICIAL"):
                    res = {"GP": gp_r, "Tipo": tp_r, "Pole": g_pole} # Adicione os outros campos se desejar
                    if guardar_dados(res, ARQUIVO_GABARITOS): st.success("Gravado!")
        with a2:
            df_limpa, _ = ler_dados(ARQUIVO_DADOS)
            if not df_limpa.empty:
                u_del = st.selectbox("Usuário para excluir:", df_limpa['Usuario'].unique())
                if st.button("REMOVER PALPITE"):
                    nova_mascara = df_limpa['Usuario'] != u_del
                    if deletar_registro_github(ARQUIVO_DADOS, nova_mascara): 
                        st.success("Excluído!"); st.rerun()
