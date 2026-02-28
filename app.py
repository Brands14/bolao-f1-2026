import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# 1. Configurações Iniciais
st.set_page_config(page_title="Palpites F1 2026", layout="wide")
ARQUIVO_DADOS = "palpites_oficial_2026_v2.csv" # Nome novo para forçar um banco de dados limpo
ARQUIVO_GABARITOS = "gabaritos_oficial_2026_v2.csv"

try:
    st.image("WhatsApp Image 2026-02-24 at 16.12.18.jpeg", use_container_width=True)
except:
    st.title("🏁 Palpites F1 2026")

participantes = [
    "Alaerte Fleury", "César Gaudie", "Delvânia Belo", "Emilio Jacinto", 
    "Fabrício Abe", "Fausto Fleury", "Fernanda Fleury", "Flávio Soares", 
    "Frederico Gaudie", "George Fleury", "Henrique Junqueira", "Hilton Jacinto", 
    "Jaime Gabriel", "Luciano (Medalha)", "Maikon Miranda", "Myke Ribeiro", 
    "Rodolfo Brandão", "Ronaldo Fleury", "Syllas Araújo", "Valério Bimbato"
]

# DICIONÁRIO DE SEGURANÇA: Substitua pelos e-mails reais!
emails_autorizados = {
    "Alaerte Fleury": "alaerte@email.com",
    "César Gaudie": "cesar@email.com",
    "Delvânia Belo": "delvania@email.com",
    "Emilio Jacinto": "emilio@email.com",
    "Fabrício Abe": "fabricio@email.com",
    "Fausto Fleury": "fausto@email.com",
    "Fernanda Fleury": "fernanda@email.com",
    "Flávio Soares": "flavio@email.com",
    "Frederico Gaudie": "frederico@email.com",
    "George Fleury": "george@email.com",
    "Henrique Junqueira": "henrique@email.com",
    "Hilton Jacinto": "hilton@email.com",
    "Jaime Gabriel": "jaime@email.com",
    "Luciano (Medalha)": "luciano@email.com",
    "Maikon Miranda": "maikon@email.com",
    "Myke Ribeiro": "myke@email.com",
    "Rodolfo Brandão": "rodolfo@email.com",
    "Ronaldo Fleury": "ronaldo@email.com",
    "Syllas Araújo": "syllas@email.com",
    "Valério Bimbato": "valerio@email.com"
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

# 2. Funções de Dados e Pontuação Segura
def guardar_dados(dados, arquivo):
    df = pd.DataFrame([dados])
    if not os.path.exists(arquivo):
        df.to_csv(arquivo, index=False)
    else:
        df.to_csv(arquivo, mode='a', header=False, index=False)

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

# 3. Menu e Navegação
st.sidebar.header("Navegação")
menu = st.sidebar.radio("Ir para:", ["Enviar Palpite", "Classificações", "Administrador"])

# --- ÁREA: ENVIAR PALPITE ---
if menu == "Enviar Palpite":
    usuario_logado = st.sidebar.selectbox("Quem está a palpitar?", [""] + participantes)
    
    if usuario_logado:
        equipe_usuario = next((equipe for equipe, membros in equipes.items() if usuario_logado in membros), "Sem Equipe")
        st.write(f"Bem-vindo, **{usuario_logado}**! (🏎️ *{equipe_usuario}*)")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_selecionado = st.selectbox("Selecione o Grande Prêmio:", lista_gps)
            
        # Opções Dinâmicas de Sessão
        if gp_selecionado in sprint_gps:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"]
        else:
            opcoes_sessao = ["Classificação Principal (Pole)", "Corrida Principal"]
            
        with col_tipo:
            tipo_sessao = st.selectbox("Tipo de Sessão (Selecione a fase atual):", opcoes_sessao)
        
        st.header(f"🏁 GP: {gp_selecionado} - {tipo_sessao}")
        
        with st.form("form_palpite"):
            # Variáveis vazias por padrão
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            volta_rapida = primeiro_abandono = mais_ultrapassagens = ""
            
            # Renderiza apenas os campos necessários para a sessão escolhida
            if "Pole" in tipo_sessao:
                st.info("📌 Palpite apenas para a Pole Position desta sessão.")
                pole = st.selectbox("Pole Position:", pilotos)
                
            elif tipo_sessao == "Corrida Principal":
                st.info("📌 Palpite para a Corrida de Domingo (A Pole já deve ter sido enviada separadamente).")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                    p5 = st.selectbox("5º Colocado:", pilotos)
                with col2:
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    p9 = st.selectbox("9º Colocado:", pilotos)
                    p10 = st.selectbox("10º Colocado:", pilotos)
                    volta_rapida = st.selectbox("Melhor Volta:", pilotos)
                    primeiro_abandono = st.selectbox("1º Abandono:", pilotos)
                    mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos)
                    
            elif tipo_sessao == "Corrida Sprint":
                st.info("📌 Palpite para a Corrida Sprint (Top 8).")
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                with col2:
                    p5 = st.selectbox("5º Colocado:", pilotos)
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)

            st.divider()
            st.markdown("🔒 **Assinatura de Segurança**")
            email_confirmacao = st.text_input("Digite seu E-mail cadastrado para validar o palpite:", type="password")
            
            enviado = st.form_submit_button(f"Salvar Palpite - {tipo_sessao} 🏁")
            
            if enviado:
                email_correto = emails_autorizados.get(usuario_logado, "").strip().lower()
                email_digitado = email_confirmacao.strip().lower()
                
                if email_digitado == email_correto and email_correto != "":
                    dados = {
                        "Data_Envio": datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                        "GP": gp_selecionado, "Tipo": tipo_sessao, "Usuario": usuario_logado, "Equipe": equipe_usuario,
                        "Pole": pole, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5,
                        "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                        "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                    }
                    guardar_dados(dados, ARQUIVO_DADOS)
                    st.success(f"Autenticação confirmada! Palpite de {tipo_sessao} registrado com sucesso!")
                else:
                    st.error("🚫 Acesso Negado: O e-mail informado não corresponde ao usuário selecionado. O palpite NÃO foi salvo.")

    else:
        st.info("Selecione o seu nome no menu lateral para começar.")

