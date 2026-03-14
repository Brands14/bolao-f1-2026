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
import plotly.express as px

st.set_page_config(page_title="F1 Fantasy Palpites 2026", layout="wide")

# CONFIGURAÇÕES
GITHUB_USER = "Brands14"
GITHUB_REPO = "bolao-f1-2026"
EMAIL_ADMIN = "palpitesf12026@gmail.com"

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    SENHA_EMAIL = st.secrets["SENHA_EMAIL"]
except:
    st.error("Chaves não encontradas.")
    st.stop()

ARQUIVO_DADOS = "palpites_permanentes_2026.csv"
ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

fuso_br = pytz.timezone("America/Sao_Paulo")

# ESTILO VISUAL FANTASY
st.markdown("""
<style>

body {
background-color:#0b0b0b;
color:white;
}

.stButton>button {
background-color:#e10600;
color:white;
border-radius:10px;
height:40px;
}

</style>
""", unsafe_allow_html=True)

# PILOTOS
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
"Sergio Pérez","Valtteri Bottas"
]

# CALENDÁRIO
lista_gps = [
"Austrália","China","Japão","Bahrein","Arábia Saudita",
"Miami","Emília-Romanha","Mônaco","Canadá",
"Espanha","Áustria","Reino Unido","Bélgica",
"Hungria","Holanda","Itália","Azerbaijão",
"Singapura","EUA (Austin)","México","Brasil",
"Las Vegas","Catar","Abu Dhabi"
]

sprint_gps = ["China","Miami","Canadá","Reino Unido","Holanda","Singapura"]

# PARTICIPANTES
participantes = [
"Alaerte Fleury","César Gaudie","Delvânia Belo",
"Emilio Jacinto","Fabrício Abe","Fausto Fleury",
"Fernanda Fleury","Flávio Soares","Frederico Gaudie",
"George Fleury","Henrique Junqueira","Hilton Jacinto",
"Jaime Gabriel","Luciano (Medalha)","Maikon Miranda",
"Myke Ribeiro","Rodolfo Brandão","Ronaldo Fleury",
"Syllas Araújo","Valério Bimbato"
]

# BANCO GITHUB
def ler_dados(arquivo):

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"

    req = urllib.request.Request(url,
        headers={"Authorization": f"token {GITHUB_TOKEN}"})

    try:
        with urllib.request.urlopen(req) as response:

            data = json.loads(response.read().decode())

            content = base64.b64decode(data['content']).decode('utf-8')

            return pd.read_csv(io.StringIO(content)), data['sha']

    except:
        return pd.DataFrame(), None


def guardar_dados(dados, arquivo):

    df_atual, sha = ler_dados(arquivo)

    df_novo = pd.DataFrame([dados])

    if not df_atual.empty:
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    csv_content = df_final.to_csv(index=False)

    encoded = base64.b64encode(csv_content.encode()).decode()

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{arquivo}"

    payload = {
        "message": "update",
        "content": encoded,
        "sha": sha
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )

    urllib.request.urlopen(req)

# PONTUAÇÃO (MESMA DO SEU CÓDIGO)
def check_ponto(palpite,gabarito,chave,valor):

    if str(palpite.get(chave)) == str(gabarito.get(chave)):
        return valor

    return 0


def calcular_pontos_sessao(palpite,gabarito):

    pontos=0

    tipo = palpite.get("Tipo")

    if "Pole" in tipo:
        pontos+=check_ponto(palpite,gabarito,"Pole",100)

    elif tipo=="Corrida Principal":

        pontos+=check_ponto(palpite,gabarito,"P1",150)
        pontos+=check_ponto(palpite,gabarito,"P2",125)
        pontos+=check_ponto(palpite,gabarito,"P3",100)
        pontos+=check_ponto(palpite,gabarito,"P4",85)
        pontos+=check_ponto(palpite,gabarito,"P5",70)
        pontos+=check_ponto(palpite,gabarito,"P6",60)
        pontos+=check_ponto(palpite,gabarito,"P7",50)
        pontos+=check_ponto(palpite,gabarito,"P8",40)
        pontos+=check_ponto(palpite,gabarito,"P9",25)
        pontos+=check_ponto(palpite,gabarito,"P10",15)

    return pontos


# MENU PRINCIPAL
menu = st.sidebar.radio(
"Menu",
[
"Dashboard",
"Pilotos",
"Corridas",
"Palpites",
"Meu Histórico",
"Classificação",
"Administrador"
]
)

