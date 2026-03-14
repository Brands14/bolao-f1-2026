import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import urllib.request
import urllib.error
import json
import base64
import io
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="F1 Fantasy Palpites 2026", layout="wide")

# CONFIGURAÇÕES
GITHUB_USER = "Brands14"
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Configurar GITHUB_TOKEN e SENHA_EMAIL no Streamlit.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv"
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

fuso_br = pytz.timezone('America/Sao_Paulo')

# PARTICIPANTES
participantes = [
"Alaerte Fleury","César Gaudie","Delvânia Belo","Emilio Jacinto",
"Fabrício Abe","Fausto Fleury","Fernanda Fleury","Flávio Soares",
"Frederico Gaudie","George Fleury","Henrique Junqueira","Hilton Jacinto",
"Jaime Gabriel","Luciano (Medalha)","Maikon Miranda","Myke Ribeiro",
"Rodolfo Brandão","Ronaldo Fleury","Syllas Araújo","Valério Bimbato"
]

# EQUIPES
equipes = {
"Equipe 1":["Fabrício Abe","Fausto Fleury"],
"Equipe 2":["Myke Ribeiro","Luciano (Medalha)"],
"Equipe 3":["César Gaudie","Ronaldo Fleury"],
"Equipe 4":["Valério Bimbato","Syllas Araújo"],
"Equipe 5":["Frederico Gaudie","Emilio Jacinto"],
"Equipe 6":["Fernanda Fleury","Henrique Junqueira"],
"Equipe 7":["Jaime Gabriel","Hilton Jacinto"],
"Equipe 8":["Delvânia Belo","Maikon Miranda"],
"Equipe 9":["Alaerte Fleury","Flávio Soares"],
"Equipe 10":["Rodolfo Brandão","George Fleury"]
}

# PILOTOS
pilotos = [
"",
"Max Verstappen","Lewis Hamilton","Charles Leclerc","George Russell",
"Lando Norris","Oscar Piastri","Fernando Alonso","Lance Stroll",
"Gabriel Bortoleto","Nico Hulkenberg","Alex Albon","Carlos Sainz",
"Pierre Gasly","Esteban Ocon","Valtteri Bottas","Sergio Perez",
"Nenhum / Outro"
]

lista_gps = [
"Austrália","China","Japão","Bahrein","Arábia Saudita","Miami",
"Emília-Romanha","Mônaco","Canadá","Espanha","Áustria","Reino Unido",
"Bélgica","Hungria","Holanda","Itália","Azerbaijão","Singapura",
"EUA (Austin)","México","Brasil","Las Vegas","Catar","Abu Dhabi"
]

# GITHUB DATABASE

def ler_dados(arquivo):

    url=f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"

    req=urllib.request.Request(url,headers={"Authorization":f"token {GITHUB_TOKEN}"})

    try:

        with urllib.request.urlopen(req) as response:

            data=json.loads(response.read().decode())

            content=base64.b64decode(data['content']).decode('utf-8')

            return pd.read_csv(io.StringIO(content)),data['sha']

    except:

        return pd.DataFrame(),None


def guardar_dados(dados,arquivo):

    df_atual,sha=ler_dados(arquivo)

    df_novo=pd.DataFrame([dados])

    if not df_atual.empty:

        mascara=~((df_atual['GP']==dados['GP'])&(df_atual['Tipo']==dados['Tipo'])&(df_atual['Usuario']==dados['Usuario']))

        df_atual=df_atual[mascara]

        df_final=pd.concat([df_atual,df_novo],ignore_index=True)

    else:

        df_final=df_novo

    csv=df_final.to_csv(index=False)

    encoded=base64.b64encode(csv.encode()).decode()

    url=f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"

    payload={"message":"Atualizando banco","content":encoded}

    if sha:

        payload["sha"]=sha

    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={
        "Authorization":f"token {GITHUB_TOKEN}",
        "Content-Type":"application/json"
    },method="PUT")

    urllib.request.urlopen(req)

