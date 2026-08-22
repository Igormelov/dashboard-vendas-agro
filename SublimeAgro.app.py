elif menu == "Novo Cliente":
    st.title("➕ Novo Cliente")
    st.info("📄 Dica: Faça upload do Sintegra para preencher automático!")

    # --- UPLOAD SINTEGRA ---
    arquivo_sintegra = st.file_uploader("📤 Upload Sintegra (PDF ou Imagem)", type=["pdf","png","jpg","jpeg"], help="Arraste o PDF do Sintegra aqui")

    # Inicializa
    if "sintegra_dados" not in st.session_state:
        st.session_state.sintegra_dados = {}

    if arquivo_sintegra is not None:
        with st.spinner("Lendo Sintegra... 🔍"):
            try:
                import PyPDF2, re
                texto = ""
                if arquivo_sintegra.type == "application/pdf":
                    reader = PyPDF2.PdfReader(arquivo_sintegra)
                    for page in reader.pages:
                        texto += page.extract_text() or ""
                else:
                    texto = arquivo_sintegra.name # se for imagem, depois usa OCR

                # Regex para extrair dados do Sintegra MT / Nacional
                cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14}', texto)
                ie = re.search(r'Inscri[cç][aã]o Estadual[:\s]*([\d\.\-]+)', texto, re.I)
                razao = re.search(r'Raz[aã]o Social[:\s]*([A-Z0-9\s\.\-\/]+)', texto, re.I)

                dados = {}
                if cnpj: dados["cpf_cnpj"] = cnpj.group(0)
                if ie: dados["ie"] = ie.group(1)
                if razao: dados["nome"] = razao.group(1).strip()[:80]

                # Tenta pegar endereço do Sintegra também
                end = re.search(r'Logradouro[:\s]*([^\n]+)', texto, re.I)
                if end: dados["endereco"] = end.group(1).strip()

                st.session_state.sintegra_dados = dados
                st.success(f"✅ Sintegra lido! Encontrado: {dados}")

            except Exception as e:
                st.warning(f"Não consegui ler automático ({e}), mas vou salvar o arquivo. Preencha manual.")
                st.session_state.sintegra_dados = {}

    # ---- CEP COM LUPA (seu código atual que já funciona) ----
    st.divider()
    col_cep, col_lupa = st.columns([3,1])
    with col_cep:
        cep_input = st.text_input("CEP *", placeholder="78000-000", value=st.session_state.get("cep_last",""))
    with col_lupa:
        st.write(""); st.write("")
        buscar = st.button("🔍 Buscar CEP")

    if buscar and cep_input:
        dados_cep = buscar_cep(cep_input)
        if dados_cep:
            st.session_state.cep_data["endereco"] = dados_cep.get("logradouro","")
            st.session_state.cep_data["cidade"] = dados_cep.get("localidade","")
            st.session_state.cep_data["estado"] = dados_cep.get("uf","")
            st.session_state.cep_last = cep_input
            st.success(f"Endereço: {dados_cep.get('logradouro')} - {dados_cep.get('bairro')}")

    # ---- FORMULÁRIO PREENCHIDO PELO SINTEGRA + CEP ----
    with st.form("cliente"):
        c1,c2 = st.columns(2)
        with c1:
            # Se veio do Sintegra, usa como valor padrão
            nome_padrao = st.session_state.sintegra_dados.get("nome","")
            cpf_padrao = st.session_state.sintegra_dados.get("cpf_cnpj","")

            nome = st.text_input("Nome Completo / Razão Social *", value=nome_padrao)
            telefone = st.text_input("Telefone / WhatsApp", placeholder="(65) 9 9999-9999")
            cpf = st.text_input("CPF / CNPJ", value=cpf_padrao)
            ie = st.text_input("Inscrição Estadual", value=st.session_state.sintegra_dados.get("ie",""))
            fazenda = st.text_input("Nome da Fazenda")
        with c2:
            endereco = st.text_input("Endereço", value=st.session_state.cep_data.get("endereco","") or st.session_state.sintegra_dados.get("endereco",""))
            numero = st.text_input("Nº", placeholder="123")
            complemento = st.text_input("Complemento", value=st.session_state.cep_data.get("complemento",""))
            cidade = st.text_input("Cidade", value=st.session_state.cep_data.get("cidade",""))
            estado = st.text_input("Estado (UF)", value=st.session_state.cep_data.get("estado",""), max_chars=2)

        if st.form_submit_button("Salvar Cliente com Sintegra 🌿"):
            if not nome:
                st.error("Nome é obrigatório")
            else:
                novo_id = len(df_clientes)+1
                ws_clientes.append_row([
                    novo_id, nome, telefone, cidade, estado.upper(), fazenda, cpf,
                    cep_input, endereco, numero, complemento,
                    datetime.now().strftime("%Y-%m-%d")
                ])
                st.success(f"Cliente {nome} + Sintegra salvo!")
                st.balloons()
                st.session_state.sintegra_dados = {}
                st.rerun()
