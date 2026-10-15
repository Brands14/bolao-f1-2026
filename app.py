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

GITHUB_USER = "Brands14" 
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Puxa as chaves mestras
try:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = os.environ.get("SENHA_EMAIL") or st.secrets["SENHA_EMAIL"]
except:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    SENHA_EMAIL = os.environ.get("SENHA_EMAIL")

if not GITHUB_TOKEN:
    st.error("Erro: A variável GITHUB_TOKEN não foi encontrada.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv" 
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"
ARQUIVO_HISTORICO = "historico_alteracoes_2026.csv"

# --- LOGO ---
nome_arquivo_logo = "WhatsApp Image 2026-02-24 at 16.12.18.png"
nome_para_url = nome_arquivo_logo.replace(" ", "%20")
url_final_logo = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{nome_para_url}"

try:
    st.image(url_final_logo, use_column_width=True)
except Exception as e:
    st.title("🏁 Palpites F1 2026")
    st.write(f"Aguardando carregamento da imagem...")

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

# 2. Motor de Banco de Dados Permanente
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
        "Mensagem": f"O palpiteiro {usuario} {acao} seu palpite para o GP de {gp} ({tipo}) às {agora_br.strftime('%H:%M:%S')} no dia {agora_br.strftime('%d/%m/%Y')}."
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
        acao_log = "alterou (pelo Administrador)" if eh_edicao_admin else ("alterou" if eh_alteracao else "enviou")
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
        st.error(f"Erro técnico ao salvar: {e}")
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
    
    Seu palpite foi registrado/atualizado com sucesso pelo VAR do nosso sistema!
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
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
        server.ehlo() 
        server.starttls()
        server.ehlo()
        server.login(remetente, SENHA_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"ERRO DE EMAIL NO LOG: {e}")
        try:
            server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20)
            server_ssl.login(remetente, SENHA_EMAIL)
            server_ssl.send_message(msg)
            server_ssl.quit()
            return True
        except Exception as e2:
            st.error(f"O servidor de e-mail está inacessível no momento: {e2}")
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
    if val_str in pilotos:
        return pilotos.index(val_str)
    return 0

# 5. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        
        st.markdown(f"### 🏎️ Piloto: **{usuario_logado}**")
        st.caption(f"Equipe: {equipe_usuario}")

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

        # BUSCA DE PALPITE ANTERIOR
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
                st.info("ℹ️ **Você já possui um palpite registrado para esta sessão.** Os campos abaixo foram preenchidos com suas escolhas anteriores. Ajuste o que desejar e grave novamente.")

        st.divider()
        st.header(f"🏁 {gp_selecionado} - {tipo_sessao}")

        pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
        v_rapida = p_abandono = m_ultrapassagens = ""

        if "Pole" in tipo_sessao:
            idx_pole = index_piloto(palpite_existente.get('Pole', ''))
            pole = st.selectbox("Selecione o Pole Position:", pilotos, index=idx_pole, key="sel_pole")
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
                        st.toast(f'Palpite Gravado! Acelera, {usuario_logado}! 🏎️💨', icon='🏁')
                        
                        placeholder_animacao = st.empty()
                        for _ in range(3):
                            placeholder_animacao.markdown("<h1 style='text-align: center; font-size: 60px;'>🏎️ 🏁 🏎️ 🏁 🏎️</h1>", unsafe_allow_html=True)
                            time.sleep(0.4)
                            placeholder_animacao.empty()
                            time.sleep(0.2)
                        
                        st.success(f"🏁 Maravilha, {usuario_logado}! Seu palpite para o GP de {gp_selecionado} foi atualizado com sucesso.")
                    else:
                        st.error("Ops! Tivemos um problema com o servidor do GitHub. Tente novamente.")
                else:
                    st.error("E-mail incorreto! O palpite não foi gravado.")

