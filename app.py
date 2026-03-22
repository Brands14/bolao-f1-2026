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
                            elif menu == "📊 Dashboard":
        tab_class, tab_regras = st.tabs(["🏆 Classificações", "📜 Regras"])
        
        with tab_class:
            st.header("🏆 Classificação do Bolão")
            df_p, _ = ler_dados(ARQUIVO_DADOS)
            df_g, _ = ler_dados(ARQUIVO_GABARITOS)
            
            if not df_p.empty and not df_g.empty:
                resultados = []
                for _, g in df_g.iterrows():
                    p_gp = df_p[(df_p['GP'] == g['GP']) & (df_p['Tipo'] == g['Tipo'])]
                    for _, palpite in p_gp.iterrows():
                        pts = calcular_pontos(palpite, g)
                        resultados.append({
                            "Usuario": palpite['Usuario'],
                            "Equipe": palpite['Equipe'],
                            "Pontos": pts
                        })
                
                if resultados:
                    df_res = pd.DataFrame(resultados)
                    st.subheader("👤 Classificação Individual")
                    ranking_ind = df_res.groupby("Usuario")["Pontos"].sum().reset_index()
                    ranking_ind = ranking_ind.sort_values(by="Pontos", ascending=False).reset_index(drop=True)
                    st.dataframe(ranking_ind, use_container_width=True)
                    
                    st.subheader("🏎️ Mundial de Construtores")
                    ranking_eq = df_res.groupby("Equipe")["Pontos"].sum().reset_index()
                    ranking_eq = ranking_eq.sort_values(by="Pontos", ascending=False).reset_index(drop=True)
                    st.dataframe(ranking_eq, use_container_width=True)
            else:
                st.warning("Aguardando os primeiros gabaritos para gerar a classificação.")

        with tab_regras:
            st.header("📜 Regras Oficiais")
            st.write("""
            - **Fechamento:** 30 minutos antes do início de cada sessão (Qualy ou Corrida).
            - **Pontuação:** 10 pontos por posição correta.
            - **Volta Rápida:** 5 pontos (válido apenas para Corrida Principal).
            - **Empate:** Em caso de empate, o critério é quem enviou o palpite primeiro (Timestamp).
            """)

    elif menu == "⚙️ Admin":
        senha_admin = st.text_input("Senha de Acesso:", type="password")
        if senha_admin == "f12026admin":
            st.title("Painel de Controle")
            
            st.header("🏁 Inserir Resultado Oficial (Gabarito)")
            with st.form("form_gabarito"):
                g_gp = st.selectbox("GP:", lista_gps)
                g_tipo = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"])
                
                cols = st.columns(4)
                g1 = cols[0].selectbox("🥇 P1", lista_pilotos, key="g1")
                g2 = cols[1].selectbox("🥈 P2", lista_pilotos, key="g2")
                g3 = cols[2].selectbox("🥉 P3", lista_pilotos, key="g3")
                g4 = cols[3].selectbox("P4", lista_pilotos, key="g4")
                
                cols2 = st.columns(4)
                g5 = cols2[0].selectbox("P5", lista_pilotos, key="g5")
                g6 = cols2[1].selectbox("P6", lista_pilotos, key="g6")
                g7 = cols2[2].selectbox("P7", lista_pilotos, key="g7")
                g8 = cols2[3].selectbox("P8", lista_pilotos, key="g8")
                
                g_vr = st.selectbox("Volta Rápida:", ["N/A"] + lista_pilotos)
                
                if st.form_submit_button("SALVAR RESULTADO"):
                    gabarito = {
                        "GP": g_gp, "Tipo": g_tipo,
                        "P1": g1, "P2": g2, "P3": g3, "P4": g4,
                        "P5": g5, "P6": g6, "P7": g7, "P8": g8,
                        "V_Rapida": g_vr
                    }
                    if salvar_palpite_github(ARQUIVO_GABARITOS, gabarito):
                        st.success("Resultado oficial salvo!")

            st.write("---")
            st.header("🗑️ Apagar Registros")
            df_limpeza, _ = ler_dados(ARQUIVO_DADOS)
            if not df_limpeza.empty:
                col_del_gp, col_del_sessao = st.columns(2)
                with col_del_gp: gp_del = st.selectbox("GP para excluir:", lista_gps, key="del_gp")
                with col_del_sessao: sessao_del = st.selectbox("Sessão para excluir:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"], key="del_sessao")
                
                palpites_filtrados = df_limpeza[(df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del)]
                
                if not palpites_filtrados.empty:
                    user_del = st.selectbox("Selecione o usuário para APAGAR:", [""] + sorted(palpites_filtrados['Usuario'].tolist()), key="del_user")
                    if user_del != "":
                        if st.button(f"CONFIRMAR EXCLUSÃO DE {user_del}", type="primary"):
                            mascara = ~((df_limpeza['GP'] == gp_del) & (df_limpeza['Tipo'] == sessao_del) & (df_limpeza['Usuario'] == user_del))
                            if deletar_registro_github(ARQUIVO_DADOS, mascara):
                                st.success("Registro removido!")
                                st.rerun()

if __name__ == "__main__":
    main()
