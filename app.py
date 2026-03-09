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

# Puxa as chaves mestras do painel do Streamlit
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("As chaves de segurança (GITHUB_TOKEN ou SENHA_EMAIL) não foram encontradas nas configurações do Streamlit.")
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

# --- FUNÇÕES DE BANCO DE DADOS ---
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
            mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']) & (df_atual['Usuario'] == dados['Usuario']))
        else:
            mascara = ~((df_atual['GP'] == dados['GP']) & (df_atual['Tipo'] == dados['Tipo']))
        df_atual = df_atual[mascara]
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    csv_content = df_final.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
    payload = {"message": f"Atualizando registro: {arquivo}", "content": encoded_content}
    if sha: payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json", "Accept": "application/vnd.github.v3+json"}, method="PUT")
    try:
        with urllib.request.urlopen(req) as response: return response.status in [200, 201]
    except urllib.error.HTTPError as e:
        st.error(f"Erro na nuvem: {e}")
        return False

# --- FUNÇÃO NOVA: APAGAR REGISTRO ---
def apagar_registro(usuario, gp, tipo, arquivo):
    df_atual, sha = ler_dados(arquivo)
    if not df_atual.empty:
        # Filtra mantendo apenas o que NÃO é o que queremos apagar
        df_final = df_atual[~((df_atual['Usuario'] == usuario) & (df_atual['GP'] == gp) & (df_atual['Tipo'] == tipo))]
        csv_content = df_final.to_csv(index=False)
        encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"
        payload = {"message": f"Apagando palpite: {usuario} - {gp}", "content": encoded_content, "sha": sha}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}, method="PUT")
        try:
            with urllib.request.urlopen(req) as response: return response.status in [200, 201]
        except Exception as e:
            st.error(f"Erro ao deletar: {e}")
            return False
    return False

# --- DISPARADOR DE E-MAILS ---
def enviar_recibo_email(dados, email_destino):
    remetente = EMAIL_ADMIN
    destinatarios = [remetente, email_destino]
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    corpo = f"Olá {dados['Usuario']},\n\nSeu palpite foi registrado com sucesso!\n\nGP: {dados['GP']}\nSessão: {dados['Tipo']}\nData: {dados['Data_Envio']}\n\nEste é o seu comprovante oficial."
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(remetente, SENHA_EMAIL); server.sendmail(remetente, destinatarios, msg.as_string()); server.quit()
        return True
    except: return False

# --- CÁLCULO DE PONTOS ---
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
        for i, pts in enumerate([150, 125, 100, 85, 70, 60, 50, 40, 25, 15], 1):
            pontos += check_ponto(palpite, gabarito, f'P{i}', pts)
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
        for i, pts in enumerate([80, 70, 60, 50, 40, 30, 20, 10], 1):
            pontos += check_ponto(palpite, gabarito, f'P{i}', pts)
    return pontos