# PONTUAÇÃO (ORIGINAL)

def check_ponto(palpite,gabarito,chave,pontos):

    if str(palpite.get(chave,''))==str(gabarito.get(chave,'')):

        return pontos

    return 0


def calcular_pontos_sessao(p,g):

    pontos=0

    if p["Tipo"]=="Corrida Principal":

        pontos+=check_ponto(p,g,"P1",150)
        pontos+=check_ponto(p,g,"P2",125)
        pontos+=check_ponto(p,g,"P3",100)
        pontos+=check_ponto(p,g,"P4",85)
        pontos+=check_ponto(p,g,"P5",70)

    return pontos

# API RESULTADOS F1

def resultados_f1():

    try:

        url="https://ergast.com/api/f1/current/last/results.json"

        data=requests.get(url).json()

        r=data["MRData"]["RaceTable"]["Races"][0]

        pilotos=r["Results"]

        lista=[]

        for p in pilotos[:10]:

            lista.append({
            "Posição":p["position"],
            "Piloto":p["Driver"]["givenName"]+" "+p["Driver"]["familyName"],
            "Equipe":p["Constructor"]["name"]
            })

        return pd.DataFrame(lista)

    except:

        return pd.DataFrame()

# INTERFACE NOVA

st.title("🏁 Fantasy F1 Palpites 2026")

abas=st.tabs([
"🏠 Dashboard",
"📊 Resultados F1",
"🎯 Enviar Palpite",
"📄 Meus Palpites",
"🏆 Classificação",
"⚙️ Admin"
])

# DASHBOARD

with abas[0]:

    st.header("Dashboard")

    df,_=ler_dados(ARQUIVO_DADOS)

    col1,col2,col3=st.columns(3)

    col1.metric("Participantes",len(participantes))
    col2.metric("Palpites enviados",len(df))
    col3.metric("GPs",len(lista_gps))

# RESULTADOS

with abas[1]:

    st.header("Última corrida F1")

    df=resultados_f1()

    st.dataframe(df)

# ENVIAR PALPITE

with abas[2]:

    st.header("Enviar Palpite")

    usuario=st.selectbox("Usuário",participantes)

    gp=st.selectbox("GP",lista_gps)

    p1=st.selectbox("P1",pilotos)
    p2=st.selectbox("P2",pilotos)
    p3=st.selectbox("P3",pilotos)

    if st.button("Salvar palpite"):

        dados={
        "Usuario":usuario,
        "GP":gp,
        "Tipo":"Corrida Principal",
        "P1":p1,
        "P2":p2,
        "P3":p3,
        "Data_Envio":datetime.now(fuso_br)
        }

        guardar_dados(dados,ARQUIVO_DADOS)

        st.success("Palpite registrado!")

# MEUS PALPITES

with abas[3]:

    st.header("Meus Palpites")

    df,_=ler_dados(ARQUIVO_DADOS)

    usuario=st.selectbox("Selecionar participante",participantes)

    st.dataframe(df[df["Usuario"]==usuario])

# CLASSIFICAÇÃO

with abas[4]:

    st.header("Ranking")

    palpites,_=ler_dados(ARQUIVO_DADOS)
    gabaritos,_=ler_dados(ARQUIVO_GABARITOS)

    ranking=[]

    for _,p in palpites.iterrows():

        g=gabaritos[(gabaritos["GP"]==p["GP"])]

        if not g.empty:

            pontos=calcular_pontos_sessao(p,g.iloc[0])

            ranking.append({"Usuario":p["Usuario"],"Pontos":pontos})

    df=pd.DataFrame(ranking)

    if not df.empty:

        tabela=df.groupby("Usuario").sum().sort_values("Pontos",ascending=False)

        st.dataframe(tabela)

# ADMIN

with abas[5]:

    st.header("Administrador")

    st.write("Área administrativa.")