# DASHBOARD
if menu=="Dashboard":

    st.title("🏁 F1 Fantasy 2026")

    df,_=ler_dados(ARQUIVO_DADOS)

    total_palpites=len(df)

    col1,col2,col3=st.columns(3)

    col1.metric("Palpites enviados",total_palpites)
    col2.metric("Participantes",len(participantes))
    col3.metric("GPs temporada",len(lista_gps))

    st.divider()

    st.subheader("Próxima corrida")

    st.info("GP de Abu Dhabi")

# PILOTOS
elif menu=="Pilotos":

    st.title("🏎️ Pilotos da Temporada")

    cols=st.columns(4)

    for i,p in enumerate(pilotos[1:]):

        with cols[i%4]:

            nome=p.replace(" ","%20")

            url=f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{nome}.png"

            st.image(url,width=120)

            st.write(p)

# CORRIDAS
elif menu=="Corridas":

    st.title("📅 Calendário F1")

    df=pd.DataFrame({"GP":lista_gps})

    st.dataframe(df,use_container_width=True)

# PALPITES
elif menu=="Palpites":

    usuario = st.selectbox("Quem é você?",participantes)

    gp=st.selectbox("GP",lista_gps)

    tipo=st.selectbox(
    "Sessão",
    ["Classificação Principal (Pole)","Corrida Principal"]
    )

    if "Pole" in tipo:

        pole=st.selectbox("Pole",pilotos)

    if tipo=="Corrida Principal":

        p1=st.selectbox("P1",pilotos)
        p2=st.selectbox("P2",pilotos)
        p3=st.selectbox("P3",pilotos)
        p4=st.selectbox("P4",pilotos)
        p5=st.selectbox("P5",pilotos)
        p6=st.selectbox("P6",pilotos)
        p7=st.selectbox("P7",pilotos)
        p8=st.selectbox("P8",pilotos)
        p9=st.selectbox("P9",pilotos)
        p10=st.selectbox("P10",pilotos)

    if st.button("Enviar Palpite"):

        dados={
        "Data":datetime.now(fuso_br),
        "Usuario":usuario,
        "GP":gp,
        "Tipo":tipo,
        "Pole":pole if "Pole" in tipo else "",
        "P1":p1 if tipo=="Corrida Principal" else "",
        "P2":p2 if tipo=="Corrida Principal" else "",
        "P3":p3 if tipo=="Corrida Principal" else "",
        "P4":p4 if tipo=="Corrida Principal" else "",
        "P5":p5 if tipo=="Corrida Principal" else "",
        "P6":p6 if tipo=="Corrida Principal" else "",
        "P7":p7 if tipo=="Corrida Principal" else "",
        "P8":p8 if tipo=="Corrida Principal" else "",
        "P9":p9 if tipo=="Corrida Principal" else "",
        "P10":p10 if tipo=="Corrida Principal" else ""
        }

        guardar_dados(dados,ARQUIVO_DADOS)

        st.success("Palpite salvo!")

# HISTÓRICO
elif menu=="Meu Histórico":

    usuario=st.selectbox("Seu nome",participantes)

    df,_=ler_dados(ARQUIVO_DADOS)

    if not df.empty:

        st.dataframe(df[df["Usuario"]==usuario])

# CLASSIFICAÇÃO
elif menu=="Classificação":

    st.title("🏆 Ranking")

    df_p,_=ler_dados(ARQUIVO_DADOS)
    df_g,_=ler_dados(ARQUIVO_GABARITOS)

    if not df_p.empty and not df_g.empty:

        lista=[]

        for _,p in df_p.iterrows():

            g=df_g[
            (df_g["GP"]==p["GP"]) &
            (df_g["Tipo"]==p["Tipo"])
            ]

            if not g.empty:

                pontos=calcular_pontos_sessao(p,g.iloc[0])

                lista.append(
                {"Usuario":p["Usuario"],"Pontos":pontos}
                )

        df=pd.DataFrame(lista)

        ranking=df.groupby("Usuario").sum().sort_values(
        "Pontos",ascending=False
        )

        st.dataframe(ranking)

        fig=px.bar(ranking,x=ranking.index,y="Pontos")

        st.plotly_chart(fig,use_container_width=True)

# ADMIN
elif menu=="Administrador":

    senha=st.text_input("Senha",type="password")

    if senha=="fleury1475":

        st.success("Modo administrador")

        st.write("Inserir gabarito")

        gp=st.selectbox("GP",lista_gps)

        pole=st.selectbox("Pole",pilotos)

        if st.button("Salvar gabarito"):

            dados={
            "GP":gp,
            "Tipo":"Classificação Principal (Pole)",
            "Pole":pole
            }

            guardar_dados(dados,ARQUIVO_GABARITOS)

            st.success("Gabarito salvo")