# --- NAVEGAÇÃO ---
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Meus Palpites", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        col_gp, col_tipo = st.columns(2)
        with col_gp: gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
        opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_selecionado in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"]
        with col_tipo: tipo_sessao = st.selectbox("Tipo de Sessão:", opcoes_sessao)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        with st.form("form_palpite"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = vr = pa = mu = ""
            if "Pole" in tipo_sessao: pole = st.selectbox("Pole Position:", pilotos)
            elif tipo_sessao == "Corrida Principal":
                c1, c2 = st.columns(2)
                with c1: p1=st.selectbox("1º Colocado:", pilotos); p2=st.selectbox("2º Colocado:", pilotos); p3=st.selectbox("3º Colocado:", pilotos); p4=st.selectbox("4º Colocado:", pilotos); p5=st.selectbox("5º Colocado:", pilotos)
                with c2: p6=st.selectbox("6º Colocado:", pilotos); p7=st.selectbox("7º Colocado:", pilotos); p8=st.selectbox("8º Colocado:", pilotos); p9=st.selectbox("9º Colocado:", pilotos); p10=st.selectbox("10º Colocado:", pilotos); vr=st.selectbox("Melhor Volta:", pilotos); pa=st.selectbox("1º Abandono:", pilotos); mu=st.selectbox("Mais Ultrapassagens:", pilotos)
            elif tipo_sessao == "Corrida Sprint":
                c1, c2 = st.columns(2)
                with c1: p1=st.selectbox("1º Colocado:", pilotos); p2=st.selectbox("2º Colocado:", pilotos); p3=st.selectbox("3º Colocado:", pilotos); p4=st.selectbox("4º Colocado:", pilotos)
                with c2: p5=st.selectbox("5º Colocado:", pilotos); p6=st.selectbox("6º Colocado:", pilotos); p7=st.selectbox("7º Colocado:", pilotos); p8=st.selectbox("8º Colocado:", pilotos)

            st.divider()
            email_confirmacao = st.text_input("Digite o seu E-mail cadastrado:", type="password")
            if st.form_submit_button(f"Salvar Palpite 🏁"):
                if email_confirmacao.strip().lower() == emails_autorizados.get(usuario_logado, "").lower():
                    dados = {"Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'), "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": vr, "PrimeiroAbandono": pa, "MaisUltrapassagens": mu}
                    if guardar_dados(dados, ARQUIVO_DADOS):
                        enviar_recibo_email(dados, email_confirmacao)
                        st.success("Palpite salvo e recibo enviado!")
                else: st.error("E-mail incorreto.")

# --- ÁREA: MEUS PALPITES ---
elif menu == "Meus Palpites":
    st.header("🕵️ Meu Histórico")
    u_c = st.selectbox("Selecione seu nome:", [""] + participantes)
    if u_c:
        em_c = st.text_input("E-mail:", type="password")
        if st.button("Buscar 🔍"):
            if em_c.strip().lower() == emails_autorizados.get(u_c, "").lower():
                df, _ = ler_dados(ARQUIVO_DADOS)
                if not df.empty:
                    meus = df[df['Usuario'] == u_c].drop(columns=['Usuario', 'Equipe'])
                    st.dataframe(meus, use_container_width=True)

# --- ÁREA: CLASSIFICAÇÕES ---
elif menu == "Classificações":
    st.header("🏆 Classificações F1 2026")
    df_p, _ = ler_dados(ARQUIVO_DADOS)
    df_g, _ = ler_dados(ARQUIVO_GABARITOS)
    if not df_p.empty and not df_g.empty:
        res = []
        for _, row_p in df_p.iterrows():
            gab_match = df_g[(df_g['GP'] == row_p['GP']) & (df_g['Tipo'] == row_p['Tipo'])]
            if not gab_match.empty:
                res.append({"Usuario": row_p['Usuario'], "Equipe": row_p.get('Equipe', 'Sem Equipe'), "Pontos": calcular_pontos_sessao(row_p, gab_match.iloc[-1]), "GP": row_p['GP']})
        if res:
            df_res = pd.DataFrame(res)
            filtro = st.selectbox("Visualização:", ["Geral"] + lista_gps)
            if filtro != "Geral": df_res = df_res[df_res["GP"] == filtro]
            
            c1, c2 = st.columns(2)
            with c1: st.subheader("Pilotos"); st.dataframe(df_res.groupby('Usuario')['Pontos'].sum().sort_values(ascending=False), use_container_width=True)
            with c2: st.subheader("Construtores"); st.dataframe(df_res.groupby('Equipe')['Pontos'].sum().sort_values(ascending=False), use_container_width=True)
            
            st.divider()
            st.subheader("🕵️‍♂️ Raio-X dos Palpites")
            rx_gp = st.selectbox("GP Raio-X:", lista_gps)
            rx_tp = st.selectbox("Sessão Raio-X:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"])
            gab_rx = df_g[(df_g['GP'] == rx_gp) & (df_g['Tipo'] == rx_tp)]
            if not gab_rx.empty:
                palp_rx = df_p[(df_p['GP'] == rx_gp) & (df_p['Tipo'] == rx_tp)]
                u_rx = st.selectbox("Ver palpite de:", [""] + sorted(palp_rx['Usuario'].unique().tolist()))
                if u_rx:
                    p_u = palp_rx[palp_rx['Usuario'] == u_rx].iloc[-1]
                    g_o = gab_rx.iloc[-1]
                    for k in ['Pole','P1','P2','P3','P4','P5','P6','P7','P8','P9','P10','VoltaRapida','PrimeiroAbandono','MaisUltrapassagens']:
                        val_p = str(p_u.get(k, '')).strip()
                        val_g = str(g_o.get(k, '')).strip()
                        if val_g and val_g != 'nan':
                            if val_p == val_g: st.success(f"✅ {k}: {val_p}")
                            else: st.error(f"❌ {k}: {val_p} | Oficial: {val_g}")
            else: st.info("Gabarito ainda não lançado para esta sessão.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha Diretor:", type="password")
    if senha == "fleury1475":
        st.warning("⚠️ MODO ADMINISTRADOR ATIVO")
        
        # --- ZONA DE EXCLUSÃO (NOVIDADE) ---
        st.subheader("🗑️ Zona de Exclusão (Limpeza de Palpites)")
        df_adm, _ = ler_dados(ARQUIVO_DADOS)
        if not df_adm.empty:
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1: u_del = st.selectbox("Palpiteiro para apagar:", [""] + sorted(df_adm['Usuario'].unique().tolist()))
            with col_d2: gp_del = st.selectbox("GP para apagar:", [""] + sorted(df_adm['GP'].unique().tolist()))
            with col_d3: tp_del = st.selectbox("Sessão para apagar:", [""] + sorted(df_adm['Tipo'].unique().tolist()))
            
            if st.button("🔴 APAGAR REGISTRO DEFINITIVAMENTE"):
                if u_del and gp_del and tp_del:
                    if apagar_registro(u_del, gp_del, tp_del, ARQUIVO_DADOS):
                        st.success(f"Palpite de {u_del} apagado com sucesso!")
                        st.rerun()
                else: st.warning("Selecione todos os campos para apagar.")

        st.divider()
        st.subheader("🏆 Inserir Gabarito Oficial")
        gp_ad = st.selectbox("GP Gabarito:", lista_gps)
        tp_ad = st.selectbox("Sessão Gabarito:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"] if gp_ad in sprint_gps else ["Classificação Principal (Pole)", "Corrida Principal"])
        with st.form("form_gab"):
            pole = p1=p2=p3=p4=p5=p6=p7=p8=p9=p10=vr=pa=mu = ""
            if "Pole" in tp_ad: pole = st.selectbox("Pole Oficial:", pilotos)
            elif tp_ad == "Corrida Principal":
                c1, c2 = st.columns(2)
                with c1: p1=st.selectbox("1º:", pilotos); p2=st.selectbox("2º:", pilotos); p3=st.selectbox("3º:", pilotos); p4=st.selectbox("4º:", pilotos); p5=st.selectbox("5º:", pilotos)
                with c2: p6=st.selectbox("6º:", pilotos); p7=st.selectbox("7º:", pilotos); p8=st.selectbox("8º:", pilotos); p9=st.selectbox("9º:", pilotos); p10=st.selectbox("10º:", pilotos); vr=st.selectbox("V.Rápida:", pilotos); pa=st.selectbox("Abandono:", pilotos); mu=st.selectbox("Ultrapassagens:", pilotos)
            if st.form_submit_button("Submeter Gabarito 🏆"):
                d_g = {"GP": gp_ad, "Tipo": tp_ad, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10, "VoltaRapida": vr, "PrimeiroAbandono": pa, "MaisUltrapassagens": mu}
                if guardar_dados(d_g, ARQUIVO_GABARITOS): st.success("Gabarito atualizado!")