# --- ÁREA: CLASSIFICAÇÕES ---
elif menu == "Classificações":
    st.header("🏆 Classificações do Campeonato F1 2026")
    
    if os.path.exists(ARQUIVO_DADOS) and os.path.exists(ARQUIVO_GABARITOS):
        df_palpites = pd.read_csv(ARQUIVO_DADOS)
        df_gabaritos = pd.read_csv(ARQUIVO_GABARITOS)
        
        resultados = []
        
        for index_p, row_p in df_palpites.iterrows():
            gp = row_p.get('GP', '')
            tipo = row_p.get('Tipo', '')
            
            gabarito_match = df_gabaritos[(df_gabaritos['GP'] == gp) & (df_gabaritos['Tipo'] == tipo)]
            
            if not gabarito_match.empty:
                gabarito_oficial = gabarito_match.iloc[-1]
                pontos = calcular_pontos_sessao(row_p, gabarito_oficial)
                resultados.append({"Usuario": row_p['Usuario'], "Equipe": row_p.get('Equipe', 'Sem Equipe'), "Pontos": pontos})
        
        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Mundial de Pilotos (Geral)")
                ranking_geral = df_resultados.groupby('Usuario')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_geral.index = range(1, len(ranking_geral) + 1)
                st.dataframe(ranking_geral, use_container_width=True)
                
            with col2:
                st.subheader("🏎️ Mundial de Construtores (Equipes)")
                ranking_equipas = df_resultados.groupby('Equipe')['Pontos'].sum().reset_index().sort_values(by='Pontos', ascending=False)
                ranking_equipas.index = range(1, len(ranking_equipas) + 1)
                st.dataframe(ranking_equipas, use_container_width=True)
        else:
            st.warning("Ainda não existem Gabaritos Oficiais para calcular as pontuações dos palpites inseridos.")
    else:
        st.warning("Aguardando inserção de palpites e Gabaritos Oficiais para gerar a classificação.")

