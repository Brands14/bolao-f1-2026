elif menu == "🏎️ Fazer Palpite":
        st.header("🏎️ Registrar seu Palpite")
        
        # --- FILTRO DE SEGURANÇA: MOSTRAR APENAS GPS FUTUROS ---
        # Pega a data de hoje no fuso de SP
        data_hoje = datetime.now(pytz.timezone("America/Sao_Paulo")).date()
        
        # Filtra a lista_gps comparando com o cronograma_gps que você definiu no início do código
        gps_disponiveis = [gp for gp in lista_gps if cronograma_gps[gp].date() >= data_hoje]
        
        # Se todos os GPs já passaram, mostra o último para não dar erro no sistema
        if not gps_disponiveis:
            gps_disponiveis = [lista_gps[-1]]

        # Criar as colunas para os seletores
        col1, col2 = st.columns(2)
        
        with col1:
            gp_escolhido = st.selectbox("Selecione o Grande Prêmio (Próximas Corridas):", gps_disponiveis)
        
        with col2:
            sessao = st.selectbox("Sessão:", ["Classificação Principal (Pole)", "Corrida Principal", "Qualy Sprint (Pole)", "Corrida Sprint"])

        # Verificação de horário (30 min antes)
        agora = datetime.now(pytz.timezone("America/Sao_Paulo"))
        limite = cronograma_gps[gp_escolhido].replace(tzinfo=pytz.timezone("America/Sao_Paulo"))
        restante = limite - agora
        
        if restante.total_seconds() < 1800:
            st.error(f"❌ Prazo encerrado! Os palpites para o {gp_escolhido} fecharam 30 minutos antes do início.")
        else:
            st.info(f"⏳ Você tem até {limite.strftime('%d/%m %H:%M')} para enviar/alterar seu palpite.")
            
            with st.form("form_palpite", clear_on_submit=False):
                u_nome = st.text_input("Seu Nome/Apelido (Igual ao cadastro):").strip()
                u_equipe = st.text_input("Sua Equipe (Ex: Ferrari, Red Bull):").strip()
                
                st.write("---")
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
                
                v_rapida = st.selectbox("⏱️ Volta Rápida (Apenas para Corrida Principal):", ["N/A"] + lista_pilotos)
                
                submit = st.form_submit_button("ENVIAR PALPITE")
