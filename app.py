"""Bolão F1 2026. Execute: streamlit run app.py.
Mantém as assinaturas públicas, os cadastros, os CSVs e as regras originais.
"""
import base64
import hmac
import io
import inspect
import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from urllib.parse import quote

import pandas as pd
import pytz
import streamlit as st

logger = logging.getLogger(__name__)

GITHUB_USER = "Brands14"

GITHUB_REPO = "bolao-f1-2026"

EMAIL_ADMIN = "palpitesf12026@gmail.com"

# Bancada de testes: todos os e-mails ficam somente com o administrador.
# Manter ativo até a liberação explícita da plataforma para os palpiteiros.
BLOQUEAR_EMAILS_PALPITEIROS = True

ARQUIVO_DADOS = "palpites_permanentes_2026.csv"

ARQUIVO_GABARITOS = "gabaritos_permanentes_2026.csv"

ARQUIVO_HISTORICO = "historico_alteracoes_2026.csv"

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
    "Oliver Bearman", "Ryo Hirakawa", "Rafael Câmara", "Esteban Ocon",
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

SENHA_ADMIN_LEGADA = 'fleury1475'
fuso_br = pytz.timezone('America/Sao_Paulo')
URL_VIDEO_GITHUB = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/f1_bg_2026.mp4"
EQUIPE_POR_USUARIO = {membro: equipe for equipe, membros in equipes.items() for membro in membros}
# Atualização do grid solicitada pelo organizador; nomes antigos continuam no histórico.
PILOTOS_INATIVOS = {'Esteban Ocon'}
EQUIPES_PILOTOS = {'Oliver Bearman', 'Ryo Hirakawa', 'Rafael Câmara'}
INDICE_PILOTOS = {nome: i for i, nome in enumerate(pilotos)}
CAMPOS_PALPITE = ['Pole'] + [f'P{i}' for i in range(1, 11)] + [
    'VoltaRapida', 'PrimeiroAbandono', 'MaisUltrapassagens']
SESSOES = ['Classificação Principal (Pole)', 'Corrida Principal', 'Qualy Sprint (Pole)', 'Corrida Sprint']
PONTOS_PRINCIPAL = dict(zip([f'P{i}' for i in range(1, 11)], [150,125,100,85,70,60,50,40,25,15]))
PONTOS_PRINCIPAL.update(VoltaRapida=75, PrimeiroAbandono=200, MaisUltrapassagens=75)
PONTOS_SPRINT = dict(zip([f'P{i}' for i in range(1, 9)], [80,70,60,50,40,30,20,10]))
ROTULOS = {'Pole': 'Pole position', 'VoltaRapida': 'Melhor volta',
           'PrimeiroAbandono': '1º abandono', 'MaisUltrapassagens': 'Mais ultrapassagens'}
ROTULOS.update({f'P{i}': f'{i}º colocado' for i in range(1,11)})


def _tem_arquivo_secrets():
    from pathlib import Path
    try:
        caminhos = st.get_option('secrets.files')
    except (RuntimeError, KeyError):
        # Streamlit antigo não possui a opção secrets.files.
        caminhos = [Path.home() / '.streamlit' / 'secrets.toml',
                    Path.cwd() / '.streamlit' / 'secrets.toml']
    return any(Path(caminho).expanduser().exists() for caminho in (caminhos or []))


def configuracao(nome, padrao=None):
    valor = os.environ.get(nome)
    if valor:
        return valor
    # Versões antigas desenham st.error antes de lançar a exceção. Não basta capturá-la:
    # só consultar st.secrets se houver um arquivo (ou diretório configurado) disponível.
    if not _tem_arquivo_secrets():
        return padrao
    try:
        return st.secrets.get(nome, padrao)
    except (FileNotFoundError, getattr(st.errors, 'StreamlitSecretNotFoundError', FileNotFoundError)):
        return padrao


GITHUB_TOKEN = configuracao('GITHUB_TOKEN')
SENHA_EMAIL = configuracao('SENHA_EMAIL')
BREVO_API_KEY = configuracao('BREVO_API_KEY')
EMAIL_REMETENTE = configuracao('EMAIL_REMETENTE',EMAIL_ADMIN)
NOME_REMETENTE = configuracao('NOME_REMETENTE','Palpiteiros F1')


def _url_arquivo(arquivo):
    return f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{quote(arquivo, safe="/")}'


def _headers():
    return {'Authorization': f'token {GITHUB_TOKEN}', 'Content-Type': 'application/json',
            'User-Agent': 'BolaoF1-App', 'Accept': 'application/vnd.github+json'}


def _ler_dados_remotos(arquivo):
    """Leitura fresca para escritas: falhas de acesso não são tratadas como CSV vazio."""
    req = urllib.request.Request(_url_arquivo(arquivo), headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return pd.DataFrame(), None
        raise
    if arquivo == ARQUIVO_FOTOS and data.get('encoding') == 'none':
        # O endpoint de conteúdo omite os bytes acima de 1 MB. Ler pelo SHA
        # preserva a mesma versão usada no controle de alterações concorrentes.
        sha = data['sha']
        import re
        if not re.fullmatch(r'[0-9a-fA-F]{40}',sha):
            raise ValueError('Identificador inválido no cadastro de fotos.')
        req = urllib.request.Request(f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/git/blobs/{sha}',headers=_headers())
        with urllib.request.urlopen(req,timeout=15) as response:
            blob = json.loads(response.read().decode())
        if blob.get('sha') != sha or blob.get('encoding') != 'base64':
            raise ValueError('Não foi possível validar a versão do cadastro de fotos.')
        data['content'] = blob['content']
    conteudo = base64.b64decode(data['content']).decode('utf-8-sig')
    try:
        df = pd.read_csv(io.StringIO(conteudo))
    except pd.errors.EmptyDataError:
        df = pd.DataFrame()
    return df, data['sha']


@st.cache_data(ttl=20, max_entries=8, show_spinner=False)
def _ler_dados_cache(arquivo):
    return _ler_dados_remotos(arquivo)


def ler_dados(arquivo):
    return _ler_dados_cache(arquivo)


def _escrever_csv(arquivo, df, sha, mensagem):
    payload = {'message': mensagem, 'content': base64.b64encode(df.to_csv(index=False).encode()).decode()}
    if sha:
        payload['sha'] = sha
    req = urllib.request.Request(_url_arquivo(arquivo), data=json.dumps(payload).encode(),
                                 headers=_headers(), method='PUT')
    with urllib.request.urlopen(req, timeout=15) as response:
        sucesso = response.status in (200, 201)
    if sucesso:
        _ler_dados_cache.clear()
    return sucesso


def _atualizar_csv(arquivo, transformar, mensagem):
    """Em conflito de SHA, relê e reaplica a operação sobre a versão mais nova."""
    for tentativa in range(3):
        df, sha = _ler_dados_remotos(arquivo)
        novo_df, contexto = transformar(df)
        try:
            return _escrever_csv(arquivo, novo_df, sha, mensagem), contexto
        except urllib.error.HTTPError as exc:
            if exc.code != 409 or tentativa == 2:
                raise
    raise RuntimeError('Não foi possível concluir a atualização concorrente.')


def _mascara_registro(df, dados):
    chaves = ['GP', 'Tipo'] + (['Usuario'] if 'Usuario' in dados else [])
    return df[chaves].eq(pd.Series({chave: dados[chave] for chave in chaves})).all(axis=1)


def registrar_historico(usuario, gp, tipo, acao):
    agora = datetime.now(fuso_br)
    registro = {'Data_Hora': agora.strftime('%d/%m/%Y %H:%M:%S'), 'Usuario': usuario,
                'GP': gp, 'Tipo': tipo,
                'Mensagem': f'O participante {usuario} {acao} seu palpite no GP de {gp} ({tipo}) às {agora:%H:%M:%S} de {agora:%d/%m/%Y}.'}
    def adicionar(df):
        return pd.concat([df, pd.DataFrame([registro])], ignore_index=True), None
    try:
        ok, _ = _atualizar_csv(ARQUIVO_HISTORICO, adicionar, f'Log de histórico: {usuario} - {gp}')
        if not ok:
            st.warning('Palpite salvo, mas o histórico não pôde ser atualizado.')
    except Exception:
        logger.exception('Falha ao registrar histórico')
        st.warning('Palpite salvo, mas o histórico não pôde ser atualizado.')


def guardar_dados(novos_dados, nome_arquivo, eh_edicao_admin=False):
    def substituir(df):
        if nome_arquivo==ARQUIVO_DADOS and 'Usuario' in novos_dados and not eh_edicao_admin:
            _validar_gravacao_palpite(novos_dados)
        mascara = _mascara_registro(df, novos_dados) if not df.empty else pd.Series(False, index=df.index)
        alteracao = bool(mascara.any()) and 'Usuario' in novos_dados
        return pd.concat([df.loc[~mascara], pd.DataFrame([novos_dados])], ignore_index=True), alteracao
    mensagem = (f"Atualizado palpite: {novos_dados['Usuario']} - {novos_dados['GP']} ({novos_dados['Tipo']})"
                if 'Usuario' in novos_dados else
                f"Atualizado Gabarito: {novos_dados.get('GP', 'Oficial')} ({novos_dados.get('Tipo', '')})")
    try:
        sucesso, alteracao = _atualizar_csv(nome_arquivo, substituir, mensagem)
    except PalpiteBloqueadoError as erro:
        st.error(str(erro))
        return False
    except Exception:
        logger.exception('Falha ao salvar CSV')
        st.error('Não foi possível salvar no GitHub. Confira a conexão e as permissões e tente novamente.')
        return False
    if sucesso and 'Usuario' in novos_dados:
        acao = 'alterou (pelo Admin)' if eh_edicao_admin else ('alterou' if alteracao else 'enviou')
        registrar_historico(novos_dados['Usuario'], novos_dados['GP'], novos_dados['Tipo'], acao)
    return sucesso


def deletar_registro_github(arquivo, mascara_filtro):
    """Mantém a máscara de retenção da API original; recusa máscaras obsoletas."""
    try:
        _, snapshot_sha = ler_dados(arquivo)
        atual, sha = _ler_dados_remotos(arquivo)
        if atual.empty or sha != snapshot_sha or len(mascara_filtro) != len(atual):
            st.warning('Os dados mudaram. Atualize a tela antes de excluir.')
            _ler_dados_cache.clear()
            return False
        if isinstance(mascara_filtro, pd.Series) and not mascara_filtro.index.equals(atual.index):
            return False
        return _escrever_csv(arquivo, atual.loc[mascara_filtro], sha, f'Removendo registro: {arquivo}')
    except Exception:
        logger.exception('Falha ao excluir registro')
        st.error('Não foi possível excluir. Atualize os dados e tente novamente.')
        return False


def campos_sessao(tipo):
    if 'Pole' in tipo:
        return ['Pole']
    if tipo == 'Corrida Principal':
        return list(PONTOS_PRINCIPAL)
    if tipo == 'Corrida Sprint':
        return list(PONTOS_SPRINT)
    return []


def montar_recibo_email(dados):
    campos = campos_sessao(dados['Tipo'])
    corpo = (f"Olá {dados['Usuario']},\n\nSeu palpite foi registrado/atualizado com sucesso no Bolão F1 2026!\n\n"
             f"--- REGISTRO OFICIAL ---\nGrande Prêmio: {dados['GP']}\nSessão: {dados['Tipo']}\n"
             f"Data/Hora do Envio: {dados['Data_Envio']}\n\n--- DETALHES DO SEU PALPITE ---\n")
    corpo += '\n'.join(f'{ROTULOS[campo]}: {dados.get(campo, "")}' for campo in campos)
    corpo += '\n\nDireção de Prova — Bolão F1 2026'
    linhas = ''.join(f'<tr><td style="padding:10px;border-bottom:1px solid #ddd;color:#555">{escape(ROTULOS[campo])}</td><td style="padding:10px;border-bottom:1px solid #ddd"><b>{escape(str(dados.get(campo,"")))}</b></td></tr>' for campo in campos)
    html = f'''<!doctype html><html lang="pt-BR"><body style="margin:0;background:#eef1f5;font-family:Arial,sans-serif;color:#172033"><table role="presentation" width="100%"><tr><td align="center" style="padding:24px 12px"><table role="presentation" width="100%" style="max-width:600px;background:white;border-collapse:collapse"><tr><td style="padding:24px;background:#111c2d;color:white;border-top:5px solid #ff463e"><b style="font-size:23px">PALPITES F1</b><br><span style="font-size:12px;color:#c1cfdf">SEU PALPITE. SUA DISPUTA.</span></td></tr><tr><td style="padding:24px"><h1 style="font-size:23px">Palpite confirmado! 🏁</h1><p>Olá, {escape(str(dados['Usuario']))}! Seu palpite foi registrado/atualizado com sucesso.</p><p><b>GP:</b> {escape(str(dados['GP']))}<br><b>Sessão:</b> {escape(str(dados['Tipo']))}<br><b>Data/hora:</b> {escape(str(dados['Data_Envio']))} (Brasília)</p><table width="100%" style="border-collapse:collapse;font-size:14px">{linhas}</table><p style="font-size:12px;color:#657085;margin-top:24px">Confira a versão mais recente em Meus Palpites. Cada nova alteração gera outro comprovante.</p><p style="font-size:12px;color:#657085">Direção de Prova — Bolão F1 2026</p></td></tr></table></td></tr></table></body></html>'''
    return corpo, html


def _endereco_email_simples(valor):
    import re
    return isinstance(valor,str) and bool(re.fullmatch(r'[^\s@<>,;]+@[^\s@<>,;]+\.[^\s@<>,;]+',valor))


def destinatario_email(email_destino):
    return EMAIL_ADMIN if BLOQUEAR_EMAILS_PALPITEIROS else email_destino


def _enviar_email_brevo(assunto,texto,html,email_destino,copia_admin=True):
    email_destino = destinatario_email(email_destino)
    if not BREVO_API_KEY or not _endereco_email_simples(email_destino) or not _endereco_email_simples(EMAIL_REMETENTE):
        logger.warning('E-mail Brevo não enviado: configuração ou endereço inválido.')
        return False
    payload = {'sender':{'name':NOME_REMETENTE,'email':EMAIL_REMETENTE},
               'to':[{'email':email_destino}], 'subject':assunto,
               'textContent':texto, 'htmlContent':html,
               'replyTo':{'email':EMAIL_REMETENTE,'name':NOME_REMETENTE},
               'tags':['bolao-f1-recibo']}
    if copia_admin and email_destino.casefold()!=EMAIL_ADMIN.casefold():
        payload['bcc'] = [{'email':EMAIL_ADMIN}]
    req = urllib.request.Request('https://api.brevo.com/v3/smtp/email',
        data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),method='POST',
        headers={'api-key':BREVO_API_KEY,'Content-Type':'application/json','Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            resultado = json.loads(response.read(65536).decode('utf-8'))
            aceito = response.status==201 and isinstance(resultado,dict) and bool(resultado.get('messageId'))
        if not aceito:
            logger.warning('Brevo não confirmou a aceitação da mensagem.')
        return aceito
    except urllib.error.HTTPError as erro:
        # Não registrar corpo/headers: podem conter endereços ou credenciais.
        logger.warning('Brevo recusou a mensagem (HTTP %s). Confira remetente, chave, ativação e créditos no provedor.',erro.code)
    except (urllib.error.URLError,OSError,TimeoutError,ValueError,TypeError,AttributeError):
        logger.warning('Não foi possível confirmar o envio ao Brevo. Confira os logs transacionais antes de repetir.')
    # Sem retry ou fallback SMTP: um timeout pode ocorrer depois da aceitação e duplicar o recibo.
    return False


def enviar_recibo_email(dados, email_destino):
    if BREVO_API_KEY:
        texto, html = montar_recibo_email(dados)
        assunto = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
        return _enviar_email_brevo(assunto,texto,html,email_destino)
    return _enviar_recibo_smtp(dados,email_destino)


def enviar_email_teste():
    quando = agora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    texto = f'Teste dos Palpiteiros F1 realizado em {quando} (Brasília).\nEste é um teste de e-mail. Nenhum palpite foi criado ou alterado.'
    html = f'<html lang="pt-BR"><body style="font-family:Arial,sans-serif"><h1>🏁 Palpites F1 — teste de e-mail</h1><p>{escape(texto).replace(chr(10),"<br>")}</p></body></html>'
    return _enviar_email_brevo('🏁 Palpites F1 — teste de confirmação',texto,html,EMAIL_ADMIN,copia_admin=False)


def painel_teste_email():
    with st.expander('✉️ Comprovantes por e-mail — configuração e teste'):
        if not BREVO_API_KEY:
            st.info('Para usar no Render gratuito, configure BREVO_API_KEY e verifique o remetente na sua conta Brevo. A chave é cadastrada nas variáveis de ambiente do Render.')
            return
        st.caption(f'Brevo configurado · remetente: {EMAIL_REMETENTE}')
        st.write(f'O teste será enviado somente para {EMAIL_ADMIN}. Ele não grava palpites.')
        st.caption('O provedor precisa aceitar o remetente e liberar os envios transacionais. Aceitação pela API não garante chegada à caixa de entrada: confira também spam e os logs do Brevo.')
        if st.button('Enviar e-mail de teste',key='enviar_teste_brevo'):
            from time import monotonic
            agora = monotonic()
            if agora-st.session_state.get('email_teste_ultimo',-60)<60:
                st.info('Aguarde um minuto antes de realizar outro teste.')
                return
            st.session_state['email_teste_ultimo'] = agora
            with st.spinner('Enviando teste…'):
                sucesso = enviar_email_teste()
            if sucesso:
                st.success('Teste aceito pelo Brevo! Confira a caixa de entrada e o spam do e-mail do bolão.')
            else:
                st.error('Não foi possível confirmar o envio. Confira os logs do Brevo, o remetente verificado, a chave da API e a liberação dos envios transacionais antes de tentar novamente.')


def _enviar_recibo_smtp(dados, email_destino):
    email_destino = destinatario_email(email_destino)
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADMIN
    msg['To'] = ', '.join([EMAIL_ADMIN] if email_destino.casefold()==EMAIL_ADMIN.casefold() else [EMAIL_ADMIN,email_destino])
    msg['Subject'] = f"🏁 Recibo de Palpite F1 - {dados['Usuario']} - GP {dados['GP']} ({dados['Tipo']})"
    corpo = (f"Olá {dados['Usuario']},\n\nSeu palpite foi registrado/atualizado com sucesso no Bolão F1 2026!\n\n"
             f"--- REGISTRO OFICIAL ---\nGrande Prêmio: {dados['GP']}\nSessão: {dados['Tipo']}\n"
             f"Data/Hora do Envio: {dados['Data_Envio']}\n\n--- DETALHES DO SEU PALPITE ---\n")
    corpo += '\n'.join(f'{ROTULOS[campo]}: {dados.get(campo, "")}' for campo in campos_sessao(dados['Tipo']))
    msg.attach(MIMEText(corpo + '\n\nDireção de Prova — Bolão F1 2026', 'plain', 'utf-8'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
            server.starttls()
            server.login(EMAIL_ADMIN, SENHA_EMAIL)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception('Falha ao enviar recibo')
        return False


# Apuração por e-mail: o mesmo cálculo oficial, sem alterar palpites ou gabaritos.
ARQUIVO_EMAIL_APURACOES = 'envios_apuracao_2026.csv'
COLUNAS_EMAIL_APURACOES = ['Id','Usuario','GP','Email','Revisao','Estado','Total_GP','Parcial','Reservado_em','Atualizado_em']


def _texto_apuracao(valor):
    return '—' if pd.isna(valor) or not str(valor).strip() else str(valor).strip()


def detalhar_apuracao_gp(palpites,gabaritos,usuario,gp):
    """Snapshot serializável; pontos por campo e bônus usam as funções oficiais."""
    p = palpites.loc[(palpites['Usuario']==usuario)&(palpites['GP']==gp)] if not palpites.empty else pd.DataFrame()
    g = gabaritos.loc[gabaritos['GP']==gp] if not gabaritos.empty else pd.DataFrame()
    indice_p = {r['Tipo']:r for r in p.drop_duplicates(['Tipo'],keep='last').to_dict('records')} if not p.empty else {}
    indice_g = {r['Tipo']:r for r in g.drop_duplicates(['Tipo'],keep='last').to_dict('records')} if not g.empty else {}
    esperadas = sessoes_disponiveis(gp)
    ordem = ['Qualy Sprint (Pole)','Corrida Sprint','Classificação Principal (Pole)','Corrida Principal']
    tipos = [tipo for tipo in ordem if tipo in esperadas or tipo in indice_g or tipo in indice_p]
    sessoes = []; pendentes = []; total = 0; legados = False
    for tipo in tipos:
        palpite = indice_p.get(tipo,{'Tipo':tipo})
        real = indice_g.get(tipo)
        linhas = []; campos = campos_sessao(tipo)
        pesos = {'Pole':100} if 'Pole' in tipo else PONTOS_PRINCIPAL if tipo=='Corrida Principal' else PONTOS_SPRINT
        if real is None:
            pendentes.append(tipo)
        for campo in campos:
            escolhido = _texto_apuracao(palpite.get(campo,''))
            resultado = _texto_apuracao(real.get(campo,'')) if real is not None else '—'
            pontos = int(check_ponto(palpite,real,campo,pesos[campo])) if real is not None else None
            if real is None:
                estado = 'Aguardando resultado'
            elif pontos and (escolhido=='—' or resultado=='—'):
                estado = 'Regra legada de valor ausente';legados = True
            elif pontos:
                estado = 'Acerto'
            elif escolhido=='—':
                estado = 'Sem palpite'
            elif resultado=='—':
                estado = 'Resultado não informado'
            else:
                estado = 'Não acertou'
            if real is not None and resultado=='—' and tipo not in pendentes:
                pendentes.append(tipo)
            linhas.append({'campo':campo,'rotulo':ROTULOS[campo],'palpite':escolhido,'resultado':resultado,'pontos':pontos,'estado':estado})
        bonus = int(_bonus_principal(palpite,real)) if real is not None and tipo=='Corrida Principal' else 0
        subtotal = int(calcular_pontos_sessao(palpite,real)) if real is not None else 0
        if real is not None and sum(l['pontos'] for l in linhas)+bonus!=subtotal:
            raise ValueError('Detalhamento divergente da pontuação oficial.')
        total += subtotal
        sessoes.append({'tipo':tipo,'homologada':real is not None,'enviado':tipo in indice_p,
                        'linhas':linhas,'bonus':bonus,'subtotal':subtotal})
    return {'usuario':str(usuario),'gp':str(gp),'sessoes':sessoes,'total':total,
            'parcial':bool(pendentes),'pendentes':pendentes,'regra_legada':legados,
            'corrida_homologada':'Corrida Principal' in indice_g}


def montar_email_apuracao(relatorio,atualizacao=False,emitido_em=None):
    emitido_em = emitido_em or agora_brasilia().strftime('%d/%m/%Y %H:%M:%S')
    titulo = 'Apuração atualizada' if atualizacao else 'Seu resultado no GP'
    qualificador = 'parcial' if relatorio['parcial'] else 'final'
    assunto = f"🏁 {titulo} de {relatorio['gp']} — {relatorio['total']} pontos ({qualificador})"
    texto = [f"Olá, {relatorio['usuario']}!",f"{titulo} de {relatorio['gp']} — Bolão F1 2026.",
             f'Emitido em {emitido_em} (Brasília).',f"Total {qualificador} do GP: {relatorio['total']} pontos."]
    if atualizacao:
        texto.append('Este relatório substitui a apuração enviada anteriormente para este GP.')
    if relatorio['parcial']:
        texto.append('Apuração parcial: há sessões ou campos do gabarito pendentes. Os pontos podem mudar.')
        texto.append('Pendências: '+', '.join(relatorio['pendentes']))
    secoes = []
    for sessao in relatorio['sessoes']:
        texto.extend(['',sessao['tipo'].upper(),'Item | Seu palpite | Resultado | Pontos'])
        linhas = []
        for linha in sessao['linhas']:
            pontos = '—' if linha['pontos'] is None else str(linha['pontos'])
            texto.append(f"{linha['rotulo']} | {linha['palpite']} | {linha['resultado']} | {pontos} ({linha['estado']})")
            acerto = linha['estado']=='Acerto'
            fundo,cor = ('#e7f6ed','#137a46') if acerto else ('#fff7e5','#825500') if linha['estado'].startswith('Regra legada') else ('#ffffff','#4b5667')
            celulas = [linha['rotulo'],linha['palpite'],linha['resultado'],('+'+pontos if linha['pontos'] else pontos)]
            linhas.append(f'<tr style="background:{fundo};color:{cor}">'+''.join(f'<td style="padding:10px 7px;border-bottom:1px solid #e3e8ee;word-break:break-word">{escape(str(c))}</td>' for c in celulas)+'</tr>')
        if sessao['tipo']=='Corrida Principal':
            nome_bonus = {300:'Top 3',450:'Top 5',600:'Top 10'}.get(sessao['bonus'],'não atingido')
            texto.append(f"Bônus ({nome_bonus}): {sessao['bonus']} pontos.")
            linhas.append(f'<tr><td colspan="3" style="padding:12px 7px">Bônus exclusivo — {nome_bonus}</td><td style="padding:12px 7px"><b>+{sessao["bonus"]}</b></td></tr>')
        estado_sessao = 'Homologada' if sessao['homologada'] else 'Aguardando homologação — não entra no total'
        texto.append(f"Subtotal: {sessao['subtotal']} pontos. {estado_sessao}.")
        secoes.append(f'<h2 style="font-size:16px;color:#172033;margin:26px 0 6px">{escape(sessao["tipo"])}</h2><p style="font-size:12px;color:#667388">{escape(estado_sessao)}</p><table width="100%" style="border-collapse:collapse;table-layout:fixed;font-size:12px"><thead><tr style="background:#eef2f7;color:#40506a"><th style="padding:10px 7px;text-align:left;width:17%">Item</th><th style="padding:10px 7px;text-align:left;width:31%">Seu palpite</th><th style="padding:10px 7px;text-align:left;width:31%">Resultado</th><th style="padding:10px 7px;text-align:left;width:21%">Pontos</th></tr></thead><tbody>'+''.join(linhas)+f'</tbody></table><p style="text-align:right;font-size:14px"><b>Subtotal: {sessao["subtotal"]} pontos</b></p>')
    rodape = 'Somente acertos exatos pontuam. O bônus Top 3/5/10 é exclusivo: vale apenas o maior atingido. A pontuação segue as regras atuais do bolão.'
    texto.extend(['',f"TOTAL {qualificador.upper()} DO GP: {relatorio['total']} pontos.",rodape])
    if relatorio['regra_legada']:
        texto.append('Há pontuação legada por valores ausentes no registro. Esses itens são identificados; confira com a organização.')
    aviso = ('<p style="padding:14px;background:#fff3cd;color:#6d5100">Apuração parcial: há sessões ou resultados pendentes. O total pode mudar.<br>'+escape(', '.join(relatorio['pendentes']))+'</p>') if relatorio['parcial'] else ''
    revisao = '<p>Esta apuração substitui a enviada anteriormente para este GP.</p>' if atualizacao else ''
    legado = '<p style="color:#825500">Há pontuação legada em valores ausentes no registro. Consulte a organização para esses itens.</p>' if relatorio['regra_legada'] else ''
    html = f'''<!doctype html><html lang="pt-BR"><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;background:#edf1f6;font-family:Arial,sans-serif;color:#172033"><table role="presentation" width="100%"><tr><td align="center" style="padding:20px 10px"><table role="presentation" width="100%" style="max-width:680px;background:white;border-collapse:collapse"><tr><td style="padding:24px;background:#111c2d;color:white;border-top:5px solid #ff463e"><b style="font-size:24px">🏁 PALPITES F1</b><p style="font-size:12px;margin-bottom:0">SEU PALPITE. SUA DISPUTA.</p></td></tr><tr><td style="padding:22px 14px"><h1 style="font-size:24px">{escape(titulo)} de {escape(relatorio['gp'])}</h1><p>Olá, {escape(relatorio['usuario'])}!</p><p style="font-size:12px;color:#667388">Emitido em {escape(emitido_em)} (Brasília).</p>{revisao}<div style="padding:20px;background:#17263d;color:white;border-radius:12px"><span style="font-size:12px">TOTAL {qualificador.upper()} DO GP</span><br><b style="font-size:36px">{relatorio['total']} <span style="font-size:15px">pontos</span></b></div>{aviso}{''.join(secoes)}{legado}<p style="font-size:12px;color:#667388">{escape(rodape)}</p><p style="font-size:12px;color:#667388">Verde indica acerto. Confira a apuração mais recente na plataforma. Direção de Prova — Bolão F1 2026.</p></td></tr></table></td></tr></table></body></html>'''
    return assunto,'\n'.join(texto),html


def preparar_emails_apuracao(palpites,gabaritos,gp):
    from hashlib import sha256
    from uuid import uuid4
    if palpites.empty:
        return [],[]
    usuarios = sorted(set(palpites.loc[palpites['GP']==gp,'Usuario'].dropna()))
    tarefas = []; sem_email = []
    for usuario in usuarios:
        email = emails_autorizados.get(usuario,'').strip()
        if not _endereco_email_simples(email):
            sem_email.append(usuario);continue
        relatorio = detalhar_apuracao_gp(palpites,gabaritos,usuario,gp)
        if not relatorio['corrida_homologada']:
            continue
        revisao = sha256(json.dumps({'email':destinatario_email(email).casefold(),'relatorio':relatorio},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        tarefas.append({'id':'apuracao_'+uuid4().hex,'usuario':usuario,'gp':gp,'email':email,
                        'revisao':revisao,'relatorio':relatorio})
    return tarefas,sem_email


def _alterar_livro_apuracao(transformar):
    # Reserva em lote com SHA: dois administradores não disparam a mesma revisão.
    for tentativa in range(3):
        df,sha = _ler_dados_remotos(ARQUIVO_EMAIL_APURACOES)
        if not df.empty and not set(COLUNAS_EMAIL_APURACOES).issubset(df.columns):
            raise ValueError('Controle de envios com estrutura inválida.')
        novo,contexto = transformar(df)
        if novo is None:
            return contexto
        try:
            if not _escrever_csv(ARQUIVO_EMAIL_APURACOES,novo,sha,'Controle de apurações por e-mail'):
                raise OSError('Reserva de envios não confirmada.')
            return contexto
        except urllib.error.HTTPError as erro:
            if erro.code!=409 or tentativa==2:
                raise
    raise OSError('Não foi possível atualizar o controle de envios.')


def reservar_emails_apuracao(tarefas,forcar_pendencias=False):
    agora = datetime.now(pytz.UTC)
    def reservar(df):
        novos = []; selecionadas = []; ignoradas = 0
        for tarefa in tarefas:
            resetando = not df.empty and bool(((df['GP']==tarefa['gp'])&(df['Estado']=='Resetando')).any())
            if resetando:
                ignoradas += 1;continue
            anteriores = df.loc[(df['Usuario']==tarefa['usuario'])&(df['GP']==tarefa['gp'])&~df['Estado'].isin(['Resetado','Cancelado'])] if not df.empty else pd.DataFrame()
            ultimo = anteriores.iloc[-1].to_dict() if not anteriores.empty else {}
            mesmo = ultimo.get('Revisao')==tarefa['revisao']
            estado = ultimo.get('Estado')
            em_envio = estado=='Em envio'
            idade = 0
            if em_envio:
                try:
                    idade = (agora-datetime.fromisoformat(str(ultimo['Reservado_em']))).total_seconds()
                except (ValueError,KeyError,TypeError):
                    idade = 0
            liberar_pendencia = forcar_pendencias and (estado=='Verificar' or (em_envio and idade>=600))
            if (em_envio and not liberar_pendencia) or (mesmo and not liberar_pendencia):
                ignoradas += 1;continue
            tarefa = dict(tarefa,atualizacao=not anteriores.empty)
            selecionadas.append(tarefa)
            novos.append({'Id':tarefa['id'],'Usuario':tarefa['usuario'],'GP':tarefa['gp'],
                          'Email':destinatario_email(tarefa['email']),'Revisao':tarefa['revisao'],'Estado':'Em envio',
                          'Total_GP':tarefa['relatorio']['total'],'Parcial':str(tarefa['relatorio']['parcial']),
                          'Reservado_em':agora.isoformat(),'Atualizado_em':agora.isoformat()})
        contexto = {'tarefas':selecionadas,'ignoradas':ignoradas}
        return (pd.concat([df,pd.DataFrame(novos)],ignore_index=True) if novos else None),contexto
    return _alterar_livro_apuracao(reservar)


def concluir_emails_apuracao(resultados):
    def concluir(df):
        if df.empty or not set(resultados).issubset(set(df['Id'])):
            raise ValueError('Reserva de envio não encontrada.')
        novo = df.copy()
        agora = datetime.now(pytz.UTC).isoformat()
        for identificador,aceito in resultados.items():
            mascara = (novo['Id']==identificador)&(novo['Estado']=='Em envio')
            novo.loc[mascara,'Estado'] = 'Aceito' if aceito else 'Verificar'
            novo.loc[mascara,'Atualizado_em'] = agora
        return novo,None
    return _alterar_livro_apuracao(concluir)


def cancelar_reservas_apuracao(identificadores):
    def cancelar(df):
        if df.empty:
            return None,None
        novo = df.copy()
        mascara = novo['Id'].isin(identificadores)&(novo['Estado']=='Em envio')
        novo.loc[mascara,'Estado']='Cancelado'
        novo.loc[mascara,'Atualizado_em']=datetime.now(pytz.UTC).isoformat()
        return novo,None
    return _alterar_livro_apuracao(cancelar)


def _enviar_tarefa_apuracao(tarefa):
    assunto,texto,html = montar_email_apuracao(tarefa['relatorio'],tarefa['atualizacao'])
    return _enviar_email_brevo(assunto,texto,html,tarefa['email'])


def notificar_apuracao_gp(gp,progresso=None,forcar_pendencias=False):
    from concurrent.futures import ThreadPoolExecutor,as_completed
    resumo = {'gp':gp,'aceitos':0,'verificar':0,'ignorados':0,'sem_email':[],'erro':None}
    if not BREVO_API_KEY:
        resumo['erro'] = 'Configure BREVO_API_KEY antes de enviar as apurações.';return resumo
    try:
        palpites,_ = _ler_dados_remotos(ARQUIVO_DADOS)
        gabaritos,_ = _ler_dados_remotos(ARQUIVO_GABARITOS)
        if not ultimo_registro(gabaritos,gp,'Corrida Principal'):
            resumo['erro'] = 'A corrida principal ainda não foi homologada. Nenhum e-mail de apuração foi enviado.';return resumo
        tarefas,sem_email = preparar_emails_apuracao(palpites,gabaritos,gp)
        resumo['sem_email'] = sem_email
        if not tarefas:
            return resumo
        reserva = reservar_emails_apuracao(tarefas,forcar_pendencias)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        logger.warning('Apuração por e-mail bloqueada: não foi possível preparar e reservar o lote.')
        resumo['erro'] = 'O gabarito permanece salvo. Não foi possível reservar os envios; tente pelo painel E-mails de apuração.';return resumo
    tarefas = reserva['tarefas'];resumo['ignorados'] = reserva['ignoradas']
    if not tarefas:
        return resumo
    try:
        atuais,_ = _ler_dados_remotos(ARQUIVO_GABARITOS)
        if assinatura_gabarito_gp(atuais,gp)!=assinatura_gabarito_gp(gabaritos,gp):
            cancelar_reservas_apuracao([t['id'] for t in tarefas])
            resumo['erro']='O gabarito mudou durante a preparação. Nenhum e-mail deste lote foi enviado. Confira a nova apuração antes de enviar novamente.'
            return resumo
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        resumo['erro']='Não foi possível revalidar o gabarito após reservar o lote. Nenhum e-mail foi disparado; confira o controle antes de tentar novamente.'
        return resumo
    resultados = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futuros = {pool.submit(_enviar_tarefa_apuracao,t):t for t in tarefas}
        for futuro in as_completed(futuros):
            tarefa = futuros[futuro]
            try:
                aceito = bool(futuro.result())
            except Exception:
                logger.warning('Envio de apuração sem confirmação; conferir logs transacionais.')
                aceito = False
            resultados[tarefa['id']] = aceito
            resumo['aceitos' if aceito else 'verificar'] += 1
            if progresso:
                progresso(len(resultados),len(tarefas))
    try:
        concluir_emails_apuracao(resultados)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        logger.warning('Apuração enviada, mas o controle final não pôde ser salvo.')
        resumo['erro'] = 'As tentativas terminaram, mas o controle final não foi salvo. Confira os logs do Brevo antes de repetir; as reservas foram preservadas.'
    return resumo


def mostrar_resumo_apuracao(resumo):
    if resumo.get('aceitos'):
        st.success(f"Apuração de {resumo['gp']}: {resumo['aceitos']} e-mails aceitos pelo Brevo, com cópia para o bolão.")
    if resumo.get('verificar'):
        st.warning(f"{resumo['verificar']} envios sem confirmação. Confira os logs do Brevo antes de tentar novamente.")
    if resumo.get('ignorados'):
        st.info(f"{resumo['ignorados']} relatórios já reservados ou enviados nesta revisão foram ignorados.")
    if resumo.get('sem_email'):
        st.warning('Sem e-mail cadastrado válido: '+', '.join(resumo['sem_email']))
    if resumo.get('erro'):
        st.warning(resumo['erro'])
    elif not any(resumo.get(chave) for chave in ('aceitos','verificar','ignorados','sem_email')):
        st.info('Nenhum palpite com e-mail válido encontrado para este GP.')


def disparar_apuracao_com_progresso(gp,forcar_pendencias=False):
    barra = st.progress(0,text='Preparando os e-mails de apuração…')
    def progresso(feitos,total):
        barra.progress(feitos/total,text=f'Apuração: {feitos} de {total} tentativas concluídas')
    try:
        with st.spinner('Processando os e-mails. Aguarde a conclusão deste lote…'):
            return notificar_apuracao_gp(gp,progresso,forcar_pendencias)
    finally:
        barra.empty()


def check_ponto(palpite, gabarito, chave, valor_pontos):
    val_p = str(palpite.get(chave, '')).strip()
    val_g = str(gabarito.get(chave, '')).strip()
    return valor_pontos if (val_p and val_p == val_g) else 0


def _bonus_principal(palpite, gabarito):
    top_p = [str(palpite.get(f'P{i}', '')).strip() for i in range(1,11)]
    top_g = [str(gabarito.get(f'P{i}', '')).strip() for i in range(1,11)]
    if not (all(top_p) and all(top_g)):
        return 0
    return next((bonus for n, bonus in ((10,600),(5,450),(3,300)) if top_p[:n] == top_g[:n]), 0)


def calcular_pontos_sessao(palpite, gabarito):
    tipo = palpite.get('Tipo', '')
    if 'Classificação' in tipo or 'Qualy Sprint' in tipo:
        return check_ponto(palpite, gabarito, 'Pole', 100)
    pesos = {'Corrida Principal': PONTOS_PRINCIPAL, 'Corrida Sprint': PONTOS_SPRINT}.get(tipo, {})
    pontos = sum(check_ponto(palpite, gabarito, chave, valor) for chave, valor in pesos.items())
    return pontos + (_bonus_principal(palpite, gabarito) if tipo == 'Corrida Principal' else 0)


def processar_resultados(df_palpites, df_gabaritos):
    """Índice de gabaritos O(G); consulta O(1) por palpite, sem refiltrar o DataFrame."""
    colunas = ['Usuario','Equipe','Pontos','GP']
    if df_palpites.empty or df_gabaritos.empty:
        return pd.DataFrame(columns=colunas)
    gabaritos = {(r['GP'], r['Tipo']): r for r in
                 df_gabaritos.drop_duplicates(['GP','Tipo'], keep='last').to_dict('records')}
    resultados = []
    for palpite in df_palpites.drop_duplicates(['Usuario','GP','Tipo'], keep='last').to_dict('records'):
        gabarito = gabaritos.get((palpite['GP'], palpite['Tipo']))
        if gabarito is not None:
            resultados.append({'Usuario': palpite['Usuario'],
                               'Equipe': EQUIPE_POR_USUARIO.get(palpite['Usuario'], 'Sem Equipe'),
                               'Pontos': calcular_pontos_sessao(palpite,gabarito), 'GP': palpite['GP']})
    return pd.DataFrame(resultados, columns=colunas)


def index_piloto(val):
    return INDICE_PILOTOS.get(str(val).strip() if pd.notna(val) else '', 0)


# Fotos administradas persistem no repositório, sem depender do disco temporário do Render.
ARQUIVO_FOTOS = 'fotos_personalizadas_2026.csv'
COLUNAS_FOTOS = ['Categoria','Nome','Imagem','Atualizado_em']
MAX_UPLOAD_FOTO = 5 * 1024 * 1024


def chave_nome_foto(nome):
    import unicodedata
    chave = ''.join(c for c in unicodedata.normalize('NFKD',str(nome)).casefold() if c.isalnum() and not unicodedata.combining(c))
    return {'alexanderalbon':'alexalbon','andreakimiantonelli':'kimiantonelli'}.get(chave,chave)


def nomes_galeria(categoria):
    return participantes if categoria=='Palpiteiros' else [p for p in pilotos if p and p!='Nenhum / Outro']


def preparar_foto(conteudo):
    """Valida e reencoda a imagem, removendo metadados e limitando seu tamanho."""
    from PIL import Image, ImageOps, UnidentifiedImageError
    if not conteudo or len(conteudo)>MAX_UPLOAD_FOTO:
        raise ValueError('Escolha uma imagem de até 5 MB.')
    try:
        with Image.open(io.BytesIO(conteudo)) as original:
            if original.format not in ('JPEG','PNG','WEBP'):
                raise ValueError('Use uma foto JPG, PNG ou WEBP.')
            if original.width*original.height>16000000:
                raise ValueError('A imagem deve ter no máximo 16 megapixels.')
            imagem = ImageOps.exif_transpose(original)
            imagem.thumbnail((640,640),Image.Resampling.LANCZOS)
            fundo = Image.new('RGB',imagem.size,'#172235')
            if imagem.mode=='RGBA' or 'transparency' in imagem.info:
                rgba = imagem.convert('RGBA')
                fundo.paste(rgba,mask=rgba.getchannel('A'))
            else:
                fundo.paste(imagem.convert('RGB'))
            saida = io.BytesIO()
            fundo.save(saida,format='JPEG',quality=88,optimize=True)
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as erro:
        raise ValueError('Não foi possível abrir essa foto. Escolha outro arquivo JPG, PNG ou WEBP.') from erro
    return 'data:image/jpeg;base64,'+base64.b64encode(saida.getvalue()).decode()


@st.cache_resource(ttl=20,show_spinner=False)
def carregar_fotos_personalizadas():
    if not GITHUB_TOKEN:
        return {}
    try:
        df,_ = ler_dados(ARQUIVO_FOTOS)
        if df.empty:
            return {}
        if not set(COLUNAS_FOTOS).issubset(df.columns):
            raise ValueError('Cadastro de fotos inválido.')
        return {(r['Categoria'],chave_nome_foto(r['Nome'])):r['Imagem']
                for r in df.fillna('').to_dict('records')
                if r['Categoria'] in ('Pilotos','Palpiteiros') and isinstance(r['Imagem'],str)
                and r['Imagem'].startswith('data:image/jpeg;base64,')}
    except (urllib.error.URLError,OSError,ValueError,KeyError):
        logger.warning('Fotos personalizadas indisponíveis; mantendo as imagens padrão.')
        return {}


def foto_personalizada(categoria,nome):
    return carregar_fotos_personalizadas().get((categoria,chave_nome_foto(nome)),'')


def salvar_foto_administrada(categoria,nome,conteudo=None):
    if categoria not in ('Pilotos','Palpiteiros') or nome not in nomes_galeria(categoria):
        raise ValueError('Selecione um piloto ou palpiteiro cadastrado.')
    imagem = preparar_foto(conteudo) if conteudo is not None else None
    def atualizar(df):
        if not df.empty and not set(COLUNAS_FOTOS).issubset(df.columns):
            raise ValueError('O cadastro de fotos está inválido. Nenhuma foto foi alterada.')
        df = df.reindex(columns=COLUNAS_FOTOS)
        mascara = df['Categoria'].eq(categoria) & df['Nome'].map(chave_nome_foto).eq(chave_nome_foto(nome))
        mantidas = df.loc[~mascara].copy()
        if imagem is not None:
            registro = {'Categoria':categoria,'Nome':nome,'Imagem':imagem,
                        'Atualizado_em':agora_brasilia().isoformat()}
            mantidas = pd.concat([mantidas,pd.DataFrame([registro])],ignore_index=True)
        return mantidas,None
    sucesso,_ = _atualizar_csv(ARQUIVO_FOTOS,atualizar,f'Atualiza foto: {categoria} - {nome}')
    if not sucesso:
        raise OSError('Não foi possível salvar a foto. Tente novamente.')
    carregar_fotos_personalizadas.clear()
    return True


def acao_foto_admin(categoria,nome,chave_upload,restaurar=False):
    senha = st.session_state.get('senha_admin','')
    esperada = configuracao('SENHA_ADMIN',SENHA_ADMIN_LEGADA)
    if not senha or not hmac.compare_digest(senha.encode(),esperada.encode()):
        st.session_state['aviso_foto'] = ('error','Autentique-se como administrador para alterar fotos.')
        return
    arquivo = st.session_state.get(chave_upload)
    if not restaurar and arquivo is None:
        st.session_state['aviso_foto'] = ('warning','Selecione a nova foto antes de salvar.')
        return
    try:
        salvar_foto_administrada(categoria,nome,None if restaurar else arquivo.getvalue())
    except (urllib.error.URLError,OSError,ValueError,KeyError) as erro:
        mensagem = str(erro) if isinstance(erro,ValueError) else 'Não foi possível salvar a foto. Confira a conexão e a permissão de gravação no repositório.'
        st.session_state['aviso_foto'] = ('error',mensagem)
        return
    mensagem = f'Imagem padrão de {nome} restaurada.' if restaurar else f'Foto de {nome} atualizada.'
    st.session_state['aviso_foto'] = ('success',mensagem)


def admin_fotos():
    secao('FOTOS DO BOLÃO','Gerenciar fotos')
    st.caption('Cadastre ou substitua fotos. As alterações ficam salvas no repositório e aparecem nos cartões, rankings e na aba Fórmula 1.')
    aviso = st.session_state.pop('aviso_foto',None)
    if aviso:
        {'success':st.success,'warning':st.warning,'error':st.error}[aviso[0]](aviso[1])
    categoria = st.radio('Quem deseja atualizar?',['Palpiteiros','Pilotos'],horizontal=True,key='fotos_categoria')
    nome = st.selectbox('Selecione o nome',nomes_galeria(categoria),key='fotos_nome_'+categoria)
    atual = foto_personalizada(categoria,nome)
    if categoria=='Palpiteiros':
        st.markdown(avatar_html(nome),unsafe_allow_html=True)
    else:
        exibir_foto_piloto(nome)
    st.caption('Foto personalizada cadastrada.' if atual else 'Sem foto personalizada: usando a imagem padrão, quando disponível.')
    chave_upload = 'upload_foto_'+categoria+'_'+nome
    arquivo = st.file_uploader('Nova foto · JPG, PNG ou WEBP · até 5 MB',type=['jpg','jpeg','png','webp'],key=chave_upload)
    if arquivo is not None:
        try:
            st.image(preparar_foto(arquivo.getvalue()),width=160,caption='Prévia da nova foto')
        except ValueError as erro:
            st.warning(str(erro))
    st.button('Salvar foto',use_container_width=True,on_click=acao_foto_admin,args=(categoria,nome,chave_upload))
    st.button('Restaurar imagem padrão',disabled=not bool(atual),key='restaurar_foto_'+categoria+'_'+nome,
              on_click=acao_foto_admin,args=(categoria,nome,chave_upload,True))


def exibir_foto_piloto(nome):
    personalizada = foto_personalizada('Pilotos',nome)
    if personalizada:
        st.image(personalizada,width=64)
        return
    if nome in ('Ryo Hirakawa','Rafael Câmara'):
        st.markdown(f'<img src="{arte_f1("capacete")}" width="64" alt="Ilustração de capacete"/>',unsafe_allow_html=True)
        st.caption(f'{nome} · Haas')
        return
    if nome and nome != 'Nenhum / Outro':
        st.image(f'https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/fotos/{quote(nome)}.png', width=64)


# ── Identidade visual: fotos públicas já usadas no site de referência ──
FOTOS_PARTICIPANTES = {
    'Valério Bimbato': 'https://i.ibb.co/DDCBrrrS/20180428-15.jpg',
    'Rodolfo Brandão': 'https://i.ibb.co/WpM5VMgq/Sem-t-tulo.jpg',
    'Maikon Miranda': 'https://i.ibb.co/WWH5RYfs/129159798-205592931152894-3590323114454579446-n.jpg',
    'Flávio Soares': 'https://i.ibb.co/TMXDpwK0/IMG-20240908-WA0070.jpg',
    'Fausto Fleury': 'https://i.ibb.co/mCR7RBxs/fausto.jpg',
    'Alaerte Fleury': 'https://i.ibb.co/B2vRBVB6/Sem-t-tulo.png',
    'Delvânia Belo': 'https://i.ibb.co/0jkhb8JJ/IMG-20260608-WA0025.jpg',
    'Fabrício Abe': 'https://i.ibb.co/h1dvSHZn/Sem-t-tulo.png',
    'George Fleury': 'https://i.ibb.co/35pS08d4/Sem-t-tulo-2.jpg',
    'Henrique Junqueira': 'https://i.ibb.co/gFrVwNPZ/653007390-18416258482123519-4856301629390269506-n.jpg',
    'Jaime Gabriel': 'https://i.ibb.co/8gXzwZh2/20241130-190400.jpg',
    'Hilton Jacinto': 'https://i.ibb.co/0yQttFsS/20180428-154832.jpg',
    'Myke Ribeiro': 'https://i.ibb.co/JwQ34Z0Q/myk.jpg',
    'Emilio Jacinto': 'https://i.ibb.co/XZ9QqCCs/Sem-t-tulo.jpg',
    'Fernanda Fleury': 'https://i.ibb.co/PG2kD09h/20241102-180321.jpg',
    'César Gaudie': 'https://i.ibb.co/VW3y4t9M/IMG-20240908-WA0070.jpg',
    'Frederico Gaudie': 'https://i.ibb.co/qMfLfk9M/fred.jpg',
    'Syllas Araújo': 'https://i.ibb.co/DgMCn3bn/Sem-t-tulo.jpg',
}
MAX_PONTOS_SESSAO = {
    'Classificação Principal (Pole)': 100, 'Qualy Sprint (Pole)': 100,
    'Corrida Principal': sum(PONTOS_PRINCIPAL.values()) + 600,
    'Corrida Sprint': sum(PONTOS_SPRINT.values()),
}


def numero_br(valor, casas=0):
    return f'{valor:,.{casas}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def _svg_uri(svg):
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()


def arte_f1(tipo='carro'):
    """Ilustrações vetoriais incorporadas: não dependem de downloads ou novos arquivos."""
    desenhos = {
        'carro': '<path d="M140 30h40l10 48 28 21v32l-27-9-1 66 25 21v24l-31-5-8 33h-32l-8-33-31 5v-24l25-21-1-66-27 9V99l28-21z" fill="#ff463e"/><path d="M141 95h38v80h-38z" fill="#f8a39d"/><ellipse cx="160" cy="156" rx="14" ry="25" fill="#0a101c"/><path d="M106 78h108v16H106zm8 155h92v17h-92z" fill="#dce5f3"/><g fill="#05090f" stroke="#51617b" stroke-width="3"><rect x="88" y="95" width="27" height="55" rx="7"/><rect x="205" y="95" width="27" height="55" rx="7"/><rect x="98" y="197" width="29" height="53" rx="7"/><rect x="193" y="197" width="29" height="53" rx="7"/></g>',
        'bandeira': '<path d="M88 255V48" stroke="#a7b6cd" stroke-width="9"/><path d="M94 51c53-30 83 31 140 0v122c-57 31-87-30-140 0z" fill="#f3f6ff"/>' + ''.join(f'<rect x="{94+x*28}" y="{52+y*30}" width="28" height="30" fill="#101a2a"/>' for y in range(4) for x in range(5) if (x+y)%2==0),
        'trofeu': '<path d="M115 54h90v77a45 45 0 0 1-90 0z" fill="#ffcc76"/><path d="M115 70H87v40q0 41 43 41m75-81h28v40q0 41-43 41" fill="none" stroke="#f2aa4d" stroke-width="13"/><path d="M160 177v48m-35 14h70" stroke="#ffcc76" stroke-width="16" stroke-linecap="round"/><path d="m160 79 8 16 18 3-13 13 3 18-16-9-16 9 3-18-13-13 18-3z" fill="#9b5f22"/>',
        'capacete': '<path d="M78 187v-43a82 82 0 0 1 164 0v72H105z" fill="#ff463e"/><path d="M120 115h115v54H120q-30-27 0-54" fill="#091523"/><path d="M129 125h100v15H121z" fill="#76e0ee"/><path d="M82 187h157v30H103z" fill="#f7f9ff"/><path d="M150 63q30 0 53 20" fill="none" stroke="#fff" stroke-width="9"/>',
    }
    return _svg_uri('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 300">' + desenhos.get(tipo, desenhos['carro']) + '</svg>')


def _arquivo_imagem_uri(caminho):
    from mimetypes import guess_type
    return 'data:' + (guess_type(str(caminho))[0] or 'image/png') + ';base64,' + base64.b64encode(caminho.read_bytes()).decode()


def foto_participante(nome):
    personalizada = foto_personalizada('Palpiteiros',nome)
    if personalizada:
        return personalizada
    from pathlib import Path
    # Fotos próprias no repositório têm prioridade sobre os links da referência.
    raiz = Path(__file__).resolve().parent / 'assets' / 'palpiteiros'
    for extensao in ('.jpg', '.png', '.webp', '.jpeg'):
        caminho = raiz / (nome + extensao)
        if caminho.is_file():
            return _arquivo_imagem_uri(caminho)
    return FOTOS_PARTICIPANTES.get(nome, '')


LOGO_GRUPO_PADRAO = 'data:image/webp;base64,UklGRgJCAQBXRUJQVlA4IPZBAQAwMQOdASqoAuoBPjEUiEMiISEjq1a74HAGCWdtmgsvXdDEDA/sXaSwmv/pUrTX6vulFvMLzJsLzj5/dV3Rcz8zv5Yf3ny1uA3h/wr/b/+9/qvwVy5PCf7XmV8uf6D+8f4f/i/6P////b7g/+D/b/5H++fG/9Vf8H3BP04/x/9q/zP+5/zX//+x3qh/uXoR/pv9//8f+W95v/jfsj75v7B6hH85/xv/07Gf0IvLb/cj4j/6p/t//P/pfZp/3PZ/8/v4Z5XvjX9R/mPyX82/yD6F/Hf3X/J/77/C//f4Bsz/sH9P/6/9L+73uN/Lvv9+0/wP+c/8/5lfL//T/0P7x/5D0n/OP33/jf579wf9v+6v2C/kH81/x39z/bn/Fft385f2H/S/2ngd6p/ov/D/o/YO9hvpv+g/wn+e/4X+M/ej6AvuP/b/q/VT7TewD/UP73/3vzc/f/6u/4/gw/ev+Z+6/wBf1b/Pf9z81P9p/////+Kv9N/4v9P/sP/p/sv///5/jj+if5f/v/53/V//X/af/////oN/Mf7D/vf8F/pP/P/mf///8vvT/9P+4/f/6bfuX/9f+P8Nv7R/+n/R/7f//o8t9gbU6vPPPFWuWmrYRpEYBjEw8S0zI6n9cfMhH9IRGyWWVNoojVai7xv4bg2TE6kzPNv9KxJZ54rN39Up2uS8wSOXdOT/EtmwpUM+6P+FabIbLCPCHvM0WRUrJzqQz7FD93GEvBM0YhS9Myqpw/wocThoGPa4q+fbGgbQ2b/BlgRw+5+vM44YjCNBfM6ktvIVnN0yZ4SisKA4DPFvx6nXX6h4fIux7ZF20qhDb7oPBINpd5oheR9apdufgcqJSGu+wObmY1UVbF5QRF1O0AFmr5YZ1Ogx6J8PaKhaTAiR5QTRnzQZH+plu+l///DHGn/z6DL1I12WEbJJH/DyhWs2iw3vSk3sRb158j3sG/2d3Mlpe3kXvIPh6L5OfL/+EZ883Bg0hNSDpzb77hrQYn+vs+9+97MsBL/nRpAUTQSKgKU9e1787IJEX0hUJQ3YU/GUoKKUWJy4B/6KdfjSGn//xhl6/epDwCdmP+7UUcJBm/KrRGij8FdwW+0oWsa2yAAaaYRA7AgKIFdWYfVi5tAM98St+KyP/gBp8ffL7WeEh3FSUlGm8/y8NRC8cfnHv5ZEb+SHjaHf7UH6R2iIaqdww+e4cHeiaHAPQaGbmVXO6uoSetYuGI52KPdbzSefJioqiyrsg+CdJdpQBqIlwtutbowK5ihK0YwCoiH2PoIYOFHEPgAksKd/a+WRJR4G/U2fBdduM1b3o4JNw66nEFyBzlMYv6tjR/5c2VfHrZT4/lb+SINiInEXh7yu4bdBKap/LOY6LRIOIBS4usIeWK58UJO/5PenVMlxIyszsRUVoAnhfQSCIMvQJFWgURKMnUx6U80cm/TBS6+WxcdSigJRs38m5pS6Fzw+SUFGlC0TfhDZg/TYoBqO6xVdk0jfxT0WLY04jcx5D1rt2AGb2sB0N+nh+DRHuPAF6Ieptm54LZ3daVNzNk1HfZjqBIAltKEBFq3qiN8HciFhYRSf0bvoF5GXcW9jpzQueeTXze1bYNvIu+oR7Ij0ccZk590dU4edXfv5ZtVOHnkw9G5IMqS70ibLIDTqQJCsi166rn3Mgn/EXYknQnSPOfy2cA9Gh0qMQOlZCyBTVYmAycyzhakA2Ets8np0wwjvyTRmOBA8g4bERw9tgJZKlnX/0pPHDqdgnGqmj4KOM07eWFg+gx4tI/q9eS4dwhKQ/A/6GPWZrmTXf0s+kAvB5r/uRm87BY93E8je2rwE7GWi2HgX3ZesXtaddaUWsT57x93Ln6ionQyDETvLjEhmozfg++DExB6NxdOTSi25d47yRRUl6PKd7/sCpEH8bF9y8fpneD9IBmeWjpFAvwC/gfAN0+LGCc+g5p/qWc3sY1zJT50A2Y6Y1O/FYkjLQz1g2lWnTlcVSYZNz206Ytme63pXoZbQEtP1HmzJicbGhqKMIQuBrvb8H1Bjla0/gUWqqJQe5aoiGyqS+FAVHpbKjXIkFCedaGc3ISZdfAut+B0m35+rJDsQT1WYxPjBx6AeoUqaqP74QFJv2F3uCZeGwWKtxZUK9SGGV/xhRqxQmuhE+CnMjGYyKxGR7Lo/Z1LKKxLykFiA5O8BqCV3dqSqVJd6xdnkqSgCuxXmIC6/in44CSXku2RttOon/fdls9Yif3xYwECNTvBYr335lfmwJjeSwS3ufe92/YGmJPFRzQpUGcnlNaJhr4qu5TQ04dwXyI3ruRdv5t5tlk9QISXb/iVHDHkVAzzLC8b2g49zLB1oq34189MMOvlN5W4Tg/+TwmpJA4tVdcmu4c+UUXsW9R7d95zXsjsOv5D7WeR2cFjGFSfa7vbxsWSDor0kFWNmJYzytTs8aMpV8xjT84o6c1UbOpuokKOQJD6XeJRPpNxu/oqhCY2821ugX6lV0pjWXyreSS6UuIpu7v0+i3bfTiohN9VP/VwgoT/zp6IshwGxZVuSsY6fe6HVPfrrf8DpgO2o6KnPXh+u3ghYoZwiWQfdPy7tB0lBnyDODsDDkV2rdU5I6ksfl3iIe3c8QLBfB/NLMO/rrnMsS6Y6g26gGez73vruXzV75sBz3p5I+p+LYYpFxjCNs/CR6nFv4Krq+rEheDENB8iNKkKUcxNOstOXWQK82vdyT6PrCyK45M+/p20MH/kr8l+dJNvAe6cAUAkWMch18NKRm4eGtpKaD7/hGGsx8deaPb98HOzeT/nRcbAW0NK5M0uj+EPFvj6n/+xVwC+HGgUZpkAdPgpRLMN3oCBk7ePjOe1EC81t9AHxOufXqBCIdHyPEdomN/42/U6zxjNbHZQiFndMSz3ooCODY7dwZN6RT1GmgEry0dFsF5O5DyaTUq7r7zxmTGlWY2CtUFx80fYLqaS7SLTVNzR0MhE/lsWYad8hydJ1ha/2VFuMsRrm//4/1TGyn3T0mdXn+xHF4TxZ/5dT24XhAjbg3xVba/Jiz5/8RzfZjnIOfQICk864IhaDp/KgmV5OUmU/Fq3MeqG61ots0kdXKSyis7SFZd7GlECb62qiYWNa+J6BF6HvLxdhhP/mKUiDL0DHZSHfISz5YPRB/dnPFNqOlV1qj2yx6zZg/mqM2O4Y5bJa3Nb9HOhnUZSfp97t4OL0betg8Bj53/phoW7Gu69a88C/92RTeMaWe7aAq4MDSQpbfmPqkzXR6zcOziRTvqmZrhsvvjvzniKCnR8/BW9HFCofbu0dkx7f0+quLNkWJ6JvS/m/Crz+lNKqBpMx7GxaZTuTkgc0pXUPXuuwJ7NAZfaXlezLSZhP4FuvpAlchaR7ViYB5OvYDwZLpJMn7fzgYdKXH/1o445+90K3OGflBiGnvpef/nQ34VD0J4qFO4hdmX947DkBxnJMqCksiLL1o5r5Ooko9alyxPe2pUTfyJKe8rUF7WBEIv3q4sDx9NPsMdRE99QvwaB3yNsX1buNyB0zB900HAPsfTA/o/vz8FHORx90lMycq0hzaEmvEwlKPcrkQEMzwHf5TnkTYn+5Sd0m0ZSDqxZksGl1N0NJA9asn2Q37g9vGLY05bssH7NzZqZGRrNigmh2Hku5YxsvVyQYkjHDFpUuYhRwFAGoRu4xB3i2/y1qQ0aLuUkAPUrS3rw2CIZUMK+pSHlkXG+11zr7fYEucJfzcSVPPIGJxHrrPm0HUQqw7EGmzXw8NMmgPJm8hKvlKKrJcYf0GQn7RfiprZSPdsnmeDKNNfmfe3lwqj8kvehw2GJqFY2abGYbi5iIb/b3dTsiMhSylQF6rUo9i7nQ2kRYvPk9zAB/IGZk2g6rS2HcCrCPTKxzU8Yv/8e74ZplwOJHm0dh+3yKJqreGZBv/JJA/tKfo4d+LgKFINmet7gzkFFTMcWhJlAx8AtP3r79S++TlFEIIVKjgxBMtmq2y7snajQD90EhJ6XywpL53F1ON8yQOwcTPEf8GvzCB86Hb5nGPkQL+qExwu/2a+gKLFUgSVeuOG1FWAN/GhmDmW5gM0Mx51r9YSkRsxM8KVJ4enXJ39RRu/cOyOoy90Fyqb8H3v02McIcno+0+fveP1Q/zLLCHoPUed3CzyBytoLhMcu9P5LIzjud5+rJ61xlvd39htGlWb/H4hZTYKKzWiksuYyyf8CV/kN7HnNBUhfsIOvjgxBw661rRKeRVI9QmnBxblphUyuzVOqAw+ipfwvhXkSGR4oVqrA6FopSsZRk1zGky6bhuF8FFH50NJ6YEyakZzyWTrzy/9s5vgtllsnBIbVxUwT8G/9bbKuqgvZZtHlQooe0b4n17MHGhC/wbDiMcIXvbMiGaH9hKlQvGRm6NCVFUFPG6+19KvRj27f3Jx+ydg4SqpoNfj+CCWEGMk4Y5K/FiYHZtRoImiOubm/pCZB/TFu9IQCRzQbtOejV1xGsr61I/bIEKPSeF9g1vhN/D1dApfEVhgiM0ZSZYhyo4ckfUDKANBj0KOA1vKjD98J+h+QD7+7Rpt1XT/yVXCOyG/l3nPKIKBuK8hgOC3ThLdK5dAXM792gj60wz37RfUrmte3wSrwd/4wT5rZvqeG+Oz2Ppzlahj8zP1w0FhJ/xGpw59bwhINQAKE8xGVY2dcri2f0zIwv8ci3w0xzye4A4W7dF3VF6NAfIMa3LI3WDp9VaFtCrN61FYaRZSYC9v7cmtsvSYsrc9+g/drJBNcxFTL4SRrqwWVJQkU4X+Yqhbm+F73Hi6dCVwBg1qpz2uQULlK69Zf1eMssGSFRGF4X5FRtlUJHEPSBqGecLmvyM3aRQBL/5vq6LE+3RaKu+tccUNK0lHqh4KHHa6s5MTHP6tLe7sGJlN9RDN10Z6BX5Pp8RXcXqqn/cjyBS6eZCskXBxCTwnwg7MpoZWUjinPJqka8kkPasiKSknUuM2vkzfvMX5M29LuLAaH+w/IxhKrKvAt5BrSVrVNIHA/b4qL7ZQk4e8QrOYK7Y+f3jl9VOKfDDznjz/emNuS680JkE5WR8oztrn4vFJId3Xg1eb2fyDI3XdGWytWPvxm4VQsM6ifx1onTQ+PPsGfbO9kK9ESmaVO4OCS8ASOkWSBkdw9KXfmWLqQWPejhy5Qm3YEiFbKoP5BNqHxm3J448Gt7RbaaXU+zY9cbUTBSp/UHP1JvhTgrYhRy3uB6L9a4AOYPJ66ne9a06EoQxoKlvLPSBo+91cRT6ff2efgy5Kx+TssVPCJIr9Ko1y6jgZB9GYcP6ei4kCcZa+2FV6FF74wevepcw5A+ixNhaLWc4equPlTVZvQ68OY/UxXVon4sw9mU8sckFMaCTshRMBO3UsB0weqGK+rXRjOousidt8YcyEwzq2d1QxSkt24HV2cCA/UQLNo605Y27KPlxQKl8u+oC5hKb+JP/bfrfuk39HDFj03Lhv5xK2VQehyUY8hslZ4rCkcyzxKzlEZlDYwtDjJv9IroN0zGoCJC2IQE2UdsPnk5d0txjak9KQaotYEc7QjdrB1mruWv8mPUIjn7lZT4NoF+51UVoxcSr/VKBBxsdpzrnfdKlcwx+sLFcSTen/AC+aVi/CMH5erXbiXqr5KD2nHWj5pS+h5zDfKA3mw1VfHOZlwQOjlGLJL3KUvxjw9GREzCsKZYGsc2uUwrsZy8u/DZZTD6c3hgaiDi+y73Kpr1ladRN2Zb1JqDLis9VUvk+6J7T31PIeF721FfHsv0zLqP8gzJdwdxoyy+Jp9jImcndMtQUTZOg+slkJCLuBogDa4/GcM/BW5iRSHACvHUwGZej7r+63rJvWseyL7G9Y5nzez2VxTeNJcbn5Ibdjsrn9HEW7gOxGp5/ROwAKX5+/bUJqU/PrXymEVj545AsH3tHiPrKTZ+Bjgm5lAAv8ceSwg2FL3Rrp6PvN6+64kg0vXWPyANyFKxn4gpASpIx3yjbs0r2aQiBzWCMNVDQJTl4UJd3vGnTamG9uAfBY7z2gWR/WgciNqnr9kJ/CKNbzTxM6M4VVrUb7fP3BFAJqwnMcOikU6mOV+OhhByQjM0wkiHmOupa+GpiDDqKtHV05Gu1Pu2z99ZBrOJAFstiQdkdOWENaGvVihBkiMl1XhZhj7pFycajtErNLLBdTaLWGfSCXhwIgjbU2XAdmF67QZf9vjaK2Z9rrDyAaU1+5N0bfF/DCTYBCve+RRjNeRiQ+HcM9MErmvHSDHGRuDfi3f7cqW87sBE8BXsn73mUqmgsiUxBl8cKGoQ+dfDPRyAQba4SzR79/EXT1Yg9miWX+iHH3rMjxpEYtqNW7hHDr95dhkopl8VRPEjHY9BOi0Ust/X69lwFkuwaew1LUsBK+ykaYZlVV/28y+3+SzuW19KRSwqH3Ci/6GczCErjH+06EBXopZyVhqP/eOY00vCasfxo6EwgPQ20YxJBKYOV1LyvkN4XNp+vPhmBZX2DeLS+WWPFcDfIopDgCnuKtIbvcHT45npcK1xwxWpvRh+vACu+w5TaKseHpFW2e6VZ8HPEv8fuBQBAA2Av7Skyo9Owm5Y6tfd2fxfPg7skA2Ok4M58GiknY1iA8PkEDe+nyTOel69Z7L6dVViE1e4ErmtK6tI5sRdEzDQk4/iFyFuU3YuvfGd8Q7NnyMSk4nxES5Vj1nklkPQW2PMtBHIZ/+s+bgZV0IrO7DgbmNPGoVfiZNaJn9rqF5St7r1a2hRBKdUNjUUL2kdEHdY/xJ9WURvtHR9i+ZreLsB7T+/eps2ChY7OIx/Bk5tRC4qkFiLmnlkCaggtMMjMh2yOixxHGadidNJX+i/c0uyRxYT28pSeo86w2rr4Gy51ayKJH9f9GTR/TsrgNjfAnRuHFbAIlk35+mebVD+HlYiDz5PhXyxun9Y/LNxwu0j1EgnFwRb9Tubgc54e9IF5ccaNtOoy6vLnKq8CGSFu5pcnQi5SfvTFMv5CfyX9cChdPk7sN2cBIRQ4VEs7z4Bcwz6O/jsjzqWOV7c812tHsKc6Wl3nnEHn4vEjlM5CYlqH7hLDRwfzIRQPYVHj8yoSQVXU3hta8LCbpY9uATRnRqCMCBBrLpU3uAjHbf3pVE+pLeor8RbhSy7pSLuNkQLt3GGfI7sQGE8onv14G3i5j7TAH9g8lGJcYay9YZqtmnq/kXVSKtmOp6wrG1BFvlNeApyYRhaVfrO5L8z/1hwrnKjRrtaJXU1/XOsTXe3cNkvCIH349Ed/0SvupJr2gCsNyLPXGzXRu4Tk4jKvaQzxF4R5mtD5NzKpz6fYAtK57Zb6pQpaE133bpnP/FT++QVwgrQlv6OX+RpSF5AUJXlFieHEmVHod/dcKCSzqTxye//PMOjloGVUn7Q07X3CYaIzonLVWBWctxX8R0E1folPrwasj8vNPAzoakFDLdZf9e14MAzjftEy2UrXUIelqY/j5fSDepea2uoQhTmZ9eCwsmpEh6Q5EJEVCzY0Q5Jw/KnyBCsBX9wDI+emlnJz1cgZ+MnNg2pz+cQlksYTl68rTJuYd3ZFcP0dpfLDV+OTngGlqOgaQTVOBjtx9LgZjHX01GYhaqMZaR95fux3/Kg4RFWOc/sArM2h34Vd11fMZCa1jXI+soeV2OAlYBKUuutljI3W5GuGSjIKAHGmclVetFNV225zhutKczXpzSr7sEofifD9MF065oVgK647R0Zamll1zUhrKYZjZuC/ZmSyjSfOCsp+1C04ksRuKkwf0xUTMyWORNVJtOHSGF3bXsOM7OGnrDVzi3QeijwROtg3EgaLt5q91+n+4ekeaFOoar2kJ279Xj2vdKeTsa8UAf3GRFMwtJrB+1O5HkauYYfv/3+SzrweexULLnsB1vE9pW0Z9nA1AiZtEj6Wf7ewSx4+LYdkCjuncCXg4wD9Q02zSzgRkfDS3gf8Feskm+l8xQH9xJyIx8NpL78E0WIOQMcsuIuPLT2+/uzCupIsjThvCuvUghtJIDTItJmMrpJdxlKt568dEvtz+7vZ+oDyO+loDCR01kAhIoxo9kqNbfSG9UrZLnuL1GmXTqOLmmfy9s1nmCWzeb8XtHScPukWJkwIotKs9cCFcINafsYKFiFb7jnNlWWm6V8pX8BMukbstSNpYIoLMVto/iLXsz23qnSyW/6hEW+J9EF68WU4N0LzIaZCp3ilJ1Kugeqf/8DLfbJPvHkLGzYDfxnxIYrxVNv/tEAhzTsXsW7/4TNYffxrqYfq7Lu3JBHl9FBNOe0rEEvwJy3wDI+VUnFq+0Vi2tVYZhnrVu3hq/5l9xFD+5J0Uv0xfb4jJ7u2sCBn7HkQTv/o+xmkCUL9QToDIxZGHalA0885wO4LJ/Wk9f4sVzguJujZMhfu9gGuAt5LPM6JI8H5d8Do5QSeJj+yT6zLzDYiya/NYdPU19LpESWfU0Rx2BVGJ192Mve5e82qqUdT+R0spb9QaWW1tO56F06zx4tNi5uz88gU41dywzJNdAdNxncH6yL6RXNqcON5sq8QEm6uasm4nqT1zLVDwh5XgBU1FLsXLGxxSshNmxsOWg0uwlNTen1Ub3MLx55xHJSbPmOpl5644twk4r1wKBTx3rr4V7VWzKuAGH2TOrpzzdwyTfp4fiO+ufT3tsjuKuEr4yVd1IBkCvUfcUznbkdSowiM7/BSMUQ2bxdeCzHOyASf57cYGbqVNGkCOSOMX7wrWM2MYPLfmR7/sOsyIAOFkc3Kw+qZuqetjgA/v79f6vjHTib7spj5rO+h8J8du4iSYCySEC0xTVP6fbZWGBguWugNss4Q79xwQ1cCl/RCeUEKEzDibCSuB6FDKOIniGM6wL+X3Rhk5NpiM/TfYWwrC8n3C0rFLGxKerEdJ8kqcdPYhdw0jUL8AY20e5oHCGfQLU/ZUZZArLe0flijRschM6xOloIlj3/qUAYRHgBYBLMQxvSeNLG6D/TkogDUfDQxZE2WV5Bfcx2+txvUnf0lo+9mL19SjZWQZ4qerss4L12pWbKruhjKrJ5ADaTxLXq4eUAmrnsQpaJbcjrqJpPdFWUou/cG8FjfPJz0Pis9D9zeAMgGvo9yIvgGJ3gX7eVgELT0pGIR1tHx88u5dhyg47fATbvtJDxhcwcQfPw059T0lGUOAAJFKTRnivIIw2Wzca8XkRsGmjFBEzCCnhFFP89ysDO+C7mk/IvX1/y2uc0kWt+c3gRAGE2c0xwL5SzIkCRon1Q4+HZIE8+G7kY95Q0GjMS+y3rh3ujD9tJ5oubBN36WaBXLnk7dQlYBHTJDOABRy5HOAQuN2b7pMJkkJxXDSko/ptuIejSAwDt3/yKhQkpjAtLaIURgMWFprfAjyEECpw0QYYnf9zkGtYm2V9H6XNEqKlo3FPpk7yk0iCUX8TQ0C/hq4uKu0JkOTXXEdSTeU5TuiZEAQ8ler908zapPqxHdQ1A9ADFSvnp0+WbRaJ+Qj9acSdnb8S3J373Wkrs8/WajOdq6XN8RccylzSi/4B5bMLBrttPH8O8bpED5oZdTliffJguzJn0iXFFrJxoZ8lZo8HBLidFCWNtmDrcf1b93GeR3J1pIupyWBKSRrhy6AG72U2KgVhpYe6UrvJmbzX7vT8l2PABC93sbJTGG5qs+hPZvjR4KB7vB66Q+EGY/BhYdQn6c43dPNydbSgLclr2v36jheMWinpSkJdJ7cBm5A+5Zs8p71kOrjBxPVdK5UC2wABx4BwGtWRoXmI160/iNqQavSREBD7ZkgHVpJDPbsO7wG0nx1vrYE1EiVlXp39tI2sUN85SGLTN6ZlqPtOH9cG7HzfRalJuMz60I2A6Jiqx7kgpWK9iBP30xMgYLoSsiNLsEAtqC0VTMwDJcGxso1TOWy+g73AfiS/2r7COtM7gP4Cq2sBhNui2Msf0RLnN5zD0ZuHI8Y/X7SPFRcnL2leUiZk1cuA4TbH1koze99+YqR34CR0IlLELpM+tVMpj41aeC91RrJeEM6PXoVIeMfUcmaWoty08fbZ6Q+Gobg5IZ6e36cULo2yxKPsrKx+5mXeXxqHOiM5J+nqKcnbw7MPWJVcMpx5XBgMXhNW7WuLvuNrg2tDvnsQYHF1LZPGDuB4VckZrML5KwcedSj7hc+xQ4bgVH7eQKEHuScvj0TJmlwbxM2By/G7IGJdcO2Jjg6rS4pVAOjaIZSvOo6dxFAMqKvGzaVKVmDfpJMFMsXSv5irxHFmp0u7dVeOV0GQG78bPNkF8exN8nEnFEvPUugbq6r0ySl5kDpAxjKj5f6d5xKpgWwtGgEqrdDczmtnYtlPLN2aA+XoXtPTObEk2tGdjrD8mSKtvtn81v4y3cEYRzcmzGG9NXnYMzJCV3C9ZlWhxDY4nYUC2Ed6onzxPvby26yZJfvLtaFfaCkD55Sn7U5iXzAIUBy7lsDUatU5bI96XGBKQsm6eqQYDE6MlEKhoa6PiRLuPZKSW8TBQdIIT2fz2AlgJTh5xLWAKfOArddri1Sd3cj+j1pfI1mQIygslx4vFJeJw+4zprehx54R0mO5ar6b8wyt/MhleXcU61SpKX+Ke21FyKSuAOBIbOxZq8p1SthbG3XxXCDWvrIGfnrRf4Sm3mhf22r11slvn+jHNGP99ZrHgzbh6MFUEbFON/cbzOSbPLGS2qai6FpwDtzMmQTY2+ncXZ7xjFwHhxLgOW1HUkK9OSjYwVP31zk+xFBOhI9ZWyF3SUztZwYXIb8D0a6rUr/kqgJZYUldzcKMAtInSUPFIGAUe6e4HffHPFkAsGFdN/HL++3XDFeyeruLIemGx0fR1g/5/hLSSElGRlSMp/27dgK6SjPFiTTCnhxp/XklDNOm38tQbz9KomKdNNwaWOyGkKE2Mo23zhWK5APRu6rIubLmMhvmAGC+QocJN0CKreihYugnRu4ICrrbfeUETEJs3RON29AEzCk/E53hRA+UA6pI3F0c3hUA1dW6g9j+m4V31XMvMdY+xek9AORda3FkjDuMknjev/RPuHjJ1b4kERgodi6bp3cuw6NcDeep3SN7vQ+gQD0YH2t5gxSfFXdi06ECBcGkq4bPNEB73sJWm4xK/zirESi7a3GRzkCcX5uZ/pm/scQ+89RNwhTKdefp5tFWuHKCphn6+d4MoDZ5LeGe0u4o1+D/tJh6U7+fX0VLGp5RuX6oFYJu5ghAAXwvk7iknRmqBlbLri+2x3/vizzH4uj8URZj3kwzXLEQTU8ZGU72EADY2HUy9jVxMDC3JC2coO9uSUSp0FgdsrCSdwArQ09mSc2Lp6lqbo62jTfEQYGdiWqMcQp1r4uo6iaDwIY+rDOQxNsQ3KYoAHkXbYID1t7nuZ7CLMdDK7iHtLbkXIBygMugIT5A5WVrg8BopajWlIRcWW944XSYvO7HYlG+4qC5BrF68pCDKZ4pP9KFutK8S3E+LO7F46AXQkm9TQc6XlgRzNW/OpEZbiaGLQBehVWkFRFJl0co+W1S1nnZWLJzHZ+ANhhkmBZLNR1ER/iy2u+KeaKzxNjcVyAfbiv/HLBQrA25nw+7uu+OdaEnQXoElXfqOTftlCjDlg65jmJ66BM9oGOL94nXbV4aqZ4KUv+EtGV1Ih1cMN2o4s2dpxP2hGLY5TlH1reuq5uCtMQBm8hMsZ8ezHTDgIqrMq8D3t76Gu4YaIC0rWPG7eL8aWxgJHtCEJSbPCQ8hQV2oojwA+1nT5rn/w2sfkP8rAD734P7hZ6tv/U99WvXrmaoZQZ+A0WMh3921OvtuHIe+CrVshN0qalZDLjkHEURo7shMEeGWEnrqYCPFYI5lJtn2DI7oBLBSn4oXYxdm2gZcBHq9BgyZ2wiP+47fKUm97xbzLkYfAeaiJ7RkwaDo43SIzPDlU+OjMtrHtmSp0nWrLwA6pdTuTYaOd/VQR/SOBuOi4rwlGztEXNSmTyks7ro+WHZ/HRfgje1/ugqjyuNOX/hDVh1Gp0g/Zc3/+b43xO34tMl9ZJ7cluJ/LhaKGS+pLqKmDc/paBelkJK/rW10Di5fGId8uOgPTWR8LJIKcOVy0ajaGKBEVSVlsQ/x3w4qM7qDuu3HsjVHPSFO7sZrV8BJkWhTZrm8140UVTU73t5NkpLdh0eXGOXWG1ikha9Mry+6UpLjNmSGyFamwzDL/tQzGm9sWrOZVzij2QIHuu7h/7ew9SNtYvfh0Pn4jjBRCbuOiaxQVFM1jqO4+ATUhEu7Aupas/M6SH3VtxusNFKhrlLarkAGlfAAIKm3GEoA30s8VUxXeSoPkiDcgFzL9Nudck+okQZDUCGVdMPZAIjb+VpTGqft33CapYCEtFvmJMuwngd3LXd26+6sfW5XuYh3QOiFWWe7Q1wNTgs6AJrifyeQBo9trAMNgZq0n6FCX1FfseHewLLQI28SicwKWId/k1W2jVPQINLT9307E4uai8oCIOwLiiVQwOFgLmPdhtoWZQpHNTMPtlBUiRVwCwX8/i8C8Rwb3WU9bEgIuNgbSupyGXlX3lKyywIqklDnWD0VV5UhpQkoQAQmaEKcIdaP35q1Cg/dHwmkjn8EjxJ8tcMDKF2xZxYUkONDsUperI5nFkw2uzOuhyl+KlZwIbqJvgD27s8ZTY3O77rji2dppFlae6AomgqVXWhzqefZ7B0109oIwVUXiNyl7z8V1INbJG91xHz/lSi+hOYWxE7K30IQr5s52SkmZEcmDysACD6W7J8fnQj2YjWEWCQ5DtTdnMSRo5rrWKIzp1cMBDBpaQfTzZMPytJiGRsCm3E6NhdUil0Fu65PJtboecMON/w8tSyvy9V6pW9Lzo9bEd97zdd732mDTyMor+TQjMqqUrOli6IPLu4otNRwYhvTmLvCInfGfy6mM8Pa1WRoNgVVTUy1pwQnnblTEgdZAv/m6/j+3y0xcsK7nQIWBKw3F9/5+xJ4RPTr38ni2qbgXcb2r89Bb8mHpcNA1pIffa3ALokMz0jsoRRNVLVHtgE3YJBE3YSRNGyWXKOCLB0cZp5uKK8ZRtlGdLGIOcesBr5J/Y57u/dvnqhhHUVkdKx0d0/8iTd59P7TnGGbRZv/jZLk2Ndwcal7ySBMYgOTT7gSvtcVQILPXeTyOzZ72memrMp4ZL2O21BUSSiplAU7VoDofvZeHfo/ju6xGRrDpZZKDGUSRNspjyK03EtdfxOtmwTvarts6HH0L22HKmoiok/VPP/VFPDiIjRPCKSLYwBBWpnR6tw9hEeehLUd8TlLBgJXtzZwx4Xf9psqYZDeXJIFHUl9PNOyN0ZCpPSTeU3QTSVuiQ/1Nb+yFgRys+jjdzzt3PPuF1twdrB8Gy80QP+cxDPK9K5nF34FE9efSFDItmW8STwz6EsGX2Pks7eq1yl7VJkVy0fMEk/252vi4m89MwtaQtXpCEp8crz5atuWh5SLgpnrM7xAwjMfbqL/Xjlr5tCquYfbI2akeV8lw/bfbygXKq06pyFQ00v4XgsG2o4QsjWbVeTMNcOCKwR5nFUQAH50q/eHzv6gw9Yn5sRvkyJpAiV+PimBUxfIkTFwx7O4K26uu3yfTGrpnHfKxzpE6BYI+13AV/rKhcZkHiOJvzHpRTUVF7yoHgwse8zgkcl1xWBeR5Ev1qRm+OhZdNPY5y/lG2oFz6xQr5qODwy59IMnyA9T7/yfYJiIr3TG5fSYSIh5F6N688tcLy9vcxuowcdU64RkDGFu76aUjqVqZaOao60z9eYfeidg4y3KPs7StYYZ+AMAeYsJwWMij0eeuzWZ8xIS1wAUbnV9pEktCwLurcaY/+9r01l+6sJspIOIqlh8K8q7cLk6SGPQjDutiS9mJJ1oJyBHoQcgMIpNlG8TTay1BwLE2XlKLDj0tJ7BabW81c9pO1lUI9k4AjaBNA7DH1eF+DXNHjpCorRkBSCCMfq3K0a4WQB13GbHoO4NqQ+9TS7dtTz/pH4YLUTO+3KvBxVpIpomLZryNfqqHq8f2kIiwB9FijR1Jut616jG1sdpmR+Qwbh4esElFZSX1UySy/QT3od7kyUXvFZl9U3SWJmPEZrELmAyjL97vrmxj/tDvAdcXjfbM2v5nmxO5pA8m0JlvpYRzHi8TtEfjt65DVI+3Mz2itSaENw1HldPx7+3SKdm1N4VyNU/LEGicRh5SBewT/vWcgdc6rcEL84BqMBHJ1Wa2R6SHlF1g4SDItC4E6qoMFYxV1xdgYIunmiNT1YhRg803AQkQ7i4A+jCKiGxFGyw8tRvhvnGs45E03SDikYv0TmvVV0h2nBvtYFUZ901LEPEjJMah7BAYTmI9KIxlyJV1Zefd154Sx+/5dnGXvA90NuGO/0mVdJ3m1EI9hx7/DhNGHTd/Q1pM+QFCICnSLQkEiZ+xF0XvTz+kWEJQaInZZ9FhX6MSxIpABwIcBPQkGwD9Vx5JmaIsA2SA/C4g/mYTxajtsJga58rPJ9egbNgXpy4GrFQzRXhqFs0KVqUD22cQjkI4cdBqgm7h33Gc9ff8DfMveJIjaBMgMKwmKAxKZ/QP4SG4g5z9PRATi5bNBOBgqIXPN+ePvKAjwjEM9Uo7EFoCcsl3xXjD/Mwu+GmD+gai8EflXM5LRzNZ8BXh0JX7AYsNKHNak2HRyhSse7Qe0LtO7EiCnkjOIGeRVALFe5+M8aNDbFuArzMCt8b/16m58Sta0uuiQNNq6ir9g9n4l3GrzjNmNObcaOhJ/oNZVNVf5qAwQDO+0QrkbEr616N5kgMIcKTsTcc/zZ39hQaJU5ACcFAUPe66qjT36fACk+LcJ17stgxhbdpP/0APG85xaKDJl4d/I6ATQr7lNv078ObXRkNpHB0dySV/y2WOrU7i7/ao9jrkQUu1zTFbXk7K49lbUTtZFWmw2P9VXQSnV5AYOBRUsYmFz4BSwRe3bHi8PFSyxhKpf4OjRzxZ1G59uk4w51z+GSeRkNi2jz7IfYfX9z+ytLbskiS99O99iysSbEsp5lA7i+qI4dul12tXmcUZujZ96zDq6ahO9gbmsYRDRIiGnsNlG5xbp3Z/I0JNNpeX9+IfLjgL6NstEpcebB3VLydo4eQlanIClWn7dOAF+KMOAXKK0yg/bxEAq7ocuxmLUVynhyXkHEG89thgs7/39m0Y9+DRZI7GaPgwx/d2ZF6xXjfpC5+BjG7edbiXQccPdknUGOF+8F8EB9WGRNn3p+ZkXirKDliFLKcwVpf6Q+yzlXg/1EQVeIsq0/P5PisfBat361kjK8KChvmUh6enFxOqWtuJrbO2fFRppfOcsoHvSQblRISbbJ6F4N34hIKgKq1t900c3B8fWj3Z8/nBJjj42vQc0+xuDUNJxsMT3/DXA8zA96mGETitZOsN2Lukkcm7qg6C+FoQvFMsKGktoGjENa7HFnTOpWjqp9c22CNNhL/zPwigLlH6IelY66ho6P0MFjG24QN0iyx2F4t+Zjurb1vC/vm5SnCHxS22bXeSGXntzYJuUVsMewVR/N+q9G/imU3aytH+4u3vnW2diMfG0dwdHLxdPuuQpmcgyIt65vdGSTFDQ2MWMosw/PvLqsDZfpxBKsxftD4942Oz9D38+ke+DgsW0aw8uAXRgf1Yul1KFwGolbcHHEZNpdR7HVKeObFAxf1EVCs+3Dx1iY25SAKFj6oiEq88lQBPYqrWEuZCJLrFw9cXe56uEoa97Pwp/sG3wTwU+wzJlSRYDaSjiGEU3uOQTtG/vNVpNIyFr9MMzLZEm9BT1/KFuH7BOrsATrIZ67Z1tTbVHN34+weK2hhxx9zXtPb0JLE8WYXmQuIpsMlf7VgNzR/Zz3YuWtB/xT3xsxQMUJ258TYp98xieUm7U5HZjhSMu9IvZpNbk756dNih1jIm/Yxb0XAd+aSSzTRYK0S3/mV/A79q9BvzM+NUG8/w4z+oKUCp1cFBJWDRVlA4bbxDwQzey3kjzwBoZm3oTAtIY4UyRngjkZsRnVK2W8upjeC85MXxSmi4sHfyKLpPXscbs675tsO0Vy9nzhUBtTFRN5EjZJzTv24Pyfo9B/X7jkC32iGzizt+VQdNlq7ZNu0rx0fusZgnFLnX+3bW4SlgXmdpVEsrCxnvySvxIDH1SyKHCHig19T0qGs8U1kaWsMo8vPi6Oc1ZIWijoJTeQztUmMhpTOiR/RmalOt1QBjdO9DRYFdPJvefeaXaDEkUAdXTj1U1wDmpr1+QnlcwaweJscPbue5MpgqJi/6pAGkkbekVe9TnD+mUNus7Ya8ls6xSs7VrP63o1dlowQ8sJmNtm+/7SUo9VGUlFJb8MgvJk0T+2aDNupcQ00Tg37JKLqc6w3PiLiAPHTF+hIEqbfzj6PSVTYIj+dbl7lymDfk4voHZfutf/2WbyeyAhc4O2PElaiRN+oTzJBrg71Ps+6hZ4WRPOaqAb2j+ewUHWgucJM/PqlxOG1XWwS+b9F22HX35iedF4lPpsMhD+DiunYT+EQWyIRjg7FLqAZx+yB6a1enFb5RUD1jnYA3uiC04jqFxtAuIAegRj6bZEsELUw8whA4F4/vb7ZvyhL958NdhS8MZxnFC8ZS2pTBSdSGSoNBbhKAw/8bucczhFBv4yc5GUD+dHhJTg087fmZ3Qt9/jg8LzwkTuBBnNet3NDiANeYKO+q6A29rQJGOLLYpiP/ZaLtPrrtszFTSGVFWUGlH11ToqkO3nR/3G3zVDvaAa1ZYQnDCKEg6XEib+JvnS+mDXmcnoLhS4f0J/11UMD6LFThXShILe+P8o8d2fk/mBxjRPoMeFJVw3CxrhMtlHEc+EG+V6qLSQSSy0FKJdGQlPQq9cC9mdiU0qlElju5+qvy+2PnY0Msfek8EkrJy9t1kFpbIQoIG7l25ZWBoBp32cbvXByuYH0Yo6Pkf2HdtB0kVmQZiG5rA4ylMyxAkt9OmfKdKOtsAdv/ggiD0AjGltE0B4emu0R3tVFV4nQeed18X2wOOA6kXgB3hp7w9rOOEaTKEBCpNTOKVLmdJCbDklTonTswRZR79UvC4sh5DdwX+tP0z0Kh14xhLOKq5WX6Pblj3l7qpM1gp0Zdb0f1LHUQklM0EqpypOWyQ3Agw+nrcujWdLGFRywnp4R2xZSKhSymMvUeWSPbnfdHNchdoj+Ab+97kuFxlUi71kJVdQQI4N67zZHM/D2Dmy2vbjcfQip2eUy+9EAeyBe/psHLEV5YEdnWMkSghdVbBTNE4jEOhURVTErhD+uZApoOv6vzA9Px2X3D6rua1YMgRYX7CRNsxo3MB49xJLl7eLnHjfe6bl+Pn1TFRn1HDZgl7V+IYJT85u2K12c5dYrkpG5aGCuL9szbv/FD3OEjP/zidz8YDpgTRMi4xsxbuOVRi4zFlSsw3wvGpYCnVQvxx+7Ve1UpKnxR3dvZAf5W868+VYA5v4qH98lLpb5cZryqy82YiNVkTB9Xt8GgiySdKGLmWt/8LKMahRvBdwyjjsVgFyeh7ngNDLyRRWoE5Dspq9CtYlsjRSt+dfzU4UllNa/TebAE29iChLxBM0cMk2Mh8kJZLb4EGy/i5cWm/NXGS3DjKGFskr9ocpK/13TOqyRFfvUPincWvCQsH76fgoydjBr2VBK7ng6kGtfp5wY0IJYzhppYS4UQJz5sybnxveTif95s0bHqWLeUMDqXxM/1JxK/JCY0VxGrr/saaahfnwP2rW5r1M3i1inwebpsjX5QcBMIaRHAuuvOW4C4G4Bs3lmgVrj/hnbtJW9YGvFDZ24bd2EiLeai6Q0VIzFRet5qubmkqeC+dv0iF0NcEmAtbdDmvLaiW+OT105l9klls2utCx61Rq3zAujRTiXdQ+c1/W/+NHkE7Z42GMr9MCdn3jCF2QlqWU4lHwVsJR83rApMhFEzV4QiOh+1gSwKisb0s9ZJWe5Abeigd/1Qqp9eDsnMcvTcCKaEyoVHHtvop4BMBN2DR14cuDRXfJY11uzSR2oyJ0qngdgFJXHqx/y4JKtTPc8G5luOd66tyauQ4ds7q6Ycs59+n2rt7LNTYKlg2wiQPcrVzFLliaY99TRNh7iWq0RBB79bmAtNTdN5F039iG4wQgwM9KKHMJgi0U+pDp6b2qn6y6S22voSqy1oph8PPaZ48yHXyH3af5RAhxzP02kofqLPVPSlEp2ZMVeZel3otH43zspcCPvAFQdi7nxBpE5FW3n6maEbv7rFM7vG69W34Y0KuHZ6+EZcjIbnpZvi7JQp0DGf0a+aLhndpF36q/psAgrqkF/5Gb6bSzkvzrnFuSoViQsmIwIqH06Mtrw4VmZblaXUkkaFO962codiN5RKaeI4ClDqyEnL2JqpMBkC1ZEp0zOUsQ0aCDrqYz39iRW7ky6l62inBL4XH3ik4HdHiILWIKmN7AqlHy7AbL3PJ8e+6OzMcgy1Nk7KPdAEXrHpiZFEmpHUergtvWyqCZ8e7w3rJnwRqWWn1sZ8b/BDsnEIQFbBpbFLUZWStyU3FhFrxYbauubFOc8ku7OudzfrEUNPiiYfUapqecjZkXomdWqSR5DG3I2UYhlrYEXoECUeCPSao+uUeXArtJKg/QZAPsc788g7PXj3MTbqcBOgIJyk2ATlgNLUo3m58Rp5Bq2SHTfG96jYzgZCyVbQG4fMzJ2t4L0Kzpq4KUMXlIgXmZ+zV1z91xkpyWHIEprtrnYNX9J36aEYXuMCsk5v0irPclpjKK0ZUDUONIq5PUAzQa/iBC2ekjCiahQ4c7n1/DQIsuSpo/8WPnvDZdwHkMsN/9OFqYdDmI1PTkkNowZCZl3+jrnpiao6R2LPECHAz9AiDdSCO7Ut8pcC/6P0F9jJQKFI6EA5p6mqfoBU5lExYlO62fjFkc8v74GZf6qKiu4i6zAC2Jm9h0upu3NKVnNAMkTeTbMr7VFDge08RNyC2G6JgVpB9bWvDjTMFDPxCTbquG9wLH7n5FO0ee+fCePpdZb8rgiJ8++H+ghjPdbI0DOhkwq1cA6fErwt5Vfp31xgFQe9UuYB64EPwrwu7/fr6I12Uwo1y/SLISQqOP3nunhJJp+rdNzyf9Pbn8+ohfJPQf+/Y5Z86CCmrGiC1x4AQj9foI2HDFsjc4E8WD47qXcxP1EBzSdxppQ/UaSMYI3dOXl4iWyeUJkPNMPVglyPo06fEgXk06+yqoNHLx+eB0mXJo/eK6jmorVUTAzus0Z73ALthMcRMoGhXyWHjtdymepgRYxv+xbVrsxZdv/RMUbMsnVU7dMsHpFTVIFYSEyhO/ez9A0GdBDH5CSmaKVqszbdoCeiUaXu4/bHJyoyLtls1hO7KIXLFdQhTihZ6XCTzNyuX56qByfncWi6WsY4CiXnlUGw3Nvbc8Nwx/vMfJGGgtdzwUSBcSnJZtvnjSULJ0eiS5hjOudhPhDNyq/LvJnHlfQjBYzfU9V8o1V31GErc2+oArT8y83Vd3BXBbsyM5HmLYRsuCRAnYTzbJ8UeFVsWI1ojyyyEo6B2VVrhqBZh62LSahJea6Z6eBLoZlrGm+T+czBodOu4XJnuQgV5u34d6E4NrTpnI9hj51yMcBbQgEododi0DTuWAumxNpliw+Ga34ThjXPrByJaWEzkbiJor4ElpV9DaabCwspFLoN+uDqHF28/2Td4ZyR4rHRKep31HmUbzC//YGGyOItRU5yGm/Z+/G8foRKNseg/aaPEbNDT4dAIOVVHQebIPDzYKu0sO7UaoHlRgdJ2XkOd7k8YX1GZ151S57LyxoWQB3G+9Fr+efXKTpJ0JO2i++6c7P4ETBsYsd43LwgY+Kevo8cKE6up+vJ/MCSv0c27zwWcLhS3mPSxwu1L0hKNUzdunl2IM11o2g8W90p8zlTXfJltEqkII57onLI/7a5KdgnWAoVQjBCLlzg5qQBgnIsOz6SsWet4COKduYT3bRgfLdMMtcVm5qXx8Ci6aBBneKRmwBgAsix78xTGtw9SSP4tQmkIwhrz6unKaT9+iQVUd5hjFMu3awD3w6CouvUJBLQUXU5AfiWRlRlle/DlxQ9di1pJlgUlNOpyAevJbRsvsKKqquW6Uu75QNfp9eSv6xvOGxJHaKtaZhdWQEPynVv+tcvIPoxzHuWGyuFtQBRd7o95v4q2N9P9B0VyU1QqQIWVrIBzIA3cb/Qq6ok9Y3wWM+2idbPL77HePt4eNDy99m4Rfb4od2xGCGhxfxZyrzyxTFvWvlDBIRR2F2SyNilDfpZnTQWLNkuhG8QTJxRUtlUaKhSTBD4LQJXvf/8/g6T4ISrjDtfHlwAWuu8UHH0fgiScgvK1yrQwC0/WpW3htSXBasy5A931UAXUlUYZU4W+zWaFluhcLMFGm/d44dFxzpeVHTx4OgOSRBsiqBvZw2Dh1zeKCcP/tFLnTMWyZYI98gVhn8yPdMyjH8PRY+ZLv6RZZci6MbrJ4j7DspEZGbzTNisMW39sQFqkZYQHxXX1IrcSDN6pTRUAZ13j2xNItbVRXdPrirGFPt0bDYXETfHllxBgmBCsz4YXf/aIOMjtJSghFhyBV18zyJqMtQ5F4Hchn9FJ5NAnJlqdjXJhBwmHIz3kgPx/VzxD1S02mzetctgNcknoNQZV170IhtmMw/0bK1JudPQAVS4UzUvv4UD8fQE4yIMogrKCDwFA+iXoMvD6S3xS9uYgS3j6AJIltqxl9/Gzpj59L84NnLxlErJhvjqtD6a0tkLmLppsR0OjF2vOP6LZBQpPw5r1jgNb/Yy1oQZiClm4pj7D817x7FX26PiOhLLSqOyS78/n8SPYTCBdjY2yEVVjazhsMRizNeyy3NaC5UUaTCqnKS7bOM1ZuIQYyoUgVobDfgssfu+8v3BlsSBPyCnoz8lzrlxjJk7Naxk3m0HRbXrg5ARDY45bIOuLSV/Q3hivY8UkG6KF525ZDOG33d+1+G2MzhxFJGBQeW4xM/Q1xCfhVSVBSDlyvno/3KLLwsF/EvxsmAmuh1tKP9vNhuD/vy7vazC/THXATSdp+A+zC/qUgFbnVk7P1TD/F7M4OMWZvCg9zWl7beD/ygawM/YjQVl3a5y86jLANvRPKPaX01104RybZoFHiYMYAxgIVEtzK789KOskWZbN/wEOYETT6KmcJup9t8+YZ60ofkqoOkseyxKMR6VWzf0S9iUzGqeMS/5m476gFiO/9d6Jq8kvIprWkjJlNBorHV8ZVgxYweiez7qQla8AL3mEkL1uHzmqxHVWmY2/+IRndzXxq4uiygE79Fcc/ldQ9hJK37uq5WF2DWgSpd0Z4c+xI6SeHP9qlOyxDDWECUymlU3X4vse4oB0Ds29BQy4HW3e3JGU+9RYxmXmI5P3ogtBxJsEFghqXKdWZycFR1fQGH76aALxo6G09gq25IRFa/x3xB4w7uyJNU3e0O0pFp87Ef62MCE7xS+7To1A+NLM6hLO/BEz26uUYtd1lFZjJeWWBj6xI3bCvLXa4LI5N8NcEcUaI61Tngdlc+wjHf4vU9qFG6QAgx7fr8XRdyXll6vxG8uvUMkDoqtioRBokvAq6lv1tLHUbrEWIz2XDSIgqjZ02pdbEtxdyVUmkJsur3NMigkBVbB7ncV0NOtEnfauofyJoRQwpmjVISklt2EBOwcMKMa7rXSGm1PXILO7+HBReqQskbah2BdJTaXx1KVe5N/8aLixoIyuITNZXtAp7C8qL+vnov+wfn7KuHCQjxBW6JU8BCO0273K1k5PJwwOMRUDMYOTrrampIot8/etPlo79kpVRypVt2uY+RTDee2GbhFIc3poomeaQxEGTmCyg8FB01q7jx7YUR1TZbyN85pnWyFwm3AtlFf6mrUoMx57Lvk/UPr0kUkDjq4FH1p+tnI65BZePHJE4QkjvP92A+WrK0N7AWSfvoKCDuwweuL2zK/1N98uvp4CTDHbOdHaN9aoVt5CTkjez0yfm1jsnngGZrpvn4zLRTZHMSPYcAMvQxZEqTNMZwigwwNdMf0dWHaQW4kSPuMuO+p+MNiSOekv9yXA76OGYq96te8KMNa2tnsW0o5os7on5BQHu4gP0mzkSTD5kUqyn3vpihk4d+l/Bz8JPPNonflesZlpHzpxe+yeLk50lIqRnclEDHIri5/5fil3W90y0fhhMb4aYCGuOMoayVNlrMsAZzbQjq1HD/cWvi92pd10k5QpMkkH5/CTtTJ7Yeg1SeEhbvzYtkFWzQhcE0OJRMd0EEFp8FpwWJ7rLG1eh4/cC80Tx2n4kb9XfQpXylAWDY3OdtF1vVWs7WdCTNgJSlk1nUTFsPR8D+jYE4PlcdjsLvaL3ZS87jIFxn1Aggpy6+gdEdN/Mznk7CbCqUwE1uZuXKhMq8ehxu5qSBBNxHUBTur5Y3CXrggWh4g0slkZzM27yOtz7x18cFjOCjyfUU95jtehz+SXH9B3xVm2DclVguRH7Jdcq1VS2p50wyNaSvX14VaiOVDAdt5vJuO6GTQzzb1hBM30VNVHyzXQpBMp4jzIEfn7NTYa57j84w7agxa+oATFs+Dmd+5KF53qiIbYwTmsm5ZDfjhi6CjOxMYuDAw4FcDifghisgT4t6DMv867re4OuCAmoA4xukAKk+UZP8LWF8AZYYfCQdlGpBJrAv4EXR/dohkGFb/RJ6nzB5EDiRLVUfyCi+V44kNtw8Um0CrVSUlVzojWMv1RR6+u1HRYQpPJJoDLpXfIBQ2XX5rYWVo1PnDY+0xkzXgoaz/WKmQIRcSR+FGWZPz/+a+36nHK86inlPU4MIShpDWKBlUqDp9hhQZ6tfPjJQS1gwCnE08U5875Wd3ZT9lwRReSNTIRPGRHfc/QHp8hDR0KENeEAt1kDi0hkawZuRJf45R2BD/PbrAYePDg75zlYOVRQnOkZi0pqRAmR+jnh4Rz5lLM1dfpC5aXfp0YD+odaKZiltO2wOgiIphGcZ7+0dIAlRPZA9s+9s1Cv02r8QG0vq2524SaHQj4nnm/dZehbaTdgydij43Pj5857861PD5yLwi+qS2Mv172C1DPQLKtx8bsnKlw9sH/vELk7hqU+LV9HDI9lLYMpDv1VYWLUfQaRFcnKXt0LC0nZefc+XNXYiK410wgE9zbmFCFAf+QrAr5IfqPJ1OGKQI8wGYHWEap+pLi+oimDDZRW05EE0n1cwJVHYXG6I12oHYHCAp50Xc1+SaBNDNbWYhUYRefTnK5oE7B8BowOCzgDv5GXmtWznwWAwvVOmZuJVAHZBy1B9DUOOXk8g8tzBhpLt9IKjsWxMgyLfd1jCVnj6n4xSWo2NIVfH3AF/UE0hF5QjSMzmmKjfWmWWPKWlBA23lj0Awfm53+lnd7FXN2qjqyK5F/adWCvmFWAR5hTyGmd4YTqBSWhHPqRe94MNk+u5Ut91qM5OyE3mzdrf4hN2Eb4k8uo3ObmSJfG82cHh+E3/iSN+LVaTYqp7TzDkqj4K0QcO0v30XiOCr0OQZidDFEMh2WnER6Nk1EIC7vaTk7ucy9cqcKIx4mOb31R2FqPa9IhQr1H7X20kNoThDvymH6SD1aRiuRbR+78FBKhxA/s/zqUzgFgBZfrGsHkgdx3ff/yL+vp/3CLsOfceBYcM2DEzn3KurGTpUVlHm/xf7CKEywL7MdQDfxzUv/vqHmUZThJqiYtZp4DQJuJNmKCiUi7KUiz/JsDlxK5xw/51r5GkCd82Z+FnfRLg86oGUFfPua5q9TibN02CwSsgf41a61FANA3gqMpVnccKjwUgRU28x3luU0obcQqYCdLo4g58eRZgoj5XRG5ubU2Txr6m4qg/ktdVYjn8Mfmxkhe+npdxaVs8rf3k37Z5ksuI4Fqj27qHByi1fCp/JkE/0ZkLEJ6Okun42VPWy+Z1wwu6K/iLLfQR1B3iwf/KB1VbK8ZwgZqr/yZkknvc88qGqC4y6JPcCll8wjK5+xEm+GQFeEE9PsgJ7eMH85sqBKCImbQQAxsxo+N0OyUMDT/MFtSSz41UkP8V9cLMRyV95vTrASIBFSK1GaWI8PvPU5QLgsUeNTHSth9/2I7zdxO7tklt7hmlehQOPjNZ3zY9q5yPLzLAlFBaJdtDj9Hq3zFESCJH+S9K4WdK8LBqM78KNNspaJUfFiDYrncMGDZJtiKkAg+xJBxtcz0A2/9XJsU+BY+zliMIb+LZC14nl+IuZ/2ppDyXuJKGQEeiVTuzLxiZKtWnxv36U4ZA9LxhkL4Xal5sarMXoJnzu3dYmDZBitJSRD6tUy+WVocOpZY7jwpB9oPC0Hl3ihqiq63NDW2He2THRh3eHLQLJUNzkSXyCX23cyYefJC3npV/H9ucJTIQupy3WkvzQoE7e36HBetoeM6AlHNwKaMq6I3nS9GSRgk6clVnRQbYza2vqyNQ8V48J+AP33KwyonNy5o9PBVwzlW8UnLDgFZXxVjCYGF5zYx33yJQmmg+eRc/Ym4bzAM86QJtNAqGkmamJOM7JEoaSHSmkjrV4accU//Nb8j0pFHX+TghkBXZdmrby8wYRTYdDurZMkiFz3eIbtKvYucPgUYvCIsg8/PyWIamw47LLPimdrVAl12SzHkGLwz7LgVolufjSVp/L3lWG3TgExi/y2FgPkW8yQh/e7/EnXtjkac77TQ1BYCumOOhoQzqqJYYEBgL2bqrm3nc733SU3cqFh4rUh9daFr3RakdtkrwqEG8zTn8RdhdbA7J3vk4vPUj5BwWc/AJiFZ5hIZs3IVSrEBe1TSdTju6uVaOZ/icmK/bIBFwzCX2fcWuWHnGZ797Q45r56vmXXYobVh657lG+oHDjpEiZ6yCe/BGqNR1N6Sg1yetkE7idBhc+cXrIN9hbPAQuxKo2R4KsMDnxtpQjWvhY/QnUm3juWjgQ58+uYKeY5V4ZWzmu8jy3onC/qfERCsy7pT3FeT6FxLisKdlWInZu9qmlMwiQGXmT84JDx97x5+MX3R8xq3TiID3+o5lQvN3/igGSMrDFARPiFGgy7o01fodF+B1geG0vy2JNmGGRJ8mDJYU29m44wwkTqInKsX/Kr4FB+P8kS4kS4bSMSLSluwmi/xgUcKjsZWYITXD94ZajdBglqqyVYMmAQO3fYWnxVdcAh8uj9+NUQK2fEGVmaLXhWj5B41fXpPFtNoIW67asGWAqzt1VhlZuHMVSlmWi/xJ6UZ3cBAB4kZhea+eeyJLFRfdcaoV6OfflXJSIruBez2eihuH6s+WdncTFpqFkkRDEm5bj8WZ6nYHIZ8jknSl9Un3xXChoAfzmR3jOfpfugan6h4Z9U27g8dE2SLLU3+TQOzowWA4UyyoStCuxlydlTUBV7fwzNXMoZjYnQsabf8Yw0G1a87hWoAA8YirKbuRzIhxiZAOdODStr2vI7OC3dSkJOAegFpwidPL4GvkDnLSJbO3kjAqQjqR4xHxx94I6v1ur7v4/cbsXYx35optg2qZ9evPpW5jTlvM4N0OWuLy3PwhySuhoaWs6s1+bUlkvD1XYKkb+ChnWhJjmt70q45kYHS8UOCpUG5sJrcj8AiQbty3kjfxv7j9QM3B64mCsC1T46YcPJE+nVCmw2k0Jjt9RtjbHfGeUmpe7OixLCQm1Sh6o+mLUtlT/o4kGt2d+IC+V/78Y1gOn1GtW2Zs09iIbVJaJcs5Vkm4flDr4kEgvQwU/1OxIvzhgJMLEJHU8mSYeOHaayuP3bgPayxDy/Uu2Vhn5sSTxFrn4za85TWjRVUF/8Fn2UKu5NXNqKWuUKiXZKLOiQd2XWUM5IJxFFVgfmksRJr1itjF0V9zf82zsu7SNOckMb8CTfuYG7ErEWcVTuAoTkTOqTCPg8EhyfOFe0576Z7XtqR6bw/W2R/FNOoJvPW+JXlUE/c+rABKaf8YxhEvngje4gJwx2EifCh+A6Ypwmbv/qNt57nFUUO/jUEuMxRj72TaOzBbcS4x0G30whvQuWYGp0oGpodc4FND+bYwQxWoKAzKuJy7+UFCRL4H6sHoMHHrWeZf8q6rcCF3uUqQi7We7q3YsmjWDIcMpGSb9f6sIsAEp1UG6ebN799mJzXSCUKbpafHLfHFZ1DhPKxUXfIFuK0y9qcQrUdgbrIrRavXGx3hrFQdGj91J8VCdqDJ07j8FQpYA/+AJj7nG3MrDPqZba06Qlvab+8BYudPPzjbQWco5uIQjOmDWLI1agQG6ILaOaHKWmQXDlLIeUhoXDYAh4qLuJYuo50a0EI/NZc8lOlyn9ofLFjNb1qCE2I1PrEDNKAm0QCAh+OTUDe2E013iX8QI5iLuYm9PtBPt5FqSHe7JO7+D+C6o2YXsyZnmYjAEOVtYQRO51mZp/uNY2Y7DwFmb1yPc4JyzcDrVcmp2VIIeylexCA1lYvnW4zMhDc/4rSNvUcM9jwNoOHlpAmUVRgv1os9FE+rKqXL6wbu9BCn7soHujYI9JVQnyNjamZOSfF+lepcxFrY3E+YKNz/V8VdvXsn5uHYXPBHAR3mPp3PJuyEdgjigZNkhVOUEXpDKe2cAdKNhNgJBJ6knDOIuhgrNySqFRcqR6OD+NRDYuE7GWMbU4Y1DB2fWHLTefkZf5azdMicOe/OMq0Mol4yVY3072w0RNgYYhX0/LIIDPpd7vRY0bBOGAeMSUdV3Z5Znlt01C2kaVspEENoAAUptUv0sgz34iDi1Uoog4ZybCVYMLmUQMKQsA2oQljKjtW8QboLwQaGOqGV6MV/ZgPDHsbskCAr9jRbCMuaKYi/QBL3cXPKBjnsTKf5tPYr1LPxks1wdbwR/m5PTdzSojq50sdoYCF8zWGXv8lFzCS6dhn5JVMxQtTYVCJC11d7nzEIDXck3B9jM2Kn4ZVgAtCJRjrpIffJNAJCj28qo8ACiym1Xm0QtUuNBL+FYPTh4o96Fg/KxM3ezCfnbSBDNnN+bhQM9xjo7Mpq1SKnrJnCUVzL2c0Brmm2hO/Re2GvXsl6/OKrMouDfBJxrI2nDaEQPT9QJczC8ucIjz5nNuU8Ylokct+nsQvtvTXTxq8uGvRnfaY+I5B7ZQix8pqktRbZGMD6OaaQxeeZPL6S5PC8lFO7vi+QoS3AcDiRqEjPjzeIwz7JOdy0IkKu18LOv5kwX8oMZKzwao672RXzwcqRaEZ5b8UOri+l7vLhZODuh+9LWrNtHANBoocpyMNuAZc+oMD4w9Of0P6C+HRNm4LHnPuMBAaLLVpF5pQclA5Ij/bTUcSr76j5sxkOe3tdC/VuMbNzyjYEECHYOHnz4VRngKap9jQA8cI/fhjLEx2h4bYSqOXpKV0Lr018ZzJpp8l+9Ryjqt4PqI0vyilEPD9jI6lAC3+ZcX2jp2wMiRV6oya/mC7ftJVbpaIivfWR+mmwz5Q1wKbB5Y9hgkZhJNkq74IySYgiiqYNMYa4j7P3ZyKqQKZFUfqHPAlqo49DFtuOExuwn5efLT67iw4y9kIyXy7j4I9FW4yrkDIgDXp7kaCeLrFpqZVd4FXgiguTORyr/0jISebhE5IRAzLzLbXZMoPMBxp3c6aOSY762x4qGGQAMlN4N/n6pLmJyAUwDN/wZAarO1djoawCxxmvBxqRC3+877W0GAli2HKEUmwQTPSXc+0lis3q9CYPqiLlsSHpYhQhzG2Okw9x5nyVV7jkfXkrTcHoBOO6YpYTjNiSsV2Iw2BwA055cLhsPErIMrFo/KiEHWZ3KkNEf7c5II1HDrmFscYfTBpU0h0dgG6i6ctu1Pyw4mt2rqy6jz+NZWY4IdW7j/JVs2IPMPL6FhGdbKxJZ9Sf931mBYq+vXErbVOHQELJjOPr4FhN1/pX8CwqMDF6NO8GUQJ4e4lk3SBx5n9kZyT1t0ppeM8c4MfCscSP+KnaCHpkpyvvE9vC7n40lahEkAqVbftyLbXWyxLUAqkePPGl5qgPTZh0cdFsJiloWi6ptk6GTFMq4Yb/vCe57Mxnk5drNTdu2BrxKZ9Hsb72jaevlaszdzewx0qmwZh96amfw6ILSk/+8f292zB7Avnyi0CGqpWKd18/Usvx9SRwYr11la+uVhw0LAqev5pj5M2QCGCV+KzM99edMrBWxE+EcwGmTYkspd0pWBJR8b6V7BR7hdLrHxdvwPwEkrhER0PCo583eCB7QGKLh9U5inZJGSW9k6AP25rBpQqXyTJjIVgmw4GaPLGTPWDXDeLYjmLQkNCs2fMV82f5iOX0Tc7XIdUBH/UxtWqc8yha4EGzh9kCPCVdRWYBUgtO4aBsAf2Gv1vLGjyNnBzjLUxg6o2s6IstGarneoXh4bPwzVPTw4FxyEqDS1zc1dvGKgMJpg8K0+32eYae1NY0qL6G/7v4uF6VHqPQmZ0Odj2Zwm+UJXb2pAOONdO5rml9wvU4u/M/dEziTHeZI0QwJYH0HGWVF8+GI9GR9z7yZl80t8VNFov9B9x3wZy5Vejihz+eVTYo/w6BepO01JHpyAiLItx+g4TPnPZVCwdkpgQiN0VLRUzL92/Mu3L+nhkMtg+oaBaE4mOWjaJdBepi1iXsVsdqgffLwysBHNvbKo7prZ3NDkrM9dtLlLXchYEJz//rD1mbVpehwaDCR1mnA2YniOckOK/8ogUOnCgc3Ax2eTS4tygT6VpNWEitI2s8hHVdTBQCNIHmGuZLmhak6Y7v5BdMrzMNh4YqvzaE7QQTm2K/LiocdJtEtQ37TEqrRvA9Is80NoL2NhAl1Bjm+Jmzk8xuM3iNMHN8K151jkBeOfgUVV8/OamXqDmoEzJlSD+9tpbWU+meKsSC91n3YhYVIHFqLe1l9cOyMC317Rlc2MVb2ULls5Za1sQYK6LJli4tewUsZ6vkz4tX+qTTM8Bz+vnx4kJkem9PL7gXZjmVpmvWKfPbtg48J1FvNR/i5Zkcm3BOXfAju/9o9NcTG494CnRWHYwY389Ud3D8/4EzBdNqUNbkidySHLnA6chioTEQNIv8bqfwBYB16CCQuayMd9TUWSqRkjHPXkTFW5SGTqxrjV6tz0FxQBslgTNw8A/4x016peTZgeCzwWR8Cue73Nf+U/96odatCeZLzhYv/05WVh1N5/ruQGysUZMmPW291ixhVw+B8h1e471IGApgbyeQAmqhE3E3ygKSwrODRCeUmCGGTRK+7rVJTeXVhF8uRYbB69HTrlfNRDqtWbQsJGqjBXIXOlipudsYXLIEXfLOoD/uFn85ySc7AO1bBeKlQWVlmHjCd6Gd1yMMWXDyJP+LlITFlNNo3fhlQuUusGA3omD0nb6fv9I5PgjIJmvNb5xONEDN/+yn0FNQjgxBlFhUPi89TtiMQO9czpenB91YOwTGzYFtuigAY9IWlA9plt0Tkj2c+l35wfN1QHcYOtJfFCj508yzGWDR/f1lj7NxTYoKcA7xED6YSb5nC8Y9dWcf0MWnU/2+O+BO+cfkPfCDAcNmM4njphKyKnjiIjp0Ja2Oab8PUKslPXh9drfWNuJkkAIb2VAxw1Redg6z+0MTbl98nrmjvkcGUbngrGB0UbYaxVKfOs2rKMExaGZwfJY+hjp0xCfcm/LgZEBg0S2d4EXJrueerpwxxfudmqWxOdVVx3SSjlzoUYAg2MWXwo2aM7XPeePZLKOv2z/Q4nLoXh7SdSTazrGxPznBvOM6k1HIN/Lw0bRA3gPopOaoh0THFAngHs7aA3A/oi5HfpMq44Y+u8mAGPozJqnHyEfg32dhoQR9VSRXk4NvbHetu/ynZNdfNivKbWB71DwVxZcyhZ/4y0xCsfg5tKPlKb+If2WG37i/c+3kwjUW85NPmOUxO7Tkr+h0g+juecPMrcD72XMCYxC4LMh+WCvkG5LkI+iUAr+fkPTi03m2If7MoQPx/Cjveniq0z1cbkE24/QgpllOwvZeJq+XEQlb4UVfTBNJ2AbdVGCxvA2ue5vpzEtk+/luT5aJassZFHU1tq0JVy9VhxodGqhmpv1w5bvEEuxyH9M24ochXpMpAUuCFDqKmyUbOQ947x9sRp495ekc753Gs005OIXMyBysp4/b8oesj0o+1cLNVKJhSASyEsbJg2gwNu7GBLpxvVJvypdqrEs3YT7HvG3IMb77Cn7tF7BZhZiq4fPurhu+2CgYink92GDxVjQydrBtmhvzkrYZ3Lcm3nXIlFbCN7p36j/cOFoaBaFwWt8/PTlJSIpAMxQPsJKjNZ9DA+nERo4FqnNblf8ef6mt/hUnBhrSoRijWFDfC0RBiw2gX7biPCrEiCN3xR7so+rf1b4CeHqG+owlQN8vMGCMssTOeLsFQHMcygcF0v9v4dtqlgO8UyZNaRaIkpCpAQ31xhyzCJHwD1HUYRtoYZYG295ZyT52CFAPgHLikzqlzGsZDcgHJVf16oD/D9vdn2PGvAAl6XSCMuX/kAMO9YOZ0qxg/t9VUGlN6H69tGQAAU0K8G5go8P1A2TN84yipYXDD4fT9tPcFCkEIqhMEkwPRTOsdvyljOrla72Dw/52RFQ6hiUBxx9ncRkrG9RyGTvGk1xztIJveql62bxh5fqIHXht4JxviPbXDGKpwvxe8eTilxXO+eR7jXmWJ0e7OlDbM7734qik++LvVdOmQinFPFM/Tc0BrMz87C3ju2DiUiLYvKs2deN5dnXjYDGDjuoo9URv3ZxeSmB4Rj/550p6gOSZyzBDokG91FfI6BqTcePzDCimAiLV8rNYWw7S30mTl6m+MGO2O8oUiwDoRof6Z1MBW8Hc73hXpVWxZFHTrClwHI7Y2k8J2tNJzeuvpzVRNqPjq9nK5TLM5tCBCiPBbPGZFE6OfSZsRhcjEQprmvEzErwswyqpvVh5k7x2FDBnyQsEVp0NlaB2Fqwo0ao8heI63BrqrTBb6NK1tzJEYQfIvBMIZUr1ZBb2C7NP5fzj4jMm4lVpQxqCEO9iGRTziRXd8sjOqYyUdSQfjuELxhi952pXTSbxSGuUcr2T2AMy+Roz/dMNpL22rbV5SOAaOj3cG9SIjwOA9aDz+e5HHoyg5SJ4U/Np4JevfOcXcp1Otqe6wvf/g23TuUTztu/mgHmn+G7BlLdUiL+n9aEx3IoNA/H/rO4qhceD/ONAA/gJjbdpxTC8ePS0PrpvPhiNFFvJNYQOh2o1eqGLO8rS0YwCYHUfdwKr/mmiZfg5mHl2j7uzeK8q9lbeCdVio4ZPmVRFT4eGQ7R2LC8Eb42noLveN129RDwFkMrPtvlLHFW4tV/WwLt4i9ZGStqf4uyie/r9+icRpJf0ySzaftgP+nU7dLvlYZ0Vvn+Y4flRukR5Nk7Hnaa3kdQqbRmTk639DXvGZbr7vda+8SC8/3ftNbAf8dA5jaxquVyhM2T3PIiDXcgwEPZA4oA38oU1Mmxwc8VWYtocBJncnFeY7u4tS3eYY/v/+1pGZCAXQvco3vXJdJhz6LMx+RMf6wTsyrE13/G7xwe29KOC5RSD1rtIul8+R1dBdBLPcyZaoiYw2ShgTboSoDh48OceMtNYdm0T7lpmau+pyRCreTrYmFsdPuOMFChx1J0hc5mvVC7srfK1GbNWqBlLYochZk0bVCChBClLIzmO9O1MCvX6r0EqOIFrX4/44OEHCsKp8pdInFdsyC5/CsfEVxMLQb2cnGiIbkcCrL1MxNqn7xAV5VszuYLWu8bNeDtOwhxIIDi5nAzshVwQOG9IWIwzFe2geEEswkhepXvp9zbAIGMVvMr3dnAPksvZu5eYYDaC7dKsgdvHFIX9OU4rRR1EDg5JtML9OklyXsMfvVbeZqcv3FVbIlF9q7qUu2codNPAloqGMu34ZGVgsam0sYNrtlD6VBCMW6Xz5in2VadjFJyx2qqRZQoB37cmpA5ii3e135zWb4BAfOV//z6Rzg+YYQkcmex2p69bfc4sPn0rXM/w+bFsyyHQuBZ23J+mHSMJRSiyXO8yz5VjO//brWXRW7INQJ0mLcRw7LGH+rXaZLJk92QcAoor2NNK9UZg8w3zD/otRlHcd9gQ2A2fQYn/Iw+EfuGAjPl4at1+VptAVOh/ddcKjbnPPuz5uy9lw1iNgfvmtBHvdXXW/D215oA8vQjt/MhMBJEUWu+QKSNY9Wmfaod09WLQ0xWaigzjkN0mn2qecQebYYSYVRM4wJmUzppipnP8bMVD+Wr8mNg2K/rOLDVPs53kWjkyuspBfzoPZs6LXCv6Gn9E3EHpI9KN0dRyS5zQfEJfT+CQCn2/l4XatXBCU1kmXt1HZ9rU8F0ySyzylnY17XNhRa5DxPmF3NynFXdL3DIVoPvUw2G1ElF9E/F5hoJKuxgFuatBqYNc430mvtttz8eb2aUu1yM+boUWCFZrMhirCDc5iVqd5Kcdm8nCcYHssoeTd8ehM/Yha0J/4lANO/MzfRQLgszQt16XyzVDFhzxtvOwlOQizAbZNtzqjgALZXEUgUgGDyscEd5KI4HzcrtU2z0LcVZT570EyNXd1WKbgvG7uNDUCNHdQifPC5hjdKSbnyi+Xhpfn8UAkP4lk0cfe/oH6WUQ6CZEFrzE0DN+1OimECyHvENRg6FGwAQs5XtGsaw0sx8VuNxIyQyG5mfZa0mitK/20NRGx7PO9VCt3m45l20xKMacfVl6x1fH4ayi/OoH83bfWlLE1CLs2I1/KCCe57tRhjlSPNa3RkHY6dZ15zdH+baOFhD8QmHZ0hthAsOCzh+MQSVfPvQfcQYHBthNvW2YlP7BLwWYENL/KbPXyy6Nm9n5QP9ZbOuOxMLo8vfSsRe14IN/ddoHv/HAZl5v0tAFqit86la8cxlzQaVOXuSES3HCiNaguUv1dKp2MS71qmJC7UCWoD/pRRoUcLrCQx7cQail1fa3QV9c4bE8eC3caQfJLcZgDQ6ehzIuSfHgKpKl6fCet6R4L7IYGMCsYuX21PDWZCYyfqALwTbdIo8LusRQucS6v+/hum1dncGLOvUlPZFxHRO2dWdOjJ+T1+lxih6xcAYdtoX/5lydph22aZWo7eDeBpkFXXFjnvrP1mL1Mmxk/IpMyH64gI6HQkzt6JdnVFH4Y9TcEpTpVZorp2d5ovjxA+Bn2RBS6IFINqDwYq32Tv8p4FxnxieS1yckriqOq+O+pucT24PQq9fmsUYxmVkIQRlExrw8HFPumi/jrJQ9YkJeVKKz5rDFw2NYVlze/kz43npSPmkqIL59ZoaQgg1z08zR+veO0mIXPGLCh9UnmMQnc0/t1vEtsXGlgcl3KD0pvrgZt+Q/wh//MGTYKJvf8SeH5L678/2WimwB3EWJ8qGPjOGNsPAG4+7x5hLGvIYjeU2YqxYs9whvOJQg0Xg5EDRRpLLxnYDmhZYF29sY83vMTi6p83bU8fwGCjo0qN7O6BVCf8tVrPfRGUTxAQ6plMuoGz/E2dD/7oRpkeEcOLV58BLBGKUE3PZBW9ctLSva9V0spr/y4yT2XHg7TW6jtx8Z3MEpjSbKtnYo5ueha8Oog0yn0NTcfgLRAcKdjBEIwhQgwOyF5kRdlxgre9FYKmeFcWY5r+9mr8q6AiBLSMmqQjTOh/xxvMWERW+DuF/J5f/b84WWP4qSalpsA3DlhK0koValbrGQlaqIfUkgrDC4RoX4JQ4qqAUOGnADnyvK8Rz1V326GRN5Sbrij/j33NoR7t4nKerEfBjEOt0Lp702pgyW1puk31pq0NtPmg7WdsMpYK0EgkHM4P7wqA2tuOQWNEle7fmUHfEMlpFxByzKyhMTWWRlVFlwO28675vrk0aKLmYEaS7R+z2smqUK/XmOWeSIZfLWSxN7GdhS1wM3vD+HCbBIuvzWtKMQfjPzZh+V4zfVdOIGvCkykMro18s4GQsfTKcdgz1v1e+kPd7ilx1DlX4QEX6MtymLsMycTM97rjBAqXxOa+0lxD9vFU/5lSFkPh5+BX0tHwm6r2YgfjYd07gTOPOWjPTS4vkmbSxSDziwp2kNXyXOQFS3uoNmArDvZR4PqqcP7Sqb4h8f7+UFYLy7aneMaqWFgQIjNHX5yRL5owW1C7IPBfITKSf9rwxiuw2gJT4jQmyhgXSfUYF10zQUMuMbabNbLXvb2QDhszLTHHryDkVJiTtpVPa7bdSD425Sh1uGalF1DNW0I1og0+3PpK+9Zd8yR+OVjiTcgo0wKZbjS+GqzFY4KCKlteNLWMGTm0e/X+hs09fecRDjCUDiiOWXiK8N3TYmYyjZt+wh2fKUZgVr6hjI8JJtEXsO4bSvgkm80B43I7/mLyrxJaeMrZVKa2YwdmgncKfPxUM7Eb8QuFAzpIwSntMOIK8LHUujqrEQsb5m3hdxQmigPgiRntm6i0nGPDx2qA+Tw5+kQfmwoLYpDIvcCnHsk4CV3rMHzi5KRVj87YZXQJOuldH8Q+ckJByTOj18e6tf79H3LRFck/SAY/5UXUPYFx1Bvfvq33HMD+U8r2Tb7N2pFDv0Y2YZwE6+yUcNEmFhWwWYeRfEMHFO157trVJr3nZ2jHJ6FYgHNkq9jes8WG8ucn3CkNj6Yi7rhc3uvtMTGdWi2VuLN4wSuBBgpaHk0Sd8zifioDNUS2FfvgljFj0STVSUfC4Ks7ww3yyN46YFXfw56aORxEGm+5zY9wbmLN2PacFm4kAxgJH0zMEvVexJD+yTQpiEhp5pw5KuRWTaCyCdEEia2uwV5SIjJxzDsFX832dRxeAAAIzLw+MfETz6ZelijiHlF/NU6+i37YQJoED5gjSXk8P5+7Y6ZbFM4qLqslI6/cCtLYG0fR2acT1vE3WRe/UZbIA2uy1M+ipvZRFl0X7vanyHuQdZCFmRH+67hG5fy9Nc+NZGR/SyLFGz0oHwqcD8WZ3yNe28xuWvQKWiTQVYMskb31cYqylYH/fbzNnOWAn1LvBV82m0JBBCzOFYe+M/frKvbn6PbRXH1+rm7QPN9sHVFJaEhm38JBGD9IuFwYpKX/paIPVkFtScn4gheZ0uqdnDzXDbPnMe5PBqffXn4a4uwIYjeT6sqmATwGIpOCjFt6ggcnMTBPgVTsfqmhwKqz5mUBa2sL3oCJGqvRcQ3RCD7VaWnlrbHIvP7cAmqTvhKmff0b23aGHvsAx6XXh+Dx5ly/87I/s9OxVp5ZI+HoaXCBg1ooi9fZ87jTlqZyTm0yL6jON2WbSQo5WniF8yMHYLrF3lAyXXHwaOeF6dIhxyuqS62pNcApD8J9+IQzjXbIUFiTz2Msscd4LPre7fVjfcz0iY2FNLSazNOGQwl6HMk8JqzLW3g3HtRGVvMV2vGHMeXkcHjbGNKpE7rbncpkavWMYiz/3xPd1LYEBVInDgdrvEr1ek5WO3G6WDBl5blquYBbDbVjc7L51mbIVG6ZqX5VP5z37stRqJDFte31AK+O6BxKCXqd8toGv5hXN5PIS8lsiYVtGpQghxjiTyJcxApTEpESwA2aHKxKsRO30u7VRKEYY+OBTw/vLJ7aOuAMIm0zs6coaRV0VvZimdmG0ANyh6BvWxgzRi91i1JTAX/DKo8MjvhU4P3jHePNFfGiiE2BWAaBAVdAQ+0KsQ9kyJNqpI1bSq0gJQZOfHOXVY1dOUtzb7euHNDx/Ju4y+xQrqI/vuWq1vL9Er4H8B/M+SznCXJUWu5tEjmx2us9S83aE907M51WysLVS7rCXKzkBI5UIU+9b75F6tKEtLh/w8yE+vYBeZwnen2ArwiCmFsFImQ/CR2j8hnU98PCZ+2cVsQofRcpZW5YNQ5L1VeeBBgEGwcc8pQvUp/jc7TrBWWATOvkMuU+QMT1y6Eyo1aZoH6GV0MGPiiGv0fPxpFAKWlDtv3cn4jQzi0nJaGmk/oQIDH4IxbeEKCwAHqv6ss0INjQlNtLUNAIeJKUZbImZXGr5DEeT0eNK1XmucbxIycDHLw9/YgnHSZ6HLTFH7Tn4FdCl78ladbCCZSnKDTVbiUJGWeSpprzgM1IfRciUVpbx8B8r8roWoj7shgMfmhceTFJt5hVcpBjPVCb7YyZY86aKvlKT74Q0b/P/iDfUmYi0tvZINWBvQHzhMp2tAp7h7lL+Dka8YT1DiDPaU5Yx5COs7ZzunMjpL69oa3/K4klMvRvfVoUEdZPRUsYXpyHmPWaztsrj0+ftVuMWIh84aowFKZ1oH//E7KwUQWFsML9WQUQJl3yZo57HCvLiwKOwDQbVRoe7OM83tK7ujOlI+1NYPvM6bsWoeBEsbmnbSKVC/6VDBoTiZJj9RHBz2ENBhSYdkMjvdfWruQnDGBVRhPaN0q0dAIy7tc+7a5wjEpLbDee4kr/S9HdWaprhfM15URgQ0MYlmboUFeJ2LzYEOUA+e2IE48gERc0J7Hd3oBU7HMhGq2sipvZkEIXMgJ/V/KgcyArhbWJYTFqxaBlibkJC4SpkpV8vLMzyptwM4wNa45qlDgvIvXJNq9EAheFKgDrZZY5vQXfVQp+seaB+NkuulPNq5oRWr9ttGckzzPg5MvNVrTkbA54tPEj0b/AUMXBiTvbJklbM5eEtC2YvHx9FsltmdyFTpErL+eNPGT+r6fppwkDHhVOP1VgjR5qIu5YDrbCyMGdCST8rie/7CF+Qj3fEws+QXOkRUeBaa2AwuReNWlJ7fjQNvDWnG7f5yf4doYKcEtwu/tatS5KgcnTr10PaV76FnfrEvcrV2if3qp5wZd6gxONOFqrBX0YSxoDovopn0kGvaqtawqgOL04Emh3ylloCKqTo9+9IelAmY0WNTV8mv0dUXkrKH4x0X0UbrXitv+RA73cjmuu1G8vlu4K8yZa8cLu/ffJEOpto+tIzVK/8L2Jq7hizlvrLnanQAVJS4LkoYthmiWs9+gpd6odpx29iVcMiHTiizac+dBeU+CWmKmtJJON5a7ScepibfIIxumZMy/eN8iw3swhQzPiyYohAzew9HsnNe0GUalPIre1jdrRY2pdiO90InjJmc/bS4e2TNQLN1MrTE6/NtXipWSD4QAZwYklahl0ApvLClLDv5EKqLz8bzgCDdQbyYzz7zpkka04Au9P5SuXZECsOtTsv0Lr9VARNe74sgunUugbf9Bmy6q1+oecOvpgYPQ/FkBqGLbe+/TysgKkmeVSmNVXonZ/vfLtGArGCMaeG4A+Lt9tZyxZZMFf7e8U1F9BWauu/SEyo3H1AAQTksfcQEWBJ4fl3VZ7QYhawdOgbI+dPh+F8KdLRfeelzgNaZS7XyZwtQF6WcS03LYag4HNaLO9bWliWilDwcTy7Y3gmFjgzcAb6EaYXYDSWpTadbI+qoRcBrXs4E1d8hInpOmoK2ugP429hsRYxHaySydPsUaB9ffE0m6yXRMG+EX4DwegvJJ/J+1bQpeGuvCkBj4Dci9WRVSBoGUvB+y7J8ugU6RSvjzkk0WQn7S2uID+22m0kcqUIF1Kl6K9kyGmKYr3zJQCO/2y2iuNOL+c/eQgLeUT/CAjokBRyeaw6WYIce2hdBtDiyFDEux1+mIX3d71iyCjm4ORCtV5uucnfo/vBPzlIcQYxz+FnbEimSoS8j1wnjLV0roWetkJsh/s/XPsRvtCgrL6+Pmm+O+Oy4y3W3OaOf9C2qQjwLyS12CKRLot5PBmWrXhtouqHgGMylMKSX7mPjZE4D1/DxLLQQQsrBIyUnKeYad/WF7Di6A590ZIAYOQiMyCXgNA6mOPB0o919dahLMqExZS2fo31QoXVwEo+Qa3S7EVxdd3D/gNCCNH5Y6QfxCi3g7agUFOHmySyvQbSAOkgMEqKwkl9fTUN3e6oXCMq8uZsYY/WED7Jy+mpy2IWBJJ3l08SPCCvv04/aRr7of4sY41K19YdhOl79gV15oG2A1dR3qPa3qnrus++aKmdp9k6JXrn4bxugcctlWoHNn7eSKrvNl/tgMdqa4s10oY2zxb+y+gRpvGzIz2Hcw2mwestcbR8XqhZTea+0gC62Lul0p1goKIEaaWNEFqakiu8rKtjPoPakyPkYhfEctzTQyNwGYQ9caWcz0TCMWb+mI4pcFPi41/ok603SD9mQ2bMdGt33Oo13vXx+ZEiShu578baF1ObFtaacDdxd+0DJK/NkYlE2KyQF0t6UXmqD8xh0o//PcCCkm/pR/VflVOnZo+xDbIW9i1wJbuvKB1YhJ6jsr0IPxWV0I3+kkpZDJnpua7EEoNvCNHRWP5jbVaB/MNI+++fAuQDFa66YIrKfS7znZ6QgheGeB1dHKRODq62zm2GDtPo7g94I9Zn9lzq0IWzjEt9x3clPfCJAA5LNPGSXZeOD3wdVFbVGolGRIFVYm+VRyQBNChtGysaydwZLh2m+KrTDROJEwiGUMgO5crrfnmfUahd//iGoftkceaqsYCrhNc+Vv8ykLycLcNh83PTQxuE2cpA1SSRqMaMhYx2wEFW5JczAq/rh45qSHejd9Q+4EOU9oEfwULJa+56zbwG/1eBPmCikDgTgKuMnIHU/noaUItcV2QRQdLXk3ufPWrIFS6VDCoTiVpXKexYkVgMRmG1NCrYpQLn0FKunhbnmXdeTDEaiJV4+I4GTFHX7cX+8eIRV3zw3wgoIe4/LumFulSQhyuJV0AAmuaYDRbq2FS25dJY06woMQNBZy617gqC+2G+2ykYodxxieFwjqJIYFyq/i991F6cfPc1LUKcZgDlSBT3mjOwMm4zH+g6x5ZZHVfBOPaltnScwnyd4wIyF1vLda6kbQx+iKux4/dk41SYQw57ioYlR2ZjvbY/ho/zTDFmsX6sReKLPI4HYxdUoHCb674BXkb4hbtPWiKfmA2SK67ZFQDXuGs/O48OduvNMMVIETYnxYnr7IEdBv6P2HWDF3mw/NxNHF1JVxhw7vgnllYdmatlJSRB0Mbj3+hA/cxwwo/3+ByfcFEFPTwGP1S8taQARSGWSBrvrtwvvcPSm3GfuDOrqMAuVvPocBl268yARzp4XzifExNrI8X9CjW2cs8rzCgC0x07Hk0USx/GlbJmhysvgcZTKonSPf7Gy9DxOkqdfOWaKrF2viCE9iRw1ukUwV5rravU9bMqYZ/dcU96xk6CijQBOCh51O5Iwhp3J75rQQYLom7Eroa/UXhVjTPncKgO/4TGTh2LFXtwRLoB+2voWPs9WFJjYVgVtzMaYEuS+rMflBavl5lYOeQpoZ6VydGwwhmjaGSutpkDDY0l5TZdU923bemxHPRImsArfabVh2oFn0bmWT96TVYPsujPmH1LgJFkIo8Uwo6oOw++tEI4+jdyDrkWqSqZ/ERHVG7vA0Ptxdf8JaI9tCwmRkxEiPzGthzsPsmCjLFVYxvca2XuFOyaSzF3jrKhx6a8fbjRqKONXzOSlfhtfZq7KhnGyQZsQId22G5oBleoNDBPMmM5KYpxJ1Fqve5IGEVAeEogfRoQIZ1Zn/dpzy64rSvReBIP4Phtu5iFPukK3azf4o3NjxSz/rGfAn6sWx1c5zOh9bc0dOwk/ek3RYBNhAYBhLJeLe/fPiWyleN+NN+I/DwNZD+/wU7ub8NDjV95+ed22rBbtkCglUxQHe6b/uHweFdXvgxtmMg3Rhs5IGMOTm1uQztAYry4xcQzKCKnzzRnKqIWqQoCw7Ot489piIptXFTdnnL2lwU+85CAyM6eCbPj/l92blkPC9uvMv/zv4PoNuHWTsl2CsbBA7n0MiL0F/EZ9WDY+didEUORKM3hlM1vI/uaFsEx8bB+XW1upKxRyA9ZwI/ul1sT75GbjX5yuDcPzmri5loEedfggvHCF71JR30NPMtEMhAFzFzOEu3jKZEcHdlQ0VCzfVCZkbrNCeTppuEVACRh7mGP7sYASRE/rhR7YrMtTskkLWw3AtKpK+4E48fyLzZW2d4CJ2USdMNwlrUnQNkyB0o68NWu0V/L4TC2VftTmzFue3z/dj70v5866ZYYdRGVAfqLR8NkDqJOwrovOY6mOeETmVqZ6T4y5yWPlk/PJSWI2X6R38MytB/WXEXPAmR1RvdhQNeh5uVOJFZe4qrG9P3vI0CXpqSYa5+1d3hkwpuUK78H8DCA4ZyKP/crX85VwOuCt+zbDcXZrP8tkqI7XWgKyy9hxqUEfjKUntXrJEDBlXJJSyKSxbWJVM4wzAbU4v10vC2i0rj4GaiEe4E67LGvLD8rWTXzuH4PN8GcFB/1qZ5pKBdtiBZrNeMLbWpowE/XxdLNXC5XunTkHuph8f9CrIxbH4fvVxXfl9alY5r0Zw+BlQ1cUmEV8Yx+yeF0beEWo4KpbxBdl1JomYYZaRIrPHT2c2Vvzg0Rr9DZdtwfUvMRa/TUBSJYh02XKI69PXnaO1mSOGX6YgC5DDaC30J/SHbxweozZ3pksKd/VxMxyhfGACg+F2ZQfdt9dy0sogpkQl47Xl2BHdhiUMVVSH2FisEM8IShH5BRzXKGTySveA1exK7nT2c0U4teDv4/3xJb1pTq2IPEsvpkRClggZRYosTEO4ElodFynmziWshMHCa+GXN1M8Go0eNvkMUvteTulr4nXWn012vITq2x8AD6GEc/d6S3GuBmGxotiqZpZXaW/1UllXA/5B3UdLkN8udv+J9lhmJSmojLm/a8w5YWS0I897N70ANEv9WNp+91jlIgZemfOc+psJGx+UsedbfXGeS05YjR3p+M/ZqwzQsZSn1hVD7mUKeYsC3kThHjQ3VhId1yBbioi9vtZJ5vio9z1ePYibx83/+6MWYapSugBWAyZ52QGvPkBG6YVTYiq+luCG3HuvIj32dypnihC8/W7W32eTmBq75TLaISY7vIVV/FHUE+JPMN6yHVf+5r9wbT8NmOeH63jhvEOohOX2mxSwkIj229UXfYaXpRa9ySTSG6scPiknUxJunUDC+1qAR5Uo5eGG61pwqTYR6oNaU9XRQ01H3yPpGTLLf6v1hLXLtVmJevzRBKewLvd/mUYlGRzIER/d2TFeVHxmqkKo47KZYX72tTZDT/uDSgOI/G4fC9RIHjRIDcLYxw15BvtdY+ET74CkhNY7GP33NegL7Ct8Xqqpieix8GADIDP6PGHK+xn+1iaTjZbB6ldeXUaj8cDe109krmDQhHpFMV3dixrXZiyOx0pFSKicuKRIZeWEZiPFbuknTHIKShlAdVSS1LJg2hr1AiyTxziwi4olzK5KIBcbCufhCtvRrrmp5HtMJbFIvHdphgZgNQ6DwikfhXbkxsMA8AN7k5wAh5K020EjuXGPSxpTiZq1StGIGrFfbSNTJ/Va9AHLpDiN9k0FC3L8o2ZtLlqZ/J2RqZJ+AkFQ/0M88F/X4CcI12tAyGAErqWHtLJFNv9SlwMe5+uE3xH4SCVUQZP6ad6BX3p8ScNO0FfIkiI5rKh6vLyed18ijHamM8Tav3r99Spy6S4RWpnhVqzH/8bwfMyj8c9kxh2cCtk2S9cWgfUlX6HeqlfBowiyFF7+v9SjdtCU9Nv9LefDnwbRIqanKKWSQUiJgpTQZ5WVAeqT0HSZFqeS64gOBUhD8pu+oU/+r/qPMiTZ6rLqYunBZOuE06lPbBKJ9SDd8jbF/4VN09XFvJ3GxxI3p9Wru2ITgazDXgk8sC4bl2n5L0ZyITMy/oNZOFh+uvvqfhqJ39ubnd3SeviY5lCEfSL15TgTGT881ulTRIkV0Y/7I9SU9Bo/+YfKr/wEbZ88riq7yBodU9B4gi5gn66fYSGoU2wV6MDaBxjQWSs4m8TkoIs6ROVT+vgkjRwakKfOguLy0k5iLxIUZpuIOucqmbgTUGl415cWmGPTs5FBi7RLp7Z+RCedIyfMIjdYGddRzFz7u8tfqdI5DmzumNBKiutil9e6Fl7A4iODylpxXubupS4ZjOJ9LriRdHbtrp9mrarazoMrGKxF4HBkIZsEANT0+xm7vn+DJtshFrHtoQkYW9Ucdg+EYpJnN4dTY5Y6veEw7K+VIE8fuk2X1HV76bec1g9GwgM5UrW7asdZsbixNu/Ij2T3MDzm97G/87LI2dSSp9KYuXqfbb9hrA/rcZgRVev5cUt1c4fQ/M32NIWIFLyy8Va5G++2G5qctaDj+KAdrPCQ7RLpAxYFY0aAuATZAzVouj+/JMoN8kTs5mNTzJFJdaPbMwH6AuCmVgz+NgExTtATq818Q5a/E0le0W+fLeJd0+UuOZZDxu35D2VcvP0eBBeD84mSmeHR+erbYiyao/u5Sleg3suNmXtMW7nY2OX7DimkgMbL3oMNKrcPHQOaNEoj13KBBZlaxAGAX5jx0xv6B1FL/F0F2EPuEj92+BN0DJCpzVMns2CnbYkD4HtBWgOuJvdbkGFzKo527KiBNcsglJqLvNuOH6A7ZDEB24AB7hDaOI3WkwExr+2AG95oVwZxpNlyM3LGDtPfTnjtLBwFcJmS0bl807AI40ljxsOKEvj6iKtrdW+LF3/1Sn9qCJqJpD1sGGQJd9CNrNA9cnGtnDH0uo4Hb8iUktDEcpoEAmnza104PdZm9DCcN/b2LdaoFgBk8OFQzxwlmwEnmhJDLvoHDn+tEl4rAg3h/PNam7e5xJoST4Q0j6JdOMaJUtB58+SRcZsjyS2qD230XRSPw/wD3nnDgY1oDHCYAhutcPChKpGUvj7SfMqNFL0/nnRE0QCNtpifvFyb2sxijTFevEkD4J+ms3bb4W6j9cfzzER0PB9I2AAXQrk+F6RsA6EGlPl1RzjzF4e0N+HIpPiV5MdP2h2ra/BAKuf1g0EvM5xC9voUvtTgWuNc/CgsFREblA4BSj1Vl+0Zi2XZRdFtKyJiR4mbKJgotecli3pWYZkgOfYov2gCdD4Q558qjRQ4m4bEO5Dv9yACOhKgUWya7Tj86sPNFReRVo6bkKxHEndR/DBATWTH0gtRRjR9T1JNh74IoHH44tO4VQhjcX9hwGSKJ4S7X7ArwzH/Rx/z2DOusTLakqqL5amhEaqwi3n1zG9R/SLuxHlg+AXBm1u1+LUvuRfqYW7OprJgegV2BFBYGIdZmBtfemFDX1pYgzaRsYwlS3I2Br8MGDHJmzRN4Mix1xJ7XqM9C+lJe4ztQfkx3W86IUL1tmtKgm/ArgQjPJiQIraHVidM2Js2P69FdG/sv2YktfTOrOCmVik1DMgiAVnTDsvULcqPJoTYghrA//vQikswiyIYRMlw7SvsfhVk/yeS84MFs0AuLfFTyGOJhpcQC9otlddJOqaoD2S3qvZwOqu3p+38YNhrCocXY5wUfsXU5leNcAIUK9Mpxm6TPSvV6Y/ptJO/AqdsgdN1Z1MWBxVKxmWThfqWnTnwDoB2j6y7ZWmjU3rTpf8PX/A4rjZaoX48QBlFLFlOoEyzoCzRMCV2iyqMedkCfiVopq7xF9WuAmjPeELIt45Vv0wPs8kUck2f16tvVefosYg+VOMAoslkDPGzqZBT9Qdti6bwwz7NYXJrgR/eLorWrOQY3/Due+0BGtojZHmDdQfsqh7GBfs0vqHUPiSnigqM1Y1/+/qGtqKo3jfCz25jitzimh8HAYFSKlKvgzkjZHQsb2HK0N7AsmKe97HTCoy00ENHYAS2mQ9mc75/iwY7qGxBh88YDNcagV/doA/7onWtDo1VwjXHBmxwvfIvx5cXY1VhPd4pK78qdBMy3xn0zJQTO/IeDQ1wdoQtTXQP4EERDK1O7XbyCBu05ZeiweCOlcOvL7XGaHaoLeDLX1G41GAmNaZdcj/qZJRPy9Ay3e/eyUl5yJmAOIkYwnqgKdGZHZNuBXLzMm/MQbIS+gAB7H9J73wmxh4wED1b1bynIenlITyW4Ah8JcAP5Gr1QYnvLgvbGPdBOqca10hPk93WRUpAj7h4EoezWuP7vAYQK6es7pgom/OTTSi2gix8ap6DeegOwwTlFlgI4ms1BwH8eI+H46Kouc1maHfIWX7ZMcF1ewSCn8HgakT4Xo3TuyI/qIyS0kR5amWvgmW9TrXj2ph1tesYXm2SVWYev84QCTqs1qKgqfXyHcC2OQFMLnpe2XAOU5djtY8mkUmNaVog3YAee1xOdeDDXbtPMyDg0tRh8+nvgA4xsaoirXZAQbBTyGsW1C+cXbyMM9prLZ8xEehEiFXUXBOlJaODwHq4nofQiSifyU1EMFSMPpm3H97npsUw/qiDYXqrPS64iPBPo6T9dkgju/RqwzBWgAJPJkVh73h3FtI3Z6P5mGeq4nAy2+4gABTfLnURFId2wc1TGD+fQpSFulrzJyS/+RlWEqLviyrjKSvfxbVDNEinto64xgZsomQo92+J1jfIRCK1iP8PZPYtVFcxHienivPJmNTcNkO80s8zH/EBSqDC/Kactnx2E+9PGyJtjElIO8N0lpjKlNoEeOiwayCUXSVpLyUb2TkIbLSvuRvkeU2JttlSNf5VWtcXiyFNdMSQv+szq6GCqiKLyCQzYuHizV1gqerg5BRKy63KFl3Yxe4BCRIuoQdNZi/kDQIajX9p6U+480o+WxSLTE+DyukNN5/Wu9DldosQwNTLv78grCMoYPzPCDhjbBPIBevZbS/+shhvu0g4PtkIGcl2pr38zTLGYot8Ae2FEDFPP2CXUZhiA+I7sWteEGEXO1zAiaAXebP5OijT5DjCnSYG1T8nhDluqG1csuBjDMhHvVikluTuiz3NVVCTT9TZ767kJk33k0IJeGZ4B1GjCtd1eXmijUWx2gxMiaUnwxt7VBi41k3Dct+Q+8KSpMqKTt+l10dIh1kaMgnDhQbynnsW7VUo0xUGOp92NFGRgeprsW70Hbq3REB65wxNAcCJPQcoOpu7n0uVmgmZZ3eY9PPlx+oGbLppN2dLbPweLYpDAMukzZ5moBrHgrZ59NIZ7lD5NQ9W512rR7Dsq124+O0cQsV/i0m6GKvqOLQGI3mvj8vkBD0D2zf/dtp8MFYNN27S+Sk7Fd0MTYzuv7QjHafIjNgzbNK38D/6wYmYgeKXDJBXW4/TH2/jk0hjb8udpAnJ0LyiepHsrDzHOm8uTv/1f2NQw4N3SWt0OWzbkndRql4m9oGCbV3GKOpFua4pLIYvHZTxPZ0ITijV7bbC9S4YLJP0KBJh5872Clh52Goe7oShn+x0N8SKZ2mLeB0pl/bG9kjk0b61HMHbNbs1rBGH1L6nw7RRvEDRxC0sTPIV0c9ubTj4rRHEqVROeERuO3PtVKdgUzS+ue6a2kDU8RAk/g47nL2bI21cwt19tmCGAsfaJnUIq5zCAKFcoGH8klyhJ8YiXtuYz/Q5vkBByYTQgQ/Oin8xG06OZGLd+O/EbPNevimYXhJNSUJrJCOL5jlZsfvM1qXW7zd/OEDC1rl9Sc/HweDVT/1dDeLZJ828M2ln2O6eNQ7oogln/tiGcX/Ix6Yf8jTtIR3b++iXf5O0CGO/IDLeNW84bLCYE8xjl9toVJxDCjtWr7nZgcFHdmX2ah3LUQscy+WtGWzTYXoJccHFzK8FT6/aUGNK7kK4v7KJYDkqeFyN0zv8zuEBVEWKo4GVtplMKBBLGvd2ZMdoqAuhydWNjUgb2pRUVBhV7K2FDqkw/m3DfbhvF5nLct6Lu351SBac04wK1LTOiTzROYSVmTNt4lfBHtH+4S60QMuSFSZVl3lceoI7yUipf22X/kUgDBH9KDslSVe0u6myQQUmrAzEjJuFMsNFM4PiNKoorEtkQlo4MqIA2PZzVfeHmvhzj80WRB/dIfBuzyKm9G5oDbAs84wCSBwie1MeVhSLB0wfH3Tlyf23v1WMu5nzDBYJXlEzj8oZjGdK8MC6KvMGLXcFYn7oLnBWh2Pcygergjb+VkxTgd5W6jmm8nMBxj2+/cxlM0XzRUpvLrz/ykQ1HYKrb7TKlaP9ot37Z/oeI03YXtx532Nwmj+wNXkKoTVGOZWeQVBq3U7evYoVQBItN679TcTaXt1dprbmn2xzd35/vXJuvN5/D6oKuC/9mkknrHEVoOV3UAPe3EDjh7lACUctC/E5NZZ06Y+qKUGLVGAtwbxYu2nJbax/MRUbZZqcN08/v2Jn+BnsT7ZyfcgAGQPk3CzfCBuuPrL8sBnelWNDtTapHTOWEOCSti2u2eT3WvR/fm0rv7aORssEwhV+mIg7PuDHQYyFi8tNqK5A6EXMiCFnb+Ja5kRJr2hPysbPRuZ9VgubhWC5miN/GG3w9yGPVg8l8CjzUkpgL2m1t86OjD+0AzyV++MLFRCnZ36tS49yVy6kUR7ZS06wFqNgGLYaYD1afVFMD/PFHYssgPRLcUctWLqRa/sLFXqqzsvRJtsUklc9W6/MxziG5CCvGcOjlur8jpOKEjb3o2H5aty/Jb1SA785WPrEaZKN/oa2bc9e/SQkLIuc563MQjtQpkJzLGCwh3IHDN3UJouUabRU7Be+ailCONZe2lmjmsQ8SWrj7TybKXzWRaVMNbffT80zMNgMkQNeAQP4MECdhnYnDZMilYHPSt+r00826saFCS1OO+9exShvLU6lXdTA6OGCoE8pUTBAeR2c9FKRzzJcXVi89gJXaAf0Jzyqtwavqz9994nrpIvPOeSJQ9tQGVrTTJvZWoXB/JVSnxqpBuV2AUMzYFfC5HEshRgdYykRyhvmEk14wh+M2wTtFHEDyUw3ANh7YmXvq231bvHhuiwrnppeDK7qCcGA6El+NVXZrh1m/0PAHufXzgXWTtysKqDtrLI/PboCKpG4lurbL2wdHTHPkdbrVaA480eIatWwh77GcScanW+4e7CqUmlwhKKnsfbv3xb3aV6KJXr18D99qY/Srl+qnxGG81Ftokkhm1sYyBpFxR6YQACmOfg6iicAte16ytjeDIDFHx7F+ILb7Lx4bpZe6ZYRgfPjk5c6w4nSpwKqsjIzbFcikCqMyEOLKdtRcBridJJieQXxYN7fUspfphfJQlpCNhKbV7SI5+7do6K3SI7CK3ZZAUNjDAj/VlAlIp0aCnlRv4ffjQNu4ZzMKOiKjvaOixGDgSyNYsOFmUvRe7cpyTpNF49lhc2ZSEi/f3XH1PnsiIXTCzJhcRTYj3mHjjXizrzN/SbNuB4FLCnFLPeRwRKesPJR8vuO2glvsRpmfFD0FgRPSoQ6joow9e/AwSASfV1Qg2pLQ+7C1lxWxHUmotDuHnRnpHAa0RYjYtGIqwfGVFmuhRrUOqHB7onAdTFPC1kEKZfn25S5f4E9T8lOddHOtXh0pr/zzNKKr9PwIDAx9iaKwUaUC2W81xUdJ0PDCBGpuBFVN+g46r4ifJE2hd4JaCh1QH5WmLQbvnTgN3nnYe/LnfmDqZZ3xoV7THCXjUzjEmReSjJEvR+2i+ofOAvjrgIFVBMPNcePafDrNaJDLVx6xTsqNvtrSay5DrhhL+ELpHwGZKULWsb071RXMn4wzW4QtckrIXnibdeulcjjR+6rdvmPObH8Ux2i88doWohLjH/PAaCUAAnYAQraqXuUQJi761qSQa1MFfIDW87e36OgFm8heDNrVyc9Tf8AdXqGcVfOM/A3t7eOzK9rmVt1eLuJAvvFkyjGO96xicM0y/bGBIR2GmBhn33wueRsZDfOAxO7r1t+qzcAJArJQs44tplFGnS0mb8/xXoR+BfSr5KILZJ9oY+qRhffgrGMjQJsfqPbIf22wDwYQNosysgYKGZZ7dyNEeHJSAi/w39//+/9VAhff3xzlbFM3x++C7M6F5+9HgbuA4rYH8j3aMCR+g8U7U6LIf6Dh7iXiH1XnKiyNCPrYygWhfcTnVxXSA83gesvU4URhmLOR39F7ZOmj5FGEO5F3UcNuBqgv+CrcawNyQSadMaDWB/DviWtJjuxAlPX6Czgz6RHfo1oktWLtV+QIKatZ2yGF44fC5Y7oSug97A23Kbp6M8yUZAm9vcLUVfg8msap29qPfbRgrd5dq05j1yKf9WSRl2x/0JARqZhQJBB+IxfScPB5HZpFz4nZNHV+i66L12+HXU3L3MXeC3d322C/R1LZnC6J0TqJ2//RkU5FhcnPYHPzF9CNhbj9yqMWuL47xi/cRRcH9bcndzTXRDFAcWVfLLe/u48tKh4bGt/F8PVW0wp49omhtvwkD6QLGFr8YhGiiWC/R3/nu/HXaZ/9KD3DbBBv3VUsHvQ8WWUJ53N/+u7Ox+qkcIdpgHDFZ208U03yQbKl0EaXuOGOjbiZXAUy+L5n9kMZs629oUPQI3uUp2TjJWFvggD2cWV+YMCTRdQPrebss4/Yg3LDNG8f+mLGHjZ2YxGl6CpOpn1VkWgb9nlJCukJTx2ip3lAfBL9xeUB0KnEsFV70H6yiXAjBobxmGmUy3Xe9dt2zVALqF37Pqx+8KAKSl3jiahmciO1v2DJ5ANwqDF34vkJPYe9B22EBKqSwMTsnWJlVO7W/SKgZ5Cm7TpFrwpBqMNSeNMJQ7eoLff+Csm4OVU9xYR4ZHOS2VOW2XASARNXPc8wDYKpknxARNOsOkHseRIaIWM01jFaYiYv3PvXLC0NmElWP/yTyMn7kU5BlXXzcTuwVB2x2hlbB3Zop/6+T/QD5scdFGENeHYIapJHeCmFXACAy9ye6RmLGRxYX5VZytPhvbW1taC7HHdPfk/ou1/yHNMaUBvixiihbxedcqBthfEL60ZJOY4AX489rscflXUjhhnMVOuCBGgXJ976udhwXjiRtDSmG5jcgX75IkDKqKdERMKMrlvc1atkf8Hx5MdFk4k2MlbY2P2sPfIAUVL7mRNGISoI4SCWSBdfcj+r0pW01iFewbEtozkjdWLM2AEkzd65NpDmqyBhdpPqTkDQfmwhMzlTEVJqy5BQZSnW1IoGYyuZ8m61++SPpH7MEKS3YQuZ7+94cYKoD7DG+drdqsrIA578oVsGk84MXAo+Pmnu2gdGPw+PZQKwwduho6EePaC3FwwO5QgzbkFuP3KZiqpkBTILGQbbHVOKI7nmR13sOcdyKJT4auUAP0mkJutam1OHvF0MHQs8qJ67vKEqG5OD9sY0qhtUmTTrE0oWuKWqAkpZy0EWZlCeVfX9jDYJXmF2c1IjEPEIXMOB7+HDnc0hvw2kp24/1C07HuDY0D9PH2/4fxAUbp3A70y6LomvODfcrkOQ0Q/ATTt2tacJ3znMBhibew3Re+UNsvQ0yjGRqJEQXhXCi6KmYUsejldnvqaTIa0clRCvnJMqfAfH0nJcag35qG4wWaXnHwtOzO1F+ahW7A9sg8vfyBRMqn4YwjCs62dgS650eOV0yPW8YUCpJ6JsOMNho1CSTr26520C91+l8H2yW0i7a8SoxJRXVVRIKAu6zhUo7TYrlUKXiMov9z3y8snevbp3irFBpL92ATkOY225mZFmlOUltbsFlcEdLlX684f7wh/znxX6KgJMUT9J08lRb/eGrh4LrJn96Zb6w3NxcKpIn/g/i9ArjPFqQXjEMIbqewDX7zkKReKv03gTIhf46QLLBAQIQ3eIEHtEvq3TfQEWofnH/bXD6b2WyX7x3ewJe89Jg0t2kTy/Uz7R9AGQvJzbhklIJBqROLvyiSBJU+O7MC1MaliSykZCgEfZbAc7NXcAJ44rP1hDGfWsDwljNRxFynkbBB/A0sx8xVx+o98smx8hXg9HoYXfnMwrW9raaJ4UEbsKjOghElGp+jlQkDN7B+jg9Ht5js8gIVy2PlimbJVMsFlbAMhLTbBLmESxYpO67TC5JgntuSNali7Zw9TcVn7N2vx++FQ4lQ67EC2nUzzLnNX4H1zddbO+fxHuRnEzXtAf1DrvovLMSwdXsKSzvTSzLPJOf7+YML/mhR2TYy2M+NJHfg00FoApwzCbu/4j5phFYCGzGdST15wFV0IImfJNEwBhacpeUm7VjIs5G+iUKHMLOPy1L6gZcMzfkqtdSX9IkqLJsuuuJWYfiKRinxPUCFje8YMSY1aAiI0tVL99PpV5KMdz3KO56bhVFDbpXye/veGA8YBpz+V5H17kNujcp+47GNuD3lWpVbYO5tnvSBGXH8RbCEyGF+PiHSyuHmW+JmiTBeskF+LRv4I3Lw/jozIlia0r2JZ3iiynm79eICUcCv5+s7QjSP5BQTvpXB+6IXaBhzKdBlAOByRPCgTyk7IHr6VovLqTw93xZfcBdTTOg1zbxCmxvc5CApb8Fnz9L71cFEQ8Ton8vTjEi292RmPoAViFeR9XX3fwuNpGKfFbMWjdj8b0jpxSJqT/4xCV+trhaJpEwuRQ5BYPbxJSKWLqdKmY5DKCOy85UHN8h2NJ1TVOpgGepU2VeK/L0YEtAtuAU/AjXHd5kIOkPofw63AlGcPMCWl+9Zt04cbP2WlpgbIBbYaCFz5PQcE6niI5qrZ1NxKn/Vhobhxc+qK2eOjitNujhOZIU+YOYfgo4W17ynEXnh53dAJPsL4eB4ViTvW2hjNL4H7Hy3HKdBDUkPkfw5on2XRMpPOGWJyxUtw5vdLA1mAuyF+7FCvFgtAJ4tvqeAnbHPEqncSxANH9pcJCX67Ud25R/swNppnMTH+qDfnuEywRcWRo+SgHW9flV0Rt0ZVfk0m3O0XEgkXCaM9LF9VAKIKI5L7TFXQKYvCCEmNf/erD0m9HgTJR7ug/UaLqUtiWTJgHNioBxUIj5hU3oA9L4jKuNcJJSTM22CMjVqJZEst+fagej2fMW0gqiai7nPwE43c6DQk11bZz2HOKcwpxDlfRSMztH03NeQ5RqT1fklInGMtV4t+cQGLpqcm+1xfOANLk0zDYjkfRSFr4MTEBHVGSgLciKdVwl/+2n3gq5oxHMGdQ9VGTjuQjgZT1KUdEFpH/ESlIVlKVofQQeAbsO5QcjTuDzOMPGqQr0WaAYW4Aywu2S/QspY83ZEd09JkXgvb8q9C7762k+bQdX3a5bSyMBirDs1xpUZGx5i4lS4Xb9oJU08AoKFUNpC6fGr6TOyyGv1kwqUaiG3gsnL+us/PLwmTdZ4MkCOo6mhHfcIos2evEOQtRvkRzu6NIZci/GRy/Ri0JJ4Y/EgVaOkkhYPEOnv9ztG8oRuyVSgYdVVnkNOZNy5BiqC/yDLmjiFv9ILWZkRfR9SYbeXheX86rjst1yJpt+eWCNapcn0QKflyw/6A4TEABGgT0+/Y0DTo/imSRHfwi2nYlbTzArH16NJgQBJaKktXBKVUyPSvc/XWKHjgncV08Y/NQzDJd3I+5jLAz+dUXbiQxcekyhHdW9PogSNQlLpac8TbtFJsWonHl8s/a8NXiBeYIH3qSX+j+ciXJ5eZKk5q4NnosbRR2ps8x176RQ4f5/QBePferVg0ZDrY3pJ2h3RO8568NeFGKYeeiEFlDCLxVYWD2edEhJ+gokPIPTWWznasXsc6+M3rGNmN30GyaLxCXxqQS0YrWDsYW95aK6dnimNmEBVVyBJXjTsTXB0cYOEimxc7EOXvuN1IpxwDtY8SMpXn4ysIh60QWT2KeZViDq3AMORnEiVOyOHYmovn6lW6MvAsnixYBggWJEHoWgAzuqd0OICF9fgSfst+PnuuJhoKEw/kCKuniA91ofIihmY5f3b9ZpHrCm/YKnWImEm875rSXqnPXU/EC5o2Lv/1fTFMr3xJcKHasCDF1oevwCyi+9HIpTXOd/hVUiOKkNR4WVBdZmQRCo1pAWfXXcqrX+2dmNtDysqnhxRuDBrrPQrLWJ35M/NCZlbad2UpbOInEpuMrpM52KZUquLEG0tlbxzppFgf0V6lVNOmkKZu5qA8cxM2ergRxRB2udKC933nVbgmHpI39vdDmyO+gTwSSql65zyDKrbnZkJqLnbiLiYzEbqbn1UELfd7a/yIlNGtB9gJYIY6qX1r4MO91KzjvkhiE4qe+Oie7irFq3rRxnvU3vVLNgNT5YTr2kSdXzbEAb0bz+ZwD7RkEXJQZ4q5aSijs/3+09B71Xc6rK/7EBsbRRHvV0WDow6UfaB8IEyA/+psuuNnyd1FfZvfCpQb98aVHPcMgcLpaRAYJkzzWVT+UZ0WyXDMBpAO4KmIlef7H219jnZf9HaOv1Kodsq3gTblFIhO/Sn3CWIBcaRsrw04Ti6cwh/TiU0z+qXRUIUtazCvpW0/q1uCpUGTErcNgsG7gtj413IwprTEnCL5u9R0l/jyrmuylvihWJxJQ2nW3KaadgtFZfxmBRf98ei9cd6Bjw0I9VLce/VPIPPEyPwEJgcBHBYrYLAUdElHbyoa5w65YFzC3u6lDjfV7K83dncgLOC4/2wJ8nmJYvK7UvUGvy+QTxZTY/WfoquwPMil1btcobhZ51MfgsdeSwPQw0tumrK/aJIb0Y+FAlF7yoDAkYDF7CNU9TpYLXCVvP36gCyWL1jKwTK/qmvR5ZbsgB3vrZoLFnhL4k6To6DU3nrGJAByE2txCwDzRrV2w/DdP/4Y+XJcvw2pMRbSyF3Tlr999b24FBqj5xTJ2722MDPruVzEHZkDX747zdndEdhvqpR2U3P76xTIjjrWdcNgrvNXDdPaoHwmMctNKBzBCYEpaQa7VbBmQ4i843auzQeaMpc+5/ncOMTch5B9M1+TRe8L9pjdoSc03Hx7exSwkFIzGS4T5ysjGla3LjrxQbnsDZEmSDhy7v7aDPKHdib6VsMCgFqbesc+A+f8nYLx2pThNvSxnGhjty33HWJstg6o4+ESNFk5sHlHU4rtCsecTTeRnh8d8fRs1j802gJ1S67R9mImZatoW65erHF2ui0NELOySB3eSb3bNRBBl8zwDyTHY9dwDHTlzFnipjaQ/SSI565TYyUp2h+/XZicg6wgmdLq+EmacNMVzLq86QfupruAMqC/GM+qW2T6suEcADyWyFttEmDPDK6kfYAgoOjlohSC1T/f+4VZOT6oNQMIUOBkf1bWd8A9ZAjj6eI8oKCEi43Rd1BUpACV192wGno/rJrJixvn9qmypP6UTdwWwThhrX9plblza9zbOLX2BgxEbTlzRWUKEcwf3ziPjvDOIzS6E/FwFFNVucwlOI2Fvo81ouz8rbAvNYZBvg70b9L1DcMG7ayH2AXf74BdXkpMDxVloGY78Wko/j7hJQY4qZ5AmmspHeUvvGlxYIPYL0P54aBQW2L1fJCQr/4UOmK/II95EG0MeZTNOsn4YgbQ5UTpl/FguGpZnaK78OXzfXKCZf7NeehLRVEHTV7CNXOg1hLgWQI7wkaDbThG5ufKeyU4F/7wocZzKgzZ0uSZGWR5x9+VeT0yzGmr0ojM7GOxmocpsMqBSsEFikmSme5Bt1ul03WJpAR1q1rcpg3phDLBDGz6ZvcBCMTwQLUPQ18e6B6jNEhLwkByofuNYPZvOtxVjIlQvIbJSWIPCwS62m2eIZRgqzxrh1DE5YejB5pKdxIuEFj1Hebe985kcO9DkJdVpBX9NQOlg3hp929dutrb4upsyb9dToD7xNcuHADzc476Xw/PF+ECJcvJ86Ep4DEySW2xhLpsL/Ep+g/TJGJ4EQLCwSn0ZmyHrm5h47w50GVtppByT7k5g/dCiqvA2I0lIhFhzajV8saOdoEMXQETb6kOYj7MW6cEOGTW2QwpAbMLKMbc0odwJ79XIsZQyqP64G1A3d4omgKKsVroJZ0aH3fO9AlGE0O5H0bx8Vk1oDNMhFEUdejyi6h1Ed2kcP9Yl+dgpSB/kWYqBSoO9hp6GBn7IEN54VIe0sAJNG3pX9TCjmmK0LuOrGH4/VnvYXNwF7bEqU44vifZRMjx/aF1A5rVoUWvKeVakMyxJXuJ+4nM6u/A/SY9EQvPIkUZDTyLHDUnUPVgCp1vY7Z8+rNBlni6OQPxrAYh59JpT5vFXnSK9/YHYL/MEetOhOAK8/sd/Kqd17V3dRvAEWS8zWMKUDDGIgcOPSsjhatY3oKKveGIhzWQ1xCNmuLgZPHJFq49KPl/oqf99mTIO0y5EUwkvHqO+ZPHJ/5PB2XA/B2W/1YUi52LUmNFkzJVlLZdoeAMasrRpKznTJw3woH/XuNCm46EX7cTCBPscymVFY/haXAfXNa1bhItXHckH29Vr9Huk/J5KmkDT0rJcR4HmTj4ZTtRBs+0Fkc0DF7TGyUXov0rhyCG8JdIf8RRbdH+Qw8epgXqUWdB/qzOe4HCBTduRRZfBHdzBkgsLndnXgLYd9I/y2w/IaO2xzq1Tl4wFyM4cNDKtHdjMt4ACVhwWLJcOubpfLTL8oyd7X5VEtE0o0ET5IbKvmW4PpFtCG7e9O1UZbx/qt4tJSowa/kvU63b0/LiDuobeW0NSuW/3sS3DELCYtc4kczxMAsEpe4VIr8+cMAypCL/iFHltG+Z5ZmRcEYhT7z0XgC/Gk6aypvwwwCEMWNJI1u0Q0S69kgr/c4Dlj8UnP7DkUMuegMx2zLrHFHIpqw7mc1i4s2K4Qh2J0852Z+/n8S5sGv0Y9uzUp/t7aOsqOnOs1JtKlwyX4MAGXC0zWiIJc7DbihnPuQk128m5zkbnWaAVgd7wX25RT8FhFf8B+Ub+Pd2gVVgSuOfOfmA4iYnHpNybvUATMDod6WbxopQC5c4Ft2HSkUVHatEbe5pzCbeNZFmd1HfYzhYTMDhVaFNQGveJSJylyI8Axrx1RL+TtqMTPsbCd8N4rui8+EA49IYrScsOEB9gOYeC5uS4rxX1BgxOinjwti4Ox8xua7bqNjIyHXxSmQ9SW6PlwIm8SV9Q5Nlj1dGqFsjGQzfdaIdHbhRRSb8HFVlnkw/+SEYgMQ3jRngmROYMR92hqIEZwF71txgpGquNPFeG27/FW5EoWWxBNl7If2lYV9KNOle/fM94jJD4JDaz2DHs03Bwhfy9tPn/54I7bJLSKQDT1kBeakv4BP8FcvF0vR4aTtkN1QE4uKOr3CS4ZdM4eeklh2MmsTu6LiapuBHV8fY29F8ZoDDPbInpOp2Blr75IaylGKj6phgb8XdPd8nE8I9WvPz8medGk2Kq1wdkf7IDzvc+I2Rw2w7sYkSUJs6kqlon4A3lnYvPtvrRHUt1seERUbB7zkRchvM0sQ3BJEJJv6adWTDqNxi0J4JlCwjcgQeLuoTnsC4VOTxqrixtQs8xiio91xBX6EaWwwQMgQaI9g4bif3QbgvmM1WKjZqtDCV2Et1yC3n3HJNLnaL9X5m1rU8VaFu4S5cKKwTw/N0OsOk15Vr/Lm68B4px1iwHPW/tranqVigO5dqjYvEIHuNmRQ9vG02wrMDfFTXJGyqrwPgJNt1xrU5gM2I1D4lh+cXDmBzEhfAIICA/f0yMWNo0apdMZ6oxmIHSPb/LxDm0CwcMEhs7kuM08q0Q27kNMcZdxZzAN375QLThr7IGnpO0VcG/Dn00SzpYqi0b3nz/vQE3lTb1jTfca/+iAIIYHI61IyqIk9T03DgB2VGdK3r8VID/jugCV+uFsBtMFTXCF2x/J9/dYP7h6JBWcev2pe5GyXlkUWKJmYn627d1UEcsWTtakRf53Re8+3lP4Agcu0D42cjl12pFSzt+tn6O6pfZNcbq+5kuTKb7wsHlHrIZvweAvcx8WgQjlR6HcZjshQp+ZzUvvAZRy7rwIbUjGPpMhHYUH4Jw6wD7/laDbHx5LpNkBDR/5fL+Gf/lFPsVYC3OvUOELJw1GQ5R6hPoA9acNK0lSzZ0/nypl94F/FcgGbvgfqvxDAqq1HfrebqDm4mChADmf7FcefYvv3x62hcjYcXoeNLeYwElVZ66zzZD9e0Pl6busFPceuBVX8/PLWMVYBNDcRCqhgmV/o+f0MqES9WrbInrJ90htkAdwYpM84gPbiwQmVq55fnTay4SqsYx/JNxEFisi8wbOHhN/ksWc0sglOG6YGO1n0RTJ/kgdrKf+MAtE6neBhaclHc7xaO7k55uBKGEWxHuVQ/cbJpZGi3kEBJPEasJCwceCUWcfYESR+mt1LhVydT5dec4mIji1V7JpFTrF7oKeMs+Sll7qb5Szeh5KAlmWSsGb0FRQfw/uDNnMwrmaxaEyhkT2J+k1HDsm7K3GKcA6GvjtSxSUUNTkTAeRzNv2SziltaqGeQtVd5Fj5NVPisCZ46yQ7/qxh2/Qn7pWsmn84viygCfGzhBWw/x1VWqv/mD4u0/pRcnTNBxe+yytpIh3JSQ4Kik7NH2PxW+A+30xFdAlY24wfg/iExkvDe3Gk7Dtk0pnRtsD4WgF/pbE4K/gkLXgiYDDlY5fz1CEAvpCelipTeg8RbZvXVtN77+e3kRiwu7DIWMNNKgfVMpx4ddH35L46fWZUaCNj0uUolEZVTcFwy/n7HkOVcaTJWt4zCwWv9w4M2osd3zJi9r3IKU4almrvlxQTkgyvz2+WoM9ptARMr+CJkGbgHTx74JwMmXGuId7w3ywdOiHKHWEUcvTbm88qjs/8C1PLcurNVWdkyV3GmdnoPStC+OMy5RoRDhS99sDsn4/jVcjadpPSHZk7QVGadUJEtQJUI1nyRWsDhl6ncyTJmvQ5oI0QNQVZjXDMz+28h1tyraEDwWFA1wa/L+xvMAG7x34HcmDvJsYXowgnKAWCOvJMC8r67XK9hatZvzVrwMDx+r1KEJwG87rFAUcttlHP2JoOrHe1ETlNFIE5b/H+GZD2u271eBzr7ss9gIF7ZroL4NC+Y8eWige5V0C9OKskdG+Ijy4xVeWlS2WY/NdxcOtX0DaypsEi8lEBsWgn1awbQsZ6TFQK1eVqwekr0Jgj8nUBTEaiFCpDlMVU2X0G+CoLR5vg+1IMzW1pZzzge76An0cbwLK0kbANidm9s8ioCAuS99/VeW3XaXmvLduxFpoELpNqNNoT4mhas60DjI5BaGFxo9RHlW3Hi+Jc/LTd4trfIP7o4V9jDkVwHq9lE0+Ovw2Z5IWjFUSTcjtMiwkbjNYw6MafdAnDQkIDr+S+AZ3nNz0M4HfgD+9z1ZNJjU1FzrhsTOd113zMxq2L+qKwmVjaRg/lHP0nRXhEM/HS9l0H0ds4QGeBJbEBfNWQvx8tTKagMpd0UdO1MHJ3fKNcKnDQYXyydXvXjQ4Vmav5Eza+UBHm3OiYRXyvcjI4uMBgvuaKBiTIBupU6I3I5RziZzHekLsoEXzcu99zIx6MGvBHPsLHGoJqE5UAcvqNivYe6ZuNxYL/z1Z1QasDuv8mfgBUecEI5KMHX55LkMcR4D0Q6C8JBq+Vx1NxY6LCK0k3udUC9y3ArNe2eK0lHpHU81gb6thranavNdwHrSgVx35XLK4mfT6/sFZlqBm/mCr9AYefz/XYA/gsFgE1RUgjCmleRlH0jHmC1F0bwi00PQxIveMhDKeiosBHVHaIddcjY6+BsH58x7hNSKxLeol2SqORIZoP6Tqmti+z0cxcVjIPoBX+3eyNSXTjjvjz5mu/tZPkMgNYVlPIglWuLBzSFxRem9OBmUGZdIZjyKx0U03ys0QK69AijMD8u22JTgB42+8kyoCEU5YBmP6RCORrDBEglKbBJDmuOBVYBbWhfkJ5gTEKbLCJyU9AzZWKth7lFtYnfCCppmSEJFzUcZy5fubGVeuPomUxxM/QQXeAw3nH/VcqFXZ1pbI8fGBZDdlarL24qpMxowLUnCjQIY8VUHumn0mCzLppAvQMbFMhMXfGUqu39T2tOkP4SkKjhSysJMKcOR3sFQthOFr23pVRNjkurwsKscgkLmF5gbTdNXI32RkxgNGahInmvykIWkJV1tnK6LkfdnA37268/2540QmcDYLUbBUlLBKU90UNuI+tXhvjE1g8avhcw2AdtqXVu7qO5CA2CaJFhWTM0PGtGHXqkkvauosjkv4AjXlpDbrX0rOPYn97uU2RSeddaZNWbPGIotJdfBcuTfCbq0N6UNw+lt3UIRBKVtGHPrHAS3BTuJQ2MEuXc7zkFPcr4Ag2FkCTeSMMpM3nCazfsCnjQpsaLvIGU3dQl7ZEaTIY5ptIr+mkGrQEaWErKvPWjMRVlCCpnc8pC4B+2KUWaQ4R8XacoZU2RvJVSgHnISzCi2AmpOzHHNpn1Gny1wyg/X80JtN/1K/c4lNVis+tNHAbsZ3MpyfSDHAmjJuHFVCVDb4zhbJtFi6iabv5qNhiLjtd5aGfPYU+ZroxcJ2OWjl2amNBg4JkLABDb9WIIKimdMLQLB7lWeiXrPaJpKs/PrxKp/ayai1JPRGdQqUFNL8nZF2zJAZB0vX8DGF/ZbbM2cT6lfdTJGjWI5KjoSJKDyFqj0w338yosGqczM1i3LZWnIUBn5UqB1IoUozn7HchVjiP5RnGnqJIglE9e2B0Et7NitiVPx736HUvdbeLtXtdGjZD/UrHSgFZBCsgZJjWkmoliIMrbJXIuE8naXVfN2dyp1BxX1+ssVTZ9fQTpOvSVR/oKnZ8lNnllehGmrNkWyU2Dqtfenp1519YH+vkoX/wVhNgMUJhRQdIuVgYqnOimvN7EFYnZhq2yeoJUr4kEZ2/WYG4iQigtfkX0amoikWqJESWenk3Pd49BKTZhOu67GB1S3jeBVsDCHJKPeV/m7R0NYjss3OqKV8/V9vyrdmORje9cDv0y1SSMKGaNiWsERIa3W2yyo8zZrJazmDUUxSVmOFJNzNO1J03ON8iSTiMoXGvsXewyG04aU7UyhKY6a139AID0/K05gwUfzJCxFcX5lwAbioIxRqjrynitE9Odl/S3JsPDxOra3EWQwwRV66FHMS+fhp1WkSAGVqQrBKMows8sTO7IWBdItjIE02HEJYEfjG6naHLs4Yx0u/9j+CrIHnkpxy6VBNkJ8eLux+2cvYk05DnvtRRbBVnr4MfYGBnLK9M7a+76w41odNBEw9MYsVGYTsybz7pbFN5zT6EaCX1NH6U505CTPEminNXYAlcHxwZ0oyCcG6P8TT9bkQcsEe6agh7IDLVNMidgx9LjyzV+FlzsD5GWDJ865D1HupjB0M8s85+eJQJmpsrhZZzSauxoSwVnD99qKiu3OEk/0iyjW+oK+7FNtCIyD4wTuiNSlPcNJwBjsnvDOsEkzY59RGZx+Ij9LYv2mC9NWq0xLuFThZ01MP1zeLRMiX0/QVWhndDf7RwL0YdbodJZRM1rNA7YBJz/K1AJCaI/GAkayeIhtQdw16d72YklZdNitao9tkCa+3gwjbr/+dHztgJnrrMe4xMjCHp/3pbjFdsKMsceBWD+iPHvMdr+S8g/dP4ADgsQM0ZlBRwgOr+DT48qrdCb8w3xX3XMyh5Y8b1n/Ye1CFTCzHaR7EPB0JtFRY0e1pVNg4PF8jjbJVUMA90RAbfEpS4IiiruVFpbv8W4S6OGULZWch/6CnQnMICoFv77q6kZDpaq82VnB+des4Vb+ST3sB/OaGtUxPgeyK5BdStAM8f7mch4TgYBjIWKbRV+K6O78dwVESj64ipSgHa2M/V+yyr3Fj9T5NGDJDtl1hSzLiUnERhdEZUNOAM07lULfPY0Ir2uAJxjjFa/ji4WYxPRYEyfm3xnhQORSn28S9hfWhH+Zw8gf/B0i52Ghj044z1X598i6bi/NJ9wPgIMFs3BYcIsI4WJjKuxUoxKS5/wxRIgugVuhP0Wj9zqCPJucuX5nq5847Wyd426rWf4yqtMVaq06WYzXjE6+qot4mgFKBmSnDZG+VZLZp3lP/gUgImo9AbmtDo6/HT0DUEZVP9HYMRvt2VoiYfoUtWfE4p1xaSvNRAQv7Y6I8YTRM4KUzErW0hS9Ff6F8ABmTDmXcQemR5YDAl7pp9OuE6uM1eXvJRTZcSGB2BHvXJLkej72OdFuOBfZ6+O2+q8YCSQMGpPf/Zu76MLCWQ5K+AiN4qoIcSPtaqnl0uAuExtvsuo9DqPgRBmB31+V1qnZZSRBp3kCXFLdfb2qtrq4zXc4LNNh6ivstx9lgEmxloQW1JuWN1USz9hrtoDoLqkKZrfgRUIDyrIG9kYkUh9CyiMc2uJqGC1IwxivfOggRJleRy+rvTZRyhWhhLWI3dEBeiH01sBbQ8pOrMDS5Y/PAeBf+7j9P73aPU349YiiUZWSp961QwZT/2uThtwW1UGHIVlFVK285HYGnEVRdfZ5RmMF4KVEMedrPzEEO3QYnSYnHURzuWOYEAg4aGsRAPESuvtzXglOA+8kMYpwpuzgmQAZN8el3dzKdGpXsxhNigRi5vL5Y5E8SBn26ri8UeoO/tzLIgVU/PpcT55BUqdux9omsB5eM+PlGxyp+sea+vbQo89FMqfKGF/AT2bYnga015wiGhaN6UteEUtA8ptwrx7MSGD3ALDU+b33x8GW92Gq/SH6DMViQwl999X66+hAGS8Bpuk0prERvDfJdwGyLe6dgPNmCN5lkz/q1H2DgdwvmcT6n8JESVn1vQZYgIit3rCanR7p8X7O4pKaD7+j7HdB+PzYEkGUgpGXlcskWmsfiH0EgY4d5ciyiXqqswHIvl8xNZRm0/+BXoYYJ5FXCmuYTIBse4kOq+Q8cOTiZHlC+U4Q+X8sB99WBe5O8/j2QApycRZVWoQYfzQRyPymz8OO+TF/Hto1xGnz8iCG26ngXNyDwpGAb9pq80qZytdcyVOesyWZppiFRKlpRZ04Oyn8FOCkwFh7gnjF01Yi/AyJTmQiL4lIk1Q6y5X0J56VrAGFngVVL94DOI0i5FDPSOlElcKxx+rVc/X7bTZroM8o08AKX105GV/UUVsk6JqnXU+T1uiQ3GBBldVAxAC1hJQ1B5nkTan/hivvGEcJk8igvGJ2hjCjoWJYUeQav5XafSzj6yl0uRWsFxhGPtd9AtQ+KMKCT+fIWgqpSmrnne5GeY3VGWUMJvvFe/6QeMJlgay5Armpfikk+sUhvwvKaSwF//fPemuYCG/z7uM7pv8OCqXLdn639ykp/Kwp8Ux8oCBcmhRhjgyLPZTmBB2NF0XPIhSVbxkZ430GFHT1Mh2bRvft4/5V1KmY6Lv/6r75GUndEYP/sIaNaQ0IbxdGPISMUesjuFvdQV69JbYojyBc49qclntjJXvbgO5xHoYz5C3yovTGsCisEqkF1WOxxYSeFM4KfTQdtcrVgyNQuAGwxGt7gWCY5ZLwku/KN/n9QOB2Ei6ZZ4pxJtpf8g2byfIkF6HCFHP+Q0HPmYaL4ZyQ4V2b6sQzbH59Rb/IahgFZ5jRSi1xbGZI25PveTxDy7oFwGD11wNC+Zritx1pw4K5lvFDhpQSky8AzMhcl+CWl1k4zP+jCFg5geiept+afM93OlynWvl4mw5vNH1tqOuT0Il753Q/SmDzbrqtfniN5TRCr2yw99RGF5qQVNTloq5oj8nAyXJrap6qR6SdZPFfnZWca7JZ+6GO1PBEaONSPdNb2Wpu6A02K7+NhR6idA/SFxyNm6QjB6gusxFD/EngU+4fR+9nJuikIbSXKJe0SSq5wXoYLbaQhn4Fux0yM0prxLRKhT0bMBs1NSJ1UEkdgzYAkgtJieOT7Yi/ZBM6WCWRQWFCZZbPpCLWWA8cnKrW3Ev0T0Z3qs00rJJ8AriKiLTSOUsn84IkQo0Uwdoqn8JhkJ06jHNSozUMh33nxsSZxGBBU3mzrX9uQM+wF7LKUvvLLLK+LDs32hLSx2/kKPLcfvceChDvzptek2mZskJ7Fe9hJm0M3ILaSezg+T96D5hrZaRGn7LHv/S4cbyvUmpBupvqdsq2YkUKj+X14fcxJhQmkgcze4Jeo4mt5wGWzjjN4d3I3Fw2uUCiSr5DnyuRCYTdw1Y80NJ870AuMmeDVyt59OAiUpgPfocFNsOF1cVwQZqkR05J18UwaBXoDfZOxY9nXd/JbdkhFbQnmWBhuPZmagiT4LgB4WHbkUn2V/UiLAuy+DMSUkTj0ZUcL4naOLBqV8ApncxcFJ56NAhUKVMC8oh/p/9SeyboxcJqKAdoSpMtuoASqHfTIffikEBxm1C/NaRvMmp5GnIShKUg/UbwUYXSurJel2FQg2adkLSP/AARaYoZfLkLb2T+THNlrwtjhflmPb8X8eLPioyPLgTy4boEWfTrO/pegL8+siygRQvI77rd2N/Z+Zb3Z2URZNbyOcAGIq8yvT2uk1ykydDKe8vSSUb2GUKPndV8S3KeBtcfS38U4flWpHYgiZ1G6+mgCOYqpuMN79BXkm9qfjtdra2nKBd8i9WAhlRLDrSnCYzj7VMtYvtQ37rDCZ04gpsv54BF7IVZ8alEPHEGCM1PFhihRCRFqxgiu1Qn0Nk1SXxtDQWR1oGxlZecSrmrRzXyrJC2jhLewHz5+Qb8+/8L010c/dRDBWgH9qigQp6trWZgGunvtLyqUomv8jRLRRVa2fhKs0F1EQ/uDkfJoYxpLJhRpcG5ddhjsox2QNTREJcdSfWKnUlZnVWHOO+8AylSudqAYz+ulV6RtB+oZH+sYRd5fa39E391C/bmxjM6E6JBj4Xdhmq8E0b+5uJe2JsAkWQY2aQlLFs+edm+iC3ekrUmjkaVvx5h/l2F0KnQdgfL7qqL40V2HksGCcjuAU4XF7xsBfbPKNoG+VTsR+iwG3yW+NHzEEInKYjnvWVhwOSL4yPzhrpTQ8u09ruV1n4zUMn8YxWDABLrAIkcFGJ0buaZuhiLdz6EPvumlOWkJXN6yLkOu5BVR3Jz8L/+Geg7deoZ2zWtsxu8JOekPw3FTw2OwHs8ZngDOCaDsSUIGnewkXHf6NZ6UHbtMLczUoGRX3isToxzSbiZ15+HDIxjd9HJu1MLVy7vkH3DFaOpvURxpZ0sEHYcaKb1K0OPEstEjm4+2d7LUyBZW816YDR3djaS3+YXIfig35IZyNKc4x6tb1SM1QPa5b9s6pDWRV/M9PUMYXERKASFKIIcIWNzmkGtTU+XaHQTbAMca9/O0GKWZXuJxx19rgLcbZ3uqennOXA4pkpMs7mHAXaO2VxWZTfYA8ficIkrg4CxGthjEKDazUXqK4pb9cn56pee3WuGh4s+ks8W7o7KRQYrseb37KTAICYS6v4szYTci4uhrLjJmpo65gxpL6zfBttLBMuhXVQDk/qT9bP2+timBr2UeNGLLmZ315uwhxza0lQvPK+Bn4aXDS9GE1Fx+VMNzmRjK9ERckAypmJFFfSNfbkQ88E1f7TeNKyWznF/hiu5CtjXBdhqTdCXg2XsP0uSz0YdWG2W8TQ7OwwnsS3q8T8EiBUgHmy59pe1AmhtyCzmBiJKEfuVJUBXwH7Rpgf+IDTshSlZPS5q3sLEJywlayJCi+44qrRPVYP2BpU1tGyeX924fqfX+xQ3V/kC+zaL4CiMrpk3neNc2a6RhppHy65lzhX5mP4bBvls5eGqxz6UDS9JC+z/+bOAOaQ6FKCDoiNmYRFNi22rkyRFiVHQMR1mFoSEAVqWvILIreiLNHB489jlm+dCcYr00KYjxC6uj8mPZ+aHIyfzvxzSOztgd3zf2a12QfKJVmt9dPLf/rUKBZDW8QFU/jNMrriOvrAA+xwFEHUk865bXNtxBWWb0lK6q4ZpHNkcVAwT83lJgc8bEgXIfvsaMbAuHQqXqFnjW6oJ6MpU1S2ReNtioI4c2NrBiQfTCA8ZjuoEHqgLxUZsIs4uMnUMsH0eDOrXcO3va/AHWqkTm6ReRPIcVPQv6xuD5BJIhj3K8tLyic02Kv+uOoPT5UzRJkzjHY5PFKtJuxUPJ1X4EUM/RK44O6BFPjxPg0zKP6wsaI6GYZ4B4SQFhfQYA90aauc+a5ngot7zMndjMeFIlBF0XiUpRxLMHwt2S9Kear2LRv9nDhW31B47hlSTyJGDDYQ4+LN12qGpR3MDXPECbSql8k48Z48SPLyD64NGwl1xc6d36Pu3QjiMxQ/X/7EvPHAjjThd1gmSujIPDAadnr/cp5sI8zM790aksdhfm+cWgK9lK8UOW9corNo9tbYMBBkEQKrpPqKUtFIjRbTaQtz4/NWroIOMkmJJGv6yElIz8GEP0Ab+piwMU2i3keGBGzncZA2BZZNTSGLJKKqHyvaviLFSNWRhMgrg8yua1Fi6Tm91zgJCFXY8l+UNdXvo5jZiMTEkI0DlGaE/WikR/NHrPmgEfKnAQnMqQ9jXSSmlY/TZ8Jo6FcNkCvf1QRe0xg4qz1qzR+kxotkgABJ/enwVqJ1biEgrwIAlhUmNzYGSLX5nMAfv+s6PFnoIuUDf8Go8GQJRyO4aGY83D2Jp3AoT8NNspPZQNh09SRtG/YP86lauAWCEHH4o8iXNGMSXrtZYN7HlHtFFLOKgqpuaidEsZ08QFm+zigISuOqAOumigYqPVMOYyemtKt6gNK6rL1r3HnvlOreUvnuMaq6A2wS+3sbzzaGTP/j0w5J0bLaKmAAxSbouLSk7So89FLqBA9jVfN2y2gjUgjd+uTDxEBsQgJL1/M2CSoxB4ur+wusn6yrd9sgctsPsH2P6tDa7h+ys0K5kOoWdcmfLei9amtZ18T5OQXN9Gs8CBmoyUxOj9974D6F06M2rjP1lcPdbtDW/QmQUHu0v226qOBUrTv4XMX3cqeym7+mhfc7gDxU6lG9aRYX+LpaAQ2ROZr22gflIuXreAjDKs5Mn/uQ7GT11JG8TBfVt7CegVLQ29I9bbLvj4fHUgSHa9ieYHRW0OkcCOCaF7sKrKvROwuparDc9NPi41vR4O1NWK3bv/sjvLg2zwmpxtJVPJAenqeXy7W6rEjM6wxk3dTgOJIlsgLT3YBkondBVKL/sCSQDI2mgCtpXg+HnDuOaKePTgaZxERGdHcYH/MPjBm75xK/CBcRr0wK9SI+BHqjH3Yt9pQGUqq+BRDLc7i7EB4aN1OjfI2B+RqjzWSWfT0tRpK5ziSDJD0xxru0mrqCrI8eN3X2ib3nM3CsrGGyxodn2kM076LDopfBX+V/QC79NPSEHttZQ9Wa3tJKBTCbUxLP2ybe+AAL3DPo68bae0OVARpq5z4tWAnD0Ek3Or4+og+TF/ApICX2iuGVPFcASadHGhloi27xB5GDa76kq1Cru4U8zK+AT6P8SK6T2Or172OqZTp5GiAD56JLsH45y0dQb/l9XafZPzR3MqIGc66r4VHqeKXywGex7FrtCIZwbauKx8W3T6tpP2N8iyRMOd1OQr4kZR9KS/fp431X2dwSyjfCPO6+HpDhZz6zOoa7ikQmn2Z+n1D8bdUeaqCz6q/OxLcrwm5IaTlIcdhmFdhJdp4gmKNmCje1Mv11H4hqoIRYn1j7QgnSmqMZ+hfUfMMtHNQQ0VFCbREog9WOG8rKcfGySjyagQvpSbowzrCmgpI4c6aqvMedl8mDBUDxY8Gb90qwQVlqjelni2le4IHIWsPfY8GFSoOG5DR0tGERnn/FGmrGiBK8bNAmeieatCaACfEIWQxnMfhuCk7GPIPSt0ZCMfXJnLVX1g9I0uyDc66DNc18i3QavKAWQLTwRq4oHBPeTsFGASU7ZzaoqSMcA1CjP5k1f4CqrgsOa5IRpuH4OYhVlyM/nd5cMhQ2xQ4QPyWmAIEuqeVXplKK3xbmPkoa1jKfIE9XiQHOJTWG8Nq52mQgHmY1zxS8z/31p9C7+rMy21cdOCgwkFrqtw112LpO1geJWYM3I0qsNL+BGkmkaB45Xl/48K/q78u54WMvqGJM5As6e+YR2Oh1R96WaF3eCjUL94LHl3r8Ucl1sibfxeE9vVJL2LCAAXp/o5BQZA+O02ZDv6yanv61k7Ul4zOJ88bb8n0trELNqoxGwDRxFoaC66Zb2rXpazsPZYztDo0XRr05ZlH4A7v6bqEoiZB90BE8vQMa6Q0eICScOi0mo16iRhr+QWx8+NPHiu+GH1/7MGx0hNy6NyLjYBDFTDqqfWdqNZjKmsYWLDR1cAzfxhEMmUcFmjNSdHho0ke0nozeNe/YmqKDyno1YKMKH2cC2bRd2hfF2w2zDTTuThhDJdcPTYPg7hHge66d65o2a7IOQ/5B1FReZfPm1axl4hQnIJ8ZxB0ebBfudGO7N56WBMXXTYpf1P3RJ3PTftAnQQMKFTy/Jz2osvWFAyfeGkME8QBI+dZcGwGbfp2VMjeWhI7md4lCvseMpjqLH54wV1Zev8FtKUbftp+o9h5Be5KRiVgpQ/+A4uycN93iLx70PB9VuhgiIlHaUyNjT4VfQJewLlo+9Z5wCA4Mm+2Q4qTJ/SLS9vEH3njjO9z/9aTel8cVUHGwVedMx34A4tX7GnR93RuBaWB4IJAeKfbKLq7P0DxH1tIbmMwc5CiqgGVR6A1+1ltn1v5c2UXwRq1IzbUUrsP3wFEJ3dLil0/cA+saXR3C1neksxqgfSElwLbVUZN9TPgFELfDa+wA+vz/WLDhWGJ64ydaE1+k09hEn0p8/wmeWDQdMiKv2Pdy9q09Eq/dmasdj+yuItLFLjx/rzeOeg1nUm8ACYRK/6RxHdzsNXazJi0ON5hdIesP2MR5I5nOBrVe1q0wDt1O20odQgIeFdHhyoeyNk/foBW4+HH8VknkiTLXU1yg5p5OpLrON6WjhQmc5UmEQVFMwd1QZ99HoqaSl1QqB05STXVAIYMQq83kPs6nByMBstauoVSjkxtsbvjbvDmTfv8jpm0gpRUyDs5+IAMZhlEDztBRRtEeSx62pTFlEfBUEV5eFXZJvdhp3uDtD75wCJkHj/XBwcLjfu9QOXEJM6n4zKIJrISMWxWPlikC6EpJ6s15/nNDjY3avZWmboWK3L8OdrOGYA3FvzQnbw4uYh4v/8ezp/HS7ViqGAacW4bQte2iKY65S5qfo/9YBGTJRwhDfFiPDX9iUQZWBu2V/dTsVmbfLy6JGlBDMmyJliiTYEEEH0q/V5TyumW8LGe+aXtwRhoWkV/oyO2Mpt2dupuCHpmiBDSBjIaLOuoyMWjv562WTgcmSomyHqhhFJt2FT2LejAfWMdDWgK4ohvEWH+cNDeTLcVQAa6xT51JvLgAHeLwc83MwiF3AR3NEVoFBWrBakDZ/qRn8PwhC+cpW5vNKm9/4lGtv3ChsxMWKdDQCi01c7nxYYHYUNXRDXJRRK3QUSxqzEoB3Y5pI0ngh2cNQ7uk2eM+oLn5KlZvUEfBXjoXLA9/V323+OnH6ASTgMTNscYq5Tw2Ig8QoSw7dRhxQ8rOrPKLJ5tnhV0W1ewQcI+1B79r9/zhhnrIQFjrW7BUFePWD/TDFQRfqDyUNxXNWBSzMUBp5S5EB+Ga9AUZgmsdr07cIfE75GE0Gnnk2PGlN9USCKtVxX3YQBgsIJcs3Y0Q5s+Tl0FYuWZhq4/jtoPWN0pKqhyEyw06mFy5Fx5OAawc9yxlGRF0ISSlAs1Dj2MCggyEWLq5GQW0QYtMvb9Xs+5PnQzmnwxUIrYLNn7wNA878yJg/qENfFuI/3iTurQQQ8WZcpgy7ueoRVm56mRosDwGuU0BO1r8DHo0dL7izR1REB9gkVS4KIUja41GRhStveJT8tSFqy6P/VNkl0U40URL+h19eLwTR9C4rg+FE/97Bfr+dR0UUoKxuDlOmOQPvommKeIadolJcqaDzkWArp904GpAhWMFt1xMRQMvh+xOydNwx8s29eTglOQO/x2dfc+PxaUEkZW3RDKu22Sj4ufRtia7lYegLFi6TNhauNy+/AL/gs+Xm8TJ/W6mxb5qUEt+wbLKLp34q1Er9AINyGSU8tOl+yO47DoP4bjk3aE0QIjXZbCo+4HSX1AC1mgqKWi14dwHPdYo46MSC7ln3oKMjkhFcsYdBocczt+G2L9DvngiIg2wpLZ4LIX7bQcy/rSty9ztTTpHAx3gjRGOOzrn+2Yjv4+mhTPsFiL1YsvxtEXFcHn5czP/NkGKduHxCy0cT1gajyP/67wvlvzppLXir0yHHzkHqh7KL7yfmlH4/9isnun/IEi0TOxT9CX4JaOKFWiXvxYogaSOr45AikafoTHsTRA2phrO/ukr0bApvYpDRi9tIrCmz7XwARNp6hb6hrUsFH0fVgjx9zqDevSuXaRtaGxMHtbcqzSsqPyK5VTXSqXsaTDJThV0LrUb8TNlY8gmICG6sPiTRwrm/xgAST9wMiKNfT1MJYOe5xKpuzP6798N5nOtKHfcjkaMijtrk5e1CV+tIRI4M32ve8qpmy0XpAxqTmNBWDPiKJkWOcHX1ZLbzE8aC8iIvIeIBtzfUVuLFW/lcWnun5hUy+GwTNXCrg3+NlkySWMFKm7SjeK13WTd+7Kj+sGiyzkeLxwH0QlIkzRCvGcgfsa3SFZVFPR7IgUjtls3IOOSS2X5gZL+e0KkOtNq1TmKhXt8jjbkckat4GX1tCTkdvPiViaQuMz4JvuKIEBKVqrhypQdYU/ULezMCZLIAE8lTpCVmS0uVAWctRcFgyT1dxVvN10UQIW1YDU8Zgn23Y8b3Nk3TQ+Y/dKFMvUWGlM7Pv5OXwTN9HfN+OobNtBSxGOtfmtxiJRSg9rgbYY0aJ2Dat/0mr38Lf0oDMUKpGVGGV3T337ko+ZP0ysnO1WGNW4fiaJNQXByVifZ17bTXgHombKaqM6AvSvSEEeM8NvP1wUQgGynjdDnbC/Rtob7i9br4W7VM4jvnPNKofhFBar4Lm7MjgXKkfM2vxkBfuCYS5ctwk9Di6vEOFh8+q7QNrWlozT/1Quj+TzhXq90BH0ecXSq4GQbjri2XG1M+Q1LOWxXQepCwhg3U7jRJ5C6hnSFDxVVdi6rQLPzngvwoYaPi58zoaT1GZuKOYny7chFk2RZ7WHVSy+0qNVaXXDTtrK81CMWAIVnRO7Se4i5gS70Zo4rLFnFIGCMooO24xq7Ydh2vrs2tgo3doHeoFsKfLBxE31VVScw7McmrMK9GEnbI7pmAwUNkwfLg6n8+MJjwhQK4f9ML2r3/xFYJUSZz11OM3yeA4i5bBuBS1U6ziJRoTtcz4j9s+/EVgWWqyzzEreicabooInR5lObzwQHNPqejwXE3ikZMYyOxf+1LcyNRcNY45I3zFtjBGrwUlDEmYH2k2VkXd7zecOS63yUC7iHo4wLx2FpU77iGpEHDqCepajx5arfa5l6DaY1YtP/NAom3lwQenzhxf4dHPPHFY2htgj3LUBEir4i5Wtmum9QGcfd6xijvFh8R7p+vXP/JJZXo/PZnx5sEG+zr5vj6oXSOmByzjNlM9Cpae9t4npDUJ9EI216Dls7XriCDdpKAtnZqEJK2OFHtUj2sPZBVor6l2K8LSdlaTMqaCOGfHvOgZOoLkTwC+iMDFkVq689hq2u6fcidPIqgkAt1hAGpCu3Wzx3Q8g31X8BvLsXuLl7z2Sz8Q4EQhx8AEAG8I8i6jENLhKJ0a8wcaDrZah1QmOzsYEPIMsLO90mmCAFTFlc++CwHKiOm7CvqZ9U/Wo+F8nqqIsp5Q36y2vR+kCl8Rzvq7FcI8wF5ukB01vjBB1mcCntNV7qJg7VbQPaPwhQL5h9Zvlbz1y/eD9Y8dyKypisqQj1Lt32Kau5NWebHZN+RyOPXVWidxRZltAhi8oE+52Fb7alD9urNAQWUfoiiUNA3dQEkG59aycXbhzEQRkTlPac72Dm8Mh0fTAFtSjIt1ZapGLvb5eyoWLbwV8+pC7ovijHdvINTDbyxYkjTD1jpyeDJZ4mFphMO4qFOGtc4VstKiSlKehsv81rzxZ4kin74dvxMTIfyip0Ugl8idx7btj/0W9pKtdLkV3lhN+CUWWPetOBasAY9Cx3IzRHdXtH27Gda9T3sHklFYiX0uWqulSlx+mtCchn1eE/733eV+fxMQH80lns6/IUcMMYuxsWc3De9/noeYHBv8ugcVaRoDdyzCd6jVGIedu7z2PlaA9R6YQ0LYWvRYzJbfKYxgC+ngO+VLTglhu0K/HAbgOZayKtgKKdeoFLRRHhk17RhVgOrEwhJTtrzXmZswHDQZvSMBWDWo610VURvx8ObfyAIOOvBAqaCNUoJCOP+iGesClvYDw04gxd1vrBwH3Om7wFoI2RpEIObW+5oPYInB1T9qRj5Ez7fUTVSjemDylBUMl3OM78noRQzNoDPw7QQUD3GeocebvbwNuLQE4Ihrk4K00kG08o1R17RmRt3+Phevk63POYYc/ndGR95FL1gzBqQf1s6TD/Y65cEWGOWu2Nwqx286+LuzITCG76UK8kLlSHDm0bBzQEVRPosRO7rsBEJxrjkqvTMLaVABtYYa/fE/1bslUkMJNUpXQPLeRQwX4RpggTpAQvA886jRdrrsgBqI1Sz3h3tS2rxlLe6S36Ze6WBW/W7RJHgpsApPwf7Zq0zV6wDAWxS/o9Z7aEQvroJx8XVMRUlrcZ9TdYCz+lZtPPxozCu0eNZcCZY4uE+Pvlct2TCVKj32JBrID/O2/gLkFxMgwMuI4dAhpM92wEztAdLIqJuYDMsKwU9GwMzHG5gkZc75vcXRAUOeeqXzO2QI1zDGFMvqcXzQcVRTgvCqm/QplGB0VKf3IbcQz69SM0KDj8RN+gTa4gXzaK/R53cKng5bqaQgFXyFoDL0YuiicMaxQuPjSmihyJYF15wRUkLnoDamX3vxRQX4M1kGy7GIuWDu38oH0DbpV7lzrywyrMmt11M2E0WkxgZPgn/cQqOVlgw3M1iLJg07cDxaEAesGqYGKUL7T4ayZzZgqBYioPSghFTMMFD1qQ20BTpWBjShAFb1jFZtcB1XT1yeJKcm3Kkbg9dtLJnhVOB/1mAmkSDF+Dh+EgZDzYz6DNukLFVoTBZ5BGDb53iQfTFg5P18/iqG9Z5T8zCZg8LM5Zz/AXP33AVTAPSqXWH2npU5rOyaISY6Vi5npFf1uvTQomYE4wTD/KLdT47z6DDKIeig9y/LI73Z1jETj6XwRVwXW+4zb47pLR3qp5oAQBV7fJ54iaYyEbZ7jhUboQCvY5tuDPXXfQZPYtknbLXtx3EGnwrH6i7Z7FcgzOvtgPzBxbjwAJlDkLp62234a8EfZJHKjj4YYqtXctw8m0XJbnjY5SKvIEgumVS3na4rhiZE955TQBo+nJDSycIGQo1h6R9uEFT3RZW4mN/bpM+dp9S52mljxPDqU+rvZSiwx5V3KeYbmejZkMiCsbprIqRgx//H3MbY5cniZX/C+fQLt0kaUWANw57gVv5nKzMG+4g/KjAM5R3GV8y9e446Cgx76AVYf8Rkw+9BeC34cqikJWi7jju6y0PaPI2trLWtEclR1akVK2KdUZXlwllkJN0kUp3mK4IrwNJMl+bsVLpw8l7z8xqTEgl3mygVa+0IrCCvSQwV9UVac9Zejvn5f0dul9LiCjyVrT3tkIIWy3aJ/qe4XH4e/lw3TNDxtOZpTQEUU9jjFxJNB4SCeZqs2aRR5oz0AmwYVZVCTf+hHxPQWuEX+cPmDD0p+rSbhwHlgb7++M3W/2v4l8kxQarnIO6tXV/umRHtTq25zKnBMIJKQ0sxEZJewZKzl9UBob7GEFBD3qqnyIkdJi6yTsLXSV48fKnnFrfUaEIhiVPNU4/qydsQHHzcfS9X9cRF3slTqKhR+fbiGQSn/+94oNCIIS/pALx9sCPymzxnCffIapZ0Wl9ZsU9Luy+Pw3H9FiDao+n7/3OHh25rLQ0T+aI2aruq/qT8O26d07TpbYn0xobT/AOEpsI+CQaRh6lG2T91VaZp5aTxNEhKfD5UYZoEpJ1PvD0pJrhX+Z4PhUq+OHPOHMZTC2fr5sz3mt6MhO2q6sK27LrIghtdkI4lOUv4RtPanoaPtdyac1t5nqn3+OEW+I1Mq2i0T8By1ozokXIHfQFTGgOfbPELc0muE07VRTWLaGh8gfCYfBgZiR6jsqn+YtnspDtqvjlFLvZm5lky4IaJMi8ioLUTMIGADUBpPNCW5PuIXFHDom2+B5LX2KpUaYnAVvBYVND0jfVofNBAr5OMjp7U4G60UeufveyvEGJJAPJu6ml1fF/HvVW9cIoUyMZwGN7OqoflYOgKDPOoOXgXsSHEjLWLLCkcODdQDvZgmrSuKn3mxzDyTZJfi58+U9FHIikrddNc+4q/CvZoxfOlDDG4gu9YOztoh/Yh2l6PvdA2WTZqfH+j3NibDwRbvtI7PKufDbyvQwq0fjDLjHzB0rvx3O3pRWAa4AsVYw/er94LxkkzFM4+LO+jOK1iB/nwvye3sGF/qF3mbOv7Do9IONTX8Qa9lO6NLOA5yyK/zjeMfnte/IMabcohyUKwOuIONVlEECp6gn6CWwRIZit+G6EEsAACc3jFr2NDs/pTALwVWnPPX29iaOApNKWdHJm6yYtyY8UreYwP8yLnPasSDQXgff85F1hrn7xdRbuMyvTsOg8op1KsrHxCT+Wmy9MIu7dz/Vv3UR88ws4zQstWP5o2DaxFiYLK/tYMg5X/Vr66LwtUhEJrdFOW1pdgO4Rf7855V063SNyIouBw/v0Ec4aNn87BgnoESOCbNw/5V9rhCEaL4Xxr8Czi//oBhQbspIpv2yRS45iH8Fxc+07Nbv6JRiL6xBhHXGbpOgTekqaSnWR+gENH7ZP3h7gpSUTzq7Srts2I8SdsI7BLxAXs/kLI1nVd3Tw5wr1/Ps4a7xZjrF8uAgMrb4of2bQeEqfqAj9E4YFHtBlD/aDuw+u28DCAro0SvI9bQaH3xv65vdag7h2iozBc3tb352zVg9PoJu8sMoEF5Cze7mY0fnNHOw6bCFSwCSkHKIodwxhG59/TL2VS9Nih/NLE+b8CxV2kZ9wUHovuGpLWRkH1xztF0z4A8IQn4mo3SiQT6OiiWdZBOjalm7oYant2Cm1J2k1P+2y+6ufFAWrORxzayX5QW6fhSTq+eekdqwuaLHAnu0NotzS2WXSSknZDaXup5s8ohGuxSPOl2DwrLZRtaz0dyvoU48tT6q3CiNbWNftAJpoHEziJfB4Nw9/+mOuLxALT3YaUpgOESN/wN4xUap2f5jFzWKtcWjQkbYzLHsGCd/OfmtJRk3JIzhCunmBZ8Fev0TWW6Uze1e0VQHzeovmGRIwZirNNtjtoKSvkJaBebCezl8cIOfasm1SjV3AjHwksCgV8CP+i5UEMwmYG7x4WJz7cRpiPBARnslQwTGEwM2cURnm5l5oyfUjzH9cSbLrc3CLw/Ug8Feas+77Zsvdw7l4JNUz7gvLG184+piEViD1eMlCZVDG8qszsmVrSOzVhxe+gpa7f1s1zN1iaspA5d2CUDxPhwmstzGqabrIEPNBOmxIUuP7Ujp8W2Z3nl2jXgyZH1vKT1Qotm+naZ3y35P4c7Cg2cfU3au4VVBdxKWHVv8BglxcqRe1yGgmM/2TC5SRwS1Ix3oVWkmb9CCCOua4Rk3T91177bxQBrk7BxzhWlyzQAn0RNuYH5b/ru6/PnXcG6aitNiEOwv7uW8J7C4rxfc6pU/EUQGNcXT6i4Qup/dgTNSd3ewV783PQ2IrIitoE0DjbmI3NmZiGZhXJlXZrLAjXoCV6/AtHhQo20ESFCa7pWo4zqLwQEcllPugP8AgqT4KbQxvW9RZ7/BeuSyFWPZ25bQcctwnHcNC+78O2n1tLq0bqS9HhmMkU+DEkRaO3sy77RHa8wPvTiRTFfzvmpU2kx7DLZpm1CZ7iwbMrz+5mqK+JGn/5oDsT1O9gen/c44YF7z3BLxpABelk56UuyQG+X4HJiMlA1yj+58SDB+OQYNKBgc65kQIruKT2RfcGu5E4AmEIxc5KKvSnXqyURCM5XZv+Rd1MrBEZfh5Db40BRqZqjxqgDKldyz1ogyj7gbgdryFq6WblIz/1GEkzqqc8epbulR99COMNIgzN+lq3gbIoSCvp/0w4nvguaox9NkQ3JaM5NWwgY3ADW0Pa2tZsBmiWuhyCoiWf4vsUu/wXc4dTf4Fmv4cLWXj8D4Pq5j/NV4dxOmY9b2SeWFogZwViYzDErsCcxANyw/Jyzrlqr5waZD+WaUic88XMb5rfejyuVgCh+BWBGP/kyn/m3PjquTwAXHpRAB+Q3l/bDnIKPuKFIjuGoc7T2a8ZIByfjU/l1rLz1BjzD/H2qYxdTrGvyWsE5wcqBttSFGaHT8XTykCuMrDkzPSvI0BqgRe/qoTm8c0tAAVVqqLJ3WoVQpssCCx4UT0Y6i+9fXCIidivWTiwWQOasvvRZX76JIu9ycfO7AajPZvdNSzMJL1kgVV5+cbrkJWp5ut/Rz7RuRrznz/Ah1YHeiRacwsyEsW6Ec03WDk4t2cAiFqpZtBbBPuVhhDSRE6OKEBWpR6nZFFtb3JtqN3fbVxx2l07afEo3cBXt8ZAala+LlO9FzkL/BYF5bhfFJH2/MfKhCcGXr43UUZjdi9yg6eJswo6gVFEXs4A4HeY8R6x77hEUacZnZYQjdDxwwvsf4vJVcGXIDbIjwpMdSx5+64+/YzaDXDGU3L65cIbaDB4C2g4tMvmAZs3KjRyiaNpP4+3rS0BCTH89zDdfD8kB64zwbsUteWCllPSSZ5g7UeHkpDFy3KQyl7UnKGBvzgs8ZOIYncKBwFdVWT96xLZLnWf4HTcNP4MhSsH3PgqC3s+BcxVDmdpAzRZd9POfklcVZqwzLJ/s+CAFJIgCHMwcKBnsxEUCLtmh/shEiUWC1vU/SxozTeT2fjCikLh16eZ1pbcSpVlxxi32+mkkTZfgTwZF9594ElU6ymSE7lVjGe8IR9iJQ989Cf2sYNcXvw6qAIeR5z15op5aynB3o5JsbJCSAlTWxsxthxlKWZKnnWPCGAc6qXs9hfpnqF25qUfiMo8esllaQ8iPVcJ+1XS4df9Koh8YgqzcXPFkx9SZJg3ZnRb6xa3/HOVfQzGbvV9ERCQMMLc+c4os5kS3c2k1OPI0oaC4VO7C3/ZvFV88GT0Ltt262HdpQJEjbfcpjdsYToawoGfYyocIUT879qtaQEh+OQAkNnPUVVARhZiX90NzBA+XKYRAA6BVZ0uO9evduEToAv/SElOMaXQjbxLZpKlt2ue/hSuf4SJi0w/bqHR+NxzSGSGBsqoYG31dPfT9gSrsmYldjuXjnFMhbKLS6b9avjVeIWu4VZAHh+0C1np82kekVC8eDKlyvzoJnqjD1dfbvPzpEX1hyPQyRQJ5c3QoWHnfwi8AhoSisETIoBBt3B5+XqjTgFMXl73Gb1cTvBwaiRYs7xwoa1Cc3aarMQ4h5+exYTHaBp+Q+zYgy/GyJi2IQix39LcTZkscAMSnqPUtEZDZq7zHWRIil0jTVGGc4G4vaKtdvRtGCYEY23zhLgp1NAR0ztSq8jrhU1SiczSuGR3Zy+wNlE1SKXWB6cTEuCcP+/H9rZxApb6Ck38Jqf8xCgnGT7n/JG8xFU4pm9i4QGtHKpvP1bLU0kyBy2Ixmx5IzhPIbNPBQ3BBi6gN5ljb49sDTE2pJZwiPdRXunsL/wdaRSGgFBMxGJtnpKXSjHB8ZlkLw67BaZEMR1FQS/gNMoepPrtpskxUsBn7aDUsbNlbePQFbEae5/t88mRtNoNdRq+rBxzFHVrtD1Qs9zrkGvxD1j4WABI5sa6LUwAepB70gpLyfn4TPsDkm46JdeLPQGmPQmuwZXV/IgbZs0QKPllo+HRmcucEoMLlGLbla9FqvlZ+9HsU2tgNNxh1UIT2gTtXvvye1gsgwtKFrTq3I/cM8PlyhdP0kYuRHmb/9Uaep9NTDEX6OvWRHzCj019xMri7iWnMPtlxhtO9pv3wiZ3muRrwonVUwBbrqSGaevD/IxgjcHsuXs4WkdRwPlhMJdVUrNEkHcWgDDBY/hC5iHrFKI8z2ClEjZzuy6I8muYstw25y+Tp3Mrkur55TQNF+TGpO7O8f+EtNWTQY6bBhlimoafcU+aU0/vlQORSUyeMpHcxktsUEZEcEobxYiYt3/vtT+UWEV47suTG4G62cvE/6Bkrt6z6cwG0JJBaJc5pRb3lmwucf4nRnoa+LOcwqa2zMtccs6ngtA55ew2vWuUq4uX/uors8RDjJ0/vi16nNtCgbTvBqFyQBJWH3gBCqqBuuqORJTvUAZcnx7fR4qkuE2nJ6hPh8iyO7p0dztgoXS6f6gBE9cxwMVpeZVrVW0EEEHd9Xpx4TgDRtgPk/UJPfUK2BjuvYlrfnmEgtIYQmf8bqiF5A6PP/KkYeIpsPnuVi+X4EclyHHPyfExxc6Kf0Xd5xTfFPgLEsUR8SH8xCfI8sKsHE6cbjFiPPuvKA3Lgq45b7smnCjoje7k0otCwEPxFH0Fwk8jjnhj2BNYtCOBDQAIVzt6msyOXw8AOSlpnb+HJaG0wKpM5R26haXV7KJdK3KRvDxEtqjUDlntJsuSB+lx+oj6ZrDmJEfOQMWAHSZtO+QdI2GoaQKnlEzM5uS94u7HTLE7BQp3bYVF9IIrsCimKhAmKOH8yZb4lZpWFXdG/dBZBHDY8mY+yRcj8eYvOzhvYWkEAw8Lh9TtggbUj1phl3enTHKegLT6mLZnGo+e5rvmUzhIbtkYs5NH2wMVdmdZMYH6iYKcTYVRR/owPh3aAatY2DFXWMFtkC6KYz9mAFKz9rCQBvzXsuI20k1W6/sGHqa5Jbrgoh/iqVpB+d5tTcB7c/L9arBAHJgnYLcn0PzQfXRrcPTwBBcQp2qtOeoFZdIb0CTTzRKmb3R/F9Ndxn/tWBwehFmQW+5bGeN5Qsyq6659iIZyjS0KGoOf/mhJH+ZR5t61R5cIKccYwpPaJcXiGQER/t3lnXNrfVfAWhiC7vHLwFFnHm4JlbnZPk5GO4/m8z2bY88IjqMsR3SrPmQErsy+E27tKUjpyy0ahUWe//2MU5BjBDb47HuRkGTGxRjC9D6HC55fVsWtq+EAdfxlTwZuYNXHvXelJMtRfMpfoCDiySgnQgjUNBaurtGUrZw4yu2VnFFlKwtlktElx6q3HBGtMDuJzZn87z+m8E5Kc7Q1j1wuPFGBDgjPXtrNFuWm7T+meBdhzOqO3ZfqydlQn6OBuXYGxd8ic0fr4gbG0/CG2ez9RdX+TK+UpEW7EkWeYTjy41YmmhDlmK18Sa224zxME4Mf7JXqa55UP8Hou2fY1YoHswFD8B+Re/Ad9AxFDiBSo+lR9xjUY4L7Ss5kNWvnQdoDGQrm/6Til6kbIQwb6W7DKZQTxVQxGQB+GZiqjGZqVsegbIY3G/AnIyJzW9WhInyZCCWjcKObyHH09i/0U6ZhLxpmQLGpESLpNRDVe39s84RnrVDchJQOpvvoFlr1PyMJs4sayDhuob7Kzd9TUImUr4RPghXEikvfq+sI8xw4ERDKYcCu2MV9Z6WlD1wdr0IpAnZXYgbZLFPmK8d98soSu3/GGGtI9HFTkj68L6Dqj0n6W3XPoCOVHI7C6xsHP/bUK9FONemspjcMSq7G+rcsqX/D0O0OChA3HXqtElquVj9v9KBPd50ZI1mbpPjg9yIpqS4CevxwqKESrPUZe6dRbf19HPt3IbUM3/gaZXj0GpDaANRiPc8ucv04otrA34c1mj7u+LRKPYbtyHpP8SfHa4xP3GUlq7fYVX3okmqiD8Moomu/1vnXtytGrP1aidt89nrS6DPWXoPq1JEHw6B4VwxOtNQ5iVx7Ig1Fg+Z70Se+7ybstLWG9ocDg/Kz8+amctMQ+uRTzhED/62P0EaH2jxxmAdEouGI0dYA7ZFs+sPEFDwIZoiWPVlEI06TTAakVO/L2cpervoz0GQah+RF7uHNPbzdpgi037cnHsGsztSy1oWzn6F6cLbgZI1Ujo6Z/sezpGa0jqi4Hf2GYSWcHoymQJgsOLd1o4aiDZ9QMexOX+McrhwIbbao5J5TwTkwywY0CbT6HM2evJ1vhfCTINd/vYSvafQ3iDlv+UbdODhGsdE7Qfq7Ohu424shioCTvHNNHqNDI7jgHRH3uXo2ZKqTCK9EnMRIU2k/VxMA7h+WQyERtfvH9/WD0S4juM6mtKUUaibKezKABJosWjnSgR/lpovddOg1quXF5op3nhfaxl4c7l9NfX80e2DlPhhSvtdNX8Eb1L+xqIdDXwzgHqjObAmjtbmpHADgxEbTgm5Se0azbFPdCfVRo2hVsGnhiT+3UhJRlpabNoA1XQLN8mrO5DkN3+xwshcBNW8SY7IiuWSlJ9Ot+MW6p40kGrvT+An8I3evvYwWvZtZ0yK7a1oW0QLCUgzy0Wve+xVo8NgBo3sAFLcS3RcgHEDsxkpMORg5x8pHBTAxf9XX/9FIQj1b/n1iAXnexL+Z22SkCjk4qwE51aJDK8cC2r1iMdcRkVquyN1km5i/XNDW/wJDtiGghrSjxvV7g7qN3tKMeUx7otduu1EpyTMmIuGSiOSYfvtNC6D4/+1NEqlStbAoO77StE9Vq5EYJx5Z1QPW/Xna363m7ihqQ3VV/hlxHlZGTMdPwfEy0twc0sFHCA04h2RnVJ3xa5z/zETGAOlyYm0XxRi+106lEL/NQqdrfHtM6c48Og7s2b3mrisDCp51ly7Bi/lYaeFf151jASKkjk3tWGmgB/HMLENx0BH4t0lmLFm/2qQa1g96ynmLSeMGN9PD2U+v8fuNcrDuG24xWuZG9Xeg1Bkg+jwncWM6b/Iohb+2U2PLLypYgAocASqo093afAkXqBgf3WkzLfo8Svez1+9SPavZg+B0qWJGXkZSLQ6VOTX2zI7RoIpbCrKqRshfjqJ+qejxutSLBJZbypXNM4Dzqb4niCBnCVwjNRyYKCOM0DwDRTFUE/QrAPw42pXXIBPKCL7Mr2n6nyPfB98j1mAiBgU8hGr4OFogjuVDYqmyiOGWfvaEmmOoMcWe/F4Ljlub7fAbU0sz7gdqHc9VaE8FuYlnAI+7rP5Z981UdaCM2/5yTSK7++WAC1zZLfobjCs+pKC9v1vdHLbi22M5T/G33cz3/8cjY9eQ2X/cFW01WhGATNAOKvrGgcJ40DiiBJGpYL1D2TH9xDi7jnL5zz0taTlcfR+zeqGiLLD384TFWXvdmTS1dPCeB2EPLwXYwXGW4neDfE5jIKYSi8n5SbrC4Sy6gKoa1N0IkrUu+if1FwMBVmnoI/IvIsHwIa+4NQWbekSqvNlgnIVLHX61HO5kbGWEwopue04nXcqAl3w3ucFzMIbFaA1PsRVPkAktSafoAUDiSpK88QBwUiFGAQCm4xAEw9mj8xOffhjKWUambwuJ96zPHboQI08t3KodZDJ9PUWz+Bybd/bEkytDUOIq3NmToKtKWUxn0TolCIsoAhuT8i/daSrdrM5mF5ieQMIBNl3hvzO2tuM9q8ZXR2bdFfdDvZrqkloDWKeBoca/Z2kmlIBtyUNhbqIl3+be1p838xQPo6UlSRFylrxQ0L1CZarOIgl/r/lQ6B4B6F6P1El037G9aT5kkX1iF0jSNqCO35yUQNNDDXmmpQ7ppJiaHDuPpmyLZTjwY8gCq2VFFXyjo/uO0VtQTsZ/6uYQ7m6VZmORhWb2B56LdKWx2f5PZtatYqCsrdCRB5ZbjniTaHxveN4CdcWv45WpBwNER6qO5DQ/vyoudG6bga1QvagEI4ui4TAOCtKRUcSNaAXmQPYKyCNT8sX8v9jsPgmLXsCF2q24ZTN0eg9JQFTl0AFMJwgK9OsIFpcl2nVAT0xKHKLxwOBalVDZHxIgoBbpI7ixLL0xkvNijI28W4dVOQvt1NEoQlIjp1rRg7BOUHnbM9K0fiPIrAC0IjOE0vlIFIDh/APYcTs5Phfc3oHrxpNlMVX+sfx0d2zeCXOwrGxF829lOj89vkxZI7aaYl5pVMz9ncOJfd5hrrvevV7ezMrbjEDvuvB718FHesBMFpMwIS/j7nPd6ZpcgM43oGfLd2vI3H2N1Uh5WfQnv2/jMr2B44DLexfK/M11H5Quu0g2V2LqcPE/q1Rzj0fG72fuSwLFIS76RZTt38K5mVDDiITAZm22Er+GDHBg0Dw08S5cKkq496TKi0RnqVS0IyJJB186G+kruyjlkwPUcjizpOCUWrMoQp6kJZbFhZnR/9Rbf3XYozmCtCfZdS2ea3an0oCrCXjAgjVnvTqYXWGBiUmHHvEBBNnOIC8mpNmGriPq1Zrpb0taMGG8EsRyIZStYKkcPj0a3TYccdiuBSrzYDxJAK/9RJhhPoOE4TJB+2GG9EhL/4N58W8yAivKMy8M54aLm2a/Oag1bpezzvxtnUxvFElUjaA4VkK/YKBW4CXQc6DWmJGGEFMEA3KXWaCdufx1QOtWjv7IHODttXgv9yfw+RHZ66BWg9kPXWwWwVUpToumIg0c94x4CW1KbWVkyivCDl3lilG6EnvZulCebtqTDCyvoWvKxlGTFZu2Epg+FOHXL9GNBaXL7kTqEbEFdWO4KQRlutHqRD0nPSoNV50YSGorq3eVsOCzzmErUux569owLJfvQATkkai3ZUwfZus9HW04NE8TUnNjA0bhANmMt0P1ozik7JruwC8t6Zy4IN40fVyGvEhB8Sy+McmnQvUNQQnuvqRqRb/QKE0Shpqme2FxTBjnLDFayiO9U4NP9ZjURYMdVVx7Uk1+vYywSfCohPX13lB2c0RhbT1m7K0FZSKRMtoXKRgMhIPmLbVhjh48E1fickl1+Vy6qjciE3THya/VtFyhYCUxqA1CvkfuiLM+RqdK/uGUklSFKXxANlaLT1sIDTMJ9Dfd0YMeKtn6r48tFkaE47556n9u9VS/2bia6RrN55pmOf7tYB2Sbrtu0Ro0NDP7/AU1OaHtWWHEpbcd6/LeBigyZrhIJpWYgcU6eVgwfRyD/ZIp+RjRB2rW2G4VShrvvhcnwOk/y3WIlox68b3KfXiGBTQW9qRnPVwLKfOI9PyvhOdYvMUJJx2B/mnQQ7DhBNFb0+HheFKAeE72stDGLC+9fjcXSLwH/WJq4Xb5GA9btaodC0S2qCtBZkNYVVhe1fRz9hg/btCp17MGOxa0YtRrP0MsOjLcaP5Od8dmkSHR5ToNKi4flq00hg8SpDy3wh+s3BOh6Rzxgrofc1P/OVpyCe82EMFydthxtJdmf9hqB0cOLS/kQ+LFlGODMxR2KPmv56X/ZeplfyTQqBpAkyShlllkHfiwEn1YSUnGxJfK0sF70OUFqYr6Cc6sj7DeMVKLg1savmvwJlejRZh3p2Sx8wM6Zuaf20yWSXjQu8+SfYBRGfCMNqADWJ23clXtLdjr5aNNfmzDyQrc6kqclPKnTyrJ3JBj2xYvXrAT+k4k41tJt0rJ7qiUzNFTNxLLP1bRtkkFK9vmAQmPSq/tf4Wu8T16QAVMbLMoboA++MVFcGq7ArWKNwan9OxLaZYir+2q0BWLmBxI30bMAUFzvqlaFayCI6u5SuY9e2OUo8QEyGUKRlXWy0jJfuKx4dLoah7rPvy9TjrQCOL4TkP3VLJ1/dB5tCGmJ0hoZn5THkah2G85kBfs4R0JIHKVkNkNXVZPkynPqlFn/V7rKfGQpK8Sx2tAU+P216YWwupCMzSw21BPM1wLQhBO4IeIraNOBtf0I/ay7OSubr9W28h+L7gh8KmTE8y5kc1cWc8q7mIxQnEm8e6UYeJxzKaRkpQYY1HAO8f1sEFGeGAoqDl6zaQqmjXbUY4oQn5GJLqG1OxM+3vkRJsdQ+KMYbagmnRASj74GW5/WcljVLSMzSrsU/qxIvuIKSJ6L323NtAZzK8F9DVkLBLCBLlY5z2rRva2vXlsAW9VXV87504+u6XtldBY3tdM2HeL6tEulVLZgiVWVBRYj2I91rj8iFSeyV7cr0op664iLDVIp4ktTCe7lrH5Zv63D/rYjqj+Hnf4TLwN4+gf55XhWDh99yB11zbbMqsUeUSWOkJmtHR1FD8BmG851gmk7x/TF6I0NRX7SkwO9FMWqCannpMAHVy/vg9h5gfuzBfGkXZv0ct/2VdIsu+L2tpiSqpsxS70qkbtyxwphom2Jh78agBD3pjhBqqYXGkwaDjXS/T4DchRR8nvhXOHD8lxzHvnyDZTUg8LkPmsWtvXAimJN4JmTi6nrIrbocQSkTNZbUK8VslbCeLeC7liTeQpgxeIvofasjHZDGfxNL6KHbXUzgYjpFEeOjAe382Jd6l6NhirtxDadqgV1tcP1WzL1ekDuEJzq8c3UOfp23R3xdJ7tfidZe4Wce/udHfF2Voyq/cR+RGfJxWh1CTpYYGIaEserGvOUXnx1/VUp4HonJje6q4fAxcnQ2bR60JIwVK4rVb4YyLaHooTyA0usqz0Yw0/S+o7Ew20aClOaDA019leLhW76nfXPPFLslvPH6+94qvb8wDlqeFdDuGfH22gQ7wQ0UrhFj9giM0o/kMCPDskFl6tdSroM8WtyVxKuubPxf45KFcQlTQBWpC0MvuQ0N8ph1vDz5OCOs2q2Dx1QrKH+araqs0WE4Xfm0yS7RIKdlbon/HD3jPqAdWX2cAQ7dKEin9Jy2Yi/52P61d5pUsMr65ITpI3jCNPUjlTQ8tsaZDWyECAqG8qCNXHTngNs+nfjlIDl+6A2UG4siZU/kKVQIdGdNPcvvXKAtLQca+E9BEVLs1yIDXC16GSbbNDKqj4lLwrMkQNSsYfmtYfLXPo52gv+Gt4zkHaN4iCKH96BQCb68VOiv+icFYfkWy5VD/iHPWmhoawP3kSphsvLn08SguwEW2ayO9um9PpTDXoo7AOWlZmAzhPKj8NGl2T5kJENtnosMPfweKpiGG4jXQUUB90BBPQXetjfqRCgHfXwimuPrt+AuDiMW2gzaJsb7kskOzrzNswPU7ZWX+hPG+y5ZvfEzjzKhlCpE2AJqG7aOjXpTlSH5pE1agSzyr4cu0lSXdCz5nF5ynYQAy1kD/gKDFDAlo6+lE9XLZtoQZJV7YNGfc2TDbYF6H/BgCzdybGqLAocEIMXdg+O+6tSv78+xe/OV494kpybXCLE17jNPvK6NTpcgJVXEiobfq3po6LsG73hEnKosrcX2fBjz1ICIIukTWZ1D1AmsmSg0dBWWvlmEgSRtUzGIqhLWg6/kpH8hWa9XryYmlVdRBCK5OIqyeX25kf5I3folnsIa/rBhqbHTbKaOixte8OzANDhE4kXrC7Tg9MhRGSQpmhWsiMaRzIn21I34tysbADoLQSOnF95PuBOohdtOmVMOX9OvSD74OertwVf4YxNAnL0WGqQzZuMjaXHCLxmyGlFEffXd7Zt/sJwg1CcJN2a1YBTRDZeI21djPxtXcE1nY5mfVbR4hRU2QUpfOXXXY3xq4oBTn29xfllsrMj5zNnIL7WTKod4xmlK29gzaO/km6ufWIm4R4V7VPYin7SvpT9Gf+MjP569bQo0yIF+gNVYZxNLT6tcTDF0sP7r2io+gqd+BhZfWpJflhdX12eCvC8xpB6nKb9Ja155wwmacMWlIxPfgV/Y8x2zTBdSgg26UFpwXxic+7kHpeireoiv+OSRrnvzNluWef9RrW4EIrNhdTbWKt2cy6Xm2B8aTu1JcvmBAMOVy0swWwd3FLzEnAsgs8sWk1g/eK8i1/Mj3XtyWFNCLBStNO0pQxAGwxLq3cWz2EZQdlpjdc/UhbF9Qi5KHQHiE2axr04lSOtk7PSXxubndxdkxY5j6le4Z98NCOIlBAAxA+vFZ/cimzhzlSR2QbCo8BFIc8LK7YA+6YfruOtTwoe+sM8UyhTaxPicwC61kIJVcvohp91/GDmpaPxLZ9jAzEkcSAwAn22ct32d0ZRff43UC6lOOhjjryLdn+Gp2DJA0k/a9CLtqdyvubaNt3jo64o13IL+s1k2mDwsfTcoccT2iuwIJh/vUzb9mfO/sNa+TMAlwGwUIK5moB64uCU7XrG9xHurT8V3LcqENmRNoO/SfbyKdwRZhiXAdx3pJlEMqpj2ujJtCGWMzPEKeuC8Hw9P14Jf3MVBBVWLypDexVwb++PpgONLVq227k0Q8xb8NdBr1cA8ZosSXr/UPlVyts5Ap1uD+QIa035RazeXKn6ISfG33panpVxbsXMARPpAw5Wjmy1u+nmRqA/DqpZ2x7bJPZ3UTFVZ3f3qO75wDH9yTnW3H9nR2BuqWrPW58lMjJUD+1d832huxwPUG02+oh8IrzSpWQ+U5sszvKR1Z8fZ39IrBDbj7mXAFhoNJheuZ1N8ReXuw3VuehF6mZglIeyoBbLQbujBKhncEF55JYAMVvnPXQBUEesV8oxbyI5V3cado6KChUBekAdI5d/+9sB4hTS+/Rj4Y6o+TuAkdhceCzwUS21A/sALQz8EqjXFVLMWO1lgDiQY6k9D3JnZ0R4Ec6Yu1kaiRRczbjHfysETM7mZ6iixndnlmt1rvwLaoBKi7jUuQgNKkCexM0B9HhKC8MHNvQfaBNuzQkBZ0leb+YLaQxw0sS+cqhe2gEd07cIJ8hveBVjZSHLgFBjSVcvQ0ZD/HZDD2w2p47v5cb8ngfi7OqtB/YhHRzsnSWUhx7UVvfczeEm4HD8tDClfaRzNMaZsqM1/8g5thaQIPyhPoVUktjUt6li/LcsN2hys/LDoBce22FYCCJ8P83tmZbEx+fDSQ10pdv0cNUKHRAVA0tQY47nLp+itPVyv2GXMQmGCIiZRFSxH/V3bcaon68Ssx/V/tYW27V8fohwIcUZwRtMGSLQHXF91HoStyDG1kuu1h0FBXWLXV+Ce9LC7usRdyNrSLv0OD8F7AXMfFW5fo7qQY27u9xHVqTivrZh8ME/N+lwxamSHE6+ojxHIuO8Ci5kdIBRjZ3K7uzn5wlsooAZrfJk8A0NAYzFyr/IoARjhfjHKgKIargz76CWZqPE30mzOdkUsnpLIcd+gvcgWHxvs8mslYmssly7jn2SVDgrdoGLOd1kNCuzKziwyDTXcgnrxZncH2BVlPo0NmiEoiK9WRNVlXre6F9/143AN7dVYnvoFuPjophSNZpDNqZGwdXGIGx2ZMFSQ6fgp5I9svb+MSGv+mxWCQq61kis+S2d4FOFCNNnxHGKbaV3mZxwNqK8a84MiD9Emx02Git1StGTXwahTDFqwHhOfKLBhbigbuTMVU2/bpqcrt+y32u0Ba1AaoTKMhriwi2FP9kLj8hobK+yBKNJ3zKLP/B37tduFqi1Mt/8TUU3ELcr1EbDvc8XTuTCKtHG12ArnLIPtigZgpk9LPCOq689rizBShlysh7aR+BexVOz7kny4t4JVp76A+wiqI5TqT/HE8PRlE+mMJpLBv92VKgZZLuiBiTjCaVCzZvt7Jvz560WBzwYu+OgkUhQeLC4bcnkrDjVFNMvKf7gY/Hltx7eq8OmV2f2mtYJqCyGTBGHp8eKVIOpmSRbv2hk+Z6v+BuAfdgY7dOjG3cMtksJINzGHT3MadtofJatv5kItBHd3bmjaDMk1iFG8XffJnQUsndnXYozpULt8Nk90wX7hkBiXJhgoNyJ2Nlg0hDqj8itdamTq2cCtbNBwHinfRa6Vsmb/RaTlawQgUS8YUSTIzAJ5umPO+ZzfBOvPbarjx7RBNPEkozjIe4leU8pLPXiMGMxhs1dueL0XfjEtxWINj9G50b23qp4y0/Oc/jm0anKjLjpGfO6F7d4izVR4Gg38p7D9F/x0YoK1PyRDQdQeoa0DCAkdVIIfh98qtH9pg0LixVpRVA+SwCaqY02QouM+dEwZSqbD6oS5KIArNyzHE7hI/FNbJPBmUeNhQXhHiImCHWT/dD+Jxq7mVixuWgIeL4GGr1z7LLSyJYMnLxYe9jITtEWowsrP2TFeKgcnoj5Grwoe59zUngXT2u92/onX/pggqQx9xPrXDxsFjMxcsU9kPvIx2zdk65Q6hS+vQ0iY6MHShZTxqg7dHo8DA1hQVp5faYCz1VtDLFBVSFytOBp58PofKR/U8J6zJridr512Wg018b3BAG4XVFLebKzFgtGtOpaVw7Cr07rtZ+3IsbtbIaLcxLG4NLUt3Y+iby8Abw8fJFxcKUt1DeFCQ/vNiOqG1JlgMgSY1gCI6h5hJ18BLrH4oiz+eTLU4MnA7fWVESZLpl1LExqvAGgmt0RLIz0WYxOZ63zldHSzcpZ7pPsvw8vZwjgCDYNWe1kFEXjTmVXWrKZfXbg1MDjFBfWurV9fUZKCArlbF48s/f/xpsAAYqbGoQaotGIa61mQp0cXfVKsmArv8vKGds5PRLJRFyKdBykBye1qbJ5cl8us9+NNQD7OdKcA2zVarwI5dmgYxxPtI1rWEPvaV4BT0ansDdL8lmMJjo7UM/XEDEsWmUpdzquT1pR3GQkKKAw8qt8qThDiPM4hF6qbl3tvLkXdNruAuCIfC6UThtLXWbIwbkXNHjapTnqK1ST8+lyYwg7gjCgNEhqWe29rc9gugUIjMmUrEr9l614kuNxEvZqVGvfUh7jfJ9LFwV+zdKnt//4oZCbBvpU6XV0I5gncw+s6Z+0I2Rpb7cr5fW2dttfgPnwvZaPXm+rMi/c7qmevM1qQpCZLStNr7w/hqtIA3uRaXPSwWMubtNXueinE9uw6vVHwS2VjErJ8wSAiM2cnnrkrmYuusB5SRhzrv985BgBnD9BZb//jKy/8gSA0uEXYaoW0k7Qoq0azCsJZNdybXA0rLpJl7QnlBVtqJOW+f3/HVbQM9q1r7P8ysq+YtoxzPWA+gmQMd35REcI5oOiP2R0STyYz9HsRdMGi/P7WwWPptJNpkd16RsmQIhG7nt5rzZX0oA5DG6edwWnEfL1WOz4ccnm2oa0+dV40VgVM5KQszWdY2M2Cq7Dtp2ejYu+qD05NQXsUd0vOsvvQNagVCXdthIvZByf6k7BRUsTeGyKQT9cgf811faQe+N9v1cSJC3AxScTbmC8oSpLOyT7L6qR/gGJZ2aFdK21MO9vpAr1h/VGiPiRk43OnDhpQyxJ3oh+AxpGUO6fEWE0ae1r6lWjJYH2KrLrRLjRZcoOkZOYiklcVDrUXm2Ip0osI+iXWtBW87nySDFFkQIpUVbakgfiAzxusfcBjl1sqNmiwT/9Dl5hmJOqp+QJZz9UmWjpOLoCh7s9aoKGK2dGC7QsjuEczoOUigR/T2GF5igPqKO/fY6iMmLkfLcTxWF45pEnFvjsC8ezsLNfb7aG+dRIRRZQN8wIQYl4Oe4ttpr5Y78GDm3/Tm2YGbnowbpqDaqH2X5UbgKoNy5xvJqRcYN29UBtdFGb8X4sWXVjtcyEzeyRAh++Ljwz8qL54ax4HhXcsLDqK3I7HxvlFCwqWiwxcDmlkmO18L9YOWdgo//UrTY+tO9YR9b5Ct93BzLk/1o36BrfSY08j83erCEOe1pmRJzRKNip4AmFetTQfS/CzNrUrrCMGmzAsDkIs+0Mgrt0WJTi8uJQp2vV2BVERzVrWPWsAqZnWMz5knKRGEXKcsKxxlgr0+hIUFyp0nCXOIlTKoB4Nf5RhGtf34hZDTVm7eWtjPM0dyA45tr+tLk+7E5E7H/LfHarce+L5krXUuVbf04TXBwZb+9hthPEYP4SwwLwV1+ivgowh88ACD00gNg0h/dXwL7IZ9+gv3hhdvMYMyWyPO7cQd97lJWC2w8gSQVrgIRKq9HNA03Z1bIcPGpVutk/88HV0j5kke0zuLroaWcPTVCC/ciNdBILVMsS5BNh5cg8SumSE/cb9NA7JbU/UW7CdGPtBC3KuSBUHlb4rNJ5Gj5D3UPe8UOJraw13T18IJaFBYub7C66jD2+Vsj8Phm1E6C+a4lYcdkpaO5IQC2poAprHvmauN+uYc/HyP4QhOYBaq41mZI4VgyGrqhAJbusZYvQlYvM4FY7wVyCKQqVyJQu1dMwxhakgiIbsHiXrBpwGv5O1m2QKLlx2FHvil08lDsp1qyf7fezJwfiWOiti3uiTZ3d03+MlD/xPppja/USmTPoZF1tvZjcItof2a4Ld5bjAML7KWO+B+cmRr/DTauztvRohESX3WzzqLpm0RYVf2JWq1Y3wUcFN7/fbCcDrTiD6rcb1i2sawEE5b11XFiCzxWVcRMvSIOWK7yahq0bd6R1oOFa97m4X+2EYQMXSxCaGNsmzMlb8F/f3Viy31457/iay73ttjiCpLWctJMuPlxgaZ3MAlYF9QBujbdPQELHF4TMv12K3FJyIzU9q+dX1QMK/P+vFYnUfgdnTY57HjkMjETukkoNoNGVU5JhckiZEyCdRnwyicY0LErgmd2wZp8s5N1NJMd+pSp4RmXOthazxs/AskOjMywmSfJvQ1pyiMjJCzvdAxhVhjn2eyL9uJeG1Ct1VIsJkiVd7Zi5/aMnCMSiVjT6gxp+MAZM868E3UnxkjzAw7bSuhFbM9QzqWOpAkk6oMhZI8ZwGA/QY+zX7HbEl2urz0H9CHqsbM/ygrkdJbHmrGsIOVl1j3uGIQWASclrE/dMmbiBy8qenXmwWjISoTJja4woxy+e3U6q19sayOcSyzI6gDiQGg+2ul+EHvoq1O3DjMfH5V7+qAksIP1kaPUD8cmzV/+9mE8M/vQ+FHBRpc+iekIULvDzd4LFf7Tw3AeicBqPabNXbGhOjuxb2gddAoYjXT0BCsv5HIa8dPbGcLgShYa3p1glz6Iqk6L4miONxnRvpzLIPpjMBtYGMP8/S77aQ0Q01x30hTQIlDhu0DD6XjDh6cvsGODeDsvKebMOB3RjkeWT9I9wgqMRXxeUOqKniIcMr5Y4i6yxb5AqOiZcsy1sg9QQ1C9WN8VtbkHhycqsehhw/uX31bijFp/hKCA8wu7lDsPrROX+XgLSPsToANkQM9ZgamNRc9Q0W3p81TgTVxheTu3XMG+BI53KxaqCs4xgzfSGNzhjo2AtD0L6350oxfdgkMiWoxAddI3i6QiXO/qdtyEZX0cjG08lybo6dKqlDVk1sCGzT2tksHoMtOqSDvpu+zQk80CIJfymqwbDoKdJtcOFtz5l5zXNdlTfXhWWyI0NXmVjbwMUDFkRffQSzRmB994XSJlptYaHd/ZdjL9I72uCd8+Dm9qE9LLd1uMknQGftffkG0pODhraGT+4fg4in/MhR6iV1XknF520nh26W7e3Jq8UYEfBQBS723cJBq6vYADztDOSdnUnDi5Hi+U4B+BH0bczVfTsz2CgdSEQuHgAGRgkQighFocx3pA0lS/T9/dO44Q+FUKqklkMllGvjmGriCsIpK3sBRga2HaiuUDpHpjVwdy8DWcJVwpi3J06SVRr1SehYswfRD3zOMCwOZIp5XDTwEdeaIvWWZy6NGiuol95svcSeOv/CAxvousVqGKrc0dBBT2j/C263KFtJup34O6yxldTiW73aKxrDPJS9cv5pso+OOIYHDx/xtM3qqBIRaMzroaWWK7OLiG+QTxXTbTHEcNOvtzwUAckkEMxDkQmO6tDf2Oi6+Zc9jYC9saMg0fPl3h23dh2K0updxtCXHxbRwa/8Nycx/VHNHCmwoQspi7EYOajnLnZNRQbef2G0nlBsBrU0rzBbR1C/NbyYjED5nCS+4jcI5i+Ef/b0ETPG0VZE/w/vnwagnBQvYlNDQgVt8gKGxE7KJ7/KaI16XztLK6NiLcOcN3W5Lc5Cf30V439h1eiYM0ZHi6CDqGLcs2eoGbuGBfNzz41jJdoVsLNPJU5CDh1dZ94a8S3bGSuAU7vjZ0ovO4MNlsrYA3l5lPP3KSbbfehxCyPBsHhjd/p3cDYmGesKLN+iI/9SXcg6iAfyUcOrMzNNbaRzH5EW42JxrHoq4/NlPoQnq6Hf3Ko65J/G/AEIboXdCqeZ7nwLH/DrcVbNAhGfRWBI04JU7yzOQNpzHjcccndaBdo9R6I4SHZU2KdmczMRQKjjR+2E+P/CLOMXMnrYw+E5jhd9s6JYVsd0VgufB9Ln74+9cRHotn6pCKh3rsuffwxz6qEBIo0CQdjxRRpkncb67Gq3G56dSwtWKw71tYkgonkFNJ2plzY+d4v4yKrB0xlvZrlMDSUpeK4HZlmr9U+yhZpy6K+LkH/+AGokrZsJF6NusO5YQAJaNe4Uc+MP+k+ZtuLSYGcP3XuuuLLbC/zXZ+Afyr0RGypu4obRwy/WvdSNzdGHxj2hTy76+ygWRvGkFDfF4Nue5fJoMNj+J5phcDwmYXuKxpTprSdwm0c/LgVoFOLi8SO1T384tS+Db6xyl2HsbXA1EdriCv8Lzg8Sn1dZPLTUZcRRX3cdn4LHFS90IKWKFqKnI4vEb65mZjEhUDM+uIaNmLlfSV3nw6EXJg+CBEx38rIT7F/LqqI39+DEUnQZ6TJtSAo4riH2he/Mf0/mRaIYcqOoZXwzY9NdOwUGs1nKU4VJaBvzCB8EsllS77kRpGkuxfCpvnb28ttTqr5fpKvvii1aLPtdRPjhjHSM/zO6qm4WH7Ivj+gz+SG6XajwA2nAIl+/UVEUtg20mwPkN9VAlz33bkBMwgDyH35ICUXXuAfaHGVEX7ZDNgy8sLeZr5dSTn71L/kKWwyhLSUxXrLsZstbVXT7uGYSXs9hXwf26wrGUlQMTeeIHCwsXYdfRtEdRS1X8mGJU3+BX1A0XRM/kQuNE41uAQklFjjVPkvHdlF9qgyHzzvrC0kAXIxfjLLVNqa5PVkJkctJ7N44HwAlDIR59P2Z15dcBikB4mMZ2If/HnPAN8TfE4HFVPD6+Wh2JN1liggvlITGj8CUaNLz0Y0xNp+o4IOPbrxVl/VYim+bOvvlToAsEmpd5gnc+tBg1oOk6p/Jtpv86ac/DvuUIyL/ArPMW7nckAKF/PYs4h70ojuUNGSacw31TSlBy8J+Opz3JkQyUQGv5QlIbaevtBcrZj4rTzh5VlVyRY15sVlaq/n7o0I183Xu8rDdmX3TK/OmFG+sj/o2IYm0aP3HXK8L7Yr/xsR1Rl3rURa0u34BX/sfKJ8UTlzPVhiohLGmZmVstNV7muIVx4Yes8rJwg7tVHgBgQiLp0KDw5A6TNnC0bKSh+XCO3aJRE6LdCyRJqSt+H4jd0eGGE3569v5gisNdLc1wfbrReN42uZ4KByZBq7gFo9ZRiwkf+pTgZZm0fTP9JODPrB9OW4ldb809AsxpNbsqHGdAJzKQ28TD/8dnAEoko6+Ll72u9Wv8O7GK78twdr5Gl+IdhQhoMYfgdneI/Yh5CDQEVA8C0ceXs+60uoPXabgNCL0mIY5crTfR+6DHfVc8hkoS8vjf5Z6HkTSysme4dzGWsNPJLs5eEOnqi4hMK92sfU2DQyky3EZiIjEMwfUKU1A2cxD/L9/aukbxgTOr0ITVg/APt0WM6sHTkoB6nwG9AWXg9AjVT3NewMz5Vvms6BtAxIP4HhF1MyymG4Z6nb1+TPMceL1w4IDEaHG0kujeTXDJYaUnz0zP11k0w4Lj6iLkHEbKeW4BdDgK4ePgPzvuEBhcM6MoJi47r8yEKNQdrC5KLQZi4ErrV2PJ5VsPd22xBEs5tzQN/d7BKz80sLNzKHm0euikNMYR7TAyBtEwX/QBvaAa7BxDjM6d6Xva9M5KoZzM+OgnpK+k67co0hfnteSE6gLS1X+7p6M372TLWsodhA+x+hYdXSCCtgrWm1wOqvRtJqqteNoCb3+G9WWAHQdkEJ5NHWlvj9t2W9eKfSBaACbaV78J/3q2S6UFDcZemEP3EWgDUygcwUZsyLwxpUstMEumqLDiB3SkUKsMk7jYUi09bxZZ6o9s2k4nYnNQ+fnKQ1n2YyZw0d/d7gan44wIEcnl5HCVCQNBGgV/8c8TWxcT6QEKNnReKrlvvjta72ku3IacvBlEgFntPOCBiYL4dIATQVhNoRHuEY+077tw9AJXMNNgBSCstWG+6JjY3coc5UMdIyZpw84iyObRe0L9TjDgMwyD1z4STZd1zLCnujUEzV1QPLEnnQEa3hmanc08DlybgJFUFfyQ0JL4soycuHubkGxGkIeD2tMLf6H00ZEwoI80L/zjNTN+kc61eCIfjA1Knu7wnnm7MEyp92jbu9DyEgJJYAwHfalbxJiakYZ9L5KYIRliSnknpD0R5v+fs/utLzKWJSZyig0gTknVjvgQJGb4mlOJcH/6E1IpERRqEMCUcz1jJdV1b8JSpoVcF5QhhEzo8Jp0o5g6m+irekCjwH4M74t16Q1lsEfCLu+ki0lWwTZoD2rDekGMcFN+hwa2woIxil5I5xATZWDU38mXWpbuWmHzlPaY1qMC1r2gt8Xp+Evo0I609yMDzf1l678nQWNOhL38RQ9sjGtBw5b6NvHp5+sIbOqBuuN7GzOBeeYuWUb0cW/VuOGiAoAVnzRa+zpM3+vyROqkTGRHmdpJLJf2XyaXtXIMVOEazAwv1hNRdEciEAcHEsUUsEZQwBDpFEb3OlMEn+w8t/Gk8tc4ydBahynHqy5iwYZckCwbaaRcpr6b1TE+3DNZLMKViVUqOwgmUiE/R63hww0TsOCQG325sS2rywcEyvb0E3NgFkgf9tbXSkEE/DtCUxon5vl22nAxvUEpOROS17X83qpvjH74JJPHLfOjP5LdupkuCiI4Pq44Pg7A70sSZ+GPgcmgyjbXKyekmG8NOixMm0ezeAx67YeHqWGRcTD38yylsEybn9N0cROR1xfIAPW5TK+8bu4e/hYg8i3JkEFyIFlU8vPsDi7miKWI798j+j86c6Rbeyj9YszeSMsmkXhhGonwKeMSBuXqJWERHrhRrWNHIydIba1ao6ywmAoP4KVTwiW08vsexMGTRCR19TZQqb4STgOAtZuomQwEActrxoe7zU5/QDGjOL3Vh4ThlHrJVMe8b/Mck+T748R1zgJwlKpK47EuosInPSh9ne7KrbbfFul5kU0AloKnhAVKfx+kAwfCOWZbka9ShRF56hE3SZYVaQKZjVD4X+HV7yOhS0FMsKbZx/H8Gt2147Ur/GUkD1hRi8wxVogExZjgC7+kfTYylkQ4kF6HiVY5WJs0IQ4z2cfznLPCzzD5JdpTMASKqs2c9PyGTRv5VW/qhsZf2DsYsBTb3b3gbBV6Tf078OTt38wm0FN2mphY+mLfT+R9v3vRTZP0V/Z/AcS36n13J9o/tlXkE1BQmurCFMLadSU8fMNqs4GE733TrknscZear+LBxet6IX/ilml0/wstMZgwv/xcDxHCBvKwCG2LswEeotIGlloR1W8IThBo7+hnx29RFndhL/qGibm035lI+yU45KhH0c4J0QdD1DYhL/STDF8RD+ofmjPR4qDXtqfKQI5nstFtY44CkykzYG7scT2ULOVzuZFJFdCFYCN0wzRVVPevkVcv7PnK8CGeJomUEdi+W39M4j6siNCEeBTe7ee3hIqjzp/uABpnx4bgvyBfP795QGFP/v1FeUM2a8o1/cCpoRAW6uz0LhyzKSAjCml1c00DK3uvQSHZaVYL+KaqXRUMp6DX+1knpAPWvTIvv163wRNx9OFpz9V5vgjVl9Lm65zmAuq7R9YN7VJrhBfxO0holeERoTLVWW/yt4UYaeEHE6psTofbA/yNGPmJbb6mpa+P15Jbr8vRIK19U9UlLJUampFLvRJzFjin83E0fND2oXsCdrH3hO0QzftGPVs4yhQSe5Ecck7/M4Dm4FTaSf2RQwScRk2rye57Yl7q6xL+XICSGU08yeSaLk07eJsmGfxS3mTAqC5yzgPdl41w33qxB8RTc1lo1HJzzr/LFkYCprRJ2KaZy3ZrvfnJl31ekykqhioDHVkk/yE3Wu/GRkCfvv7sXV1PZWabO1YXxCZQMIdoflgloNTQd6W2ugTXyELXaTaagZ7O1Vvc5m/3M2SSSb/wL18Ykm2AYadVGlfm7B+s/ASavHd2mwqzYLny1BfvXcugoLjUy6XbckojLTzrIzZ7F8Qua9WacQB0d6Em+r9T40dtLm876mB0c9LepV4ac8IB7w2GVJOGnwWQoPoIyDhb8jcUokCq/cHdEk5pNPVQQweN4I6Mo2ffmw9GzQsVTWysFqsP8MmhcgR5jeeAjYWitnjA1CbWpb3xiLKmZmiYajZ1gPm9pC94uFn/8yfLdUVaq1aOihpm8TQxx4mTN3sokIOzf0/l7rceebTNgFXD4pM1jHr8JoJ83iGUY5+ixdBaq3CKRTO95qklSbzy++XWWGqaHjvCF8r0bZPKOyF4sQxQ1mqhhrGm753qcXouOsfSsU8NzRq7SZky7v7Ju10kTcfLC9wfJ/RD8MLoN/UOiRxUu3oldTCmGJES5KpxEIIDC93dMuxqyYKxkElCfWcJ7b2toIXeTtQDMxPDnYZVCslfb+KPOJPyqlwfsjNfvNdZPLOtsFZYnvUWrFthL7pd+tPRRcWEJhdYQGtEow0GosOXOYU17FlLXbGhb1Qod213h2e6M9JG+BHBgqrRMIcUJe28X0jwXduCI4SI2AJFTlRUwaiI47FKDqufR6rUkfVcKxc3e12+LVojt6IK063lkjV9+THDMTTczUNeX3cNokJUGVGoOJtCt/7qm2vyiFOYAxBMY0qt5KY61QBTyQ4jtdOMzmneLQHrIBrU6FdiK4clzbz+vatHRwXBmp+LubEVifZXIRcVJ+XKXXWQTWwIKTXns/BN1BOsQacpjifPTAmvuwtsNIHY7zoPkKxuJDd1qt2S95/4BSugOOVhAsmsIP5m2XgmzNPRk1OAU01ZO8dQ2XENybgAfql4gGZkyRK7vxfjq3nGk5EgvOVpQv/LtOK/qi9P/p3Y4PsSiHmirOsBmlF5xK8U46HjaVWFVfcgtgu56YWvns1Za5VlsvdF38d2PyYfGaOEhLi/qsu5uxq7Lz18F7HcILuJR6UOVP183UmRn/HdRlnai+y0OWgHKkABJeg7encX/XN+X8EVCD66VLwlJMtb/u7tsU9AbNEHgYMo8xKS9e0oKYiJfdGKJoC+Z+ZqeUw5B0EikZUC4gguYz0+kqZlRdk5OFi3qHHmuw28bhqEDDSflGJ8XV2WqluDM71E+R7MmZLitx5aLOsIYHDZY7r8DgugS95wJKGwYikrrjQrJCJrl1LV1SfaoZzTMevL3MN6i61yQx6juA42dMH6vklbR4DD7D9+mGSn3dwetHwkm5ato5fiAN+rFDie9TxAivlHAtOe5hqaO2A+LxZcsdfIO2aX8zPp2GZVQ0OKs6d3ElHJ0BTG6Wb4U7e/wVrAZ5zr2MBpL6n5CXy2QEn8BMCnsyPhfz6GKlqcuFEnJrlrxN8y3RFfyyQHL+u+rkAit3YvSIe8jumTfi9+RoJMQZLVCyaHXUIPekQYXnNpN2RQAHjVjtrICC/9DZLVDMX1fVXWQnZlH6swGOlnNFiiu7fjjiY18bKt8vyX9kt/Ig1GLGsGMtaMHSMTYGvR7SyE7NXEu99gH9L+Kk5jLAm4lz4UKAp3CoNdOtxj3sGRR51D9xvVsapybo3oCCWS9jaaIQNxp8OGg290WkQQDYDnHQNiIhYeQCanqEZGp57DxK2ODAvynm2xyMwseQ67wjPWgSHd228amSCedxbYUqPuV+Zjo/IizAWajzT4WPbICmpoYcEBy6+B4YuNPpOER3grOaeVciY5dGf99hUB+1DjzvZOEazvWZ63feZR9YrrEFlHKXl58tslevs2Uvm2yd9dCcf9fp7ui0sOyY5n1PyL5SCnmOyUmYttPxofwT5f5NPexZyhVtGV17pP/4LrElA+o5xe0/phm5tWTxwzmQ62u3oxN19bnyDOewobFpinZHTevpUjoLeJdE3V/fV5ixLjSVOrunoML/elswn8BMgSGyAW5yV1GHiDtu9Vs8ntRMw3p/HC1Wu0dh04IVBdBmNTzikfPZybIJyaxiPufrVnJhwG0bJI1TyUi14t2brRrA7jt7aUM18VIxfLm3AZNIQfoGhV7Xol5FYqxa4ujUZauakWvbAVEdzeBHK8f+McumAiJcSkqLd6O7IQBywb0pcNRJrfaO9eZdUH0Jbq1vNtJid5mP+CGv7azTRI8RBJONYkHUdb/EzuOHoz/PmAwsmdff2yilGw6Yx7cBlYJM138PlJTK1QHxKEbctcyeSPJbUPKDprN6xXwLy6tX8nORdRN+XbBXQCbJ/kakaO1naY5HZK8cKqbZvrPshAz0yLnqkbs0bVRZs9khKpBkbu2fh4+k/9chfOcL6WDqSRmO/LXRdwEr1CXnn+5oX3SA2JHDjdRIaXgrqiqmekX0S1Z6FdglbFZvYY4KNNrIXmxkc6QEbodMB/Zc0GmjiUjRU5m4Rir6CAQEPECHTETwvpGfZj9LgJ36I+Fl3xCR8a5NwZzjT6zcEeVzfbtgNh7h30R7PqfKT2ij8RYXpqmEL+JZSZBtbXzOhtY0ZtWI0YHGTxZg0Smy7+bU7FPXb5ylI8kxqznrWrgXjqjmMrEaR4ChPaszUKeS4cmTszjXc0LlWan4Uo+0MEtXxoc/ukcJlbZyEldZd6b6GeUzlw7roCXXgUZxsfQE28LsVWdMjsIhR+3qwt/sCxWwMFxR47H7dr8GEMrtsOewjmr3wSWIAaeIAcSX2nkR2v8pPQ9zddGQ0zlifewHURJDEFyKNEI/76GUZyOYO9jw3xkU5E8jd1zoMuoJ7vLatQ5C892FrWDNPjH/01e+TYBJLOM06Y4u0o5hnSI1XZn0BkP3Ua+0IsmioXBcYR4nzp3i71Rpvp32CCoaMnRP9qy+VlAn553e7N6ErY7rrEpAVUp86ZaUCirW5VFSEYTySiZAProSYcHOQg1hEOeS+57gM/3ovqZsAnvSFNGC5UR0l6RSqWLZ7vd+Mmkdh8vANw3ikzPK7c0EzkMY/sF6qSVmwtQzd7PrcoPiH5Z/HBKKQGxEpz+VHGqUWUaV3s+iDBmZtQpBRH19JRwhJyw4jTh88f5Ye8uYnTSxKRyJg7j7thkZjT4x/kZenIDgoZu9YfXHCJfuansZEoD/pvdEFuP6UIzch2jv7CAfj68b0WHhOnVgpaOMHZjSe1Ed7UTY31K4ktmlpMFyW9odeFyaX7F7TTsGZRqKFO3q9rsjXBwFZFJaI3LV5h0n3vFx46Upt4pFvrSH7PKBsX+7mpo+/mD12dD4628o74Vlfpt0+uhQtlTxD5kdrZXCc1xrw4vpx866HupbM0+3fYz7Iq/mz9d9S3UpUgxmC4dK8M1GjnIar6hsGTg64yeKsFagVZBnE/PYi5G+svISwi+kOMkO0AyOsRm/aK3MYeJ6GjSv1unEZN5dutI+OpmvQv4DvmWr8oI1gSn4ZF6iEU80x0rzSU8/u8njXPIhYek++smTo+Qk4qmxq/MWmKRYwQyYF4u4b3SWmIxziuLH7Mgnp5J7ZYMRWgqv7t1vUZQm4buehdQhvz+a3Ij6VMtUE6Zv6NZQaSkQ36hb3gKiaOQpMBHYyjajaegmH0xd+qrSG+SzuZIbcXCVh7ctTzD1D1tdYwtZ/7oaoPELRPlVVneEG07konnvJqm4WYg/azPWTSWsqU2xepjvyF6P0k+qN5CdgkqEwxs4xDrJRsCUO3LAvL6sANhcnQ8tSv8yr2eUkKRFEZpGDWdYDtwIPTQYgW3OM869htQrx86MuiM4Vbi/tZ1jD/eS9HTzDHFctrj7eISykF+O5TdsuzWvz2BmUJO3ZnVIprUC7Y1m+sH0AOvp8BqfB1c/J4wV6AOD40wMPP97E8OT2cE3nTAIyb46W8KZ32hmOwxH+eWNPnJbLdwS4d8QypQeJCNRzSTdY2ZcICJQFPsFXT6Wq/fLVcMVAUTT+ayeQeRn8BzS//fFOUSUiINlb96NwFVB/VLFF7qED4BqqnsI7sd4gUmx6CeOj2JJQLPLhJCDAnW4+xGVoKFI8Zhtlr2caJKZkQPbETzlE9wRr8kQdd1kk1GtJDhYJ+e4EezMOLQGfIWb7YxDMXp5fuo5e6lgI5w10becMF3RJ+7SREGcyCCBNpbO8NnvoEuXwl5u6MWxzQWw3K4YCy9nXxa6BZMnmtMKRlfHFRv8y88IIVAkcf9h+HJZBS46DOSmHyAEIGxgnig5OTXFdKiBWd7siHC4PFImqlL2x4KL7FnEtnPIwP5iLsqUEz4XturlUrl/7p2KBfidXHQ6luSd8iVUF7dXH7qPUPNzCauZhZKzrZfV8bm7SE6hmuC0HYBDiyiyEJ5Yz65II3Aw6zs4hx0k0o0eaDabEavVYtM4cqlonbyBIPvxOhWb2b+ShacJkcyc1HyTcBdNNBE+EAe/9L+ijzAPsXO04C5bl1QhH2wbbKVDl3V2OOq9UnWNqIXVDNF6kM6rigKaDP2y5YozQ1ZSJ1/TWJJ7bQlhmSmyj1+6j/u2zqTO9Sq/u6rARzjxMinmhjQ3Kz6n3FwiZET4y/0fycfKIU2/pbmr7wRqoeVQG53Y9sd3HUW7kwXev8fXbp+6oWZWUk14Yz251LvnDBtVEEeH6kEkGoVwhUfZ1vk9UrNJvbSvb7NIxQCFTUcDrA3HxssBXNSVLfKuNpdVT211dEVV3knkpVf6ibbPDzSTrM1VzqAY50extfiKRvb0dB8643qXRo8jJ3FYMUD5R/m5NQ/x+1t0wWmxfqsk8c6aXiJEtbLaGrwIatd9tddhdhE8IsA6cutGLMqr7xrLLLbsow0ivYWMDaa0B9jHJVRXLhSNcMkZexsPrRiYIKXCEUnf70DQcFdVDSF6ScrjfButI4KUyR3Vcj6WBefOKEPwfFUiKbsUM9qP3uwjjDELl6gydezfgJ18Acdj8SE0SHge8gh3zvW4ji3vxVTdJP7GvWRRPYfxEU9lvxz0WgAqWIdVVOiIzcQNR+n7/3SAdHtAFQxwRAHbLhZ3hn9XiZSlsB8eum2ZNIJpCtWhKnFgXcdrXC0nWrRCOe/XlI9hmgu9oCyFA3Hvi5DxaXbAKwwrHWtpPJreFYDFNa6b7j6jqwvQHdnMKZCPULcZpSx6tUK024sPwpvT6smbJElh2mOrLfuCJzZnr/y4kZrfsLSkV+r/nYKCIajmNkrt5dPIhfOLen0gKKNrqkxYwy8mXIXvO1ZFvE4Ryaj4gXN6DAcJbKnyhytSlu7/Qf3x+FGIH5F2fAN7MCirH4sydNhQj5d2G3S216Tx6ahy+rAu7pgPDxv/7zLckBAT+tLp7b5ek5RnmdWKJwsGgwYxnfDrJgOGmq9Jyovs8PYw0SBubkh7LTkxJ6aqe6GGFXw8yMcfi1ClTxG5rHKt2ETgnsuT6TaeSb611GagQ72UHa/z8O/JBeH2+GU99REQrDVeVBGJ1ovZEx8nA4y/C914J7j/9zMOjHA5/62EVKjpRhht60ftN2woKdA3fXr3DBBRECIJgSJ2y6A7TC5EQRUJ6Qew6ONE/JFdV/Wici5iLQTSh+uDEe3+JExA3yziPnkXrOgbgME6kEPNqjGWDf9r3h+MNRHxeUR3YKXm0vN+z0+dvWYKg3vZ+8hJjvQsb3WNKKJZO1eGGDTfoB8x5izmk/LOwiLa3KASAOCyST6MdQZAwKiSANVi2fVAQ/lVbfrfAi2OU7vYFCUpbnXZ2i4aDVikG1sVfRBL+5M2RsxvrvnAZrG6kfTsvz38Sp/3GF+bdPIOcoWu/JNVBc3zMWnXCSt4aBmnkA6ZSRNQmpxb7ZqA7NorT0r0OE27rDxqbRThjzP9UM2nV7LYbCH5Pc9mpvcegIx71aRgt7NbniEVc7jYGudSkyCDD1lPilF73Fal9D8B3fMxC+429AZhOSLnX4uae9LEiB7YaQendXySVkTcvk1e+aI4lpxhELe+N5/3bSAjEs/WCmG6vgXGxRPqfAIokY5oIhjg+nulGqYKQWMKt8XHsnhPUlk97a0KhQ2LBA8FigKzlj1NFdrKamnwee1tg0udYvYbDi2ysrohqdLCAIYJGWAuJp4P3nJ4N87ZHOZ0HhCu6Q4UUhDDt9kg+GKw0EEmlT84pwjAf0rHCGoD9qxwLdJLpkrnuoOT/Qg1AUj3dLImGpRDIp8gGft3iMqYXBLuE7eFh+72wnGzAHgX0s2hef1ZLuZyL3U3M/ia0//Dy9BBXibKnnXJvmEVAI63/rEfLr4iFvWiLdp1cpfBJns/Kr4nHsbsY3aaXN9+Qje4fTS7qYZjsBw1jdwRRmEK29zmRDiXeUGRafscYgAMUu1+4HvDSaAzW0a0lFCZidn3hsqTNZd48ozucAaRue6vXiRd61c39kAM98jzpL5S018KPNPqIUcgYgkNCThBLl1HOM4lpnpHUvI4Tb7fQZYyG7BmfAXfVxuDWyyq/ZbXfqzzAVvIpCrrShXjvOYpivoaSLCpJMJNP3yJEq/Y/OESkImOIO6XQh8Rw3m5/fqAB3IW2irJmpqL/p6yfeeMIaky7cT0AUk7fiP+4sJ1l4QgEwjrHwczXzMGK2hyBf6pYF7m7kMegRgysHSk0EIRJ1e5fKFAuQVAerOqV8tWpCvQ366aqYLJJ6jhgW7wdjI6rx8mTsEVxLoEhBRL5FQ17Bm8gbUggEj0Dfb1uaLGnPKNjVCAddMIgxVl+qtpU3Z/RSLn779ukwROi/vsbOHCgq4IZwXviaCSgRxtf7Zq00DsysdBfgRzd7WmxTaEKbM6G9K8QI7AL2doVm3c0N23ipl7kpIp2MP4kX071/a5JP4KsIXbNPGQL+jWkY6T7O93xCzAjs+ljZgBahYahRtjRgdS+L4ryOenVPRUHGSJQ7S5XEjbBt4xEHl+tMOrhVuAcaVejnako07VwFK6YBiuQ/EW7VmQzuaf5hOc8H9cjZfVTdt4yr75rqlCWhb+uwu6Bv/s8yEcOvXaYujTczQlfx/9aGi/W42zdnUrNvjwfEGy3M6XK45Qjjk4MHE5qyAA/VtVQATZFQqxT9yLV3bALE2FiQS+Cq3Is3k7JSGtvp23c97l8ePma6O9nykYBWMmJlga3yU5zS4v5dw8KN7poGWQBdZNm+1q/A/cvBPFHvhEnSMAmmxxGktobqt0d5+CfRMBMALWBe/9gNVtjMR0NuleEnWzTcnltpSlU8wuMFvY9xb5dY60Xd4crBqSxBpkpkD11Gomr5JJaeVZdIHYJ5mZNTHMraKj0JRw18jhmethMHOCp0R62Glwl+7kGtlua3KEsU+nXWpP7oNE/F+HfqpAEb5WcT3oc01glBvGBtBaUgFwv3TQ+UHU/4IKFUQM+dEX1KbyTeY+OllBwmtNyYHmSFW4zkICfzdgYSxvNzVQT4BS9DwIMdDCUQ59oPsoUKo/39+TJeC8TDj8NKTmZnv93mA5txWicEyG/4jQxvzoPEdSsuIumuQ1l0vzUSRkJdVZVfKiQ6ZK6z2SGaZB8GtTa2vyuTOxE6vp7wLbtPnVbuHrS/aQhpqLoab/07IHDgLR/Pde1OHb6sKb6xUDepUA6Ll36LZaFBRNksOQM8tOEXTzRx5Hsr8rYHkYe+uQaZHm4PP7iefDc5NG4egOoOV8y4AMn6Lb9VzduZuZjXEwXQmKmq2isZt8zkEdb+h9p5aClt2M6RICNILh0/RNwpFEwwOPEi1brMvz68m2xb0mxhN3AD1WldtoFtkXfbzd4+MSY/o45HrCTnzDIpqO8VMjKy6rcJcod3yoQQtq2AE25CojxJ1GTfIrytTKHNUeCW7dRYFx/kA1OZO6fKSwXe9oyIV1QsevSLpQP0rgdhOKHbfYU9MA1P4zE578F15fdTS6AQ+2Iby5zVpEJlRRetNo6wGZ55Sd7tjWpQClL0oKqh4q2YgYYo5CSAwxUMxa8jpMl9YDRejbI9rnTnosPfSMAI1/Oo4TXFmpyW6bmji3QqsCFKSuTTmWxl0Llh5eu1hmhR9VTXA+3+xO0Oi5vI3N5yFZOFllkSDJBzlt+W40zBsGB87Bu/man1Vid3+uNkiJawBb6Cx0m2c0RJvo/J8+kBlw0Q80+UaA9aCt/ht0TKbIHaWKS77iafcJpZiiaS3adXx4rq7ef1Gu+rIzqLcVKlnFF/Nu+aiQYqdCmVigHWmhoVbbOBv51Ai1W4Xr50A58hvM9RgT+G41u3g5fgA0wVvxt7itOgSTLrEr2HU26mU7iBCl9MiRYnvVlLclfHv9XZV/xLfWsxKj2CxomYEnzpz5Y4iiljIexRrvOMZ2DVOeSc4xOvCQ2sSQeCiUUd6aFx6UAPshkGMJ0bLwRKVVyASPlnIlucwIFVN900ICP/fA2iTl8lBkWV4WJtBFpBgVJXzr0K74NprUgq86U1r/awoSDc9bY4SUUw3CYRK7RNjyW3jKEGZfe+Xjl43FcNZ3MIpoTpKOUkQ/biQ08SN5FQYC5IgTgy5NogX1hmTmlK3Zjh9plQi/DR0Zn/Up6s87IG1+oP6jPlbf+9ZFOfHth45BqADp74o3+JdtDg/aLLYnOVSqtJC4IT2sa6TGvQWssoovyli+RtUyAkcxdF/7escNb2xAqdSSbspPGLhYQUwpCO46mWYh7Vb4aZWs4H7/N+DIXMHz02ozUW2x6PzbbLfBbYmNGb//2CNMA/6DzAdAUIEyG0VCVtsntSLKIOIO59sfYWkASJGCBj7crOnHsQFhg10XVSQ85Xy2urLhtpPMMDRV4WYF+mFoRiqamEV1tDa/2Qv1nO+relJWz7E9yi+gSLqV7dyf8FgRI/sOjtEhV3B3oK1+vx9gQZbZM/UtgIt0cvWRAYHUJ49/P0PPimGmFlCP1gYX1Xv9XiSNoSqMArh42MFSoy4HxYPtzJMK21NsJ69s4fMLYhCxX94jF5rRokbu572FFpwlmOMnti5AN6lZcSR0SJNRYo4N9mBDohR3w2te0AJ8QvaRW0BP3/LFCMKcNHyFTweTCp456g6fY/UYz4sWKguRfbOxBhG7eAQ21RQ5BWy2PVqTZXzvzOK96PKduweQ3r1nqA0+/WFu4KFvzj9g+nmISx5VPD123JdX8HUWQtaaxFFR0ZNsXiAhHwrDq65JY5mJgmnuSLkHz4ZufPid/Gg5r9RWuj2QRHAiRhynosAZYEzAkeuOUNvKL0DxyVWq12kGKPCV9SbYce5mheih1AlRcdYD1LKsiboTH6wFa+3LcA0sUJ5ZOj4LW91RyR4pyCQTLvaRuTHcV2Ya2+vuFQvODsnWLZ+UPoTQrqtTEB6bYuoT3eoElnAI6qwjQjP8yoU8pMf7GOXNBjVdhhXSjLgGijNvslwh0r4NniGiMQMGGNYTrSRl82KkY604ZWWxRUaeMp6m7fbK+FqfWkIkpMC/BLkyijDcVMJGGsBUnagaXA3CMJ+lfoW8P+TF0rrG8lj5TmzdDrA7jsurV9+vGNzdtwuwHGZuB6KuLZfzPYvnXIoLDQ4IVZ0xRbEcBieKf43QGyVDeQLX5jqFI3fSOXLQgNwD/x64rkcsudTyoo5TKlXLFu/hoicbNiHY+dnkCOD9CHyi8c/zYkjDv7QFWn8vzQO6jrEYtqMo/k9DndGQHZRmeN6M1B+VK/XS2uqxs560cYpLWPZ6knV+nrUn3eo2mXg4reWoU90dzpdZHlu+6jI9qTZLCk/pHZYxEZNiZ1vaUWwiRGG2lRMPGA/WT7bRhn9I6+hZ3lJ2E0w58GPLPYx0nQR5GVpuT/S8GGbx1FN0B4iKpTaZxfFbQnRMt/6oVdYQtepVVE1JLCZOQ8b99Ayu4DHbkfdNT8XkvlN0RbVj36Pn7Zqo092QVEvwJWNWCKsYw/h0vZsJAhv/2m7G6wmguy4uVxcZFD6QhtfhriPRnnHC4OB/CuW8LTN9dKZYnWj2KBK7nsSk2JS45W8dvye9Uvmj2MFJOGZuWzzhNP4QX0UTqo4mBlNMJNqk4eoS5Zk81oKnPxDpV+tEFVkTJfE/C1cmAv665lVjX+alGUmtRGj/FZYR8N5L+bQoAzqm8OD2YJMJcgJlhHYp4heJIq6nh2roia7HmmK0k7KSZUoqWt+J2sRKT74q7I4MvEvlfwm6bxjQmaK5ppH+IA79OMKDfjxKW6cP0Dy3OlPtnb06qQSvojEBHr+pfZr7r7uKSpJage8LP9z5bVqOKSjUb9Rr17Cejuj3aoRtbRcxCq6dSkjPWCNLHptMjOIZslTyGav501HzytxgPPTVPOaukNognBKaN5qBT6AAhxMmXi/+EkOeZyLD2zjsaSAD71NYxJhIhEhIVp+8pEYricEzJ+0F1FniW+Tx+i2dBGaNln6B41mtUr5F6BbSWFrczCN+nuDqlVO0XCMC1BneW7dfBjWx4iqZaAEjGNGJbUOVPwMlUJlRCWNP9WjPeFyFfSS2hIOjCtrCINE5K1m/wnWhlfAD24C/BZ+NqEJ/TcHvxcMwIGca4eo9YEo0iPcIpEWDcca1KzK2U/syzothD0MllyV8LwR/5U94AwRciEl3A6yBNIaMmmdGaez+2PIQsP5eIoHIhMd2V/tl1XMiyyZFtllsPqAV2QEBL6ykqCY2EDokajRo7i3XIrp9r+NAauGnLM6VZjGLdhj0DgljQmk/rxPFamBYunN6dGOApXybVmyt2Pdl/cRQlJUlBklFaFV6m3K5SQwUvfrhD70Vy+voaZ167Q4QtOKBSEzrxytZ8sjgao4FIDEiSWceNgjzeMlkT1nsTsPrb13271kKmqa5QMF8oj/OCGqXV/62bnUl93qzfYG8Hpi87hHOexMQGxK3DjHEhK3kU/ai2rZ0OjkeSuODdtK5wQ1pA0i+JMw4PCjfJeuv4we4Br3QNkzFVDqtK+STtOdUxKhRwyfXLII8dUhAlp0wb0Zn+mHDeSxl13kSYgoi7fDgmfIF93/sK8vWV5yaeTUc4Ju5XKarP8vqKQIFrvqdzdXMKNR+hYQ0AXGHA2A2DrxiNeW77vEAWc3gd9lpGBXiyvSttwiOteuQw9MnGubGvaVvrzV8e5zu4Y6aO8L5AOCjxHCLDJbIsROufGiahIE0IP1P35kE0qrrPerlgiBafBR3xurSNAASaRTqbZOKpPtcDd+8FYgreqVKjvOuRtJqI18mPAJH6+58fPBGamTCjGqGQnRdKHZhasD0oL1M4Z76uMPCBV74SZIxW/qYXFn5d5oktwYwqYb0XRnckVjEbQLgqTkEMwRv3T3k3rN+spDpSWaaN2FwmNVzTJGitueFjxQXv2UbOYC0lAAQ6DAwILjCp3MvPJQyzBJyZooP984BEAkatUwxAJrn64sRHLw4+lDndWcJSCi29vOdHFmIKp056cmOkQErJT6ywTBSxJ/8ek2ym/RWQSGVBDiM/y0aK64Q373JzlP+B6x7vX+xI65bfA/erKP+RkNG0DD6bcioSJT1bW/DFGFcaS8NynPKJ6Q1WQCei4wmvMFhtIYbHVc1r96fI6y3y8LSN3ZEfrvfxb043QhpH6oxPKw3pNYtygU0AAOYXgNzG3Q4OnquWX2wpbfRToiehVZqlYxqjLSA5MFKXyFaVDi/WL1Yn8iJo5Jwg0tw2ENoX8mt7SgJcFLrFqlM+dAIUFfz9w4ajgbqMjLMOvbGNRj+gV2ZUDsx/098nQ7XZ+rKXUU1ce4Rd435rjq/Ps/80Vhr9jTvhx5h+k/1Ydunztvbrpyzy47Kcc862ffWaHrdnXZ6gfO9CoGRmKd7VXdFw0/ZGr93dpY35CdYE7xE0RYvDDwhW+QWHhll23VaM43kCXcHYjlNmCRl55O4j1oZe/zInH3u+8hW2OKSrVMygssjLiJ1Xhu8G45KjSWU1/4HEgYykcAQDdC9ReinhoTuel/q1Pw7y35fk+uMGhs7PrvC8ADYQf0y8ljZusa1f1lYeW2DVVgFM0IzdSyZnlY9iMHJJLjUbX4Zvfu18kTP9BjI5FPe3rVAH0VUEJ9JuYUPiUls37VybG5YTrEe17/43srTLzqV6BlWg2I6TeUz8xfI48/O9aMMfkxMAPeEUdEBQWpeQ5CDuUJcML0IQjHb0PI4UAy1Lgd/sQBcxRXd9ejhcIsD2gMpxLkKi7/JQprnSUBbhzr1HO43NnskO/NKC3Vd2+qaZVt10CyCJHo26uHJB8GRUH81+R6/GRmcXlCQom0G9DTMmPTPR4miDVck2z37EO2oYgS7aLl1CgOcagJpq84R5KL1nluQEvuyOUC+CMzMqLjMjHhKrgzke8Rm7sB0vnr4si00IJJaL8/kyNfZy6YptHUkuqh1ZHFYZusX2vRGqj7EujwmSqjRFITSVG3i71r4JgWVRiUWopv8do5kflv3u2Qj099Y7xX9O7FggO5feNb8r92K2PXqtuCI06+p6kmle7ALLj5VQ/wHIjia8gNrXnENsnXVUNqGfgHt24M8UwLUaNi1Mfol+rABq3H1Cau3nJoCBaQbna4F3cPKotvuA6K3od2NK+d4a7lPWwC9A8oDm+iQldPaevFrA3T8qKucORSkZkYZ7BLx/W2+huNk6b8TfqjORb/Mz7sxfHN7wIT2UCahDbN6Gt+R/NJ4VuwtjFMxlxjFZV8EvM4q0rgMh87korJeQBCNIvhKZYIHAtoI+xy9wD9bk68M16j6QdTWyi9MCfsPEkeH12dC+3U1hzdlOQ5zUwSVqh57f1uPM2vPYzUl+Z01s7/M8KyEp1abEP+HMa3gNCxGjHW3crkf4YWJJ3uxTV66FJvJVNR57hAserWmKOBOt5SeMOKYYjpAJDZwOsbd6Q8+/Efe4hgWivxxhjFTHlxw+HN5qKPxXiikjI48eA0HANwqNP6SXNVR0R4Pngp/sQ/SGd4JKbuhU20MJDmEFXJ9RFR+59NpR5gokY49XxXjE9PCn9M6cPtBHRKbuqAGcn2Y88PWKctVL8BELp0cuG67DUgAjOyEuJJ209A/bM59796vpcuQi5DIfY/TTzoqBG1o7b+QjNM2BnbB7DWBHsiNNA6aU5ZFcLRq0U8YAccJuVAJyIxHI7K+Voom/gKk11zYyZazBZR7zTlqZBdTCQp9qcLGRc770psN8lmIu+JLggweytpqQtsTJ6PFj/KM95sKkm5zqw2SefS9O08/awWyPWd9dlNVk0a7rRkr/JQf9qSFd7bCQ4ZYYqrkaUEr27eHgTmrJngkKoAhUHIILQnccOBjEHbTzgfAUP8qTy597e0ZWI8+6E8B1NB90dNw6AM2OLBW7vxr4YxqhpYp+2w9fiDkp7sbVtfq8YiTKyk1YNzOOF3/oCetKBUOZwRlNRE8Zz3hl/7kyoQgotK00RLENRRDfZkQZMnsIlbeh7zW+iGCeTo9gb47EXrHfXTUNwTgvwPHyg9uSg7Y+fV6MT75WMyeoGay+PVaUUdqUpZ6iKktCTApANGEUWgDOwJ6lSo7Huof8La6YO17YROEJTnjEhcctmB0pZuzaKe4YkpiCUbZPzlHfdnAxiDIDs2QbX0MuJK05wkckHuE25UqGGUbVBy+lLu2ihR6GUJ6hsVFDYRVbXdjxxksyLVpGL2pfrTdpVroBfTPSE5xD00wVU7LRRiSz9+9cG2ffPzfOkux/3FM/QEUN2ZoalPXO2q28/AUrm3B+DslT9qNsUspCKPoXdgCjHwYos4T2pRLJJEmQOvNJQ76X6lzdxgN5oOqvMWAl71PKg3kG0bsohE/lxI5Lk8W6CWauczOf0pcS0Gk0f3JJ+SSIDGs8MAid5S0K7DpGh2l9oQn+lxovdmEw76IYLR0hCzJv7smX/k6MjcL4qQ6ouHxj68MzJyFiqBXB2T/8SLjrcDfWX8UxcPr9Xv4VZtJsDflurkSHYzYqkKKYQBlky4tf6mxjXfdU8mRTs5a2TMBeMetWhsEiBZhFJot2sLEzkaaAxas+8fMjbK0LKP/LVMwGXBHJx52i+AoM+x+QtSYfK38CiHiPj99xDcVN9nj7lecPbiJTbo3ZsNQa7nPbrZc/vz6mpI3aPgNyAklaqA93x2eqE07fUaU8cVLho0DfQOIrrPTElr+xSH3Gb0JlY1jlaWct/sIdEjEgW1Hh154cKIw28wNPQg6VE/zURxFvwbmlvbUwvboyjOkW6/D4krpD7x57P+YLBO+A2iustvLxol0FkJo+Yi7VQmx3+M6cEuWuGhWeYeJ692oebAJ+KSa+657Aw3WhAJhex+YwijoqsRe0P1NpYwuaE56SS+glpkP0HE8dz1T4ElVQo2arPv7EQmXpSbUrDWNR8qK9ShYg4NpL12V3H2jRCPoSSc9z/HzzP4kE1jgB5rbJFAdUm+F3ACdWWrOKpD5j+sDMMvaooAqprTLiVHV8+hRgVqzSTTWvC5/oYAA6GNXk8Zjfjz/r2+kEGjOEkHgbGK9ImTKR3e/nvNmtmMrzuKWG7WRI7g6wlRloVAV/LU0mVRiTZamM89Fen8By3DK5lywKzyS3N0jsKUt3Leopv/qjCOf198HMb7OAxXtH7dcVFJ4l4wg006DQh6pJlItoXofWwhQxPXHpPVsk3PjLHGDVNVw2Jj7dHxsjpd410fRpm1G18YEI9IBxokO2nvfune+IB8OMI28+Nsq0HDahD/WOTDMpXxb6x5EFfUC2nbsOimx591/sv6uqvMl70kroFO6PJa/oPyWKdg1USXOkCkyGVGXx7ikj0A4yN/V+4EqZ8Ffmj7A/8g0S8MlG/GODuoLeZ6JTJdMzFntKnUB22ecQHmfxb871/pFfSYym08TYd6qMh2mhLaVwul7ms1WBUEa9LBHoH/R9mxWmw0xHkMKFybuzT+Z74eeR5W+hle+5nHfZ3RhPKH8TSm+NAV9A4iz8rgSu/cfjRkY6E5nznaPoGu8IodjeWJDas4BcyY3V4CwLrhSYk6kTP6cd3eglYJGjTkO+yeoqFIv+pHCDafaMq2ulJvboJ0U2dVgmHvCQGyv2ayN02fiZMWhnU6BLuGov6GoG6CNkmSX/UsR+GmksXEdiXax2TAJlBGJmKpYqhxJvpRr0kUhkh36EC2jMh3pMVo0uiU1LjXAiBU75WAgIsHfQNQvf1zBMzEhVfEmZr+1C6UGl/P+lyoIIMePWPKt6d4iMHFObEemMpNTNLovueMhIyaxAcY1pTLUWvmIWDcI1E8klRmjvRh7+ZeDsozYTBM4CWpwxhX87a25W3q2Rc4U0j6NgdSVB2smcuSHS/iQIGOIwUO4DGuAJGtHQOugBs2ihKMpecBjKe0VzIwWF5cTyj/5x8g6ocPDQSBCswfeutpw4fQ5OSJfnXk0w9LrOpx4Tz0wIYJuwNf0WPRhgu9cX/6yQnxythng9qAFtkBZ+c9wDxPLXUSzqqgdqhGW3UcUb0jkQSAbKZ10bgFjlhVzNns5xBY8IXEfTmQI0oskxHx22k3kalBhdFjZ5ayAHy+Ab1s2/CDTUvRVtdrq1+qKWJ+9DvwI8Fb7brJ8y3EMyVKXrYqf7Kr74ZdRSXXnhhMzgUHzrxuNAtJA2yJg9GW7FxIvh6kVKt24RNzvjdGkftozhDO0p0YcNFhB00x3a95jxttMFtWUtD5C0t1uo5pKNup/kc+F6kWdeoGrUCs9PHSYiF5Gg4GwqoLV6g1K+OuSfUcu5UREUOynt8hhGe2mdY3TbbvPt0Whd1G+ETDzd2HW4h+d4AUtltSzRadkxIeOckWmw92Fg1xXV61Zw3JzReI2m7n1QxYYiefPLtWJmaCKC+CFBFvlKxyOyLXGDEjv+sBtudqtTqfQPcGCW/UdIXl4OswNb/8gSVOpJqG/6iNLIIPNt42Tjvz4xlNkQhb41w7V0w91hSInStJBf+nsb9l9C1SDl5MPiXyH7mI0CKZcXOhhoLRM3VXpM0Jqb0x56b6y9hhXR91KRhyOmNGw4f3Mmca2BMEFQ0AJeCyi3MDQsnvaTNifTamgqapS8k0gbYhS1qi/UnuLta+TOSVOmW7ek+9EwOipij62oWt9hP9qdgal/Klr0aTeeC3w7Q4CXRIoRpLucsVFH3rX5OMQXjTttoAXgWvsrLK3WrrF3oTXEKIp7qJSldAagVlQhSc1mQ5ZQLW8ewrKkETWSppgsejgmXjPZSCoT6np5Dbqamotd0raG5PkfcvpcdCzw9LAonBBFqAfjV10V6f00dHvhxgkmU+JJBi5Kb5KyYJPW3Qkmm3+81HTDu0AnF+ODnMU8m19vKWNypulNEE9G2xeQeYX6Kh4DQFNFjdi97aKNwG0rGUEyJ6uvjFS3VSf6isoxv8BWYzHhf6x3xf2GSvnMBY7f6CjA0K2p4fE/V08+ye+JWDGyE1q0EG183TO5LYTLDpSptIqqBlgql/VtPQ3QTFbOp8pbhWcRe/8GWBbRwHsoCWwF9TMhXtuLCAUavJf4chEcrEd463D4WtQYiaAfIYHOWlHnMmHz9y9WzCfKseKUDjR7souQmgHnwdL0QcICMMNRuUXxqacifKFbGs5ef1LpSkQ2CoatKLtxvhU9cLLJq30otVxwijAiuHP8xh217t0qPAp9txfZ3lzFYmHBC7tYAFo9IiXsfJbDdyi5HgeWaEgk6N3PWUQc7+mUQuEd1zcbXcrCjURbsh5OEWFEUy5vL2MufDAdO4oveFk6QrzBCP7BLj8JIYGOYlwbYfZJwlZxPbiYWnFAv2UnGwrzNQzMKyT49L62oV6vMcVTf1hNwCzdqCeAAA='


def logo_grupo():
    from pathlib import Path
    raiz = Path(__file__).resolve().parent / 'assets'
    for nome in ('logo_grupo.png', 'logo_grupo.webp', 'logo_grupo.jpg'):
        caminho = raiz / nome
        if caminho.is_file():
            return _arquivo_imagem_uri(caminho)
    url = str(configuracao('LOGO_GRUPO_URL', '') or '')
    return url if url.startswith(('https://', 'http://')) else LOGO_GRUPO_PADRAO


def avatar_html(nome, tamanho='normal'):
    iniciais = ''.join(p[0] for p in nome.split()[:2]) or 'F1'
    fundo = _svg_uri(f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" rx="48" fill="#293b58"/><text x="48" y="59" text-anchor="middle" fill="#f3f6ff" font-family="sans-serif" font-size="30" font-weight="700">{escape(iniciais)}</text></svg>')
    foto = foto_participante(nome)
    imagens = (f'url(&quot;{escape(foto, quote=True)}&quot;), ' if foto else '') + f'url(&quot;{fundo}&quot;)'
    return f'<span class="avatar avatar-{tamanho}" role="img" aria-label="{escape(nome, quote=True)}" style="background-image:{imagens}"></span>'


def calendario_temporada(gabaritos):
    realizados = set() if gabaritos.empty else set(zip(gabaritos['GP'],gabaritos['Tipo']))
    registros = []
    for gp in lista_gps:
        sessoes = sessoes_disponiveis(gp)
        pendentes = [tipo for tipo in sessoes if (gp,tipo) not in realizados]
        registros.append({'GP':gp, 'Status':'Concluído' if not pendentes else ('Parcial' if len(pendentes)<len(sessoes) else 'Não apurado'),
                          'Sessões pendentes':len(pendentes), 'Pontos disponíveis':sum(MAX_PONTOS_SESSAO[t] for t in pendentes),
                          'Pendentes':tuple(pendentes), 'Sprint':gp in sprint_gps})
    return pd.DataFrame(registros)


def _posicoes(totais):
    return totais.rank(method='min',ascending=False).astype(int)


def _contar_acertos(palpites,gabaritos,nomes):
    campos_totais = ['Acertos','Campos avaliados','Poles certas','Especiais certos','Sessões enviadas']
    contadores = {nome:dict.fromkeys(campos_totais,0) for nome in nomes}
    indice = {(r['GP'],r['Tipo']):r for r in gabaritos.to_dict('records')} if not gabaritos.empty else {}
    registros = palpites.drop_duplicates(['Usuario','GP','Tipo'],keep='last').to_dict('records') if not palpites.empty else []
    for p in registros:
        g = indice.get((p['GP'],p['Tipo']))
        if g is None or p['Usuario'] not in contadores:
            continue
        contador = contadores[p['Usuario']]
        contador['Sessões enviadas'] += 1
        for campo in campos_sessao(p['Tipo']):
            real,valor = g.get(campo,''),p.get(campo,'')
            if pd.isna(real) or not str(real).strip():
                continue
            contador['Campos avaliados'] += 1
            if pd.notna(valor) and str(valor).strip()==str(real).strip():
                contador['Acertos'] += 1
                contador['Poles certas'] += int(campo=='Pole')
                contador['Especiais certos'] += int(campo in ('VoltaRapida','PrimeiroAbandono','MaisUltrapassagens'))
    metricas = pd.DataFrame.from_dict(contadores,orient='index',columns=campos_totais)
    metricas['Precisão (%)'] = (100*metricas['Acertos']/metricas['Campos avaliados'].replace(0,float('nan'))).fillna(0)
    return metricas


def _detalhar_sessoes(palpites,gabaritos):
    colunas = ['Usuario','GP','Tipo','Pontos']
    if palpites.empty or gabaritos.empty:
        return pd.DataFrame(columns=colunas)
    indice = {(r['GP'],r['Tipo']):r for r in gabaritos.to_dict('records')}
    registros = []
    for p in palpites.drop_duplicates(['Usuario','GP','Tipo'],keep='last').to_dict('records'):
        g = indice.get((p['GP'],p['Tipo']))
        if g is not None:
            registros.append({'Usuario':p['Usuario'],'GP':p['GP'],'Tipo':p['Tipo'],'Pontos':calcular_pontos_sessao(p,g)})
    return pd.DataFrame(registros,columns=colunas)


@st.cache_data(max_entries=4, ttl=300, show_spinner=False)
def analisar_temporada(palpites,gabaritos):
    # Dados novos alteram a chave do cache imediatamente; não são feitas outras requisições.
    g = gabaritos.drop_duplicates(['GP','Tipo'],keep='last') if not gabaritos.empty else gabaritos
    nomes = list(dict.fromkeys(participantes + (palpites['Usuario'].dropna().tolist() if not palpites.empty else [])))
    calendario = calendario_temporada(g)
    sessoes = _detalhar_sessoes(palpites,g)
    gps_apurados = set(g['GP']) if not g.empty else set()
    ordem = [gp for gp in lista_gps if gp in gps_apurados] + sorted(gps_apurados-set(lista_gps))
    matriz = pd.DataFrame(0,index=ordem,columns=nomes,dtype=float)
    if not sessoes.empty:
        matriz = sessoes.pivot_table(index='GP',columns='Usuario',values='Pontos',aggfunc='sum',fill_value=0).reindex(index=ordem,columns=nomes,fill_value=0).fillna(0)
    totais = matriz.sum()
    completos = calendario.loc[calendario['Status']=='Concluído','GP'].tolist()
    recentes = completos[-3:]
    historico = matriz.reindex(completos,fill_value=0)
    media = historico.mean().fillna(0) if completos else totais*0
    forma = matriz.reindex(recentes,fill_value=0).mean().fillna(0) if recentes else totais*0
    melhor = historico.max().fillna(0) if completos else totais*0
    vitorias = ((historico.eq(historico.max(axis=1),axis=0)) & historico.gt(0)).sum() if completos else totais*0
    anteriores = matriz.iloc[:-1].sum() if len(matriz) else totais*0
    pos = _posicoes(totais)
    acertos = _contar_acertos(palpites,g,nomes)
    tabela = pd.DataFrame({'Usuario':nomes,'Pontos':totais.reindex(nomes).values})
    tabela['Posição'] = tabela['Usuario'].map(pos)
    tabela['Equipe'] = tabela['Usuario'].map(EQUIPE_POR_USUARIO).fillna('Sem Equipe')
    tabela['Distância do líder'] = totais.max()-tabela['Pontos']
    tabela['Média / GP completo'] = tabela['Usuario'].map(media)
    tabela['Últimos 3 / GP'] = tabela['Usuario'].map(forma)
    tabela['Melhor GP'] = tabela['Usuario'].map(melhor)
    tabela['Vitórias em GPs'] = tabela['Usuario'].map(vitorias)
    tabela['Variação na última etapa'] = tabela['Usuario'].map(_posicoes(anteriores))-tabela['Posição'] if len(matriz)>1 else 0
    for campo in acertos.columns:
        tabela[campo] = tabela['Usuario'].map(acertos[campo])
    tabela = tabela.sort_values(['Pontos','Usuario'],ascending=[False,True],kind='stable').reset_index(drop=True)
    pontuacao_apurada = sum(MAX_PONTOS_SESSAO.get(r['Tipo'],0) for r in g.to_dict('records')) if not g.empty else 0
    return {'tabela':tabela, 'matriz':matriz, 'sessoes':sessoes, 'calendario':calendario,
            'gabaritos':g, 'completos':completos, 'recentes':recentes,
            'pontos_restantes':int(calendario['Pontos disponíveis'].sum()), 'maximo_apurado':pontuacao_apurada}


@st.cache_data(max_entries=4, ttl=300, show_spinner=False)
def simular_reta_final(sessoes,gabaritos,calendario,nomes,totais,simulacoes=4000):
    """Bootstrap conjunto por tipo de sessão; empates dividem o crédito de liderança."""
    import numpy as np
    rng = np.random.default_rng(2026)
    finais = np.tile(np.asarray(totais,dtype=float),(simulacoes,1))
    pendencias = [t for valores in calendario['Pendentes'] for t in valores]
    tipos = sorted(set(pendencias))
    for tipo in tipos:
        gps = gabaritos.loc[gabaritos['Tipo']==tipo,'GP'].drop_duplicates().tolist() if not gabaritos.empty else []
        if not gps:
            return None
        registros = sessoes.loc[sessoes['Tipo']==tipo]
        if registros.empty:
            return None
        amostras = registros.pivot_table(index='GP',columns='Usuario',values='Pontos',aggfunc='sum',fill_value=0).reindex(index=gps,columns=nomes,fill_value=0).fillna(0).to_numpy(dtype=float)
        # A mesma sessão sorteada serve para todos: preserva a correlação observada.
        sorteios = rng.integers(0,len(amostras),size=(simulacoes,pendencias.count(tipo)))
        finais += amostras[sorteios].sum(axis=1)
    maximos = finais.max(axis=1,keepdims=True)
    empatados = finais==maximos
    chances = (empatados/empatados.sum(axis=1,keepdims=True)).mean(axis=0)*100
    return pd.DataFrame({'Usuario':nomes,'Liderança simulada (%)':chances,
                         'Projeção mediana':np.median(finais,axis=0),
                         'Faixa inferior (P10)':np.percentile(finais,10,axis=0),
                         'Faixa superior (P90)':np.percentile(finais,90,axis=0)})


def tabela_chances(analise):
    tabela = analise['tabela']
    return simular_reta_final(analise['sessoes'],analise['gabaritos'],analise['calendario'],
                             tabela['Usuario'].tolist(),tabela['Pontos'].tolist())


def situacao_titulo(pontos,pontos_lider,restantes):
    diferenca = pontos_lider-pontos
    if diferenca==0:
        return 'Na liderança'
    if diferenca>restantes:
        return 'Sem alcance matemático'
    if diferenca==restantes:
        return 'Pode alcançar empate'
    return 'Pode alcançar a liderança'


# Os pesos e bônus atuais geram pontuações em múltiplos de cinco.
PASSO_PONTOS = 5


def gp_sugerido_mapa(analise):
    calendario = analise['calendario']
    pendentes = calendario.loc[calendario['Pontos disponíveis']>0,'GP'].tolist()
    if not pendentes:
        return None
    ordem = calendario['GP'].tolist()
    apurados = [ordem.index(gp) for gp in analise['matriz'].index if gp in ordem]
    ultimo = max(apurados,default=-1)
    return next((gp for gp in pendentes if ordem.index(gp)>=ultimo),pendentes[0])


def referencia_pontos_mapa(analise,gp,recente=True):
    """Média das sessões ainda pendentes; ausência entra como zero, sem somar o que já foi apurado."""
    nomes = analise['tabela']['Usuario'].tolist()
    pontos = pd.Series(0.0,index=nomes)
    etapa = analise['calendario'].set_index('GP').loc[gp]
    sem_historico = []
    gabaritos = analise['gabaritos']
    sessoes = analise['sessoes']
    for tipo in etapa['Pendentes']:
        realizados = set(gabaritos.loc[gabaritos['Tipo']==tipo,'GP']) if not gabaritos.empty else set()
        ordem = [g for g in lista_gps if g in realizados]+sorted(realizados-set(lista_gps))
        if recente:
            ordem = ordem[-3:]
        dados = sessoes.loc[sessoes['Tipo']==tipo] if not sessoes.empty else sessoes
        if not ordem or dados.empty:
            sem_historico.append(tipo)
            continue
        matriz = dados.pivot_table(index='GP',columns='Usuario',values='Pontos',aggfunc='sum',fill_value=0)
        media = matriz.reindex(index=ordem,columns=nomes,fill_value=0).fillna(0).mean()
        pontos += media.clip(0,MAX_PONTOS_SESSAO[tipo])
    teto = int(etapa['Pontos disponíveis'])
    return pontos.clip(0,teto), tuple(sem_historico)


def _limiar_pontos(total_rival,pontos_atuais,estrito=False):
    from math import ceil,floor
    distancia = float(total_rival)-float(pontos_atuais)
    passos = floor(distancia/PASSO_PONTOS)+1 if estrito else ceil(distancia/PASSO_PONTOS)
    return max(0,int(passos*PASSO_PONTOS))


def _situacao_duelo(diferenca_atual,diferenca_final):
    if diferenca_final==0:
        return 'Empata'
    if diferenca_final>0:
        return 'Ultrapassa' if diferenca_atual<0 else 'Desempata a seu favor' if diferenca_atual==0 else 'Continua à frente'
    return 'É ultrapassado' if diferenca_atual>0 else 'Desempata contra você' if diferenca_atual==0 else 'Continua atrás'


def calcular_mapa_ultrapassagens(tabela,usuario,pontos_gp,teto_gp):
    """Classificação hipotética sem modificar a tabela ou persistir qualquer pontuação."""
    from math import isfinite
    if tabela['Usuario'].duplicated().any() or usuario not in tabela['Usuario'].values:
        raise ValueError('Participante inválido ou duplicado no cenário.')
    if not isfinite(float(teto_gp)) or teto_gp<0:
        raise ValueError('Teto inválido para o GP.')
    mapa = tabela[['Usuario','Pontos']].copy()
    adicoes = [float(pontos_gp.get(nome,0)) for nome in mapa['Usuario']]
    if any(not isfinite(v) or v<0 or v>teto_gp for v in adicoes):
        raise ValueError('A pontuação deve ficar entre zero e o teto das sessões pendentes.')
    if not mapa['Pontos'].map(lambda v:isfinite(float(v))).all():
        raise ValueError('Os pontos atuais precisam ser válidos.')
    mapa['Pontos no GP'] = adicoes
    mapa['Total no cenário'] = mapa['Pontos']+mapa['Pontos no GP']
    mapa['Posição atual'] = mapa['Pontos'].rank(method='min',ascending=False).astype(int)
    mapa['Posição no cenário'] = mapa['Total no cenário'].rank(method='min',ascending=False).astype(int)
    mapa['Variação'] = mapa['Posição atual']-mapa['Posição no cenário']
    voce = mapa.loc[mapa['Usuario']==usuario].iloc[0]
    mapa['Diferença para você'] = mapa['Total no cenário']-voce['Total no cenário']
    mapa['Duelo'] = [_situacao_duelo(voce['Pontos']-r['Pontos'],voce['Total no cenário']-r['Total no cenário'])
                      if r['Usuario']!=usuario else 'Você' for r in mapa.to_dict('records')]
    mapa['Para alcançar (pts no GP)'] = mapa['Total no cenário'].map(lambda total:_limiar_pontos(total,voce['Pontos']))
    mapa['Para passar (pts no GP)'] = mapa['Total no cenário'].map(lambda total:_limiar_pontos(total,voce['Pontos'],estrito=True))
    mapa.loc[mapa['Usuario']==usuario,['Para alcançar (pts no GP)','Para passar (pts no GP)']] = float('nan')
    mapa['Ultrapassagem ao alcance'] = mapa['Para passar (pts no GP)']<=teto_gp
    return mapa.sort_values(['Total no cenário','Usuario'],ascending=[False,True],kind='stable').reset_index(drop=True)


def metas_mapa_ultrapassagens(mapa,usuario,teto):
    voce = mapa.loc[mapa['Usuario']==usuario].iloc[0]
    rivais = mapa.loc[mapa['Usuario']!=usuario]
    if rivais.empty:
        return []
    alvos = rivais.loc[rivais['Total no cenário']>=voce['Total no cenário']].sort_values(['Total no cenário','Usuario'])
    proximo = alvos.iloc[0] if not alvos.empty else rivais.sort_values('Total no cenário',ascending=False).iloc[0]
    ordenados = rivais.sort_values(['Total no cenário','Usuario'],ascending=[False,True])
    podio = ordenados.iloc[2] if len(ordenados)>=3 else None
    lider = ordenados.iloc[0]
    missoes = []
    for titulo,alvo in [('Próximo rival' if not alvos.empty else 'Defender a ponta',proximo),
                        ('Missão pódio',podio),('Missão liderança',lider)]:
        alcance = _limiar_pontos(alvo['Total no cenário'],voce['Pontos']) if alvo is not None else 0
        passar = _limiar_pontos(alvo['Total no cenário'],voce['Pontos'],True) if alvo is not None else 0
        missoes.append({'Título':titulo,'Rival':alvo['Usuario'] if alvo is not None else '',
                        'Para alcançar':alcance,'Para passar':passar,'Ao alcance':passar<=teto})
    return missoes


def manual_pontuacao():
    st.markdown('### 🏁 Manual do palpiteiro')
    st.caption('Pontos por acerto exato · mesmas regras do seu bolão')
    with st.expander('⏱️ Pole position',expanded=True):
        st.markdown('**Classificação principal: 100 pontos**\n\n**Qualy Sprint: 100 pontos**')
    with st.expander('🏎️ Corrida principal · posição por posição'):
        st.table(pd.DataFrame({'Posição':[f'{i}º' for i in range(1,11)],'Pontos':list(PONTOS_PRINCIPAL.values())[:10]}).set_index('Posição'))
    with st.expander('⚡ Apostas especiais'):
        st.markdown('**Melhor volta:** 75 pontos\n\n**Primeiro abandono:** 200 pontos\n\n**Mais ultrapassagens:** 75 pontos')
        st.caption('Especiais válidos para a corrida principal. “Nenhum / Outro” segue a opção do gabarito.')
    with st.expander('🎯 Bônus por sequência exata'):
        st.markdown('**Top 3 na ordem:** +300 pontos\n\n**Top 5 na ordem:** +450 pontos\n\n**Top 10 na ordem:** +600 pontos')
        st.caption('Os bônus não se somam: vale somente o maior. Pela regra atual, os dez campos do palpite e do gabarito precisam estar preenchidos para avaliar o bônus.')
    with st.expander('🚀 Corrida Sprint'):
        st.table(pd.DataFrame({'Posição':[f'{i}º' for i in range(1,9)],'Pontos':list(PONTOS_SPRINT.values())}).set_index('Posição'))
        st.caption('Sem especiais e sem bônus de sequência na Sprint.')
    with st.expander('🏆 Quanto vale um fim de semana?'):
        st.markdown(f'**Corrida principal perfeita:** {numero_br(MAX_PONTOS_SESSAO["Corrida Principal"])} pontos\n\n**GP comum com pole:** 1.770 pontos\n\n**GP com Sprint e duas poles:** 2.230 pontos')
        st.caption('Conta somente o último palpite por participante, GP e sessão. A pontuação entra após o gabarito ser homologado.')



CSS = '''
<style>
:root {color-scheme:dark; --red:#ff463e; --muted:#a4adbd; --line:#283143;}
.stApp {background:#0a101c; color:#edf2fa;}
header[data-testid="stHeader"] {background:rgba(10,16,28,.9);}
.block-container {max-width:1280px; padding-top:2rem; padding-bottom:3rem;}
h1,h2,h3 {letter-spacing:-.035em; color:#f4f7fd!important;}
p,label {color:inherit;}
[data-testid="stCaptionContainer"] {color:#a4adbd;}
[data-testid="stSidebar"] {background:#101827; border-right:1px solid var(--line);}
.brand {display:flex; align-items:center; gap:12px; margin:0 0 24px;}
.brand-mark {background:#ff463e; border-radius:10px 3px 10px 3px; padding:6px 12px; font-weight:950; font-size:24px; color:white; font-style:italic;}
.brand-name {font-size:14px; font-weight:800; letter-spacing:.13em;}
.brand-name small {display:block; font-size:10px; color:#9aa6bd; letter-spacing:.2em; margin-top:3px;}
.hero {position:relative; overflow:hidden; border:1px solid #303b51; border-radius:24px; background:linear-gradient(110deg,#18253c,#101a2d); margin:18px 0 24px;}
.hero video {position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:.65; filter:brightness(1.15);}
.hero-body {position:relative; padding:38px 42px; background:linear-gradient(90deg,rgba(12,21,38,.72),rgba(12,21,38,.06));}
.eyebrow {font-size:11px; font-weight:800; letter-spacing:.2em; color:#ff776e; text-transform:uppercase; margin-bottom:12px;}
.hero h1 {font-size:clamp(2rem,4.6vw,3.7rem); font-weight:900; margin:0; padding:0; line-height:1.08; max-width:700px;}
.hero p {color:#c0cadb; margin:16px 0 22px; max-width:570px; font-size:15px;}
.pill {display:inline-block; font-size:11px; letter-spacing:.08em; border:1px solid #4d5668; background:#172339; border-radius:999px; padding:6px 12px; margin-right:6px; color:#e4eaf5;}
.section-kicker {color:#7c90b1; font-size:11px; letter-spacing:.18em; text-transform:uppercase; margin:24px 0 8px; font-weight:800;}
[data-testid="stMetric"] {background:linear-gradient(140deg,#182235,#121b2c); border:1px solid var(--line); border-radius:16px; padding:17px 20px;}
[data-testid="stMetricLabel"] {color:#b7c2d4; font-size:12px;}
[data-testid="stMetricValue"] {font-size:29px; font-weight:800; color:#fff;}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#2b3548!important; border-radius:16px!important;}
div[data-baseweb="select"]>div, [data-testid="stTextInput"] input {background:#111c2d!important; color:#f2f5fb!important; border-color:#344157!important; border-radius:10px!important;}
[data-baseweb="popover"] {color-scheme:dark;}
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {border-radius:10px; min-height:44px; font-weight:700; transition:transform .15s,box-shadow .15s;}
.stButton>button:hover, .stFormSubmitButton>button:hover {transform:translateY(-1px); box-shadow:0 6px 20px #0004; border-color:#ff6860;}
button[kind="primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {background:#ff463e; border:1px solid #ff463e; color:#fff;}
[data-testid="stRadio"]>div[role="radiogroup"] {gap:8px; padding:8px; background:#121c2d; border:1px solid var(--line); border-radius:14px; flex-wrap:wrap;}
[data-testid="stRadio"] label[data-baseweb="radio"] {padding:9px 14px; border-radius:9px; margin:0; background:#182438; cursor:pointer;}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {background:#ff463e; color:#fff;}
.stTabs [data-baseweb="tab-list"] {gap:8px; background:#121c2d; padding:8px; border-radius:12px; overflow-x:auto;}
.stTabs [data-baseweb="tab"] {border-radius:8px; padding:10px 16px; color:#b7c2d4;}
.stTabs [aria-selected="true"] {background:#263650; color:#fff;}
.podium {padding:20px; background:linear-gradient(145deg,#1e2c43,#121b2b); border:1px solid #36465e; border-radius:16px; min-height:150px; margin-bottom:16px;}
.podium .rank {color:#ffad61; font-size:12px; font-weight:800; letter-spacing:.13em;}
.podium h3 {font-size:19px; margin:10px 0 4px;}
.podium .score {font-size:27px; font-weight:900; color:#fff;}
.podium .score small {font-size:12px; color:#a4adbd; font-weight:500;}
.footer {text-align:center; color:#7c8aa2; font-size:11px; letter-spacing:.06em; margin-top:42px; padding-top:20px; border-top:1px solid #243047;}
@media(max-width:640px) {.block-container {padding:1.2rem 1rem 2rem;} .hero-body {padding:28px 23px;} .hero h1 {font-size:2rem;} [data-testid="stRadio"] label[data-baseweb="radio"] {padding:7px 9px;} }
@media(prefers-reduced-motion:reduce) {*,*::before,*::after {transition:none!important; animation:none!important;} .hero video {display:none;}}
</style>
'''


def estilo_paddock():
    bandeira,carro,trofeu = arte_f1('bandeira'),arte_f1('carro'),arte_f1('trofeu')
    return '''<style>
/* Central pública do Mundial de F1 */
.f1-leader {border:1px solid #384a64; border-top:3px solid #e7bd73; border-radius:18px; background:radial-gradient(ellipse at top right,#294361,#121d2d 75%); padding:23px; margin:14px 0 23px; min-height:305px;}
.f1-leader .eyebrow {font-size:10px;} .f1-leader h3 {font-size:20px; padding:0; margin:6px 0;}
.f1-leader p {font-size:12px; color:#a8bad5; margin:4px 0 16px;}
.f1-leader>strong {display:block; font-size:32px; font-weight:850; color:#f4f7fc;}
.f1-leader>strong small {font-size:11px; font-weight:400; color:#a9bcd5;}
.f1-leader>span:last-child {display:block; color:#95b8ca; font-size:11px; margin-top:9px;}
.f1-table-wrap {width:100%; overflow-x:auto; border:1px solid #34435b; border-radius:15px; margin:15px 0; background:#111c2d;}
.f1-table {border-collapse:collapse; width:100%; min-width:690px; font-size:12px; color:#c9d8ef;}
.f1-table th {background:#1b2b43; text-align:left; color:#9eb8db; font-size:10px; font-weight:700; letter-spacing:.04em; padding:15px 13px; white-space:nowrap;}
.f1-table td {padding:12px 13px; border-top:1px solid #2a384f; vertical-align:middle;}
.f1-table tbody tr:hover {background:#20324c;}
.f1-driver-name {display:flex; align-items:center; gap:11px; min-width:190px;}
.f1-driver-name strong {display:block; color:#f0f5fe; font-size:13px;}
.f1-driver-name small {display:block; color:#91a9ca; font-size:10px; margin-top:4px;}
.f1-pos {color:#e5bd7a; font-size:17px; font-weight:850;}
.f1-points {font-size:17px; font-weight:850; color:#fff; font-variant-numeric:tabular-nums;}
.f1-team-dot {display:inline-block; height:9px; width:9px; border-radius:50%; margin-right:7px;}
.f1-constructor-list {background:#132034; border:1px solid #334763; border-radius:16px; overflow:hidden; margin:18px 0;}
.f1-constructor {display:flex; align-items:center; gap:16px; padding:20px; border-bottom:1px solid #2c4059;}
.f1-constructor:last-child {border-bottom:0;} .f1-team-symbol {font-size:32px; width:40px; text-align:center;}
.f1-constructor-name {flex:1;} .f1-constructor-name strong {display:block; font-size:15px;}
.f1-constructor-name small {display:block; font-size:10px; color:#91adce; margin-top:5px;}
.f1-team-bar {width:23%; height:7px; border-radius:6px; background:#23334a; overflow:hidden;}
.f1-team-bar>span {display:block; height:100%; border-radius:6px;}
.f1-constructor>b {min-width:75px; text-align:right; font-size:23px;} .f1-constructor>b small {font-size:10px; font-weight:400; color:#9cb0ce;}
@media(max-width:640px) {.f1-leader {min-height:285px;} .f1-table {font-size:11px;} .f1-constructor {padding:15px 11px; gap:10px;} .f1-team-bar {display:none;} .f1-team-symbol {width:27px; font-size:25px;} .f1-constructor-name strong {font-size:13px;} .f1-constructor>b {font-size:19px; min-width:60px;} }
/* Programação do próximo fim de semana, em Brasília */
.race-weekend {display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.45fr); gap:30px; padding:28px; margin:18px 0 28px; border:1px solid #533840; border-radius:20px; background:radial-gradient(ellipse at top left,#5a181f55,transparent 60%),linear-gradient(130deg,#201521,#111c2e);}
.race-top {display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:19px;}
.race-badge {display:inline-block; padding:6px 11px; border-radius:99px; background:#ff463e; color:white; font-size:10px; font-weight:850; letter-spacing:.07em;}
.race-round {color:#b1a7b8; font-size:11px;} .race-weekend h2 {font-size:27px; padding:0; margin:0; display:block; line-height:1.25;}
.race-country {display:inline-block; vertical-align:middle; margin-right:10px; color:#ffce82; border:1px solid #785248; border-radius:7px; background:#3a292b; font-size:12px; font-weight:850; padding:6px;}
.race-circuit {font-size:14px; color:#b5b8cc; margin:10px 0 17px;}
.race-location {color:#d1c5d0; font-size:12px; line-height:1.9;}
.race-clock-label {font-size:9px; font-weight:800; letter-spacing:.15em; color:#c3a4ad; margin:23px 0 7px;}
.race-countdown {display:flex; gap:23px; margin:4px 0 10px;}
.race-countdown strong {display:block; font-size:31px; line-height:1.15; color:#ff7566; font-weight:850; font-variant-numeric:tabular-nums;}
.race-countdown span {display:block; font-size:9px; color:#acabbf; letter-spacing:.1em; margin-top:5px;}
.race-small {font-size:9px; color:#a59eaf; margin-top:10px; line-height:1.6;}
.race-program {min-width:0; border:1px solid #3c3749; border-radius:14px; background:#0b1321c9; padding:18px 20px;}
.race-program-title {font-size:10px; color:#a5b3ce; font-weight:700; letter-spacing:.09em; display:flex; justify-content:space-between; gap:10px; margin-bottom:15px;}
.race-program-title>span {color:#8198b8; white-space:nowrap;}
.race-row {display:flex; gap:12px; align-items:center; padding:11px 0; border-bottom:1px solid #293348; color:#d4def0; font-size:12px;}
.race-session-name {flex:1; min-width:0;} .race-session-name>span {margin-right:7px;}
.race-day {color:#8ca3c3; width:25px; text-align:right; font-size:10px;}
.race-row time {font-size:11px; white-space:nowrap; color:#a8bbd5; font-variant-numeric:tabular-nums;}
.race-row time b {font-size:14px; margin-left:7px; color:#edf4ff;}
.race-main .race-session-name,.race-main time b {color:#ff8175; font-weight:800;}
.race-next {background:linear-gradient(90deg,#1a303e66,transparent); border-radius:7px;}
.race-past {opacity:.6;}
.race-upnext {display:inline-block; margin-left:7px; padding:2px 5px; border-radius:4px; color:#8ce0c9; background:#18373c; font-size:8px; white-space:nowrap;}
.race-next-session {color:#a8d7d8; font-size:10px; margin:16px 0 12px; line-height:1.6;}
.race-source {display:flex; gap:7px; flex-wrap:wrap; flex-direction:column; padding-top:10px; border-top:1px solid #2a3448; font-size:9px; color:#899bb7; line-height:1.6;}
.race-source a,.race-empty a {color:#95c8fb; text-decoration:none;}
.race-started {color:#ffb78a; font-size:14px; font-weight:700; margin:10px 0;}
.race-empty {padding:22px; border:1px solid #334a67; background:#152238; border-radius:14px; margin:20px 0; color:#bbcee6;}
.race-empty p {font-size:12px; margin:12px 0;}
@media(max-width:700px) {.race-weekend {grid-template-columns:1fr; gap:22px; padding:22px 18px;} .race-weekend h2 {font-size:25px;} .race-program {padding:16px 12px;} .race-row {gap:7px; font-size:11px;} .race-row time {font-size:10px;} .race-row time b {font-size:13px; margin-left:4px;} .race-session-name>span {margin-right:3px;} .race-program-title {font-size:9px; letter-spacing:.03em;} .race-upnext {font-size:7px; margin-left:4px;} .race-countdown strong {font-size:29px;} }
/* Laboratório de ultrapassagens */
.editorial-favorito {border-top:3px solid #e9b665; background:linear-gradient(135deg,#3b2d22,#121b2c);}
.editorial-gasolina {border-top:3px solid #59d6bc; background:linear-gradient(135deg,#163735,#111d2d);}
.editorial-azarao {border-top:3px solid #ae92ff; background:linear-gradient(135deg,#302545,#141c2c);}
.editorial-ritmo {border-top:3px solid #ff6b61;}
.editorial-pole {border-top:3px solid #7fb4ff;}
.editorial-especiais {border-top:3px solid #f7a963;}
.mapa-summary {display:flex; align-items:center; gap:14px; border:1px solid #3c6e6b; background:linear-gradient(100deg,#153333,#172438); border-radius:16px; padding:18px 22px; margin:20px 0;}
.mapa-summary.perde {border-color:#bd7576; background:linear-gradient(100deg,#3e2430,#172438);}
.mapa-summary.perde>b {color:#ff9b98;} .mapa-summary.neutro {border-color:#4b6080; background:linear-gradient(100deg,#1c2c43,#172438);}
.mapa-summary.neutro>b {color:#c4d9f4;}
.mapa-summary>div {flex:1;} .mapa-summary strong {display:block; font-size:17px;} .mapa-summary span {display:block; margin-top:5px; color:#b8d0d5; font-size:12px;}
.mapa-summary>b {font-size:26px; color:#78e4c5; white-space:nowrap;}
.mapa-grid {border:1px solid #35455d; background:#101a2a; border-radius:16px; overflow:hidden; margin:12px 0;}
.mapa-lane {display:flex; align-items:center; gap:12px; min-height:86px; padding:13px 18px; border-bottom:1px solid #2a374b; border-left:4px solid transparent;}
.mapa-lane:last-child {border-bottom:0;} .mapa-lane.voce {background:#123137; border-left-color:#69dfc0;}
.mapa-lane.ganha {background:#102b282e; border-left-color:#5ed3ab;}
.mapa-lane.perde {background:#45242d40; border-left-color:#ff807f;}
.mapa-lane.empata {background:#4d3b2140; border-left-color:#edbd70;}
.lane-pos {font-size:19px; font-weight:850; color:#c5d3e8; width:30px; flex-shrink:0;}
.lane-name {flex:1; min-width:140px;} .lane-name strong {display:block; font-size:13px;} .lane-name small {display:block; font-size:10px; color:#9fb3d0; margin-top:5px;}
.lane-track {position:relative; width:27%; height:33px; background:repeating-linear-gradient(90deg,#354154 0 15px,transparent 15px 22px) center/100% 1px no-repeat; border-top:1px solid #25344a; border-bottom:1px solid #25344a;}
.lane-track>span {position:absolute; left:0; top:12px; height:8px; background:#487097; opacity:.5; border-radius:9px;}
.lane-track>img {position:absolute; width:30px; height:33px; top:0; transform:rotate(90deg); object-fit:contain; opacity:.6;}
.voce .lane-track>span {background:#64e9c2; opacity:.85;} .voce .lane-track>img {opacity:1;}
.lane-total {width:80px; text-align:right; font-size:20px; font-weight:800; font-variant-numeric:tabular-nums;}
.lane-total small {display:block; font-size:10px; color:#adc0d8; font-weight:400; margin-top:4px;}
.mapa-mission {padding:22px; border:1px solid #3b526b; border-radius:16px; background:linear-gradient(135deg,#1c3043,#121d2d); min-height:290px; margin:12px 0;}
.mapa-mission.ganha {border-top:3px solid #65d9b5;} .mapa-mission.perde {border-top:3px solid #f18f89;}
.mapa-mission .tag {font-size:10px; letter-spacing:.12em; color:#95cbd9; text-transform:uppercase; font-weight:800;}
.mapa-mission h3 {font-size:16px; margin:0; padding:0;}
.mission-number {font-size:31px; font-weight:850; color:#8de6c6; margin:12px 0;}
.mapa-mission.perde .mission-number {color:#ffa29b;} .mission-number small {font-size:10px; font-weight:400; color:#afc3de;}
.mapa-mission p {font-size:12px; line-height:1.7; color:#afc2dc; margin:9px 0;}
.mission-progress {height:5px; background:#2a3c52; border-radius:6px; margin:14px 0 5px; overflow:hidden;}
.mission-progress>span {display:block; height:100%; border-radius:6px; background:#68ddba;}
.mapa-mission.perde .mission-progress>span {background:#eb9692;}
.mission-badge {display:inline-block; border-radius:6px; background:#243b4a; padding:5px 8px; color:#c7dded; font-size:10px; margin-top:6px;}
.mapa-duelo {display:flex; align-items:center; justify-content:space-between; gap:16px; padding:23px; border-radius:16px; border:1px solid #475a73; background:#18273a; margin:15px 0;}
.mapa-duelo>div {flex:1; text-align:center;} .mapa-duelo strong {display:block; font-size:17px;} .mapa-duelo span {display:block; margin-top:10px; color:#c0cee1; font-size:13px;}
.mapa-duelo.ganha {border-color:#55b398; background:linear-gradient(120deg,#17382f,#19283a);}
.mapa-duelo.perde {border-color:#c77b78; background:linear-gradient(120deg,#3a242d,#19283a);}
.mapa-duelo.empata {border-color:#d3ac6d;}
@media(max-width:640px) {.mapa-lane {gap:8px; padding:12px 8px; border-left-width:3px;} .lane-pos {width:23px; font-size:16px;} .lane-name {min-width:0;} .lane-name strong {font-size:11px;} .lane-track {display:none;} .lane-total {font-size:16px; width:62px;} .mapa-lane .avatar {width:32px; height:32px;} .mapa-summary {padding:15px; flex-wrap:wrap;} .mapa-summary>b {font-size:22px;} .mapa-summary span {font-size:11px;} .mapa-duelo {gap:9px; padding:16px 12px;} .mapa-duelo strong {font-size:12px;} .mapa-duelo span {font-size:11px;} .mapa-mission {min-height:250px;} }
.hero {border-color:#354461; box-shadow:0 18px 45px #0002;}
.hero-body {padding-right:22%;}
.hero-art {position:absolute; width:250px; right:20px; top:10px; height:92%; object-fit:contain; opacity:.8; transform:rotate(18deg); pointer-events:none;}
.hero-logo {position:absolute; width:15.5%; max-width:175px; right:22px; top:50%; transform:translateY(-50%); object-fit:contain; border-radius:12px; box-shadow:0 12px 30px #0006;}
.brand-logo {width:64px; height:58px; object-fit:contain; border-radius:12px;}
.group-watermark {position:absolute; right:24px; bottom:16px; width:80px; max-height:70px; object-fit:contain; opacity:.8;}
[data-testid="stMetric"] {position:relative; overflow:hidden; min-height:112px; padding-right:72px;}
[data-testid="stMetric"]::after {content:""; position:absolute; right:-4px; top:10px; width:95px; height:95px; background:url("''' + carro + '''") center/contain no-repeat; opacity:.2; pointer-events:none;}
[data-testid="stHorizontalBlock"]>div:nth-child(1) [data-testid="stMetric"]::after {background-image:url("''' + bandeira + '''");}
[data-testid="stHorizontalBlock"]>div:nth-child(3) [data-testid="stMetric"]::after {background-image:url("''' + trofeu + '''");}
[data-testid="stMetricValue"] {position:relative; z-index:1; font-variant-numeric:tabular-nums;}
[data-testid="stRadio"] label[data-baseweb="radio"]::before {content:""; display:inline-block; width:22px; height:25px; background:url("''' + bandeira + '''") center/cover no-repeat; flex-shrink:0; margin-right:6px;}
[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(2)::before {background-image:url("''' + carro + '''");}
[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(3)::before {background-image:url("''' + trofeu + '''");}
.avatar {display:inline-block; width:48px; height:48px; border-radius:50%; background-color:#293b58; background-size:cover; background-position:center 28%; flex-shrink:0; border:2px solid #566982; box-shadow:0 4px 14px #0004;}
.avatar-large {width:86px; height:86px; margin:18px 0 5px; border:3px solid #e6b564;}
.avatar-mini {width:40px; height:40px;}
.podium {position:relative; min-height:310px; padding:24px; border-radius:18px; background:radial-gradient(ellipse at top right,#273c5c 0,transparent 65%),linear-gradient(145deg,#182438,#101827);}
.podium-1 {border-color:#bb914d; background:radial-gradient(ellipse at top right,#74532b66 0,transparent 70%),linear-gradient(145deg,#192437,#101827);}
.podium-top {display:flex; justify-content:space-between; gap:10px; align-items:center;}
.movement {color:#9ac9be; font-size:12px; background:#1a2a39; padding:4px 7px; border-radius:7px;}
.podium .team-name {color:#9caec9; font-size:12px; min-height:32px;}
.podium .score {margin-top:16px; font-size:32px;}
.podium .gap {font-size:12px; color:#c3cedf; margin-top:8px;}
.season-strip {display:flex; flex-wrap:wrap; gap:10px 22px; border:1px solid #30405a; background:#101c2e; border-radius:12px; padding:13px 17px; margin:18px 0 25px; font-size:12px; color:#bdcce1;}
.editorial {position:relative; overflow:hidden; border:1px solid #30405a; border-radius:16px; padding:20px; background:linear-gradient(135deg,#18263a,#101a2a); min-height:206px; margin-bottom:16px;}
.editorial .tag {color:#ffb672; font-size:10px; font-weight:850; letter-spacing:.13em; text-transform:uppercase; padding-right:25px;}
.editorial-person {display:flex; align-items:center; gap:10px; margin:17px 0 12px; position:relative; z-index:1;}
.editorial h3 {font-size:17px; margin:0; padding:0; line-height:1.3;}
.editorial p {font-size:12px; line-height:1.7; color:#b5c4da; position:relative; z-index:1; margin:0;}
.editorial-art {position:absolute; width:130px; right:-30px; top:-17px; opacity:.12; pointer-events:none;}
.ranking-list {background:#111c2c; border:1px solid #2f3d53; border-radius:16px; overflow:hidden; margin-bottom:20px;}
.ranking-row {display:flex; align-items:center; gap:14px; padding:15px 20px; border-bottom:1px solid #263449; transition:background .15s;}
.ranking-row:last-child {border-bottom:0;}
.ranking-row:hover {background:#1b2b42;}
.row-pos {font-size:18px; font-weight:850; color:#f0b96e; width:30px; flex-shrink:0;}
.row-name {min-width:0; flex:1;}
.row-name strong {display:block; font-size:14px;}
.row-name small {display:block; color:#92a6c4; font-size:11px; margin-top:4px;}
.row-pace {width:18%; background:#233149; height:6px; border-radius:8px; overflow:hidden;}
.row-pace span {display:block; height:100%; background:linear-gradient(90deg,#ff453e,#ff9a62); border-radius:8px;}
.row-points {width:80px; text-align:right; font-size:19px; font-weight:800; font-variant-numeric:tabular-nums;}
.row-points small {display:block; font-size:10px; font-weight:400; color:#9bacc5;}
.profile {display:flex; align-items:center; gap:22px; padding:15px 22px; background:#152238; border:1px solid #344765; border-radius:18px; margin:18px 0;}
.profile .avatar {margin:0;}
.profile h2 {padding:0; margin:0; font-size:26px;}
.profile p {color:#9fb1ce; margin:8px 0 0; font-size:12px;}
@media(max-width:640px) {.hero-body {padding-right:23px;} .hero-art {opacity:.13; right:-20px; width:210px;} .hero-logo {position:relative; display:block; width:37.5%; max-width:130px; top:auto; right:auto; transform:none; margin:-6px auto 24px;} .hero-body h1,.hero-body p {position:relative; z-index:1;} .podium {min-height:280px;} .ranking-row {padding:12px 10px; gap:9px;} .row-pace {display:none;} .row-name strong {font-size:12px;} .row-name small {font-size:10px;} .row-points {font-size:16px; width:65px;} .profile {gap:14px; padding:15px;} .profile h2 {font-size:21px;} [data-testid="stMetric"] {padding-right:52px;} [data-testid="stMetric"]::after {width:75px; opacity:.13;} }
</style>'''


def cabecalho():
    st.markdown(CSS + estilo_paddock(), unsafe_allow_html=True)
    logo = logo_grupo()
    marca = f'<img class="brand-logo" src="{escape(logo, quote=True)}" alt="Logo do grupo"/>' if logo else '<div class="brand-mark">F1</div>'
    st.markdown(f'<div class="brand">{marca}<div class="brand-name">BOLÃO 2026<small>SEU PALPITE. SUA DISPUTA.</small></div></div>', unsafe_allow_html=True)
    return st.radio('Navegação', ['Enviar Palpite','Meus Palpites','Classificações','Administrador','Fórmula 1'],
                    horizontal=True, label_visibility='collapsed', key='navegacao')


def hero(titulo, descricao, etiqueta='TEMPORADA 2026'):
    imagem = logo_grupo()
    classe_imagem = 'hero-logo'
    texto_imagem = 'Palpites F1 — desde 2014'
    st.markdown(f'''<div class="hero"><video autoplay loop muted playsinline aria-hidden="true"><source src="{URL_VIDEO_GITHUB}" type="video/mp4"></video>
    <div class="hero-body"><div class="eyebrow">{escape(etiqueta)}</div><h1>{escape(titulo)}</h1>
    <p>{escape(descricao)}</p><span class="pill">20 PARTICIPANTES</span><span class="pill">10 EQUIPES</span><span class="pill">UMA DISPUTA</span></div><img class="{classe_imagem}" src="{escape(imagem, quote=True)}" alt="{texto_imagem}"/></div>''', unsafe_allow_html=True)


def secao(numero, titulo):
    st.markdown(f'<div class="section-kicker">{escape(numero)}</div>', unsafe_allow_html=True)
    st.subheader(titulo)


def sessoes_disponiveis(gp):
    return SESSOES if gp in sprint_gps else SESSOES[:2]


def ultimo_registro(df, gp, tipo, usuario=None):
    if df.empty:
        return {}
    dados = {'GP':gp, 'Tipo':tipo}
    if usuario is not None:
        dados['Usuario'] = usuario
    filtrado = df.loc[_mascara_registro(df,dados)]
    return filtrado.iloc[-1].to_dict() if not filtrado.empty else {}


def seletor_etapa(prefixo, gps):
    c1,c2 = st.columns(2)
    with c1:
        gp = st.selectbox('Grande Prêmio', gps, key=f'{prefixo}_gp')
    with c2:
        tipo = st.selectbox('Sessão', sessoes_disponiveis(gp), key=f'{prefixo}_tipo')
    return gp,tipo


def opcoes_pilotos(valor_atual='', historico=False):
    # Um Ocon já salvo continua visível no seu próprio campo, sem substituição silenciosa.
    atual = str(valor_atual).strip() if pd.notna(valor_atual) else ''
    return [nome for nome in pilotos if historico or nome not in PILOTOS_INATIVOS or nome==atual]


def rotulo_piloto(nome):
    if nome in PILOTOS_INATIVOS:
        return nome + ' · histórico / palpite anterior'
    equipe = EQUIPES_PILOTOS.get(nome)
    return nome + ' · ' + equipe if equipe else nome


def selecionar_piloto(campo,existente,contexto):
    atual = existente.get(campo,'')
    opcoes = opcoes_pilotos(atual,historico=not contexto.startswith('envio_'))
    valor = str(atual).strip() if pd.notna(atual) else ''
    return st.selectbox(ROTULOS[campo],opcoes,index=opcoes.index(valor) if valor in opcoes else 0,
                        key=f'{contexto}_{campo}',format_func=rotulo_piloto)


def formulario_pilotos(tipo, existente, contexto, fotos=False):
    valores = dict.fromkeys(CAMPOS_PALPITE,'')
    campos = campos_sessao(tipo)
    posicoes = [c for c in campos if c.startswith('P') and c[1:].isdigit()]
    extras = [c for c in campos if c not in posicoes]
    if posicoes:
        colunas = st.columns(2)
        metade = (len(posicoes)+1)//2
        for i,campo in enumerate(posicoes):
            with colunas[i//metade]:
                valores[campo] = selecionar_piloto(campo,existente,contexto)
                if fotos:
                    exibir_foto_piloto(valores[campo])
    if extras:
        if posicoes:
            st.markdown('#### Apostas extras')
        for coluna,campo in zip(st.columns(len(extras)),extras):
            with coluna:
                valores[campo] = selecionar_piloto(campo,existente,contexto)
                if fotos:
                    exibir_foto_piloto(valores[campo])
    return valores


def _email_valido(usuario, informado):
    esperado = emails_autorizados.get(usuario,'').strip().lower()
    return bool(esperado) and hmac.compare_digest(informado.strip().lower().encode(), esperado.encode())


def _dados_palpite(usuario,gp,tipo,valores,admin=False):
    return {'Data_Envio':datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M:%S') + (' (Admin)' if admin else ''),
            'GP':gp,'Tipo':tipo,'Usuario':usuario,'Equipe':EQUIPE_POR_USUARIO.get(usuario,'Sem Equipe'), **valores}


# Agenda oficial da reta final de 2026, conferida em 03/11/2026 em Formula1.com.
# Os instantes são UTC; a interface sempre converte para America/Sao_Paulo.
# Snapshot local para não acrescentar requisições de rede ao navegar no aplicativo.
AGENDA_F1_CONFERIDA_EM = '04/11/2026'
AGENDA_F1_2026 = [
    {'GP':'Brasil','Titulo':'GP do Brasil','Circuito':'Interlagos · São Paulo','Pais':'Brasil','Codigo':'BR','Rodada':20,
     'Fonte':'https://www.formula1.com/en/racing/2026/brazil',
     'Sessoes':(('Treino Livre 1','2026-11-06T15:30:00+00:00'),
                ('Treino Livre 2','2026-11-06T19:00:00+00:00'),
                ('Treino Livre 3','2026-11-07T14:30:00+00:00'),
                ('Classificação','2026-11-07T18:00:00+00:00'),
                ('Corrida','2026-11-08T17:00:00+00:00'))},
    {'GP':'Las Vegas','Titulo':'GP de Las Vegas','Circuito':'Las Vegas Strip Circuit','Pais':'Estados Unidos','Codigo':'US','Rodada':21,
     'Fonte':'https://www.formula1.com/en/racing/2026/las-vegas',
     'Sessoes':(('Treino Livre 1','2026-11-20T00:30:00+00:00'),
                ('Treino Livre 2','2026-11-20T04:00:00+00:00'),
                ('Treino Livre 3','2026-11-21T00:30:00+00:00'),
                ('Classificação','2026-11-21T04:00:00+00:00'),
                ('Corrida','2026-11-22T04:00:00+00:00'))},
    {'GP':'Catar','Titulo':'GP do Catar','Circuito':'Lusail International Circuit','Pais':'Catar','Codigo':'QA','Rodada':22,
     'Fonte':'https://www.formula1.com/en/racing/2026/qatar',
     'Sessoes':(('Treino Livre 1','2026-11-27T13:30:00+00:00'),
                ('Treino Livre 2','2026-11-27T17:00:00+00:00'),
                ('Treino Livre 3','2026-11-28T14:30:00+00:00'),
                ('Classificação','2026-11-28T18:00:00+00:00'),
                ('Corrida','2026-11-29T16:00:00+00:00'))},
    {'GP':'Abu Dhabi','Titulo':'GP de Abu Dhabi','Circuito':'Yas Marina Circuit','Pais':'Emirados Árabes Unidos','Codigo':'AE','Rodada':23,
     'Fonte':'https://www.formula1.com/en/racing/2026/united-arab-emirates',
     'Sessoes':(('Treino Livre 1','2026-12-04T09:30:00+00:00'),
                ('Treino Livre 2','2026-12-04T13:00:00+00:00'),
                ('Treino Livre 3','2026-12-05T10:30:00+00:00'),
                ('Classificação','2026-12-05T14:00:00+00:00'),
                ('Corrida','2026-12-06T13:00:00+00:00'))},
]


def agora_brasilia(agora=None):
    instante = agora if agora is not None else datetime.now(fuso_br)
    return fuso_br.localize(instante) if instante.tzinfo is None else instante.astimezone(fuso_br)


def horarios_brasilia(evento):
    horarios = [{'Sessao':nome,'Inicio':datetime.fromisoformat(inicio).astimezone(fuso_br)} for nome,inicio in evento['Sessoes']]
    return sorted(horarios,key=lambda s:s['Inicio'])


def proxima_corrida_agenda(agora=None,agenda=None,gabaritos=None):
    hoje = agora_brasilia(agora).date()
    eventos = AGENDA_F1_2026 if agenda is None else agenda
    ordenados = sorted(eventos,key=lambda e:next(s['Inicio'] for s in horarios_brasilia(e) if s['Sessao']=='Corrida'))
    homologados = set()
    if gabaritos is not None and {'GP','Tipo'}.issubset(gabaritos.columns):
        homologados = set(gabaritos.loc[gabaritos['Tipo'].eq('Corrida Principal'),'GP'])
    # A homologação encerra o GP imediatamente; sem ela, mantém a programação do dia.
    return next((e for e in ordenados if e['GP'] not in homologados and next(s['Inicio'] for s in horarios_brasilia(e) if s['Sessao']=='Corrida').date()>=hoje),None)


def contagem_largada(evento,agora=None):
    largada = next(s['Inicio'] for s in horarios_brasilia(evento) if s['Sessao']=='Corrida')
    segundos = int((largada-agora_brasilia(agora)).total_seconds())
    dias,resto = divmod(max(0,segundos),86400)
    horas,resto = divmod(resto,3600)
    minutos = resto//60
    return {'Dias':dias,'Horas':horas,'Minutos':minutos,'Iniciada':segundos<=0}


def html_cartao_horarios(agora=None,gabaritos=None):
    instante = agora_brasilia(agora)
    evento = proxima_corrida_agenda(instante,gabaritos=gabaritos)
    if evento is None:
        return '<div class="race-empty"><strong>🏁 Agenda de horários de 2026 concluída</strong><p>Os horários das quatro últimas etapas foram exibidos aqui. Consulte o calendário oficial para as próximas temporadas.</p><a href="https://www.formula1.com/en/racing/2026" target="_blank" rel="noopener noreferrer">Calendário oficial da F1 ↗</a></div>'
    sessoes = horarios_brasilia(evento)
    largada = next(s['Inicio'] for s in sessoes if s['Sessao']=='Corrida')
    proxima = next((s for s in sessoes if s['Inicio']>instante),None)
    dias_semana = ('seg','ter','qua','qui','sex','sáb','dom')
    meses = ('janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro')
    linhas = []
    for sessao in sessoes:
        nome,inicio = sessao['Sessao'],sessao['Inicio']
        eh_proxima = proxima is not None and sessao is proxima
        classe = 'race-row race-main' if nome=='Corrida' else 'race-row'
        classe += ' race-next' if eh_proxima else ' race-past' if inicio<=instante else ''
        icone = '🏁' if nome=='Corrida' else '⏱' if nome=='Classificação' else '🔧'
        marcador = '<small class="race-upnext">A seguir</small>' if eh_proxima else ''
        linhas.append(f'<div class="{classe}"><span class="race-session-name"><span aria-hidden="true">{icone}</span> {escape(nome)}{marcador}</span><span class="race-day">{dias_semana[inicio.weekday()]}</span><time datetime="{inicio.isoformat()}">{inicio:%d/%m} <b>{inicio:%H:%M}</b></time></div>')
    contagem = contagem_largada(evento,instante)
    if contagem['Iniciada']:
        relogio = '<div class="race-started">🏁 Horário previsto da largada já alcançado</div>'
        etiqueta = 'PROGRAMAÇÃO DO DIA'
    else:
        relogio = '<div class="race-countdown">'+''.join(f'<div><strong>{contagem[chave]:02d}</strong><span>{rotulo}</span></div>' for chave,rotulo in [('Dias','DIAS'),('Horas','HORAS'),('Minutos','MINUTOS')])+'</div>'
        etiqueta = 'PRÓXIMA CORRIDA'
    proxima_linha = f'Próxima sessão: {proxima["Sessao"]} · {proxima["Inicio"]:%d/%m às %H:%M}' if proxima else 'Consulte a F1 para acompanhar a realização das sessões.'
    data_corrida = f'{largada.day:02d} de {meses[largada.month-1]} de {largada.year}'
    return f'''<section class="race-weekend" aria-label="Programação da próxima corrida">
<div class="race-info"><div class="race-top"><span class="race-badge">{etiqueta}</span><span class="race-round">Rodada {evento['Rodada']}</span></div>
<h2><span class="race-country">{escape(evento['Codigo'])}</span>{escape(evento['Titulo'])}</h2><p class="race-circuit">{escape(evento['Circuito'])}</p>
<div class="race-location">📅 Corrida: {escape(data_corrida)}<br/>📍 {escape(evento['Pais'])}</div>
<div class="race-clock-label">PARA A LARGADA PREVISTA</div>{relogio}<div class="race-small">Contagem calculada ao abrir ou interagir com a página.</div></div>
<div class="race-program"><div class="race-program-title">HORÁRIOS DAS SESSÕES · BRASÍLIA <span>UTC−3</span></div>{''.join(linhas)}
<div class="race-next-session">{escape(proxima_linha)}</div><div class="race-source"><a href="{escape(evento['Fonte'],quote=True)}" target="_blank" rel="noopener noreferrer">Fonte: Formula1.com ↗</a><span>Conferido em {AGENDA_F1_CONFERIDA_EM} · sujeito a alterações</span></div></div></section>'''


def cartao_horarios_inicio(gabaritos=None):
    st.markdown(html_cartao_horarios(gabaritos=gabaritos),unsafe_allow_html=True)


# O relógio do servidor e o calendário cadastrado definem o fechamento dos palpites.
ANTECEDENCIA_PALPITE = timedelta(minutes=1)
NOMES_HORARIO_PALPITE = {
    'Classificação Principal (Pole)':('Classificação',),
    'Corrida Principal':('Corrida',),
    'Qualy Sprint (Pole)':('Classificação Sprint','Qualificação Sprint','Sprint Qualifying','Qualy Sprint'),
    'Corrida Sprint':('Sprint','Corrida Sprint'),
}


class PalpiteBloqueadoError(ValueError):
    pass


def estado_prazo_palpite(gp,tipo,gabaritos,agora=None,agenda=None):
    estado = {'aberto':False,'inicio':None,'limite':None,'motivo':''}
    if tipo not in sessoes_disponiveis(gp):
        estado['motivo']='Esta sessão não está cadastrada para o GP.';return estado
    if not gabaritos.empty:
        if not {'GP','Tipo'}.issubset(gabaritos.columns):
            estado['motivo']='Não foi possível validar a situação dos gabaritos.';return estado
        tipos = set(gabaritos.loc[gabaritos['GP']==gp,'Tipo'])
        if 'Corrida Principal' in tipos:
            estado['motivo']='Este GP já tem a corrida principal homologada e não recebe novos palpites.';return estado
        if tipo in tipos:
            estado['motivo']='Esta sessão já foi homologada e não recebe novos palpites.';return estado
    eventos = AGENDA_F1_2026 if agenda is None else agenda
    try:
        evento = [e for e in eventos if e['GP']==gp]
        if len(evento)!=1:
            raise ValueError('Agenda ausente ou duplicada.')
        candidatos = [inicio for nome,inicio in evento[0]['Sessoes'] if nome in NOMES_HORARIO_PALPITE.get(tipo,())]
        if len(candidatos)!=1:
            raise ValueError('Sessão sem um horário único.')
        inicio = datetime.fromisoformat(candidatos[0])
        if inicio.tzinfo is None:
            raise ValueError('Horário sem fuso.')
        inicio = inicio.astimezone(fuso_br)
    except (KeyError,TypeError,ValueError,AttributeError):
        estado['motivo']='Horário da sessão não cadastrado ou inválido. O envio fica bloqueado até a organização conferir a agenda.';return estado
    limite = inicio-ANTECEDENCIA_PALPITE
    estado.update(inicio=inicio,limite=limite)
    if agora_brasilia(agora)>=limite:
        estado['motivo']=f'Palpites encerrados em {limite:%d/%m/%Y às %H:%M:%S} (Brasília), um minuto antes desta sessão.'
        return estado
    estado['aberto']=True
    estado['motivo']=f'Envios e alterações permitidos até antes de {limite:%d/%m/%Y às %H:%M:%S} (Brasília).'
    return estado


def gps_disponiveis_palpite(gabaritos,agora=None,agenda=None):
    instante = agora_brasilia(agora)
    eventos = AGENDA_F1_2026 if agenda is None else agenda
    # Sem horário validado não há abertura por omissão; etapas antigas não voltam após um reset.
    return [gp for gp in lista_gps if any(estado_prazo_palpite(gp,tipo,gabaritos,instante,eventos)['aberto'] for tipo in sessoes_disponiveis(gp))]


def _validar_gravacao_palpite(dados):
    # Leitura fresca: uma página antiga não ignora uma homologação feita por outro administrador.
    gabaritos,_ = _ler_dados_remotos(ARQUIVO_GABARITOS)
    estado = estado_prazo_palpite(dados['GP'],dados['Tipo'],gabaritos)
    if not estado['aberto']:
        _ler_dados_cache.clear()
        raise PalpiteBloqueadoError(estado['motivo'])


def seletor_etapa_palpite(gps,gabaritos):
    if st.session_state.get('envio_gp') not in gps:
        st.session_state.pop('envio_gp',None)
    c1,c2 = st.columns(2)
    with c1:
        gp = st.selectbox('Grande Prêmio',gps,key='envio_gp')
    tipos = sessoes_disponiveis(gp)
    if st.session_state.get('envio_tipo') not in tipos:
        st.session_state.pop('envio_tipo',None)
    abertas = [t for t in tipos if estado_prazo_palpite(gp,t,gabaritos)['aberto']]
    if 'envio_tipo' not in st.session_state:
        st.session_state['envio_tipo'] = abertas[0] if abertas else tipos[0]
    # Índice padrão estável: o Streamlit antigo não recria o seletor quando o relógio muda.
    with c2:
        tipo = st.selectbox('Sessão',tipos,key='envio_tipo')
    return gp,tipo


def quadro_prazos_palpite(gp,gabaritos):
    linhas = []
    agora = agora_brasilia()
    for tipo in sessoes_disponiveis(gp):
        estado = estado_prazo_palpite(gp,tipo,gabaritos,agora)
        linhas.append({'Sessão':tipo,
                       'Início (Brasília)':estado['inicio'].strftime('%d/%m %H:%M') if estado['inicio'] else '—',
                       'Fechamento (Brasília)':estado['limite'].strftime('%d/%m %H:%M:%S') if estado['limite'] else '—',
                       'Situação':'🟢 Aberta' if estado['aberto'] else '🔒 Encerrada'})
    st.dataframe(pd.DataFrame(linhas),use_container_width=True,hide_index=True)
    st.caption(f'🔒 Tranca de segurança: o prazo é validado pelo servidor ao gravar, inclusive em uma página aberta antes do fechamento. Horário de referência: {agora:%d/%m/%Y %H:%M:%S} (Brasília). Agenda conferida em {AGENDA_F1_CONFERIDA_EM}.')


def ativar_relogio_prazos():
    # Reutiliza o pequeno relógio incorporado; sem serviço externo ou dependência nova.
    import streamlit.components.v1 as componentes
    componente = componentes.declare_component('bolao_f1_prazo_palpites',path=_pasta_relogio_f1())
    chave = 'relogio_prazos_palpites'
    componente(interval=60000,counter=st.session_state.get(chave,0),default=0,key=chave)


def tela_enviar():
    hero('O próximo pódio começa aqui.', 'Escolha sua etapa, monte o grid e coloque seu conhecimento de Fórmula 1 na disputa.')
    gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
    cartao_horarios_inicio(gabaritos)
    usuario = st.selectbox('Quem vai acelerar?', ['']+participantes, key='usuario_enviar')
    if not usuario:
        st.info('Selecione seu nome para preparar o próximo palpite.')
        return
    st.caption(EQUIPE_POR_USUARIO.get(usuario,'Sem Equipe'))
    gps = gps_disponiveis_palpite(gabaritos)
    if not gps:
        st.info('Nenhuma sessão com prazo aberto na agenda cadastrada. Acompanhe Meus Palpites e a classificação.')
        return
    secao('01 / ETAPA','Escolha sua disputa')
    gp,tipo = seletor_etapa_palpite(gps,gabaritos)
    quadro_prazos_palpite(gp,gabaritos)
    try:
        ativar_relogio_prazos()
    except (OSError,RuntimeError):
        st.caption('Os prazos continuam sendo conferidos ao gravar o palpite.')
    estado = estado_prazo_palpite(gp,tipo,gabaritos)
    if not estado['aberto']:
        st.warning('🔒 '+estado['motivo'])
        st.info('Escolha outra sessão ou etapa com prazo aberto. Seus palpites anteriores continuam em Meus Palpites.')
        return
    st.info('🔒 '+estado['motivo'])
    df,_ = ler_dados(ARQUIVO_DADOS)
    existente = ultimo_registro(df,gp,tipo,usuario)
    if existente:
        st.info('Seu palpite atual foi carregado. Ao gravar, suas novas escolhas substituem as anteriores.')
    secao('02 / GRID',f'GP de {gp} · {tipo}')
    fotos = getattr(st, 'toggle', st.checkbox)('Mostrar fotos dos pilotos', value=False)
    # Contexto inclui participante, GP e sessão: trocar a seleção nunca carrega o grid de outra pessoa.
    contexto = f'envio_{usuario}_{gp}_{tipo}'
    with st.container(**({'border': True} if 'border' in inspect.signature(st.container).parameters else {})):
        valores = formulario_pilotos(tipo,existente,contexto,fotos)
    preenchidos = sum(bool(valores[c]) for c in campos_sessao(tipo))
    total = len(campos_sessao(tipo))
    st.progress(preenchidos/total if total else 0, text=f'{preenchidos} de {total} escolhas preenchidas')
    secao('03 / CONFIRMAÇÃO','Pronto para entrar na pista?')
    with st.form(f'confirmar_{contexto}'):
        email = st.text_input('Confirme seu e-mail cadastrado', type='password')
        enviar = st.form_submit_button('Gravar meu palpite  →', type='primary', use_container_width=True)
    if enviar:
        if not _email_valido(usuario,email):
            st.error('E-mail não confere com o cadastrado para este participante.')
            return
        dados = _dados_palpite(usuario,gp,tipo,valores)
        with st.spinner('Registrando seu palpite…'):
            salvo = guardar_dados(dados,ARQUIVO_DADOS)
        if salvo:
            st.success(f'Palpite de {usuario} para o GP de {gp} gravado com sucesso!')
            st.toast('Você está na disputa!',icon='🏁')
            if not enviar_recibo_email(dados,email.strip()):
                st.warning('Seu palpite está salvo. Não foi possível confirmar o envio do recibo por e-mail. Consulte Meus Palpites; não é necessário enviar o palpite novamente.')
            else:
                st.caption('Modo de testes: comprovante encaminhado somente ao administrador.' if BLOQUEAR_EMAILS_PALPITEIROS else 'Comprovante encaminhado ao serviço de e-mail. Confira também a pasta de spam.')


def tela_meus_palpites():
    hero('Seu histórico na pista.', 'Consulte as escolhas que você registrou ao longo do campeonato.', 'ÁREA DO PARTICIPANTE')
    with st.form('consulta'):
        usuario = st.selectbox('Participante',['']+participantes)
        email = st.text_input('E-mail cadastrado',type='password')
        buscar = st.form_submit_button('Consultar meus palpites',type='primary')
    if not buscar:
        return
    if not _email_valido(usuario,email):
        st.error('Acesso negado: e-mail incorreto.')
        return
    df,_ = ler_dados(ARQUIVO_DADOS)
    if df.empty:
        st.info('Banco de dados vazio.')
        return
    meus = df.loc[df['Usuario']==usuario].drop_duplicates(['GP','Tipo'],keep='last')
    if meus.empty:
        st.info('Você ainda não enviou palpites.')
        return
    c1,c2 = st.columns(2)
    c1.metric('Palpites registrados',len(meus))
    c2.metric('Etapas disputadas',meus['GP'].nunique())
    st.dataframe(meus.drop(columns=['Usuario','Equipe']),use_container_width=True,hide_index=True)


def ranking(df,chave):
    return df.groupby(chave)['Pontos'].sum().reset_index().sort_values('Pontos',ascending=False)


def cartao_editorial(titulo,nome,descricao,tipo='capacete'):
    foto = avatar_html(nome,'mini') if nome else ''
    classe = {'Favorito da simulação':'favorito','Referência a ser batida':'favorito','Cabeça de gasolina':'gasolina','Azarão na pista':'azarao','Pé embaixo':'ritmo','Mestre da pole':'pole','Faro para os especiais':'especiais'}.get(titulo,'padrao')
    st.markdown(f'<div class="editorial editorial-{classe}"><img class="editorial-art" src="{arte_f1(tipo)}" alt=""/><div class="tag">{escape(titulo)}</div><div class="editorial-person">{foto}<h3>{escape(nome or "Aguardando resultados")}</h3></div><p>{escape(descricao)}</p></div>',unsafe_allow_html=True)


def quadro_destaques(analise,chances):
    tabela = analise['tabela']
    secao('PADDOCK / QUEM ESTÁ FAZENDO A DIFERENÇA','Os nomes da disputa')
    c1,c2,c3 = st.columns(3)
    lider = tabela.iloc[0]
    with c1:
        if chances is not None:
            maior = chances.sort_values(['Liderança simulada (%)','Usuario'],ascending=[False,True]).iloc[0]
            qtd_empates = int((chances['Liderança simulada (%)']==maior['Liderança simulada (%)']).sum())
            detalhe = f'{numero_br(maior["Liderança simulada (%)"],1)}% de liderança no modelo histórico.'
            if qtd_empates>1:
                detalhe += f' Empatado com outros {qtd_empates-1} no modelo.'
            cartao_editorial('Favorito da simulação',maior['Usuario'],detalhe,'trofeu')
        else:
            cartao_editorial('Referência a ser batida',lider['Usuario'],f'{numero_br(lider["Pontos"])} pontos no campeonato. As chances aguardam histórico suficiente.','trofeu')
    quantidade = len(analise['gabaritos'])
    elegiveis = tabela.loc[(tabela['Sessões enviadas']>=max(1,(quantidade+1)//2)) & (tabela['Campos avaliados']>0)]
    with c2:
        if not elegiveis.empty:
            cabeca = elegiveis.sort_values(['Precisão (%)','Acertos'],ascending=False).iloc[0]
            cartao_editorial('Cabeça de gasolina',cabeca['Usuario'],f'{numero_br(cabeca["Precisão (%)"],1)}% de acertos: {int(cabeca["Acertos"])} em {int(cabeca["Campos avaliados"])} campos. Participação em pelo menos metade das sessões apuradas.')
        else:
            cartao_editorial('Cabeça de gasolina','', 'O destaque de precisão aparece quando há campos oficiais válidos para comparar.')
    fora_podio = tabela.loc[(tabela['Posição']>3)&(tabela['Distância do líder']<=analise['pontos_restantes'])&(tabela['Sessões enviadas']>0)]
    with c3:
        if not fora_podio.empty and analise['pontos_restantes']>0:
            if chances is not None:
                disputa = fora_podio.merge(chances[['Usuario','Liderança simulada (%)']],on='Usuario').sort_values(['Liderança simulada (%)','Últimos 3 / GP','Pontos'],ascending=False)
            else:
                disputa = fora_podio.sort_values(['Últimos 3 / GP','Pontos'],ascending=False)
            surpresa = disputa.iloc[0]
            cartao_editorial('Azarão na pista',surpresa['Usuario'],f'Fora do pódio e a {numero_br(surpresa["Distância do líder"])} pontos do líder. É o melhor colocado no modelo entre os candidatos fora do top 3.' if chances is not None else 'Fora do pódio, mas com o melhor ritmo recente entre os que ainda podem alcançar o líder.','carro')
        else:
            cartao_editorial('Azarão na pista','', 'Ainda não há candidato fora do top 3 com participação e alcance matemático nesta apuração.','carro')
    c4,c5,c6 = st.columns(3)
    with c4:
        if analise['recentes']:
            quente = tabela.sort_values(['Últimos 3 / GP','Pontos'],ascending=False).iloc[0]
            cartao_editorial('Pé embaixo',quente['Usuario'],f'Média de {numero_br(quente["Últimos 3 / GP"],1)} pontos nos {len(analise["recentes"])} últimos GPs completos. Empates são possíveis.','carro')
        else:
            cartao_editorial('Pé embaixo','','Aguardando o primeiro GP com todas as sessões homologadas.','carro')
    with c5:
        pole = tabela.sort_values(['Poles certas','Pontos'],ascending=False).iloc[0]
        cartao_editorial('Mestre da pole',pole['Usuario'] if pole['Poles certas']>0 else '',f'{int(pole["Poles certas"])} poles acertadas entre classificações principais e Sprint. Empates são possíveis.','bandeira')
    with c6:
        especial = tabela.sort_values(['Especiais certos','Pontos'],ascending=False).iloc[0]
        cartao_editorial('Faro para os especiais',especial['Usuario'] if especial['Especiais certos']>0 else '',f'{int(especial["Especiais certos"])} acertos em melhor volta, primeiro abandono e mais ultrapassagens. Empates são possíveis.','capacete')


def podio_palpiteiros(tabela):
    secao('NA FRENTE / CAMPEONATO COMPLETO','A disputa pelo topo')
    ativos = tabela.loc[tabela['Sessões enviadas']>0]
    for coluna,registro in zip(st.columns(3),ativos.head(3).to_dict('records')):
        with coluna:
            gap = 'Na liderança' if registro['Distância do líder']==0 else f'{numero_br(registro["Distância do líder"])} pontos para o líder'
            variacao = int(registro['Variação na última etapa'])
            movimento = f'↑ {variacao}' if variacao>0 else (f'↓ {abs(variacao)}' if variacao<0 else '—')
            st.markdown(f'<div class="podium podium-{int(registro["Posição"])}"><div class="podium-top"><div class="rank">{int(registro["Posição"]):02d} / CLASSIFICAÇÃO</div><span class="movement">{movimento}</span></div>{avatar_html(registro["Usuario"],"large")}<h3>{escape(registro["Usuario"])}</h3><div class="team-name">{escape(registro["Equipe"])}</div><div class="score">{numero_br(registro["Pontos"])} <small>pontos</small></div><div class="gap">{escape(gap)}</div></div>',unsafe_allow_html=True)
    st.caption('Posições empatadas compartilham a colocação. A seta compara com o campeonato sem o último GP apurado; dentro do empate, a ordem visual é alfabética.')


def _grafico_barras(tabela,chave):
    opcoes = {'color':'#ff463e','horizontal':True}
    parametros = inspect.signature(st.bar_chart).parameters
    st.bar_chart(tabela.set_index(chave)['Pontos'],**{k:v for k,v in opcoes.items() if k in parametros})


def visao_tabelas(analise,filtro):
    tabela = analise['tabela']
    tab1,tab2 = st.tabs(['🏁 Palpiteiros','🏎️ Equipes'])
    with tab1:
        if filtro=='Geral (Campeonato Completo)':
            mostrar = tabela.copy()
        else:
            mostrar = tabela.copy()
            mostrar['Pontos'] = mostrar['Usuario'].map(analise['matriz'].loc[filtro])
            mostrar['Posição'] = _posicoes(mostrar.set_index('Usuario')['Pontos']).reindex(mostrar['Usuario']).values
            mostrar['Distância do líder'] = mostrar['Pontos'].max()-mostrar['Pontos']
            mostrar = mostrar.sort_values(['Pontos','Usuario'],ascending=[False,True])
        st.markdown('#### Grid dos palpiteiros')
        maior = max(1,mostrar['Pontos'].max())
        linhas = []
        for r in mostrar.to_dict('records'):
            largura = min(100,100*r['Pontos']/maior)
            linhas.append(f'<div class="ranking-row"><span class="row-pos">{int(r["Posição"]):02d}</span>{avatar_html(r["Usuario"],"mini")}<div class="row-name"><strong>{escape(r["Usuario"])}</strong><small>{escape(r["Equipe"])}</small></div><div class="row-pace"><span style="width:{largura:.1f}%"></span></div><div class="row-points">{numero_br(r["Pontos"])}<small>pontos</small></div></div>')
        st.markdown('<div class="ranking-list">'+''.join(linhas)+'</div>',unsafe_allow_html=True)
        with st.expander('Ver os números em detalhe'):
            campos = ['Posição','Usuario','Pontos','Distância do líder','Média / GP completo','Últimos 3 / GP','Melhor GP','Vitórias em GPs','Precisão (%)']
            st.dataframe(mostrar[campos].round(1),use_container_width=True,hide_index=True)
            if filtro!='Geral (Campeonato Completo)':
                st.caption('Pontos, posição e distância são da etapa selecionada; as demais estatísticas resumem a temporada.')
            st.caption('Médias e vitórias usam GPs completos; ausências contam como zero. Vitórias empatadas contam para todos os primeiros com pontuação positiva.')
    with tab2:
        if filtro=='Geral (Campeonato Completo)':
            base = tabela
        else:
            base = tabela.copy()
            base['Pontos'] = base['Usuario'].map(analise['matriz'].loc[filtro])
        equipes_df = ranking(base,'Equipe')
        equipes_df['Posição'] = equipes_df['Pontos'].rank(method='min',ascending=False).astype(int)
        st.dataframe(equipes_df[['Posição','Equipe','Pontos']],use_container_width=True,hide_index=True)
        _grafico_barras(equipes_df,'Equipe')
        st.caption('As equipes somam os pontos dos seus integrantes, conforme o cadastro atual.')


def raio_x_palpiteiro(analise):
    tabela = analise['tabela']
    nome = st.selectbox('Quem você quer acompanhar?',tabela['Usuario'].tolist(),key='raiox_usuario')
    r = tabela.loc[tabela['Usuario']==nome].iloc[0]
    restantes = analise['pontos_restantes']
    lider = tabela.iloc[0]['Pontos']
    st.markdown(f'<div class="profile">{avatar_html(nome,"large")}<div><div class="eyebrow">RAIO-X DO PALPITEIRO</div><h2>{escape(nome)}</h2><p>{escape(r["Equipe"])}</p></div></div>',unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('Posição por pontos',f'{int(r["Posição"])}º')
    c2.metric('Distância do líder',numero_br(r['Distância do líder']))
    c3.metric('Precisão nos campos válidos',numero_br(r['Precisão (%)'],1)+'%')
    c4,c5,c6 = st.columns(3)
    c4.metric('Média por GP completo',numero_br(r['Média / GP completo'],1))
    c5.metric('Forma recente / GP',numero_br(r['Últimos 3 / GP'],1))
    c6.metric('Melhor GP completo',numero_br(r['Melhor GP']))
    st.info(f'{situacao_titulo(r["Pontos"],lider,restantes)} · Teto individual: {numero_br(r["Pontos"]+restantes)} pontos se acertar tudo o que falta apurar.')
    if r['Distância do líder']>0 and restantes>0:
        st.caption(f'Precisa descontar {numero_br(r["Distância do líder"])} pontos para empatar com a pontuação atual do líder. Os adversários também continuarão pontuando.')
    matriz = analise['matriz']
    if not matriz.empty:
        st.markdown('#### Seu campeonato, etapa a etapa')
        evolucao = matriz[[nome]].cumsum()
        evolucao.index.name = 'GP'
        st.line_chart(evolucao)
        detalhes = pd.DataFrame({'GP':matriz.index,'Pontos no GP':matriz[nome].values,'Total acumulado':evolucao[nome].values})
        detalhes['Apuração'] = detalhes['GP'].map(analise['calendario'].set_index('GP')['Status']).fillna('Fora do calendário')
        st.dataframe(detalhes,use_container_width=True,hide_index=True)
    st.caption(f'{int(r["Acertos"])} acertos em {int(r["Campos avaliados"])} campos oficiais válidos nas sessões enviadas; campos em branco no palpite contam como erro. A precisão é informativa e não substitui os pontos ponderados do regulamento.')


def visao_titulo(analise,chances):
    tabela = analise['tabela']
    restantes = analise['pontos_restantes']
    lider = tabela.iloc[0]['Pontos']
    pendentes = analise['calendario'].loc[analise['calendario']['Sessões pendentes']>0]
    secao('RETA FINAL / CENÁRIOS','O campeonato ainda pode virar?')
    c1,c2,c3 = st.columns(3)
    c1.metric('GPs com sessões pendentes',len(pendentes))
    c2.metric('Pontos ainda em jogo por pessoa',numero_br(restantes))
    c3.metric('Sessões a apurar',int(pendentes['Sessões pendentes'].sum()))
    base = tabela[['Posição','Usuario','Pontos','Distância do líder']].copy()
    base['Teto individual'] = base['Pontos']+restantes
    base['Situação matemática'] = base['Pontos'].map(lambda p:situacao_titulo(p,lider,restantes))
    st.markdown('#### Termômetro do título')
    if chances is not None:
        base = base.merge(chances,on='Usuario')
        st.dataframe(base.round(1),use_container_width=True,hide_index=True)
        if restantes==0:
            st.success('Todas as sessões do calendário estão homologadas. A tabela já mostra o resultado final por pontos, preservando empates.')
        else:
            st.caption('Liderança simulada: crédito dividido entre os empatados na primeira posição. As porcentagens somam 100% antes do arredondamento. “0,0%” pode representar um valor pequeno ou nenhum caso nas 4.000 simulações; não significa eliminação matemática.')
    else:
        st.dataframe(base,use_container_width=True,hide_index=True)
        st.info('As chances aparecem quando existe histórico de pontuação para cada tipo de sessão ainda pendente. O alcance matemático já pode ser consultado acima.')
    with st.expander('Entenda o modelo e seus limites'):
        st.write('O modelo faz 4.000 reamostragens das pontuações já obtidas em cada tipo de sessão. Em cada sorteio, usa a mesma sessão histórica para todos os participantes, preservando diferenças observadas e ausências. A semente é fixa: mexer na página não muda os sorteios.')
        st.write('Parte da pontuação atual e adiciona as sessões ainda sem gabarito. Trata os tipos de sessão separadamente e pressupõe desempenho e participação semelhantes ao histórico. Não usa cotações, dados dos treinos nem resultados futuros da F1.')
        st.write('É uma estimativa condicionada ao histórico, não uma probabilidade calibrada ou garantia. P10 e P90 delimitam os 80% centrais das simulações, não um intervalo de confiança. Amostras pequenas ou mudanças de participação reduzem a utilidade do modelo.')
        st.caption('O calendário é o cadastrado no aplicativo. Sessão sem gabarito conta como pendente, inclusive de GP passado. Homologue resultados atrasados para atualizar os cenários. Não se aplica desempate extra, porque ele não existe no código atual.')
    if restantes<=0:
        return
    st.markdown('#### E se eu acelerar na reta final?')
    st.caption('Cenário hipotético: escolha o aproveitamento dos pontos restantes de dois concorrentes. Os demais mantêm o aproveitamento total observado até agora.')
    nomes = tabela['Usuario'].tolist()
    c1,c2 = st.columns(2)
    with c1:
        voce = st.selectbox('Seu palpiteiro',nomes,index=min(1,len(nomes)-1),key='sim_usuario')
    with c2:
        rivais = [n for n in nomes if n!=voce]
        rival = st.selectbox('Comparar com',rivais,key='sim_rival')
    eficiencia = (tabela.set_index('Usuario')['Pontos']/max(1,analise['maximo_apurado'])).clip(0,1)
    c1,c2 = st.columns(2)
    with c1:
        sua_pct = st.slider('Seu aproveitamento daqui para frente (%)',0,100,value=int(round(100*eficiencia[voce])),key=f'cenario_{voce}')
    with c2:
        rival_pct = st.slider('Aproveitamento do concorrente (%)',0,100,value=int(round(100*eficiencia[rival])),key=f'rival_{rival}')
    cenario = tabela[['Usuario','Pontos']].copy()
    cenario['Aproveitamento futuro (%)'] = cenario['Usuario'].map(eficiencia)*100
    cenario.loc[cenario['Usuario']==voce,'Aproveitamento futuro (%)'] = sua_pct
    cenario.loc[cenario['Usuario']==rival,'Aproveitamento futuro (%)'] = rival_pct
    cenario['Total no cenário'] = cenario['Pontos']+restantes*cenario['Aproveitamento futuro (%)']/100
    cenario['Posição no cenário'] = cenario['Total no cenário'].rank(method='min',ascending=False).astype(int)
    cenario = cenario.sort_values(['Total no cenário','Usuario'],ascending=[False,True])
    seus = cenario.loc[cenario['Usuario']==voce].iloc[0]
    dele = cenario.loc[cenario['Usuario']==rival].iloc[0]
    diferenca = seus['Total no cenário']-dele['Total no cenário']
    st.info(f'{voce}: {numero_br(seus["Total no cenário"],1)} pontos e {int(seus["Posição no cenário"])}º lugar neste cenário. Diferença para {rival}: {numero_br(diferenca,1)} pontos.')
    st.dataframe(cenario.round(1),use_container_width=True,hide_index=True)
    st.caption('Percentuais geram valores médios, que podem não corresponder a uma combinação exata de acertos. Este simulador não altera palpites, gabaritos ou pontos reais.')


def _valor_slider_mapa(valor,teto):
    return max(0,min(int(teto),int(round(float(valor)/PASSO_PONTOS)*PASSO_PONTOS)))


def _classe_duelo(status):
    if status in ('Ultrapassa','Desempata a seu favor'):
        return 'ganha'
    if status in ('É ultrapassado','Desempata contra você'):
        return 'perde'
    return 'empata' if status=='Empata' else 'neutro'


def renderizar_pista_mapa(mapa,usuario,mostrar_todos=False):
    indice = int(mapa.index[mapa['Usuario']==usuario][0])
    visiveis = mapa if mostrar_todos else mapa.iloc[max(0,indice-3):min(len(mapa),indice+4)]
    maior = max(1,mapa['Total no cenário'].max())
    linhas = []
    for r in visiveis.to_dict('records'):
        classe = 'voce' if r['Usuario']==usuario else _classe_duelo(r['Duelo'])
        percentual = max(0,min(100,100*r['Total no cenário']/maior))
        seta = f'↑ {r["Variação"]}' if r['Variação']>0 else f'↓ {abs(r["Variação"])}' if r['Variação']<0 else '—'
        linhas.append(f'<div class="mapa-lane {classe}"><span class="lane-pos">{r["Posição no cenário"]:02d}</span>{avatar_html(r["Usuario"],"mini")}<div class="lane-name"><strong>{escape(r["Usuario"])}</strong><small>{escape(r["Duelo"])} · {seta}</small></div><div class="lane-track"><span style="width:{percentual:.2f}%"></span><img src="{arte_f1("carro")}" style="left:clamp(0px,calc({percentual:.2f}% - 15px),calc(100% - 30px))" alt=""/></div><div class="lane-total">{numero_br(r["Total no cenário"])}<small>+{numero_br(r["Pontos no GP"])} no GP</small></div></div>')
    st.markdown('<div class="mapa-grid">'+''.join(linhas)+'</div>',unsafe_allow_html=True)


def restaurar_mapa_ultrapassagens():
    # O callback roda antes de recriar os widgets, sem exigir um rerun extra.
    for chave in list(st.session_state):
        if chave.startswith(('mapa_voce_','mapa_rival_','mapa_igual_','mapa_editar_')):
            del st.session_state[chave]


def visao_mapa_ultrapassagens(analise):
    secao('ESTRATÉGIA / LABORATÓRIO DO PRÓXIMO GP','Mapa de ultrapassagens')
    st.caption('Arraste sua pontuação e descubra quem fica para trás. A pista representa pontos acumulados neste cenário, não uma previsão da corrida de F1.')
    calendario = analise['calendario']
    pendentes = calendario.loc[calendario['Pontos disponíveis']>0]
    if pendentes.empty:
        st.info('Todas as sessões estão homologadas. Não há GP pendente para simular.')
        return
    tabela = analise['tabela']
    nomes = tabela['Usuario'].tolist()
    sugerido = st.session_state.get('usuario_enviar') or st.session_state.get('raiox_usuario')
    if sugerido not in nomes:
        sugerido = nomes[min(1,len(nomes)-1)]
    c1,c2 = st.columns(2)
    with c1:
        usuario = st.selectbox('Seu lugar no grid',nomes,index=nomes.index(sugerido),key='mapa_usuario')
    with c2:
        gps = pendentes['GP'].tolist()
        gp = st.selectbox('GP do cenário',gps,index=gps.index(gp_sugerido_mapa(analise)),key='mapa_gp')
    etapa = pendentes.set_index('GP').loc[gp]
    teto = int(etapa['Pontos disponíveis'])
    st.markdown(f'<div class="season-strip"><span>🏎️ GP de {escape(gp)}</span><span>⚡ Até {numero_br(teto)} pontos por pessoa</span><span>⏱️ {int(etapa["Sessões pendentes"])} sessões ainda sem gabarito</span></div>',unsafe_allow_html=True)
    st.caption('O que já foi homologado permanece no total atual. Aqui você distribui somente os pontos das sessões pendentes: '+' · '.join(etapa['Pendentes'])+'.')
    modo = st.radio('Ritmo inicial dos adversários',['Ritmo recente','Média da temporada','Pontuação igual'],horizontal=True,key='mapa_base')
    st.button('↺ Restaurar o ritmo de referência',key='mapa_restaurar',on_click=restaurar_mapa_ultrapassagens)
    base,faltantes = referencia_pontos_mapa(analise,gp,recente=modo=='Ritmo recente')
    if modo=='Pontuação igual':
        comum = st.slider('Pontuação inicial de cada adversário',0,teto,value=_valor_slider_mapa(base.mean(),teto),step=PASSO_PONTOS,key=f'mapa_igual_{gp}')
        base = pd.Series(float(comum),index=nomes)
    else:
        st.caption('Referência: média das três últimas apurações de cada tipo de sessão pendente.' if modo=='Ritmo recente' else 'Referência: média de todas as apurações de cada tipo de sessão pendente.')
        st.caption('Ausências contam como zero. Valores são arredondados para múltiplos de cinco e limitados ao teto do GP.')
        if faltantes:
            st.info('Sem histórico para '+', '.join(faltantes)+': a referência dessas sessões começa em zero. Você pode ajustar os rivais abaixo.')
    contexto = f'{usuario}_{gp}_{modo}'
    seus_pontos = st.slider('Seus pontos nas sessões pendentes',0,teto,value=_valor_slider_mapa(base[usuario],teto),step=PASSO_PONTOS,key=f'mapa_voce_{contexto}')
    pontuacoes = {nome:_valor_slider_mapa(base[nome],teto) for nome in nomes}
    with st.expander('🎛️ Ajustar individualmente os pontos dos rivais'):
        st.caption('Os valores são somados ao total atual de cada rival apenas nesta simulação.')
        personalizar = st.checkbox('Ativar ajustes individuais',value=False,key=f'mapa_editar_{contexto}')
        if personalizar:
            st.caption('Com os ajustes individuais ativados, estes valores prevalecem sobre o ritmo inicial.')
            colunas = st.columns(2)
            for i,nome in enumerate(n for n in nomes if n!=usuario):
                with colunas[i%2]:
                    pontuacoes[nome] = st.number_input(nome,min_value=0,max_value=teto,value=pontuacoes[nome],step=PASSO_PONTOS,key=f'mapa_rival_{contexto}_{nome}')
    pontuacoes[usuario] = seus_pontos
    mapa = calcular_mapa_ultrapassagens(tabela,usuario,pontuacoes,teto)
    voce = mapa.loc[mapa['Usuario']==usuario].iloc[0]
    passou = mapa.loc[mapa['Duelo']=='Ultrapassa','Usuario'].tolist()
    perdeu = mapa.loc[mapa['Duelo']=='É ultrapassado','Usuario'].tolist()
    empatou = mapa.loc[mapa['Duelo']=='Empata','Usuario'].tolist()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Sua posição atual',f'{int(voce["Posição atual"])}º')
    c2.metric('Posição neste cenário',f'{int(voce["Posição no cenário"])}º')
    c3.metric('Saldo de posições',f'{int(voce["Variação"]):+d}')
    c4.metric('Rivais ultrapassados',len(passou))
    frase = f'{numero_br(voce["Pontos"])} atuais + {numero_br(seus_pontos)} no GP = {numero_br(voce["Total no cenário"])} pontos.'
    classe_saldo = 'ganha' if voce['Variação']>0 else 'perde' if voce['Variação']<0 else 'neutro'
    st.markdown(f'<div class="mapa-summary {classe_saldo}">{avatar_html(usuario,"mini")}<div><strong>{escape(usuario)}</strong><span>{escape(frase)}</span></div><b>{int(voce["Posição atual"])}º → {int(voce["Posição no cenário"])}º</b></div>',unsafe_allow_html=True)
    st.caption('Verde: você passa ou desempata a seu favor. Vermelho: o rival passa ou desempata contra você. Dourado: empate. As colocações empatadas são compartilhadas, sem desempate adicional.')
    todos = st.checkbox('Mostrar todo o grid na pista',value=False,key='mapa_grid_completo')
    renderizar_pista_mapa(mapa,usuario,todos)
    st.caption('O saldo de posições considera o grid inteiro. O número de ultrapassagens conta apenas rivais que estavam estritamente à sua frente; desempates têm identificação própria.')
    if passou:
        st.success('Você ultrapassa: '+', '.join(passou)+'.')
    if perdeu:
        st.warning('Você é ultrapassado por: '+', '.join(perdeu)+'.')
    if empatou:
        st.info('Termina empatado com: '+', '.join(empatou)+'.')
    st.markdown('### Suas missões para este GP')
    missoes = metas_mapa_ultrapassagens(mapa,usuario,teto)
    for coluna,missao in zip(st.columns(3),missoes):
        with coluna:
            classe = 'ganha' if missao['Ao alcance'] else 'perde'
            rival = missao['Rival']
            foto = avatar_html(rival,'mini') if rival else ''
            texto = f'{numero_br(missao["Para alcançar"])} pts para alcançar a linha de corte; {numero_br(missao["Para passar"])} pts para ficar acima dela.'
            if missao['Para passar']==0:
                texto = 'Você já alcança esta meta com zero ponto adicional, considerando os pontos definidos para os rivais.'
            cumprida = seus_pontos >= missao['Para passar']
            alcance = '✓ Meta atingida neste cenário' if cumprida else f'Faltam {numero_br(missao["Para passar"]-seus_pontos)} pts no seu slider' if missao['Ao alcance'] else 'Exige mais que o teto deste GP'
            progresso = min(100,100*seus_pontos/max(1,missao['Para passar'])) if missao['Para passar'] else 100
            st.markdown(f'<div class="mapa-mission {classe}"><div class="tag">{escape(missao["Título"])}</div><div class="editorial-person">{foto}<h3>{escape(rival or "Pódio já alcançado")}</h3></div><div class="mission-number">{numero_br(missao["Para passar"])} <small>pontos no GP</small></div><p>{escape(texto)}</p><div class="mission-progress"><span style="width:{progresso:.1f}%"></span></div><span class="mission-badge">{escape(alcance)}</span></div>',unsafe_allow_html=True)
    st.caption('As metas são os seus pontos totais nas sessões pendentes, não pontos extras além do slider. Elas consideram os rivais definidos acima. O próximo rival é o mais próximo ainda à sua frente (ou empatado) neste cenário. A linha de corte do pódio é o terceiro maior total entre os adversários; a da liderança, o maior. Igualar a linha compartilha a colocação; passar fica acima, sem empate nessa linha.')
    rivais = mapa.loc[mapa['Usuario']!=usuario]
    if not rivais.empty:
        st.markdown('### Duelo direto da rodada')
        adversario = st.selectbox('Escolha seu adversário',rivais['Usuario'].tolist(),key='mapa_duelo')
        r = rivais.loc[rivais['Usuario']==adversario].iloc[0]
        diferenca = voce['Total no cenário']-r['Total no cenário']
        sinal = 'à frente' if diferenca>0 else 'atrás' if diferenca<0 else 'empatado'
        st.markdown(f'<div class="mapa-duelo {_classe_duelo(r["Duelo"])}">{avatar_html(usuario,"mini")}<div><strong>{escape(usuario)} × {escape(adversario)}</strong><span>{numero_br(abs(diferenca))} pontos · {sinal} neste cenário</span></div>{avatar_html(adversario,"mini")}</div>',unsafe_allow_html=True)
    with st.expander('Ver todos os pontos e alvos em tabela'):
        st.dataframe(mapa,use_container_width=True,hide_index=True)
    with st.expander('Como interpretar este mapa'):
        st.write('Este é um cenário determinístico: adiciona somente os pontos que você definiu para as sessões sem gabarito do GP selecionado. Você pode escolher também pendências antigas. Não lê palpites ainda não apurados nem prevê resultados reais.')
        st.write('Múltiplos de cinco seguem os pesos atuais, mas alguns totais podem não corresponder a uma combinação exata de acertos. Os pontos são limitados ao máximo individual, sem exigir que todos os cenários sejam conjuntamente possíveis para uma única corrida.')
        st.caption('Nenhum palpite, gabarito ou ponto oficial é alterado. A pontuação real só muda após a homologação do resultado.')


def visao_evolucao(analise):
    st.markdown('#### A corrida pela liderança')
    nomes = analise['tabela']['Usuario'].tolist()
    escolhidos = st.multiselect('Comparar palpiteiros',nomes,default=nomes[:5],key='evolucao_usuarios')
    modo = st.radio('Gráfico',['Acumulado','Por GP'],horizontal=True)
    matriz = analise['matriz']
    if escolhidos and not matriz.empty:
        grafico = matriz[escolhidos].cumsum() if modo=='Acumulado' else matriz[escolhidos]
        grafico.index.name = 'GP'
        st.line_chart(grafico)
    st.caption('O gráfico segue a ordem de GPs cadastrada e inclui etapas parciais. Ausência de palpite apurado aparece como zero.')
    st.markdown('#### Calendário e pontos disponíveis')
    cal = analise['calendario'].copy()
    cal['Sessões sem gabarito'] = cal['Pendentes'].map(lambda valores:' · '.join(valores) or 'Todas homologadas')
    st.dataframe(cal[['GP','Sprint','Status','Pontos disponíveis','Sessões sem gabarito']],use_container_width=True,hide_index=True)
    st.caption('GP normal vale até 1.770 pontos; com Sprint, até 2.230. Os pontos disponíveis descontam somente as sessões já homologadas.')


def tela_classificacoes():
    hero('O grid muda. A disputa também.', 'Seu lugar no campeonato, quem vem acelerando e os caminhos até a última bandeirada.', 'CENTRAL DOS PALPITEIROS')
    palpites,_ = ler_dados(ARQUIVO_DADOS)
    gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
    analise = analisar_temporada(palpites,gabaritos)
    tabela = analise['tabela']
    filtro = st.selectbox('Etapa',['Geral (Campeonato Completo)']+lista_gps,key='filtro_classificacao')
    if analise['sessoes'].empty:
        st.info('Ainda não há palpites com resultado homologado. O manual de pontuação está disponível na lateral.')
        return
    pontos = tabela['Pontos'] if filtro=='Geral (Campeonato Completo)' else analise['matriz'].loc[filtro] if filtro in analise['matriz'].index else pd.Series(dtype=float)
    if pontos.empty:
        st.info('Ainda não há pontuação apurada para esta etapa. Selecione outra etapa ou a classificação geral.')
        return
    c1,c2,c3 = st.columns(3)
    if filtro=='Geral (Campeonato Completo)':
        c1.metric('Palpiteiros com resultado',int((tabela['Sessões enviadas']>0).sum()))
        c2.metric('GPs completos',len(analise['completos']))
    else:
        c1.metric('Palpiteiros com resultado no GP',analise['sessoes'].loc[analise['sessoes']['GP']==filtro,'Usuario'].nunique())
        c2.metric('Sessões homologadas no GP',int((analise['gabaritos']['GP']==filtro).sum()))
    c3.metric('Pontos do líder' if filtro=='Geral (Campeonato Completo)' else 'Melhor pontuação no GP',numero_br(pontos.max()))
    if filtro!='Geral (Campeonato Completo)':
        st.caption(f'Grid filtrado por GP de {filtro}. Os destaques, o raio-X e as projeções usam o campeonato completo.')
    st.markdown(f'<div class="season-strip"><span>🏁 {len(analise["completos"])} GPs completos</span><span>⏳ {int((analise["calendario"]["Sessões pendentes"]>0).sum())} com sessões pendentes</span><span>⚡ {numero_br(analise["pontos_restantes"])} pontos ainda disponíveis por pessoa</span></div>',unsafe_allow_html=True)
    st.markdown('### Explore a disputa')
    painel = st.radio('Central de classificação',['Tabela e equipes','Mapa de ultrapassagens','Raio-X do palpiteiro','Corrida pelo título','Evolução e calendário'],horizontal=True,key='painel_classificacao')
    if painel=='Tabela e equipes':
        podio_palpiteiros(tabela)
        quadro_destaques(analise,tabela_chances(analise))
        visao_tabelas(analise,filtro)
    elif painel=='Mapa de ultrapassagens':
        visao_mapa_ultrapassagens(analise)
    elif painel=='Raio-X do palpiteiro':
        raio_x_palpiteiro(analise)
    elif painel=='Corrida pelo título':
        visao_titulo(analise,tabela_chances(analise))
    else:
        visao_evolucao(analise)


def assinatura_gabarito_gp(df,gp):
    from hashlib import sha256
    if df.empty:
        return ''
    etapa = df.loc[df['GP']==gp]
    if etapa.empty:
        return ''
    conteudo = etapa.reindex(columns=sorted(etapa.columns)).to_json(orient='records',force_ascii=False)
    return sha256(conteudo.encode()).hexdigest()


def _idade_reserva_reset(registro):
    try:
        return (datetime.now(pytz.UTC)-datetime.fromisoformat(str(registro['Reservado_em']))).total_seconds()
    except (ValueError,KeyError,TypeError):
        return 0


def _reservar_reset_gp(gp):
    from uuid import uuid4
    identificador = 'reset_gp_'+uuid4().hex
    agora = datetime.now(pytz.UTC).isoformat()
    def reservar(df):
        etapa = df.loc[df['GP']==gp] if not df.empty else df
        ativos = etapa.loc[etapa['Estado'].isin(['Em envio','Resetando'])] if not etapa.empty else etapa
        if any(_idade_reserva_reset(r)<600 for r in ativos.to_dict('records')):
            raise ValueError('Há um envio ou reset em andamento neste GP. Aguarde dez minutos e atualize os dados antes de tentar novamente.')
        novo = df.copy()
        if not etapa.empty:
            novo.loc[(novo['GP']==gp)&(novo['Estado']=='Resetando'),'Estado']='Reset cancelado'
        marcador = dict.fromkeys(COLUNAS_EMAIL_APURACOES,'')
        marcador.update(Id=identificador,GP=gp,Usuario='Administração',Estado='Resetando',Reservado_em=agora,Atualizado_em=agora)
        return pd.concat([novo,pd.DataFrame([marcador])],ignore_index=True),identificador
    return _alterar_livro_apuracao(reservar)


def _encerrar_reset_gp(gp,identificador,concluido):
    def encerrar(df):
        if df.empty or identificador not in set(df['Id']):
            raise ValueError('Controle do reset não encontrado.')
        novo = df.copy()
        mascara = novo['GP']==gp if concluido else novo['Id']==identificador
        novo.loc[mascara,'Estado']='Resetado' if concluido else 'Reset cancelado'
        novo.loc[mascara,'Atualizado_em']=datetime.now(pytz.UTC).isoformat()
        return novo,None
    return _alterar_livro_apuracao(encerrar)


def _remover_gabaritos_gp(gp,assinatura_esperada):
    for tentativa in range(3):
        atual,sha = _ler_dados_remotos(ARQUIVO_GABARITOS)
        if assinatura_gabarito_gp(atual,gp)!=assinatura_esperada:
            raise ValueError('O gabarito deste GP mudou desde a prévia. Atualize os dados e confira novamente antes de resetar.')
        if atual.empty:
            return 0
        mascara = atual['GP']==gp
        quantidade = int(mascara.sum())
        if not quantidade:
            return 0
        try:
            if not _escrever_csv(ARQUIVO_GABARITOS,atual.loc[~mascara].copy(),sha,f'Reset dos gabaritos do GP de {gp}'):
                raise OSError('A remoção do gabarito não foi confirmada.')
            return quantidade
        except urllib.error.HTTPError as erro:
            if erro.code!=409 or tentativa==2:
                raise
    raise OSError('Não foi possível concluir a remoção.')


def resetar_gabarito_gp(gp,assinatura_esperada):
    """Remove só os gabaritos do GP e libera novas apurações; nunca exclui palpites."""
    resultado = {'ok':False,'gp':gp,'removidos':0,'erro':None}
    if not isinstance(gp,str) or not gp.strip() or gp in ('Todos','Todos os GPs'):
        resultado['erro']='Selecione um GP específico para resetar.';return resultado
    identificador = None
    try:
        atual,_ = _ler_dados_remotos(ARQUIVO_GABARITOS)
        if assinatura_gabarito_gp(atual,gp)!=assinatura_esperada:
            raise ValueError('O gabarito deste GP mudou desde a prévia. Atualize os dados antes de resetar.')
        identificador = _reservar_reset_gp(gp)
        resultado['removidos'] = _remover_gabaritos_gp(gp,assinatura_esperada)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as erro:
        logger.warning('Reset de gabarito não confirmado.')
        if identificador:
            try:
                _encerrar_reset_gp(gp,identificador,False)
            except (OSError,ValueError,KeyError,TypeError,RuntimeError):
                logger.warning('Não foi possível liberar o controle do reset.')
        resultado['erro']=str(erro) if isinstance(erro,ValueError) else 'Não foi possível confirmar o reset. Atualize os dados e confira o GP antes de tentar novamente.'
        return resultado
    try:
        _encerrar_reset_gp(gp,identificador,True)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        logger.warning('Gabaritos removidos, mas o reset dos envios ficou pendente.')
        resultado['erro']='Os gabaritos foram removidos, mas a liberação dos e-mails ficou pendente. Aguarde dez minutos, atualize os dados e execute o reset deste GP novamente para concluir.'
        return resultado
    resultado['ok']=True
    return resultado


def admin_reset_gabarito():
    with st.expander('🧹 Resetar gabarito de um GP'):
        st.caption('Remove todas as sessões homologadas do GP escolhido, incluindo pole e Sprint, e libera uma nova apuração por e-mail. Os palpites são preservados. E-mails já recebidos continuam nas caixas dos destinatários.')
        if not st.checkbox('Exibir opções de reset',value=False,key='exibir_reset_gabarito'):
            return
        try:
            gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
            controle,_ = ler_dados(ARQUIVO_EMAIL_APURACOES)
            publicados = set(gabaritos['GP'].dropna()) if not gabaritos.empty else set()
            gps = ['']+lista_gps+sorted(publicados-set(lista_gps))
            gp = st.selectbox('GP que deseja resetar',gps,key='reset_gabarito_gp')
            if not gp:
                return
            etapa = gabaritos.loc[gabaritos['GP']==gp] if not gabaritos.empty else gabaritos
            st.write(f'GP de {gp}: {len(etapa)} gabaritos serão removidos.')
            if not etapa.empty:
                st.dataframe(etapa[['GP','Tipo']],use_container_width=True,hide_index=True)
                st.download_button('Baixar cópia dos gabaritos deste GP',etapa.to_csv(index=False).encode('utf-8-sig'),file_name='backup_gabaritos_gp.csv',mime='text/csv',key=f'backup_reset_{gp}')
            pendente = not controle.empty and bool(((controle['GP']==gp)&(controle['Estado']=='Resetando')).any())
            if pendente:
                st.warning('Existe um reset em andamento ou pendente neste GP. Após dez minutos é possível repetir para concluir a liberação.')
        except (OSError,ValueError,KeyError):
            st.warning('Não foi possível carregar a prévia do reset. Atualize os dados e tente novamente.')
            return
        st.warning(f'Esta ação retira a pontuação apurada do GP de {gp} da classificação até uma nova homologação. O controle anterior de e-mails desse GP ficará marcado como resetado.')
        confirmar = st.checkbox(f'Confirmo resetar os gabaritos e liberar a apuração por e-mail do GP de {gp}',value=False,key=f'confirmar_reset_{gp}')
        if st.button('Resetar gabarito deste GP',disabled=not confirmar,type='primary',key=f'executar_reset_{gp}'):
            with st.spinner('Resetando o gabarito e o controle de apuração…'):
                resultado = resetar_gabarito_gp(gp,assinatura_gabarito_gp(gabaritos,gp))
            if resultado['ok']:
                st.success(f"GP de {gp} resetado: {resultado['removidos']} gabaritos removidos. Palpites preservados e nova apuração por e-mail liberada.")
            else:
                st.warning(resultado['erro'])


def admin_auditoria():
    admin_reset_gabarito()
    st.subheader('Palpites dos participantes')
    df,_ = ler_dados(ARQUIVO_DADOS)
    if df.empty:
        st.info('Nenhum palpite cadastrado.')
        return
    df = df.drop_duplicates(['Usuario','GP','Tipo'],keep='last')
    gp_filtro = st.selectbox('Filtrar auditoria por GP',['Todos os GPs']+lista_gps)
    st.dataframe(df if gp_filtro=='Todos os GPs' else df.loc[df['GP']==gp_filtro],use_container_width=True,hide_index=True)
    secao('EDIÇÃO','Ajustar palpite de participante')
    usuario = st.selectbox('Participante',['']+participantes,key='adm_usuario')
    gp,tipo = seletor_etapa('adm',lista_gps)
    if not usuario:
        return
    contexto = f'admin_{usuario}_{gp}_{tipo}'
    with st.form(contexto):
        valores = formulario_pilotos(tipo,ultimo_registro(df,gp,tipo,usuario),contexto)
        salvar = st.form_submit_button('Salvar alteração do administrador',type='primary')
    if salvar and guardar_dados(_dados_palpite(usuario,gp,tipo,valores,admin=True),ARQUIVO_DADOS,eh_edicao_admin=True):
        st.session_state['mensagem_sucesso'] = f'Palpite de {usuario} atualizado.'
        st.rerun()


def admin_historico():
    st.subheader('Histórico de alterações')
    df,_ = ler_dados(ARQUIVO_HISTORICO)
    if df.empty:
        st.info('Histórico de alterações vazio.')
        return
    c1,c2 = st.columns(2)
    with c1:
        usuario = st.selectbox('Participante',['Todos']+participantes,key='log_usuario')
    with c2:
        gp = st.selectbox('Grande Prêmio',['Todos']+lista_gps,key='log_gp')
    if usuario != 'Todos':
        df = df.loc[df['Usuario']==usuario]
    if gp != 'Todos':
        df = df.loc[df['GP']==gp]
    if df.empty:
        st.info('Nenhum evento com esses filtros.')
    else:
        st.dataframe(df.iloc[::-1],use_container_width=True,hide_index=True)


def admin_emails_apuracao():
    st.subheader('E-mails de apuração do GP')
    st.caption('Modo de testes: os relatórios individuais são enviados somente para '+EMAIL_ADMIN+'. Os envios aos palpiteiros estão bloqueados.' if BLOQUEAR_EMAILS_PALPITEIROS else 'Compare o palpite com os gabaritos homologados e envie o total individual. As mensagens são enviadas ao e-mail cadastrado de quem palpitou no GP, com cópia oculta para o bolão.')
    palpites,_ = ler_dados(ARQUIVO_DADOS)
    gabaritos,_ = ler_dados(ARQUIVO_GABARITOS)
    publicados = set(gabaritos['GP'].dropna()) if not gabaritos.empty else set()
    gps = [g for g in lista_gps if g in publicados]+sorted(publicados-set(lista_gps))
    if not gps:
        st.info('Homologue os resultados antes de preparar e-mails de apuração.')
        return
    gp = st.selectbox('GP da apuração',gps,index=len(gps)-1,key='email_apuracao_gp')
    tarefas,sem_email = preparar_emails_apuracao(palpites,gabaritos,gp)
    if not ultimo_registro(gabaritos,gp,'Corrida Principal'):
        st.info('A apuração por e-mail fica disponível depois de homologar a corrida principal.')
        return
    if sem_email:
        st.warning('Sem e-mail cadastrado válido: '+', '.join(sem_email))
    if not tarefas:
        st.info('Não há palpites com e-mail cadastrado para esta etapa.')
        return
    st.write(f'{len(tarefas)} participantes com palpite e e-mail cadastrado neste GP.')
    if any(t['relatorio']['parcial'] for t in tarefas):
        st.warning('Há gabaritos ou resultados pendentes. O e-mail será identificado como apuração parcial.')
    usuario = st.selectbox('Prévia individual',[t['usuario'] for t in tarefas],key='email_apuracao_usuario')
    tarefa = next(t for t in tarefas if t['usuario']==usuario)
    st.metric('Total apurado no GP',numero_br(tarefa['relatorio']['total']))
    with st.expander('Prévia do e-mail com acertos e pontuação'):
        import streamlit.components.v1 as componentes
        _,texto,html = montar_email_apuracao(tarefa['relatorio'])
        componentes.html(html,height=650,scrolling=True)
        st.download_button('Baixar prévia em HTML',html,file_name='previa_apuracao.html',mime='text/html',key='baixar_previa_apuracao')
    with st.expander('Controle das últimas tentativas'):
        try:
            controle,_ = ler_dados(ARQUIVO_EMAIL_APURACOES)
            if controle.empty:
                st.caption('Nenhuma apuração por e-mail registrada ainda.')
            else:
                ultimo = controle.loc[(controle['GP']==gp)&~controle['Id'].astype(str).str.startswith('reset_gp_')].drop_duplicates(['Usuario'],keep='last')
                st.dataframe(ultimo[['Usuario','Estado','Total_GP','Atualizado_em']],use_container_width=True,hide_index=True)
                st.caption('Aceito: o Brevo aceitou a mensagem; confira a entrega nos logs transacionais. Em envio: lote reservado. Verificar: não houve confirmação. Resetado: liberado para nova apuração após reset do gabarito. Datas do controle em UTC.')
        except (OSError,ValueError,KeyError):
            st.warning('Não foi possível consultar o controle. O envio fará uma nova leitura antes de reservar o lote.')
    st.caption('Os relatórios já enviados na revisão atual são ignorados. Correções dos gabaritos ou palpites geram uma apuração atualizada. O envio só ocorre ao salvar com a opção marcada ou ao clicar no botão abaixo.')
    repetir = st.checkbox('Conferi nos logs do Brevo que os envios pendentes não foram aceitos e autorizo uma nova tentativa',value=False,key='email_apuracao_repetir')
    if repetir:
        st.warning('Se uma mensagem já tiver sido aceita, repetir pode duplicá-la. Reservas em andamento só podem ser liberadas após dez minutos. Relatórios confirmados como aceitos não são repetidos nesta revisão.')
    if not BREVO_API_KEY:
        st.info('Configure BREVO_API_KEY para habilitar os envios.')
    if st.button('Enviar apurações pendentes deste GP',disabled=not bool(BREVO_API_KEY),key='email_apuracao_enviar',type='primary'):
        mostrar_resumo_apuracao(disparar_apuracao_com_progresso(gp,repetir))


def admin_gabarito():
    st.subheader('Homologar resultado oficial')
    gp,tipo = seletor_etapa('gabarito',lista_gps)
    df,_ = ler_dados(ARQUIVO_GABARITOS)
    contexto = f'gabarito_{gp}_{tipo}'
    with st.form(contexto):
        valores = formulario_pilotos(tipo,ultimo_registro(df,gp,tipo),contexto)
        avisar = st.checkbox('Enviar apuração do GP por e-mail após salvar, se a corrida principal já estiver homologada',value=bool(BREVO_API_KEY),disabled=not bool(BREVO_API_KEY),key=f'apurar_email_{gp}_{tipo}')
        st.caption('Quem palpitou no GP recebe a comparação, os acertos e o total. Gabaritos ou campos faltantes serão indicados como apuração parcial. A mesma revisão não é repetida automaticamente.')
        salvar = st.form_submit_button('Salvar / atualizar gabarito oficial',type='primary')
    if salvar and guardar_dados({'GP':gp,'Tipo':tipo,**valores},ARQUIVO_GABARITOS):
        st.success('Gabarito oficial homologado!')
        if avisar:
            mostrar_resumo_apuracao(disparar_apuracao_com_progresso(gp))


def admin_gabaritos_salvos():
    st.subheader('Gabaritos homologados')
    df,_ = ler_dados(ARQUIVO_GABARITOS)
    if df.empty:
        st.info('Nenhum gabarito cadastrado.')
    else:
        st.dataframe(df.dropna(how='all',axis=1),use_container_width=True,hide_index=True)


def admin_excluir():
    st.subheader('Exclusão de registros')
    df,_ = ler_dados(ARQUIVO_DADOS)
    if df.empty:
        st.info('Nenhum palpite cadastrado.')
        return
    gp,tipo = seletor_etapa('excluir',lista_gps)
    filtrado = df.loc[(df['GP']==gp)&(df['Tipo']==tipo)]
    if filtrado.empty:
        st.info('Nenhum registro nesta sessão.')
        return
    usuario = st.selectbox('Participante para excluir',['']+sorted(filtrado['Usuario'].unique()))
    if usuario:
        st.warning(f'A exclusão removerá o palpite de {usuario} desta sessão.')
        if st.button('Confirmar exclusão',type='primary'):
            mascara = ~((df['GP']==gp)&(df['Tipo']==tipo)&(df['Usuario']==usuario))
            if deletar_registro_github(ARQUIVO_DADOS,mascara):
                st.session_state['mensagem_sucesso'] = 'Registro removido com sucesso.'
                st.rerun()


def tela_admin():
    hero('Direção de prova.', 'Gerencie os palpites, homologue os resultados e acompanhe os registros do campeonato.', 'ÁREA ADMINISTRATIVA')
    senha = st.text_input('Senha do diretor de prova',type='password',key='senha_admin')
    esperada = configuracao('SENHA_ADMIN',SENHA_ADMIN_LEGADA)
    if not senha:
        return
    if not hmac.compare_digest(senha.encode(),esperada.encode()):
        st.error('Senha de administrador incorreta.')
        return
    st.caption('Painel administrativo · acesso autorizado')
    # Radio executa apenas a seção ativa, ao contrário de cinco abas executadas a cada interação.
    painel = st.radio('Painel',['Auditoria e edição','Histórico','Homologar resultado','Gabaritos salvos','Excluir registro','E-mails de apuração','Gerenciar fotos'],horizontal=True)
    {'Auditoria e edição':admin_auditoria,'Histórico':admin_historico,
     'Homologar resultado':admin_gabarito,'Gabaritos salvos':admin_gabaritos_salvos,
     'Excluir registro':admin_excluir,'E-mails de apuração':admin_emails_apuracao,'Gerenciar fotos':admin_fotos}[painel]()


# ── Central pública de Fórmula 1: independente dos palpites do bolão ──
F1_API_BASE = 'https://api.jolpi.ca/ergast/f1'
F1_INTERVALO_ATUALIZACAO = 300
F1_BACKUP_2026 = {'conferido_em': '2026-11-03T20:04:38.218496+00:00', 'pilotos': {'temporada': 2026, 'rodada': 19, 'registros': [{'Posição': 1, 'Pontos': 380.0, 'Vitórias': 9, 'Piloto': 'Kimi Antonelli', 'Código': 'ANT', 'Número': '12', 'Nacionalidade': 'Italian', 'Equipe': 'Mercedes', 'driver_id': 'antonelli', 'team_id': 'mercedes'}, {'Posição': 2, 'Pontos': 261.0, 'Vitórias': 3, 'Piloto': 'Max Verstappen', 'Código': 'VER', 'Número': '3', 'Nacionalidade': 'Dutch', 'Equipe': 'Red Bull', 'driver_id': 'max_verstappen', 'team_id': 'red_bull'}, {'Posição': 3, 'Pontos': 259.0, 'Vitórias': 1, 'Piloto': 'Lewis Hamilton', 'Código': 'HAM', 'Número': '44', 'Nacionalidade': 'British', 'Equipe': 'Ferrari', 'driver_id': 'hamilton', 'team_id': 'ferrari'}, {'Posição': 4, 'Pontos': 250.0, 'Vitórias': 3, 'Piloto': 'George Russell', 'Código': 'RUS', 'Número': '63', 'Nacionalidade': 'British', 'Equipe': 'Mercedes', 'driver_id': 'russell', 'team_id': 'mercedes'}, {'Posição': 5, 'Pontos': 245.0, 'Vitórias': 1, 'Piloto': 'Charles Leclerc', 'Código': 'LEC', 'Número': '16', 'Nacionalidade': 'Monegasque', 'Equipe': 'Ferrari', 'driver_id': 'leclerc', 'team_id': 'ferrari'}, {'Posição': 6, 'Pontos': 221.0, 'Vitórias': 2, 'Piloto': 'Lando Norris', 'Código': 'NOR', 'Número': '1', 'Nacionalidade': 'British', 'Equipe': 'McLaren', 'driver_id': 'norris', 'team_id': 'mclaren'}, {'Posição': 7, 'Pontos': 144.0, 'Vitórias': 0, 'Piloto': 'Oscar Piastri', 'Código': 'PIA', 'Número': '81', 'Nacionalidade': 'Australian', 'Equipe': 'McLaren', 'driver_id': 'piastri', 'team_id': 'mclaren'}, {'Posição': 8, 'Pontos': 107.0, 'Vitórias': 0, 'Piloto': 'Isack Hadjar', 'Código': 'HAD', 'Número': '6', 'Nacionalidade': 'French', 'Equipe': 'Red Bull', 'driver_id': 'hadjar', 'team_id': 'red_bull'}, {'Posição': 9, 'Pontos': 83.0, 'Vitórias': 0, 'Piloto': 'Liam Lawson', 'Código': 'LAW', 'Número': '30', 'Nacionalidade': 'New Zealander', 'Equipe': 'RB F1 Team / Red Bull', 'driver_id': 'lawson', 'team_id': 'red_bull'}, {'Posição': 10, 'Pontos': 42.0, 'Vitórias': 0, 'Piloto': 'Pierre Gasly', 'Código': 'GAS', 'Número': '10', 'Nacionalidade': 'French', 'Equipe': 'Alpine F1 Team', 'driver_id': 'gasly', 'team_id': 'alpine'}, {'Posição': 11, 'Pontos': 38.0, 'Vitórias': 0, 'Piloto': 'Arvid Lindblad', 'Código': 'LIN', 'Número': '41', 'Nacionalidade': 'British', 'Equipe': 'RB F1 Team', 'driver_id': 'arvid_lindblad', 'team_id': 'rb'}, {'Posição': 12, 'Pontos': 27.0, 'Vitórias': 0, 'Piloto': 'Franco Colapinto', 'Código': 'COL', 'Número': '43', 'Nacionalidade': 'Argentine', 'Equipe': 'Alpine F1 Team', 'driver_id': 'colapinto', 'team_id': 'alpine'}, {'Posição': 13, 'Pontos': 23.0, 'Vitórias': 0, 'Piloto': 'Oliver Bearman', 'Código': 'BEA', 'Número': '87', 'Nacionalidade': 'British', 'Equipe': 'Haas F1 Team', 'driver_id': 'bearman', 'team_id': 'haas'}, {'Posição': 14, 'Pontos': 14.0, 'Vitórias': 0, 'Piloto': 'Gabriel Bortoleto', 'Código': 'BOR', 'Número': '5', 'Nacionalidade': 'Brazilian', 'Equipe': 'Audi', 'driver_id': 'bortoleto', 'team_id': 'audi'}, {'Posição': 15, 'Pontos': 13.0, 'Vitórias': 0, 'Piloto': 'Nico Hülkenberg', 'Código': 'HUL', 'Número': '27', 'Nacionalidade': 'German', 'Equipe': 'Audi', 'driver_id': 'hulkenberg', 'team_id': 'audi'}, {'Posição': 16, 'Pontos': 7.0, 'Vitórias': 0, 'Piloto': 'Esteban Ocon', 'Código': 'OCO', 'Número': '31', 'Nacionalidade': 'French', 'Equipe': 'Haas F1 Team', 'driver_id': 'ocon', 'team_id': 'haas'}, {'Posição': 17, 'Pontos': 7.0, 'Vitórias': 0, 'Piloto': 'Fernando Alonso', 'Código': 'ALO', 'Número': '14', 'Nacionalidade': 'Spanish', 'Equipe': 'Aston Martin', 'driver_id': 'alonso', 'team_id': 'aston_martin'}, {'Posição': 18, 'Pontos': 7.0, 'Vitórias': 0, 'Piloto': 'Carlos Sainz', 'Código': 'SAI', 'Número': '55', 'Nacionalidade': 'Spanish', 'Equipe': 'Williams', 'driver_id': 'sainz', 'team_id': 'williams'}, {'Posição': 19, 'Pontos': 5.0, 'Vitórias': 0, 'Piloto': 'Alexander Albon', 'Código': 'ALB', 'Número': '23', 'Nacionalidade': 'Thai', 'Equipe': 'Williams', 'driver_id': 'albon', 'team_id': 'williams'}, {'Posição': 20, 'Pontos': 1.0, 'Vitórias': 0, 'Piloto': 'Yuki Tsunoda', 'Código': 'TSU', 'Número': '22', 'Nacionalidade': 'Japanese', 'Equipe': 'RB F1 Team', 'driver_id': 'tsunoda', 'team_id': 'rb'}, {'Posição': 21, 'Pontos': 1.0, 'Vitórias': 0, 'Piloto': 'Ryo Hirakawa', 'Código': 'HIR', 'Número': '50', 'Nacionalidade': 'Japanese', 'Equipe': 'Haas F1 Team', 'driver_id': 'ryo_hirakawa', 'team_id': 'haas'}, {'Posição': 22, 'Pontos': 0.0, 'Vitórias': 0, 'Piloto': 'Lance Stroll', 'Código': 'STR', 'Número': '18', 'Nacionalidade': 'Canadian', 'Equipe': 'Aston Martin', 'driver_id': 'stroll', 'team_id': 'aston_martin'}, {'Posição': 23, 'Pontos': 0.0, 'Vitórias': 0, 'Piloto': 'Valtteri Bottas', 'Código': 'BOT', 'Número': '77', 'Nacionalidade': 'Finnish', 'Equipe': 'Cadillac F1 Team', 'driver_id': 'bottas', 'team_id': 'cadillac'}, {'Posição': 24, 'Pontos': 0.0, 'Vitórias': 0, 'Piloto': 'Sergio Pérez', 'Código': 'PER', 'Número': '11', 'Nacionalidade': 'Mexican', 'Equipe': 'Cadillac F1 Team', 'driver_id': 'perez', 'team_id': 'cadillac'}]}, 'equipes': {'temporada': 2026, 'rodada': 19, 'registros': [{'Posição': 1, 'Pontos': 630.0, 'Vitórias': 12, 'Equipe': 'Mercedes', 'Nacionalidade': 'German', 'team_id': 'mercedes'}, {'Posição': 2, 'Pontos': 504.0, 'Vitórias': 2, 'Equipe': 'Ferrari', 'Nacionalidade': 'Italian', 'team_id': 'ferrari'}, {'Posição': 3, 'Pontos': 382.0, 'Vitórias': 3, 'Equipe': 'Red Bull', 'Nacionalidade': 'Austrian', 'team_id': 'red_bull'}, {'Posição': 4, 'Pontos': 365.0, 'Vitórias': 2, 'Equipe': 'McLaren', 'Nacionalidade': 'British', 'team_id': 'mclaren'}, {'Posição': 5, 'Pontos': 108.0, 'Vitórias': 0, 'Equipe': 'RB F1 Team', 'Nacionalidade': 'Italian', 'team_id': 'rb'}, {'Posição': 6, 'Pontos': 69.0, 'Vitórias': 0, 'Equipe': 'Alpine F1 Team', 'Nacionalidade': 'French', 'team_id': 'alpine'}, {'Posição': 7, 'Pontos': 31.0, 'Vitórias': 0, 'Equipe': 'Haas F1 Team', 'Nacionalidade': 'American', 'team_id': 'haas'}, {'Posição': 8, 'Pontos': 27.0, 'Vitórias': 0, 'Equipe': 'Audi', 'Nacionalidade': 'German', 'team_id': 'audi'}, {'Posição': 9, 'Pontos': 12.0, 'Vitórias': 0, 'Equipe': 'Williams', 'Nacionalidade': 'British', 'team_id': 'williams'}, {'Posição': 10, 'Pontos': 7.0, 'Vitórias': 0, 'Equipe': 'Aston Martin', 'Nacionalidade': 'British', 'team_id': 'aston_martin'}, {'Posição': 11, 'Pontos': 0.0, 'Vitórias': 0, 'Equipe': 'Cadillac F1 Team', 'Nacionalidade': 'American', 'team_id': 'cadillac'}]}, 'resultado': {'temporada': 2026, 'rodada': 19, 'nome': 'Mexico City Grand Prix', 'data': '2026-11-01', 'hora': '20:00:00Z', 'circuito': 'Autódromo Hermanos Rodríguez', 'circuit_id': 'rodriguez', 'registros': [{'Posição': 1, 'Piloto': 'Max Verstappen', 'Código': 'VER', 'Equipe': 'Red Bull', 'team_id': 'red_bull', 'Grid': 5, 'Ganho de posições': 4, 'Voltas': 71, 'Pontos': 25.0, 'Tempo / diferença': '2:20:28.772', 'Status': 'Finished', 'Melhor volta': '1:19.328', 'Volta mais rápida': False}, {'Posição': 2, 'Piloto': 'Lewis Hamilton', 'Código': 'HAM', 'Equipe': 'Ferrari', 'team_id': 'ferrari', 'Grid': 1, 'Ganho de posições': -1, 'Voltas': 71, 'Pontos': 18.0, 'Tempo / diferença': '+0.799', 'Status': 'Finished', 'Melhor volta': '1:19.268', 'Volta mais rápida': True}, {'Posição': 3, 'Piloto': 'Kimi Antonelli', 'Código': 'ANT', 'Equipe': 'Mercedes', 'team_id': 'mercedes', 'Grid': 4, 'Ganho de posições': 1, 'Voltas': 71, 'Pontos': 15.0, 'Tempo / diferença': '+4.006', 'Status': 'Finished', 'Melhor volta': '1:19.427', 'Volta mais rápida': False}, {'Posição': 4, 'Piloto': 'Charles Leclerc', 'Código': 'LEC', 'Equipe': 'Ferrari', 'team_id': 'ferrari', 'Grid': 3, 'Ganho de posições': -1, 'Voltas': 71, 'Pontos': 12.0, 'Tempo / diferença': '+10.707', 'Status': 'Finished', 'Melhor volta': '1:19.851', 'Volta mais rápida': False}, {'Posição': 5, 'Piloto': 'Lando Norris', 'Código': 'NOR', 'Equipe': 'McLaren', 'team_id': 'mclaren', 'Grid': 6, 'Ganho de posições': 1, 'Voltas': 71, 'Pontos': 10.0, 'Tempo / diferença': '+11.778', 'Status': 'Finished', 'Melhor volta': '1:19.800', 'Volta mais rápida': False}, {'Posição': 6, 'Piloto': 'George Russell', 'Código': 'RUS', 'Equipe': 'Mercedes', 'team_id': 'mercedes', 'Grid': 2, 'Ganho de posições': -4, 'Voltas': 71, 'Pontos': 8.0, 'Tempo / diferença': '+12.263', 'Status': 'Finished', 'Melhor volta': '1:20.147', 'Volta mais rápida': False}, {'Posição': 7, 'Piloto': 'Liam Lawson', 'Código': 'LAW', 'Equipe': 'RB F1 Team', 'team_id': 'rb', 'Grid': 22, 'Ganho de posições': 15, 'Voltas': 71, 'Pontos': 6.0, 'Tempo / diferença': '+20.899', 'Status': 'Finished', 'Melhor volta': '1:20.713', 'Volta mais rápida': False}, {'Posição': 8, 'Piloto': 'Gabriel Bortoleto', 'Código': 'BOR', 'Equipe': 'Audi', 'team_id': 'audi', 'Grid': 13, 'Ganho de posições': 5, 'Voltas': 71, 'Pontos': 4.0, 'Tempo / diferença': '+22.041', 'Status': 'Finished', 'Melhor volta': '1:20.872', 'Volta mais rápida': False}, {'Posição': 9, 'Piloto': 'Isack Hadjar', 'Código': 'HAD', 'Equipe': 'Red Bull', 'team_id': 'red_bull', 'Grid': 7, 'Ganho de posições': -2, 'Voltas': 71, 'Pontos': 2.0, 'Tempo / diferença': '+22.503', 'Status': 'Finished', 'Melhor volta': '1:20.244', 'Volta mais rápida': False}, {'Posição': 10, 'Piloto': 'Ryo Hirakawa', 'Código': 'HIR', 'Equipe': 'Haas F1 Team', 'team_id': 'haas', 'Grid': 18, 'Ganho de posições': 8, 'Voltas': 71, 'Pontos': 1.0, 'Tempo / diferença': '+25.373', 'Status': 'Finished', 'Melhor volta': '1:20.984', 'Volta mais rápida': False}, {'Posição': 11, 'Piloto': 'Alexander Albon', 'Código': 'ALB', 'Equipe': 'Williams', 'team_id': 'williams', 'Grid': 16, 'Ganho de posições': 5, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+27.562', 'Status': 'Finished', 'Melhor volta': '1:21.114', 'Volta mais rápida': False}, {'Posição': 12, 'Piloto': 'Carlos Sainz', 'Código': 'SAI', 'Equipe': 'Williams', 'team_id': 'williams', 'Grid': 15, 'Ganho de posições': 3, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+28.638', 'Status': 'Finished', 'Melhor volta': '1:21.339', 'Volta mais rápida': False}, {'Posição': 13, 'Piloto': 'Oscar Piastri', 'Código': 'PIA', 'Equipe': 'McLaren', 'team_id': 'mclaren', 'Grid': 12, 'Ganho de posições': -1, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+29.475', 'Status': 'Finished', 'Melhor volta': '1:20.690', 'Volta mais rápida': False}, {'Posição': 14, 'Piloto': 'Nico Hülkenberg', 'Código': 'HUL', 'Equipe': 'Audi', 'team_id': 'audi', 'Grid': 10, 'Ganho de posições': -4, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+29.977', 'Status': 'Finished', 'Melhor volta': '1:20.732', 'Volta mais rápida': False}, {'Posição': 15, 'Piloto': 'Franco Colapinto', 'Código': 'COL', 'Equipe': 'Alpine F1 Team', 'team_id': 'alpine', 'Grid': 11, 'Ganho de posições': -4, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+30.204', 'Status': 'Finished', 'Melhor volta': '1:20.750', 'Volta mais rápida': False}, {'Posição': 16, 'Piloto': 'Sergio Pérez', 'Código': 'PER', 'Equipe': 'Cadillac F1 Team', 'team_id': 'cadillac', 'Grid': 20, 'Ganho de posições': 4, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+30.695', 'Status': 'Finished', 'Melhor volta': '1:21.256', 'Volta mais rápida': False}, {'Posição': 17, 'Piloto': 'Pierre Gasly', 'Código': 'GAS', 'Equipe': 'Alpine F1 Team', 'team_id': 'alpine', 'Grid': 9, 'Ganho de posições': -8, 'Voltas': 71, 'Pontos': 0.0, 'Tempo / diferença': '+51.483', 'Status': 'Finished', 'Melhor volta': '1:20.754', 'Volta mais rápida': False}, {'Posição': 18, 'Piloto': 'Arvid Lindblad', 'Código': 'LIN', 'Equipe': 'RB F1 Team', 'team_id': 'rb', 'Grid': 8, 'Ganho de posições': -10, 'Voltas': 58, 'Pontos': 0.0, 'Tempo / diferença': 'Retired', 'Status': 'Retired', 'Melhor volta': '1:20.555', 'Volta mais rápida': False}, {'Posição': 19, 'Piloto': 'Oliver Bearman', 'Código': 'BEA', 'Equipe': 'Haas F1 Team', 'team_id': 'haas', 'Grid': 14, 'Ganho de posições': -5, 'Voltas': 47, 'Pontos': 0.0, 'Tempo / diferença': 'Retired', 'Status': 'Retired', 'Melhor volta': '1:21.068', 'Volta mais rápida': False}, {'Posição': 20, 'Piloto': 'Valtteri Bottas', 'Código': 'BOT', 'Equipe': 'Cadillac F1 Team', 'team_id': 'cadillac', 'Grid': 21, 'Ganho de posições': 1, 'Voltas': 42, 'Pontos': 0.0, 'Tempo / diferença': 'Retired', 'Status': 'Retired', 'Melhor volta': '1:22.487', 'Volta mais rápida': False}, {'Posição': 21, 'Piloto': 'Lance Stroll', 'Código': 'STR', 'Equipe': 'Aston Martin', 'team_id': 'aston_martin', 'Grid': 19, 'Ganho de posições': -2, 'Voltas': 5, 'Pontos': 0.0, 'Tempo / diferença': 'Retired', 'Status': 'Retired', 'Melhor volta': '1:23.696', 'Volta mais rápida': False}, {'Posição': 22, 'Piloto': 'Fernando Alonso', 'Código': 'ALO', 'Equipe': 'Aston Martin', 'team_id': 'aston_martin', 'Grid': 17, 'Ganho de posições': -5, 'Voltas': 5, 'Pontos': 0.0, 'Tempo / diferença': 'Retired', 'Status': 'Retired', 'Melhor volta': '1:23.544', 'Volta mais rápida': False}]}, 'fotos': {'NOR': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png.transform/1col/image.png', 'cor': 'F47600'}, 'VER': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/1col/image.png', 'cor': '4781D7'}, 'BOR': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png.transform/1col/image.png', 'cor': 'F50537'}, 'HAD': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/I/ISAHAD01_Isack_Hadjar/isahad01.png.transform/1col/image.png', 'cor': '4781D7'}, 'GAS': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png.transform/1col/image.png', 'cor': '00A1E8'}, 'PER': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png.transform/1col/image.png', 'cor': '909090'}, 'ANT': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/K/ANDANT01_Kimi_Antonelli/andant01.png.transform/1col/image.png', 'cor': '00D7B6'}, 'ALO': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png.transform/1col/image.png', 'cor': '229971'}, 'LEC': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png.transform/1col/image.png', 'cor': 'ED1131'}, 'STR': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png.transform/1col/image.png', 'cor': '229971'}, 'ALB': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png.transform/1col/image.png', 'cor': '1868DB'}, 'HUL': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png.transform/1col/image.png', 'cor': 'F50537'}, 'LAW': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png.transform/1col/image.png', 'cor': '6C98FF'}, 'LIN': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ARVLIN01_Arvid_Lindblad/arvlin01.png.transform/1col/image.png', 'cor': '6C98FF'}, 'COL': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png.transform/1col/image.png', 'cor': '00A1E8'}, 'HAM': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png.transform/1col/image.png', 'cor': 'ED1131'}, 'HIR': {'foto': '', 'cor': '9C9FA2'}, 'SAI': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png.transform/1col/image.png', 'cor': '1868DB'}, 'RUS': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png.transform/1col/image.png', 'cor': '00D7B6'}, 'BOT': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png.transform/1col/image.png', 'cor': '909090'}, 'PIA': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png.transform/1col/image.png', 'cor': 'F47600'}, 'BEA': {'foto': 'https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png.transform/1col/image.png', 'cor': '9C9FA2'}}}
CORES_EQUIPES_F1 = {'mercedes':'00D2BE','ferrari':'EF3340','red_bull':'4781D7','mclaren':'FF8700',
                    'rb':'6692FF','racing_bulls':'6692FF','alpine':'EF76BE','haas':'C4CED6',
                    'audi':'F50537','williams':'64C4FF','aston_martin':'229971','cadillac':'A8B2C2'}


def _numero_publico_f1(valor,inteiro=False):
    from math import isfinite
    numero = float(valor)
    if not isfinite(numero) or numero<0 or (inteiro and not numero.is_integer()):
        raise ValueError('Valor inválido na fonte de F1.')
    return int(numero) if inteiro else numero


def _nome_publico_f1(piloto):
    if piloto.get('code')=='ANT':
        return 'Kimi Antonelli'
    return f"{piloto['givenName']} {piloto['familyName']}".strip()


def normalizar_fonte_f1(tipo,payload,ano):
    mr = payload['MRData']
    if tipo in ('pilotos','equipes'):
        tabela = mr['StandingsTable']
        if int(tabela['season'])!=int(ano):
            raise ValueError('A fonte respondeu com outra temporada.')
        listas = tabela.get('StandingsLists',[])
        ultimo = max(listas,key=lambda item:int(item['round'])) if listas else {}
        if ultimo and int(ultimo['season'])!=int(ano):
            raise ValueError('Lista de classificação de outra temporada.')
        registros = []
        for r in ultimo.get('DriverStandings' if tipo=='pilotos' else 'ConstructorStandings',[]):
            comum = {'Posição':_numero_publico_f1(r['position'],True),
                      'Pontos':_numero_publico_f1(r['points']),'Vitórias':_numero_publico_f1(r.get('wins',0),True)}
            if tipo=='pilotos':
                d = r['Driver'];equipes_f1 = r.get('Constructors',[])
                registros.append({**comum,'Piloto':_nome_publico_f1(d),'Código':d.get('code',''),
                                  'Número':d.get('permanentNumber',''),'Nacionalidade':d.get('nationality',''),
                                  'Equipe':' / '.join(e['name'] for e in equipes_f1),
                                  'driver_id':d['driverId'],'team_id':equipes_f1[-1].get('constructorId','') if equipes_f1 else ''})
            else:
                d = r['Constructor']
                registros.append({**comum,'Equipe':d['name'],'Nacionalidade':d.get('nationality',''),'team_id':d['constructorId']})
        registros.sort(key=lambda r:r['Posição'])
        return {'temporada':int(ano),'rodada':int(ultimo.get('round',0)),'registros':registros}
    tabela = mr['RaceTable']
    if int(tabela['season'])!=int(ano):
        raise ValueError('Resultado de outra temporada.')
    corridas = tabela.get('Races',[])
    corrida = max(corridas,key=lambda r:int(r['round'])) if corridas else {}
    registros = []
    for r in corrida.get('Results',[]):
        d = r['Driver'];e = r['Constructor'];grid = _numero_publico_f1(r.get('grid',0),True)
        posicao = _numero_publico_f1(r['position'],True)
        volta = r.get('FastestLap',{})
        registros.append({'Posição':posicao,'Piloto':_nome_publico_f1(d),'Código':d.get('code',''),
                          'Equipe':e['name'],'team_id':e['constructorId'],'Grid':grid or None,
                          'Ganho de posições':grid-posicao if grid else None,
                          'Voltas':_numero_publico_f1(r.get('laps',0),True),
                          'Pontos':_numero_publico_f1(r['points']),
                          'Tempo / diferença':r.get('Time',{}).get('time',r.get('status','—')),
                          'Status':r.get('status','Não informado'),
                          'Melhor volta':volta.get('Time',{}).get('time','—'),
                          'Volta mais rápida':str(volta.get('rank',''))=='1'})
    registros.sort(key=lambda r:r['Posição'])
    circuito = corrida.get('Circuit',{})
    return {'temporada':int(ano),'rodada':int(corrida.get('round',0)),
            'nome':corrida.get('raceName',''),'data':corrida.get('date',''),
            'hora':corrida.get('time',''),'circuito':circuito.get('circuitName',''),
            'circuit_id':circuito.get('circuitId',''),'registros':registros}


def _url_foto_f1(url):
    from urllib.parse import urlsplit
    parsed = urlsplit(str(url or ''))
    return str(url) if parsed.scheme=='https' and parsed.hostname=='media.formula1.com' else ''


def normalizar_fotos_f1(registros):
    import re
    if not isinstance(registros,list):
        raise ValueError('Metadados de fotos inválidos.')
    fotos = {}
    for r in registros:
        codigo = str(r.get('name_acronym','')).upper()
        if not re.fullmatch(r'[A-Z0-9]{2,4}',codigo):
            continue
        cor = str(r.get('team_colour',''))
        fotos[codigo] = {'foto':_url_foto_f1(r.get('headshot_url')),
                         'cor':cor if re.fullmatch(r'[a-fA-F0-9]{6}',cor) else '627693'}
    return fotos


def _http_json_f1(url):
    # Fonte pública: nunca reutilizar os headers com GITHUB_TOKEN do banco do bolão.
    req = urllib.request.Request(url,headers={'User-Agent':'BolaoF1-2026/1.0','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=8) as response:
        conteudo = response.read(4*1024*1024+1)
    if len(conteudo)>4*1024*1024:
        raise ValueError('Resposta pública maior que o esperado.')
    return json.loads(conteudo.decode('utf-8'))


@st.cache_resource
def _memoria_f1_publica():
    from threading import RLock
    return {'lock':RLock(),'dados':{},'tentativas':{}}


def _copia_f1_disponivel(tipo,ano,erro=None,memoria=None):
    from copy import deepcopy
    memoria = _memoria_f1_publica() if memoria is None else memoria
    with memoria['lock']:
        anterior = deepcopy(memoria['dados'].get((tipo,int(ano))))
    if anterior is not None:
        anterior['erro'] = erro
        return anterior
    backup = F1_BACKUP_2026.get(tipo) if int(ano)==2026 else None
    return {'dados':deepcopy(backup),'consultado_em':F1_BACKUP_2026.get('conferido_em') if backup is not None else None,
            'backup':backup is not None,'erro':erro}


def _consultar_f1_sem_cache(tipo,ano,memoria):
    from copy import deepcopy
    from time import monotonic
    if tipo not in ('pilotos','equipes','resultado') or not (1950<=int(ano)<=2100):
        raise ValueError('Consulta de F1 inválida.')
    chave = (tipo,int(ano))
    # Mesmo com vários usuários pressionando atualizar, não repetir o mesmo endpoint em menos de um minuto.
    with memoria['lock']:
        instante = monotonic()
        ultima = memoria['tentativas'].get(chave)
        if ultima is not None and instante-ultima<60:
            return _copia_f1_disponivel(tipo,ano,memoria=memoria)
        memoria['tentativas'][chave] = instante
    rotas = {'pilotos':'driverstandings','equipes':'constructorstandings','resultado':'last/results'}
    try:
        payload = _http_json_f1(f'{F1_API_BASE}/{int(ano)}/{rotas[tipo]}/?limit=100')
        dados = normalizar_fonte_f1(tipo,payload,int(ano))
        anterior = _copia_f1_disponivel(tipo,ano,memoria=memoria)['dados']
        if anterior and dados['rodada']<anterior['rodada']:
            raise ValueError('A fonte retornou uma rodada mais antiga.')
        pacote = {'dados':dados,'consultado_em':datetime.now(pytz.UTC).isoformat(),'backup':False,'erro':None}
        with memoria['lock']:
            memoria['dados'][chave] = deepcopy(pacote)
        return pacote
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError,TypeError,AttributeError):
        logger.warning('Consulta pública F1 indisponível: %s/%s',ano,tipo)
        return _copia_f1_disponivel(tipo,ano,'A fonte não respondeu com dados válidos nesta consulta.',memoria=memoria)


@st.cache_data(ttl=F1_INTERVALO_ATUALIZACAO,max_entries=12,show_spinner=False)
def consultar_f1_publica(tipo,ano):
    return _consultar_f1_sem_cache(tipo,ano,_memoria_f1_publica())


def _consultar_fotos_sem_cache(memoria):
    from time import monotonic
    with memoria['lock']:
        agora = monotonic()
        if agora-memoria.get('fotos_tentativa',-3601)<3600:
            return dict(memoria.get('fotos',F1_BACKUP_2026.get('fotos',{})))
        memoria['fotos_tentativa'] = agora
    try:
        fotos = normalizar_fotos_f1(_http_json_f1('https://api.openf1.org/v1/drivers?session_key=latest'))
        if fotos:
            with memoria['lock']:
                memoria['fotos'] = fotos
            return fotos
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError,TypeError,AttributeError):
        logger.warning('Fotos públicas da F1 indisponíveis nesta consulta.')
    with memoria['lock']:
        return dict(memoria.get('fotos',F1_BACKUP_2026.get('fotos',{})))


@st.cache_data(ttl=3600,max_entries=1,show_spinner=False)
def consultar_fotos_f1():
    return _consultar_fotos_sem_cache(_memoria_f1_publica())


@st.cache_data(ttl=F1_INTERVALO_ATUALIZACAO,max_entries=2,show_spinner=False)
def carregar_central_f1(ano):
    from concurrent.futures import ThreadPoolExecutor
    memoria = _memoria_f1_publica()
    # Só a busca HTTP roda em threads: cache e widgets ficam na thread do Streamlit.
    with ThreadPoolExecutor(max_workers=4) as pool:
        fotos = pool.submit(_consultar_fotos_sem_cache,memoria)
        futuros = {tipo:pool.submit(_consultar_f1_sem_cache,tipo,int(ano),memoria) for tipo in ('pilotos','equipes','resultado')}
        return {**{tipo:futuro.result() for tipo,futuro in futuros.items()},'fotos':fotos.result()}


F1_RELOGIO_HTML = '''<!doctype html><html><head><meta charset="utf-8"></head><body><script>
(function () {
  let timer = null, interval = 0, counter = 0;
  function send(type, data) { window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},data), '*'); }
  window.addEventListener('message', function (event) {
    if (event.source !== window.parent || !event.data || event.data.type !== 'streamlit:render') return;
    const args = event.data.args || {};
    counter = Math.max(counter, Number(args.counter) || 0);
    const next = Math.max(60000, Number(args.interval) || 300000);
    if (timer === null || next !== interval) {
      if (timer !== null) window.clearInterval(timer);
      interval = next;
      timer = window.setInterval(function () {
        if (!document.hidden) send('streamlit:setComponentValue', {value:++counter,dataType:'json'});
      }, interval);
    }
    send('streamlit:setFrameHeight', {height:0});
  });
  window.addEventListener('beforeunload',function () { if (timer !== null) window.clearInterval(timer); });
  send('streamlit:componentReady', {apiVersion:1});
})();
</script></body></html>'''


@st.cache_resource
def _pasta_relogio_f1():
    import tempfile
    from pathlib import Path
    pasta = Path(tempfile.mkdtemp(prefix='bolao_f1_refresh_'))
    (pasta/'index.html').write_text(F1_RELOGIO_HTML,encoding='utf-8')
    return str(pasta)


def ativar_relogio_f1(ano):
    import streamlit.components.v1 as componentes
    componente = componentes.declare_component('bolao_f1_atualizacao_publica',path=_pasta_relogio_f1())
    chave = f'f1_relogio_{ano}'
    valor = componente(interval=F1_INTERVALO_ATUALIZACAO*1000,counter=st.session_state.get(chave,0),default=0,key=chave)
    ultima = chave+'_processado'
    if isinstance(valor,int) and valor>st.session_state.get(ultima,0):
        # O relógio pode vencer antes do TTL por causa do tempo da primeira consulta.
        # Invalidar aqui garante nova tentativa a cada sinal de cinco minutos.
        carregar_central_f1.clear()
        st.session_state[ultima] = valor


def atualizar_central_f1():
    consultar_f1_publica.clear()
    carregar_central_f1.clear()


def avatar_piloto_f1(registro,fotos,tamanho='mini'):
    nome = registro['Piloto'];codigo = registro.get('Código','')
    iniciais = str(codigo or ''.join(p[0] for p in nome.split()[:2]))
    fundo = _svg_uri(f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" rx="50" fill="#293b58"/><text x="50" y="61" text-anchor="middle" font-family="sans-serif" font-size="28" fill="#f4f6fc">{escape(iniciais)}</text></svg>')
    url = foto_personalizada('Pilotos',nome) or _url_foto_f1(fotos.get(codigo,{}).get('foto',''))
    imagem = (f'url(&quot;{escape(url,quote=True)}&quot;), ' if url else '')+f'url(&quot;{fundo}&quot;)'
    return f'<span class="avatar avatar-{tamanho}" role="img" aria-label="{escape(nome,quote=True)}" style="background-image:{imagem};background-position:center top;"></span>'


def cor_equipe_f1(registro):
    return CORES_EQUIPES_F1.get(registro.get('team_id',''),'7387A2')


def indicador_fonte_f1(pacote,titulo):
    dados = pacote.get('dados')
    if dados is None:
        st.info(f'{titulo}: fonte indisponível nesta consulta. Tente atualizar mais tarde ou consulte os links oficiais.')
        return False
    quando = pacote.get('consultado_em')
    texto = agora_brasilia(datetime.fromisoformat(quando)).strftime('%d/%m/%Y %H:%M') if quando else 'não informada'
    if pacote.get('backup'):
        st.warning(f'{titulo}: exibindo cópia de referência conferida em {texto} (Brasília). A consulta atual ainda não confirmou dados novos.')
    elif pacote.get('erro'):
        st.warning(f'{titulo}: exibindo a última consulta bem-sucedida, de {texto} (Brasília). A fonte está temporariamente indisponível.')
    else:
        st.caption(f'{titulo} · temporada {dados["temporada"]} · rodada publicada {dados["rodada"]} · consulta em {texto} (Brasília).')
    return True


def pontos_publicos_f1(valor):
    from decimal import Decimal
    casas = max(0,-Decimal(str(valor)).normalize().as_tuple().exponent)
    return numero_br(valor,min(casas,3))


def _cartoes_lideres_f1(registros,fotos):
    for coluna,r in zip(st.columns(3),registros[:3]):
        with coluna:
            cor = cor_equipe_f1(r)
            st.markdown(f'<div class="f1-leader" style="border-top-color:#{cor}"><div class="eyebrow">{int(r["Posição"]):02d} / MUNDIAL DE PILOTOS</div>{avatar_piloto_f1(r,fotos,"large")}<h3>{escape(r["Piloto"])}</h3><p>{escape(r["Equipe"])}</p><strong>{pontos_publicos_f1(r["Pontos"])} <small>pontos</small></strong><span>{int(r["Vitórias"])} vitórias na temporada</span></div>',unsafe_allow_html=True)


def tabela_pilotos_f1(registros,fotos):
    if not registros:
        st.info('A fonte ainda não publicou classificação de pilotos nesta temporada.')
        return
    _cartoes_lideres_f1(registros,fotos)
    c1,c2 = st.columns(2)
    with c1:
        equipe = st.selectbox('Filtrar equipe',['Todas']+sorted({r['Equipe'] for r in registros}),key='f1_equipe')
    with c2:
        busca = st.text_input('Buscar piloto',key='f1_busca')
    filtrados = [r for r in registros if (equipe=='Todas' or r['Equipe']==equipe) and (not busca or busca.casefold() in (r['Piloto']+' '+r['Código']).casefold())]
    if not filtrados:
        st.info('Nenhum piloto encontrado com esses filtros.')
        return
    lider = max(r['Pontos'] for r in registros)
    linhas = []
    for r in filtrados:
        cor = cor_equipe_f1(r)
        linhas.append(f'<tr><td class="f1-pos">{int(r["Posição"])}</td><td><div class="f1-driver-name">{avatar_piloto_f1(r,fotos)}<div><strong>{escape(r["Piloto"])}</strong><small>#{escape(str(r["Número"]))} · {escape(r["Nacionalidade"])}</small></div></div></td><td><span class="f1-team-dot" style="background:#{cor}"></span>{escape(r["Equipe"])}</td><td>{r["Vitórias"]}</td><td class="f1-points">{pontos_publicos_f1(r["Pontos"])}</td><td>{pontos_publicos_f1(lider-r["Pontos"])}</td></tr>')
    st.markdown('<div class="f1-table-wrap"><table class="f1-table"><thead><tr><th>Pos.</th><th>Piloto</th><th>Equipe</th><th>Vitórias</th><th>Pontos</th><th>Distância do líder</th></tr></thead><tbody>'+''.join(linhas)+'</tbody></table></div>',unsafe_allow_html=True)
    st.caption('A posição segue a fonte, inclusive os critérios de desempate da F1. Fotos conforme disponibilidade; sem imagem, aparecem as iniciais.')
    with st.expander('Ver classificação em tabela para consulta'):
        df = pd.DataFrame(filtrados)
        st.dataframe(df[['Posição','Piloto','Número','Equipe','Nacionalidade','Pontos','Vitórias']],use_container_width=True,hide_index=True)


def tabela_equipes_f1(registros):
    if not registros:
        st.info('A fonte ainda não publicou classificação de construtores nesta temporada.')
        return
    maior = max(1,max(r['Pontos'] for r in registros))
    linhas = []
    for r in registros:
        cor = cor_equipe_f1(r)
        largura = min(100,100*r['Pontos']/maior)
        linhas.append(f'<div class="f1-constructor"><span class="f1-pos">{int(r["Posição"]):02d}</span><span class="f1-team-symbol" style="color:#{cor}">◈</span><div class="f1-constructor-name"><strong>{escape(r["Equipe"])}</strong><small>{r["Vitórias"]} vitórias · {escape(r["Nacionalidade"])}</small></div><div class="f1-team-bar"><span style="width:{largura:.2f}%;background:#{cor}"></span></div><b>{pontos_publicos_f1(r["Pontos"])} <small>pts</small></b></div>')
    st.markdown('<div class="f1-constructor-list">'+''.join(linhas)+'</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(registros)[['Posição','Equipe','Pontos','Vitórias','Nacionalidade']],use_container_width=True,hide_index=True)


def ultimo_resultado_f1(dados,fotos):
    registros = dados['registros']
    if not registros:
        st.info('A fonte ainda não publicou resultado de corrida nesta temporada.')
        return
    data = dados.get('data','')
    if data:
        if dados.get('hora'):
            instante = datetime.fromisoformat(data+'T'+dados['hora'].replace('Z','+00:00'))
            data = agora_brasilia(instante).strftime('%d/%m/%Y às %H:%M (Brasília)')
        else:
            data = datetime.strptime(data,'%Y-%m-%d').strftime('%d/%m/%Y')
    st.subheader(dados.get('nome') or 'Último Grande Prêmio publicado')
    st.caption(f'Rodada {dados["rodada"]} · {dados.get("circuito","")} · {data}')
    c1,c2,c3 = st.columns(3)
    c1.metric('Vencedor',registros[0]['Piloto'])
    melhor = next((r for r in registros if r['Volta mais rápida']),None)
    c2.metric('Volta mais rápida',melhor['Melhor volta'] if melhor else 'Não informada')
    maiores = [r for r in registros if r['Ganho de posições'] is not None]
    destaque = max(maiores,key=lambda r:r['Ganho de posições']) if maiores else None
    c3.metric('Maior avanço no resultado',f'+{destaque["Ganho de posições"]}' if destaque and destaque['Ganho de posições']>0 else '—')
    if melhor:
        st.caption(f'Volta mais rápida: {melhor["Piloto"]}. O painel exibe os pontos informados pela fonte, sem adicionar bônus próprios.')
    if destaque and destaque['Ganho de posições']>0:
        st.caption(f'Maior avanço entre grid e chegada: {destaque["Piloto"]}. Essa diferença não é uma contagem de ultrapassagens na pista.')
    linhas = []
    for r in registros:
        ganho = '—' if r['Ganho de posições'] is None else f'{r["Ganho de posições"]:+d}'
        linhas.append(f'<tr><td class="f1-pos">{int(r["Posição"])}</td><td><div class="f1-driver-name">{avatar_piloto_f1(r,fotos)}<div><strong>{escape(r["Piloto"])}</strong><small>{escape(r["Equipe"])}</small></div></div></td><td>{r["Grid"] if r["Grid"] else "—"}</td><td>{ganho}</td><td>{r["Voltas"]}</td><td>{escape(r["Tempo / diferença"])}</td><td>{escape(r["Status"])}</td><td class="f1-points">{pontos_publicos_f1(r["Pontos"])}</td></tr>')
    st.markdown('<div class="f1-table-wrap"><table class="f1-table"><thead><tr><th>Chegada</th><th>Piloto</th><th>Grid</th><th>Ganho</th><th>Voltas</th><th>Tempo / diferença</th><th>Status</th><th>Pontos</th></tr></thead><tbody>'+''.join(linhas)+'</tbody></table></div>',unsafe_allow_html=True)
    with st.expander('Consultar detalhes do resultado'):
        st.dataframe(pd.DataFrame(registros)[['Posição','Piloto','Equipe','Grid','Ganho de posições','Voltas','Pontos','Tempo / diferença','Status','Melhor volta']],use_container_width=True,hide_index=True)


def tela_formula1():
    hero('O mundial passa por aqui.', 'Pilotos, construtores e o último resultado publicado da Fórmula 1, em um só lugar.', 'CENTRAL FÓRMULA 1')
    ano_atual = agora_brasilia().year
    c1,c2 = st.columns(2)
    with c1:
        ano = st.selectbox('Temporada F1',[ano_atual,ano_atual-1],key='f1_temporada')
    with c2:
        automatico = st.checkbox('Atualizar a cada 5 minutos enquanto aberto',value=True,key='f1_automatico')
    st.button('↻ Consultar atualização da F1',on_click=atualizar_central_f1,key='f1_atualizar',use_container_width=True)
    if automatico:
        try:
            ativar_relogio_f1(ano)
        except (OSError,RuntimeError):
            st.info('A atualização contínua não iniciou nesta sessão. Você pode usar o botão de atualização.')
    with st.spinner('Consultando o mundial de Fórmula 1…'):
        pacotes = carregar_central_f1(ano)
    fotos = pacotes.get('fotos',{})
    pilotos_f1 = pacotes['pilotos'].get('dados')
    equipes_f1 = pacotes['equipes'].get('dados')
    resultado_f1 = pacotes['resultado'].get('dados')
    c1,c2,c3 = st.columns(3)
    c1.metric('Temporada',str(ano))
    c2.metric('Pilotos na classificação',len(pilotos_f1['registros']) if pilotos_f1 else '—')
    c3.metric('Construtores',len(equipes_f1['registros']) if equipes_f1 else '—')
    st.caption('Consulta automática após a publicação pela fonte. Não é cronometragem ao vivo: resultados e revisões podem levar tempo para aparecer. Navegadores podem pausar a atualização em abas em segundo plano.')
    rodadas = {d['rodada'] for d in (pilotos_f1,equipes_f1,resultado_f1) if d and d['rodada']}
    if len(rodadas)>1:
        st.info('Os quadros estão em etapas diferentes de publicação. Confira a rodada informada em cada seção; isso também pode ocorrer durante um fim de semana com Sprint.')
    painel = st.radio('Explorar Fórmula 1',['Pilotos','Construtores','Última corrida'],horizontal=True,key='f1_painel')
    tipo = {'Pilotos':'pilotos','Construtores':'equipes','Última corrida':'resultado'}[painel]
    if indicador_fonte_f1(pacotes[tipo],painel):
        dados = pacotes[tipo]['dados']
        if painel=='Pilotos':
            tabela_pilotos_f1(dados['registros'],fotos)
        elif painel=='Construtores':
            tabela_equipes_f1(dados['registros'])
        else:
            ultimo_resultado_f1(dados,fotos)
    st.markdown(f'[Classificação oficial de pilotos](https://www.formula1.com/en/results/{ano}/drivers) · [Classificação oficial de equipes](https://www.formula1.com/en/results/{ano}/team)')
    st.caption('Dados: Jolpica-F1 · licença CC BY-NC-SA 4.0. Fotos: OpenF1 / Formula 1, conforme disponibilidade. Este painel é informativo; os gabaritos e a pontuação do bolão continuam sendo homologados pelo administrador.')
    st.markdown('[Fonte dos dados e licença](https://github.com/jolpica/jolpica-f1) · [Sobre as fotos](https://openf1.org/)')


def main():
    st.set_page_config(page_title='Bolão F1 2026 · Na disputa',page_icon='🏁',layout='wide',initial_sidebar_state='collapsed')
    menu = cabecalho()
    st.caption('🏁 Abra a lateral no canto superior esquerdo para consultar o manual de pontuação.')
    if not GITHUB_TOKEN and menu!='Fórmula 1':
        st.error('A variável GITHUB_TOKEN não foi encontrada nas configurações de ambiente.')
        return
    if st.session_state.get('mensagem_sucesso'):
        st.success(st.session_state.pop('mensagem_sucesso'))
    with st.sidebar:
        st.markdown('### Central do campeonato')
        st.caption('Atualize para conferir os últimos palpites e resultados homologados.')
        if st.button('Atualizar dados agora',use_container_width=True):
            _ler_dados_cache.clear()
            st.rerun()
        manual_pontuacao()
    try:
        {'Enviar Palpite':tela_enviar,'Meus Palpites':tela_meus_palpites,
         'Classificações':tela_classificacoes,'Administrador':tela_admin,'Fórmula 1':tela_formula1}[menu]()
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        logger.exception('Falha ao carregar tela')
        st.error('Não foi possível carregar os dados. Verifique a conexão, a configuração de acesso e as colunas dos CSVs e tente atualizar.')
    st.markdown('<div class="footer">BOLÃO F1 2026 · A EMOÇÃO DA CORRIDA CONTINUA NO SEU PALPITE.</div>',unsafe_allow_html=True)


if __name__ == '__main__':
    main()