# --- ÁREA: ADMINISTRADOR ---
elif menu == "Administrador":
    senha = st.sidebar.text_input("Senha de Diretor de Prova:", type="password")
    
    if senha == "fleury1475":
        st.warning("⚠️ MODO ADMINISTRADOR ATIVO")
        
        st.subheader("🕵️‍♂️ Auditoria: Palpites da Turma")
        if os.path.exists(ARQUIVO_DADOS):
            df_auditoria = pd.read_csv(ARQUIVO_DADOS)
            
            # NOVO FILTRO DE AUDITORIA
            filtro_gp = st.selectbox("Filtrar por Grande Prêmio:", ["Todos os GPs"] + lista_gps)
            if filtro_gp != "Todos os GPs":
                df_auditoria = df_auditoria[df_auditoria["GP"] == filtro_gp]
                
            st.dataframe(df_auditoria, use_container_width=True)
        else:
            st.info("Ainda não foram registrados palpites no sistema.")
            
        st.divider()
        st.header("🏆 Inserir Gabarito Oficial")
        
        col_gp, col_tipo = st.columns(2)
        with col_gp:
            gp_admin = st.selectbox("GP do Gabarito:", lista_gps)
            
        if gp_admin in sprint_gps:
            opcoes_admin = ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"]
        else:
            opcoes_admin = ["Classificação Principal (Pole)", "Corrida Principal"]
            
        with col_tipo:
            tipo_admin = st.selectbox("Sessão do Gabarito:", opcoes_admin)
        
        with st.form("form_gabarito"):
            pole = p1 = p2 = p3 = p4 = p5 = p6 = p7 = p8 = p9 = p10 = ""
            volta_rapida = primeiro_abandono = mais_ultrapassagens = ""
            
            if "Pole" in tipo_admin:
                pole = st.selectbox("Pole Position Oficial:", pilotos)
                
            elif tipo_admin == "Corrida Principal":
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                    p5 = st.selectbox("5º Colocado:", pilotos)
                with col2:
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    p9 = st.selectbox("9º Colocado:", pilotos)
                    p10 = st.selectbox("10º Colocado:", pilotos)
                    volta_rapida = st.selectbox("Melhor Volta:", pilotos)
                    primeiro_abandono = st.selectbox("1º Abandono:", pilotos)
                    mais_ultrapassagens = st.selectbox("Mais Ultrapassagens:", pilotos)
                    
            elif tipo_admin == "Corrida Sprint":
                col1, col2 = st.columns(2)
                with col1:
                    p1 = st.selectbox("1º Colocado:", pilotos)
                    p2 = st.selectbox("2º Colocado:", pilotos)
                    p3 = st.selectbox("3º Colocado:", pilotos)
                    p4 = st.selectbox("4º Colocado:", pilotos)
                with col2:
                    p5 = st.selectbox("5º Colocado:", pilotos)
                    p6 = st.selectbox("6º Colocado:", pilotos)
                    p7 = st.selectbox("7º Colocado:", pilotos)
                    p8 = st.selectbox("8º Colocado:", pilotos)
                    
            enviar_gabarito = st.form_submit_button(f"Submeter Gabarito Oficial - {tipo_admin} 🏆")
            if enviar_gabarito:
                dados_gabarito = {
                    "GP": gp_admin, "Tipo": tipo_admin, "Pole": pole, "P1": p1, "P2": p2, "P3": p3, 
                    "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8": p8, "P9": p9, "P10": p10,
                    "VoltaRapida": volta_rapida, "PrimeiroAbandono": primeiro_abandono, "MaisUltrapassagens": mais_ultrapassagens
                }
                guardar_dados(dados_gabarito, ARQUIVO_GABARITOS)
                st.success(f"Gabarito de {tipo_admin} salvo! As classificações foram atualizadas.")
                    
    elif senha != "":
        st.error("Senha incorreta.")
