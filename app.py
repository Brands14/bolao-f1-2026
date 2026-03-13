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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Palpites F1 2026", layout="wide")

GITHUB_USER = "Brands14"
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

# ==============================
# SISTEMA DE FOTOS DOS PILOTOS
# ==============================

URL_FOTOS = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos"

def seletor_piloto(label, lista, key):
    col1, col2 = st.columns([3,1])

    with col1:
        piloto = st.selectbox(label, lista, key=key)

    with col2:
        if piloto and piloto != "Nenhum / Outro":
            nome = piloto.replace(" ", "%20") + ".png"
            url = f"{URL_FOTOS}/{nome}"
            try:
                st.image(url, width=100)
            except:
                pass

    return piloto

# ==============================

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Chaves de segurança não encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv"
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

st.title("🏁 Palpites F1 2026")

participantes = [
"Alaerte Fleury","César Gaudie","Delvânia Belo","Emilio Jacinto",
"Fabrício Abe","Fausto Fleury","Fernanda Fleury","Flávio Soares",
"Frederico Gaudie","George Fleury","Henrique Junqueira","Hilton Jacinto",
"Jaime Gabriel","Luciano (Medalha)","Maikon Miranda","Myke Ribeiro",
"Rodolfo Brandão","Ronaldo Fleury","Syllas Araújo","Valério Bimbato"
]

pilotos = [
"",
"Max Verstappen","Isack Hadjar",
"Lewis Hamilton","Charles Leclerc",
"George Russell","Kimi Antonelli",
"Lando Norris","Oscar Piastri",
"Fernando Alonso","Lance Stroll",
"Gabriel Bortoleto","Nico Hülkenberg",
"Alex Albon","Carlos Sainz",
"Pierre Gasly","Franco Colapinto",
"Oliver Bearman","Esteban Ocon",
"Liam Lawson","Arvid Lindblad",
"Sergio Pérez","Valtteri Bottas",
"Nenhum / Outro"
]

lista_gps = [
"Austrália","China","Japão","Bahrein","Arábia Saudita","Miami",
"Emília-Romanha","Mônaco","Canadá","Espanha","Áustria","Reino Unido",
"Bélgica","Hungria","Holanda","Itália","Azerbaijão","Singapura",
"EUA (Austin)","México","Brasil","Las Vegas","Catar","Abu Dhabi"
]

sprint_gps = ["China","Miami","Canadá","Reino Unido","Holanda","Singapura"]

fuso_br = pytz.timezone('America/Sao_Paulo')

# ==============================
# BANCO GITHUB
# ==============================

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

        if 'Usuario' in dados:

            mascara=~((df_atual['GP']==dados['GP'])&(df_atual['Tipo']==dados['Tipo'])&(df_atual['Usuario']==dados['Usuario']))

        else:

            mascara=~((df_atual['GP']==dados['GP'])&(df_atual['Tipo']==dados['Tipo']))

        df_atual=df_atual[mascara]

        df_final=pd.concat([df_atual,df_novo],ignore_index=True)

    else:

        df_final=df_novo

    csv=df_final.to_csv(index=False)

    encoded=base64.b64encode(csv.encode()).decode()

    url=f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"

    payload={"message":"update","content":encoded}

    if sha:
        payload["sha"]=sha

    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={
        "Authorization":f"token {GITHUB_TOKEN}",
        "Content-Type":"application/json"
    },method="PUT")

    try:
        with urllib.request.urlopen(req) as response:
            return True
    except:
        return False


# ==============================
# MENU
# ==============================

st.sidebar.header("Navegação")

menu=st.sidebar.radio("Ir para",[
"Enviar Palpite",
"Classificações"
])


# ==============================
# ENVIAR PALPITE
# ==============================

if menu=="Enviar Palpite":

    usuario=st.sidebar.selectbox("Quem está a palpitar?",[""]+participantes)

    if usuario:

        gp=st.selectbox("Grande Prêmio",lista_gps)

        if gp in sprint_gps:
            tipos=["Classificação Principal (Pole)","Corrida Principal","Qualy Sprint (Pole)","Corrida Sprint"]
        else:
            tipos=["Classificação Principal (Pole)","Corrida Principal"]

        tipo=st.selectbox("Sessão",tipos)

        st.header(f"{gp} - {tipo}")

        with st.form("palpite"):

            pole=""
            p1=p2=p3=p4=p5=p6=p7=p8=p9=p10=""
            vr=""
            abandono=""
            ultrap=""

            if "Pole" in tipo:

                pole=seletor_piloto("Pole Position",pilotos,"pole")

            elif tipo=="Corrida Principal":

                st.subheader("Top 10")

                col1,col2=st.columns(2)

                with col1:

                    p1=seletor_piloto("1º",pilotos,"p1")
                    p2=seletor_piloto("2º",pilotos,"p2")
                    p3=seletor_piloto("3º",pilotos,"p3")
                    p4=seletor_piloto("4º",pilotos,"p4")
                    p5=seletor_piloto("5º",pilotos,"p5")

                with col2:

                    p6=seletor_piloto("6º",pilotos,"p6")
                    p7=seletor_piloto("7º",pilotos,"p7")
                    p8=seletor_piloto("8º",pilotos,"p8")
                    p9=seletor_piloto("9º",pilotos,"p9")
                    p10=seletor_piloto("10º",pilotos,"p10")

                    vr=seletor_piloto("Melhor Volta",pilotos,"vr")

                    abandono=seletor_piloto("1º Abandono",pilotos,"ab")

                    ultrap=seletor_piloto("Mais Ultrapassagens",pilotos,"ul")

            elif tipo=="Corrida Sprint":

                p1=seletor_piloto("1º",pilotos,"sp1")
                p2=seletor_piloto("2º",pilotos,"sp2")
                p3=seletor_piloto("3º",pilotos,"sp3")
                p4=seletor_piloto("4º",pilotos,"sp4")
                p5=seletor_piloto("5º",pilotos,"sp5")
                p6=seletor_piloto("6º",pilotos,"sp6")
                p7=seletor_piloto("7º",pilotos,"sp7")
                p8=seletor_piloto("8º",pilotos,"sp8")

            enviar=st.form_submit_button("Salvar Palpite")

            if enviar:

                dados={
                "Data_Envio":datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S'),
                "GP":gp,
                "Tipo":tipo,
                "Usuario":usuario,
                "Pole":pole,
                "P1":p1,"P2":p2,"P3":p3,"P4":p4,"P5":p5,
                "P6":p6,"P7":p7,"P8":p8,"P9":p9,"P10":p10,
                "VoltaRapida":vr,
                "PrimeiroAbandono":abandono,
                "MaisUltrapassagens":ultrap
                }

                if guardar_dados(dados,ARQUIVO_DADOS):

                    st.success("Palpite salvo com sucesso!")

                else:

                    st.error("Erro ao salvar")


# ==============================
# CLASSIFICAÇÃO
# ==============================

elif menu=="Classificações":

    st.header("Classificação")

    df,_=ler_dados(ARQUIVO_DADOS)

    if not df.empty:

        ranking=df.groupby("Usuario").size().reset_index(name="Palpites")

        ranking=ranking.sort_values("Palpites",ascending=False)

        ranking.index=ranking.index+1

        st.dataframe(ranking,use_container_width=True)

    else:

        st.info("Sem dados ainda.")