# --- ÁREA: MEUS PALPITES ---
elif menu == "Meus Palpites":
    st.header("🕵️ Meu Histórico de Palpites")
    st.write("Consulte aqui todos os palpites que você já enviou. Os dados agora são permanentes!")
    
    usuario_consulta = st.selectbox("Selecione o seu nome:", [""] + participantes)
    
    if usuario_consulta:
        email_consulta = st.text_input("Digite o seu E-mail cadastrado para abrir o cofre:", type="password")
        
        if st.button("Buscar Meus Palpites 🔍"):
            email_correto = emails_autorizados.get(usuario_consulta, "").strip().lower()
            email_digitado = email_consulta.strip().lower()
            
            if email_digitado == email_correto and email_correto != "":
                df_todos, _ = ler_dados(ARQUIVO_DADOS)
                if not df_todos.empty:
                    meus_dados = df_todos[df_todos['Usuario'] == usuario_consulta]
                    if not meus_dados.empty:
                        st.success("Cofre aberto com sucesso!")
                        meus_dados_ultimos = meus_dados.drop_duplicates(subset=['GP', 'Tipo'], keep='last')
                        meus_dados_view = meus_dados_ultimos.drop(columns=['Usuario', 'Equipe'])
                        st.dataframe(meus_dados_view, use_container_width=True)
                    else:
                        st.warning("Você ainda não enviou nenhum palpite.")
                else:
                    st.info("Nenhum palpite registrado no banco permanente ainda.")
            else:
                st.error("🚫 Acesso Negado: O e-mail não confere.")

# --- ÁREA: CLASSIFICACOES ---
elif menu == "Classificações":
    st.header("🏆 Classificações do Campeonato F1 2026")
    
    df_palpites, _ = ler_dados(ARQUIVO_DADOS)
    df_gabaritos, _ = ler_dados(ARQUIVO_GABARITOS)
    
    if not df_palpites.empty and not df_gabaritos.empty:
        df_palpites_validos = df_palpites.drop_duplicates(subset=['Usuario', 'GP', 'Tipo'], keep='last')
        
        resultados = []
        for index_p, row_p in df_palpites_validos.iterrows():
            gp = row_p.get('GP', '')
            tipo = row_p.get('Tipo', '')
            usuario = row_p['Usuario']
            
            equipe_atual = next((eq for eq, membros in equipes.items() if usuario in membros), "Sem Equipe")
            gabarito_match = df_gabaritos[(df_gabaritos['GP'] == gp) & (df_gabaritos['Tipo'] == tipo)]
            
            if not gabarito_match.empty:
                gabarito_oficial = gabarito_match.iloc[-1]
                pontos = calcular_pontos_sessao(row_p, gabarito_oficial)
                resultados.append({"Usuario": usuario, "Equipe": equipe_atual, "Pontos": pontos, "GP": gp})
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            st.markdown("### 🔍 Filtro de Resultados")
            filtro_classificacao = st.selectbox("Selecione a visualização desejada:", ["Geral (Campeonato Completo)"] + lista_gps)
            
            if filtro_classificacao != "Geral (Campeonato Completo)":
                df_resultados = df_resultados[df_resultados["GP"] == filtro_classificacao]
                st.subheader(f"📊 Resultado Específico: GP de {filtro_classificacao}")
            else:
                st.subheader("📊 Classificação Geral do Campeonato")
            
            if not df_resultados.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**👤 Mundial de Pilotos**")
                    ranking_geral = df_resultados.groupby('Usuario')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                    ranking_geral.index = range(1, len(ranking_geral) + 1)
                    st.dataframe(ranking_geral, use_container_width=True)
                    
                with col2:
                    st.markdown("**🏎️ Mundial de Construtores**")
                    ranking_equipas = df_resultados.groupby('Equipe')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                    ranking_equipas.index = range(1, len(ranking_equipas) + 1)
                    st.dataframe(ranking_equipas, use_container_width=True)
            else:
                st.warning("Ainda não há pontuações para este GP.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha de Diretor de Prova:", type="password")
    
    if senha == "fleury1475":
        st.warning("⚠ MODO ADMINISTRADOR ATIVO (DADOS PERMANENTES)")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Auditoria & Edição de Palpites", 
            "📜 Histórico de Alterações",
            "Gabaritos Oficiais", 
            "Consultar Gabaritos Salvos", 
            "Limpeza de Dados"
        ])
        
        # --- TAB 1: AUDITORIA E EDIÇÃO DE PALPITES PELO ADMIN ---
        with tab1:
            st.subheader("🕵️‍♂️ Auditoria e Edição Direta de Palpites")
            st.caption("Consulte ou altere o palpite de qualquer participante para qualquer GP (mesmo os já finalizados).")
            
            df_auditoria, _ = ler_dados(ARQUIVO_DADOS)
            
            if not df_auditoria.empty:
                df_auditoria_limpo = df_auditoria.drop_duplicates(subset=['Usuario', 'GP', 'Tipo'], keep='last')
                
                # Tabela de Consulta
                filtro_gp_auditoria = st.selectbox("Filtrar Tabela da Auditoria por GP:", ["Todos os GPs"] + lista_gps, key="flt_aud")
                df_view_aud = df_auditoria_limpo.copy()
                if filtro_gp_auditoria != "Todos os GPs":
                    df_view_aud = df_view_aud[df_view_aud["GP"] == filtro_gp_auditoria]
                st.dataframe(df_view_aud, use_container_width=True)
                
                st.divider()
                st.subheader("🛠️ Editar Palpite de um Participante")
                
                col_edit_user, col_edit_gp, col_edit_sessao = st.columns(3)
                with col_edit_user:
                    user_edit = st.selectbox("Selecione o Participante:", [""] + participantes, key="user_edit_adm")
                with col_edit_gp:
                    gp_edit = st.selectbox("Selecione o GP:", lista_gps, key="gp_edit_adm")
                with col_edit_sessao:
                    opcoes_sessao_edit = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_edit in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
                    sessao_edit = st.selectbox("Selecione a Sessão:", opcoes_sessao_edit, key="sessao_edit_adm")
                
                if user_edit != "":
                    match_user_edit = df_auditoria_limpo[
                        (df_auditoria_limpo['Usuario'] == user_edit) & 
                        (df_auditoria_limpo['GP'] == gp_edit) & 
                        (df_auditoria_limpo['Tipo'] == sessao_edit)
                    ]
                    
                    palpite_adm_existente = {}
                    if not match_user_edit.empty:
                        palpite_adm_existente = match_user_edit.iloc[-1].to_dict()
                        st.info(f"✏️ Editando palpite existente de **{user_edit}** para **GP {gp_edit} - {sessao_edit}**.")
                    else:
                        st.warning(f"⚠️ NENHUM palpite encontrado para **{user_edit}** no **GP {gp_edit} - {sessao_edit}**. O formulário abaixo criará um NOVO registro.")
                    
                    equipe_user_edit = next((eq for eq, membros in equipes.items() if user_edit in membros), "Sem Equipe")
                    
                    with st.form("form_edicao_admin"):
                        st.markdown(f"#### Formutário de Ajuste: {user_edit}")
                        
                        pole_e = p1_e = p2_e = p3_e = p4_e = p5_e = p6_e = p7_e = p8_e = p9_e = p10_e = ""
                        vr_e = ab_e = mu_e = ""
                        
                        if "Pole" in sessao_edit:
                            pole_e = st.selectbox("Pole Position:", pilotos, index=index_piloto(palpite_adm_existente.get('Pole', '')), key="pole_adm_e")
                        elif sessao_edit == "Corrida Principal":
                            c1_e, c2_e = st.columns(2)
                            with c1_e:
                                p1_e = st.selectbox("1º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P1', '')), key="p1_adm_e")
                                p2_e = st.selectbox("2º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P2', '')), key="p2_adm_e")
                                p3_e = st.selectbox("3º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P3', '')), key="p3_adm_e")
                                p4_e = st.selectbox("4º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P4', '')), key="p4_adm_e")
                                p5_e = st.selectbox("5º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P5', '')), key="p5_adm_e")
                            with c2_e:
                                p6_e = st.selectbox("6º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P6', '')), key="p6_adm_e")
                                p7_e = st.selectbox("7º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P7', '')), key="p7_adm_e")
                                p8_e = st.selectbox("8º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P8', '')), key="p8_adm_e")
                                p9_e = st.selectbox("9º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P9', '')), key="p9_adm_e")
                                p10_e = st.selectbox("10º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P10', '')), key="p10_adm_e")
                            
                            st.write("---")
                            c3_e, c4_e, c5_e = st.columns(3)
                            with c3_e:
                                vr_e = st.selectbox("Melhor Volta:", pilotos, index=index_piloto(palpite_adm_existente.get('VoltaRapida', '')), key="vr_adm_e")
                            with c4_e:
                                ab_e = st.selectbox("1º Abandono:", pilotos, index=index_piloto(palpite_adm_existente.get('PrimeiroAbandono', '')), key="ab_adm_e")
                            with c5_e:
                                mu_e = st.selectbox("Mais Ultrapassagens:", pilotos, index=index_piloto(palpite_adm_existente.get('MaisUltrapassagens', '')), key="mu_adm_e")
                                
                        elif sessao_edit == "Corrida Sprint":
                            c1_e, c2_e = st.columns(2)
                            with c1_e:
                                p1_e = st.selectbox("1º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P1', '')), key="s1_adm_e")
                                p2_e = st.selectbox("2º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P2', '')), key="s2_adm_e")
                                p3_e = st.selectbox("3º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P3', '')), key="s3_adm_e")
                                p4_e = st.selectbox("4º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P4', '')), key="s4_adm_e")
                            with c2_e:
                                p5_e = st.selectbox("5º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P5', '')), key="s5_adm_e")
                                p6_e = st.selectbox("6º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P6', '')), key="s6_adm_e")
                                p7_e = st.selectbox("7º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P7', '')), key="s7_adm_e")
                                p8_e = st.selectbox("8º Colocado:", pilotos, index=index_piloto(palpite_adm_existente.get('P8', '')), key="s8_adm_e")

                        if st.form_submit_button("Atualizar Palpite do Participante 🛠️"):
                            dados_editados = {
                                "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S') + " (Admin)",
                                "GP": gp_edit,
                                "Tipo": sessao_edit,
                                "Usuario": user_edit,
                                "Equipe": equipe_user_edit,
                                "Pole": pole_e,
                                "P1": p1_e, "P2": p2_e, "P3": p3_e, "P4": p4_e, "P5": p5_e,
                                "P6": p6_e, "P7": p7_e, "P8": p8_e, "P9": p9_e, "P10": p10_e,
                                "VoltaRapida": vr_e,
                                "PrimeiroAbandono": ab_e,
                                "MaisUltrapassagens": mu_e
                            }
                            if guardar_dados(dados_editados, ARQUIVO_DADOS, eh_edicao_admin=True):
                                st.success(f"Palpite de {user_edit} para o GP de {gp_edit} foi alterado com sucesso pelo Administrador!")
                                time.sleep(1)
                                st.rerun()
            else:
                st.info("Nenhum palpite registrado no banco até o momento.")

        # --- TAB 2: HISTÓRICO DE ALTERAÇÕES ---
        with tab2:
            st.subheader("📜 Log Auditável de Envios e Alterações")
            st.caption("Acompanhe o momento exato (Horário de Brasília) em que cada participante enviou ou modificou um palpite.")
            
            df_historico_log, _ = ler_dados(ARQUIVO_HISTORICO)
            
            if not df_historico_log.empty:
                col_flt_h1, col_flt_h2 = st.columns(2)
                with col_flt_h1:
                    filtro_hist_user = st.selectbox("Filtrar Histórico por Participante:", ["Todos os Participantes"] + participantes, key="flt_hist_usr")
                with col_flt_h2:
                    filtro_hist_gp = st.selectbox("Filtrar Histórico por GP:", ["Todos os GPs"] + lista_gps, key="flt_hist_gp")
                
                df_view_hist = df_historico_log.copy()
                if filtro_hist_user != "Todos os Participantes":
                    df_view_hist = df_view_hist[df_view_hist['Usuario'] == filtro_hist_user]
                if filtro_hist_gp != "Todos os GPs":
                    df_view_hist = df_view_hist[df_view_hist['GP'] == filtro_hist_gp]
                
                if not df_view_hist.empty:
                    # Inverte para mostrar os mais recentes no topo
                    df_view_hist = df_view_hist.iloc[::-1]
                    for idx, row_h in df_view_hist.iterrows():
                        st.markdown(f"⏱️ **`[{row_h.get('Data_Hora', '')}]`** — {row_h.get('Mensagem', '')}")
                else:
                    st.info("Nenhum registro encontrado para os filtros selecionados.")
            else:
                st.info("Ainda não há registros no histórico de alterações.")

        # --- TAB 3: GABARITOS OFICIAIS ---
        with tab3:
            st.header("🏆 Inserir / Modificar Gabarito Oficial")
            col_gp_a, col_tipo_a = st.columns(2)
            with col_gp_a:
                gp_admin = st.selectbox("GP do Gabarito:", lista_gps, key="gp_adm")
            opcoes_admin = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_admin in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
            
            with col_tipo_a:
                tipo_admin = st.selectbox("Sessão do Gabarito:", opcoes_admin, key="tipo_adm")
            
            df_gabs_exist, _ = ler_dados(ARQUIVO_GABARITOS)
            gab_existente = {}
            if not df_gabs_exist.empty:
                match_gab = df_gabs_exist[
                    (df_gabs_exist['GP'] == gp_admin) & 
                    (df_gabs_exist['Tipo'] == tipo_admin)
                ]
                if not match_gab.empty:
                    gab_existente = match_gab.iloc[-1].to_dict()
                    st.info("ℹ️ **Gabarito já cadastrado para esta sessão.** Os campos abaixo foram preenchidos com os dados atuais. Altere o piloto que sofreu a punição/ajuste e salve novamente.")

            with st.form("form_gabarito"):
                pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
                volta_rapida = primeiro_abandono = mais_ultrapassagens = ""

                if "Pole" in tipo_admin:
                    pole = st.selectbox("Pole Position Oficial:", pilotos, index=index_piloto(gab_existente.get('Pole', '')))
                elif "Corrida Principal" in tipo_admin:
                    c1, c2 = st.columns(2)
                    with c1:
                        p1 = st.selectbox("1º Colocado:", pilotos, index=index_piloto(gab_existente.get('P1', '')))
                        p2 = st.selectbox("2º Colocado:", pilotos, index=index_piloto(gab_existente.get('P2', '')))
                        p3 = st.selectbox("3º Colocado:", pilotos, index=index_piloto(gab_existente.get('P3', '')))
                        p4 = st.selectbox("4º Colocado:", pilotos, index=index_piloto(gab_existente.get('P4', '')))
                        p5 = st.selectbox("5º Colocado:", pilotos, index=index_piloto(gab_existente.get('P5', '')))
                    with c2:
                        p6 = st.selectbox("6º Colocado:", pilotos, index=index_piloto(gab_existente.get('P6', '')))
                        p7 = st.selectbox("7º Colocado:", pilotos, index=index_piloto(gab_existente.get('P7', '')))
                        p8 = st.selectbox("8º Colocado:", pilotos, index=index_piloto(gab_existente.get('P8', '')))
                        p9 = st.selectbox("9º Colocado:", pilotos, index=index_piloto(gab_existente.get('P9', '')))
                        p10 = st.selectbox("10º Colocado:", pilotos, index=index_piloto(gab_existente.get('P10', '')))
                        volta_rapida = st.selectbox("Melhor Volta:", pilotos, index=index_piloto(gab_existente.get('VoltaRapida', '')))
                        primeiro_abandono = st.selectbox("1º Abandono:", pilotos, index=index_piloto(gab_existente.get('PrimeiroAbandono', '')))
                        mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos, index=index_piloto(gab_existente.get('MaisUltrapassagens', '')))
                elif "Corrida Sprint" in tipo_admin:
                    c1, c2 = st.columns(2)
                    with c1:
                        p1 = st.selectbox("1º Colocado:", pilotos, index=index_piloto(gab_existente.get('P1', '')))
                        p2 = st.selectbox("2º Colocado:", pilotos, index=index_piloto(gab_existente.get('P2', '')))
                        p3 = st.selectbox("3º Colocado:", pilotos, index=index_piloto(gab_existente.get('P3', '')))
                        p4 = st.selectbox("4º Colocado:", pilotos, index=index_piloto(gab_existente.get('P4', '')))
                    with c2:
                        p5 = st.selectbox("5º Colocado:", pilotos, index=index_piloto(gab_existente.get('P5', '')))
                        p6 = st.selectbox("6º Colocado:", pilotos, index=index_piloto(gab_existente.get('P6', '')))
                        p7 = st.selectbox("7º Colocado:", pilotos, index=index_piloto(gab_existente.get('P7', '')))
                        p8 = st.selectbox("8º Colocado:", pilotos, index=index_piloto(gab_existente.get('P8', '')))
                
                if st.form_submit_button("Salvar / Atualizar Gabarito Oficial 🏆"):
                    dados_g = {
                        "GP": gp_admin, "Tipo": tipo_admin,
                        "Pole": pole,
                        "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida,
                        "PrimeiroAbandono": primeiro_abandono,
                        "MaisUltrapassagens": mais_ultrapassagens
                    }
                    if guardar_dados(dados_g, ARQUIVO_GABARITOS):
                        st.success("Gabarito Atualizado com Sucesso!")
                        time.sleep(1)
                        st.rerun()

            st.divider()
            st.subheader("🗑 Corrigir Gabarito (Apagar)")
            df_gabs_del, sha_gabs_del = ler_dados(ARQUIVO_GABARITOS)
            
            if not df_gabs_del.empty:
                lista_para_apagar = df_gabs_del.apply(lambda x: f"{x['GP']} - {x['Tipo']}", axis=1).tolist()
                gabarito_para_deletar = st.selectbox("Selecione o gabarito que deseja remover:", [""] + lista_para_apagar, key="del_gabarito_oficial")
                
                if st.button("⚠️ APAGAR GABARITO SELECIONADO", type="secondary"):
                    if gabarito_para_deletar != "":
                        gp_excluir = gabarito_para_deletar.split(" - ")[0]
                        tipo_excluir = gabarito_para_deletar.split(" - ")[1]
                        
                        df_novo_gabarito = df_gabs_del[~((df_gabs_del['GP'] == gp_excluir) & (df_gabs_del['Tipo'] == tipo_excluir))]
                        
                        csv_para_github = df_novo_gabarito.to_csv(index=False)
                        b64_para_github = base64.b64encode(csv_para_github.encode()).decode()
                        
                        payload_del = {
                            "message": f"Removendo Gabarito: {gp_excluir} {tipo_excluir}",
                            "content": b64_para_github,
                            "sha": sha_gabs_del
                        }
                        
                        header_del = {
                            "Authorization": f"token {GITHUB_TOKEN}",
                            "Content-Type": "application/json",
                            "User-Agent": "BolaoF1-App"
                        }
                        
                        url_del = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{ARQUIVO_GABARITOS}"
                        
                        try:
                            req_del = urllib.request.Request(url_del, data=json.dumps(payload_del).encode(), headers=header_del, method='PUT')
                            with urllib.request.urlopen(req_del) as resp_del:
                                st.success(f"Gabarito de {gp_excluir} removido! O GP já está disponível para palpites novamente.")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao apagar: {e}")
                    else:
                        st.warning("Selecione um gabarito na lista acima.")

        # --- TAB 4: GABARITOS SALVOS ---
        with tab4:
            st.subheader("📋 Gabaritos Oficiais Salvos")
            st.write("Consulte aqui o resultado de todas as sessões e GPs já registados no sistema.")
            
            df_gabs_consulta, _ = ler_dados(ARQUIVO_GABARITOS)
            if not df_gabs_consulta.empty:
                filtro_gp_gabarito = st.selectbox("Filtrar Gabaritos por GP:", ["Todos os GPs"] + lista_gps, key="filtro_gab_view")
                
                df_view_gab = df_gabs_consulta.copy()
                if filtro_gp_gabarito != "Todos os GPs":
                    df_view_gab = df_view_gab[df_view_gab["GP"] == filtro_gp_gabarito]
                
                if not df_view_gab.empty:
                    df_view_gab = df_view_gab.dropna(how='all', axis=1)
                    st.dataframe(df_view_gab, use_container_width=True)
                else:
                    st.info(f"Nenhum gabarito registado para o GP {filtro_gp_gabarito}.")
            else:
                st.info("Nenhum gabarito registado no banco de dados até ao momento.")

        # --- TAB 5: LIMPEZA DE DADOS ---
        with tab5:
            st.header("🗑️ Apagar Registros de Palpites")
            df_limpeza, _ = ler_dados(ARQUIVO_DADOS)
            if not df_limpeza.empty:
                col_del_gp, col_del_sessao = st.columns(2)
                with col_del_gp:
                    gp_del = st.selectbox("GP para excluir:", lista_gps, key="del_gp")
                with col_del_sessao:
                    sessao_del = st.selectbox("Sessão para excluir:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key="del_sessao")
                
                palpites_filtrados = df_limpeza[(df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del)]
                
                if not palpites_filtrados.empty:
                    user_del = st.selectbox("Selecione o usuário para APAGAR o palpite:", [""] + sorted(palpites_filtrados['Usuario'].tolist()), key="del_user")
                    
                    if user_del != "":
                        if st.button(f"CONFIRMAR EXCLUSÃO DE {user_del}", type="primary"):
                            mascara = ~((df_limpeza['GP'] == gp_del) & 
                                        (df_limpeza['Tipo'] == sessao_del) & 
                                        (df_limpeza['Usuario'] == user_del))
                            if deletar_registro_github(ARQUIVO_DADOS, mascara):
                                st.success("Palpite removido com sucesso!")
                                st.rerun()
                else:
                    st.info("Nenhum palpite encontrado para este GP/Sessão.")

    elif senha != "":
        st.error("Senha incorreta.")
