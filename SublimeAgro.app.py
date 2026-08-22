import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SUBLIME Agro - Cadastro", layout="wide", page_icon="🌱")

# CSS simples
st.markdown("""
<style>
.stApp {background:#0f2315}
h1,h2,h3,p,label {color:white !important}
div[data-testid="stForm"] {background:#1a3a24; border-radius:15px; padding:20px}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def conectar():
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "\\n" in creds_dict["private_key"]:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scope = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

sh = conectar()

# Cria abas se não existir
def get_or_create_ws(nome, headers):
    try:
        ws = sh.worksheet(nome)
    except:
        ws = sh.add_worksheet(title=nome, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws

HEADERS_CLIENTES = ["ID","Data","Nome/Fazenda","Tipo","CPF/CNPJ","Telefone","Cidade","UF","Endereco","Contato","Status"]
HEADERS_FORNEC = ["ID","Data","Nome/Empresa","Tipo","CPF/CNPJ","Telefone","Cidade","UF","Endereco","Produto","Status"]

ws_clientes = get_or_create_ws("Clientes", HEADERS_CLIENTES)
ws_fornec = get_or_create_ws("Fornecedores", HEADERS_FORNEC)

with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.caption("Cadastro v1.0 - Zero")
    menu = st.radio("Menu", ["➕ Cadastrar Cliente", "🏭 Cadastrar Fornecedor", "📋 Ver Cadastros"])

if menu == "➕ Cadastrar Cliente":
    st.title("➕ Cadastrar Cliente")
    
    with st.form("form_cliente", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome / Fazenda *", placeholder="Ex: Fazenda Morro da Lua")
            tipo = st.selectbox("Tipo *", ["Fazenda de Gado","Confinamento","Fábrica de Ração","Cooperativa","Frigorífico","Produtor Rural","Outro"])
            doc = st.text_input("CPF / CNPJ")
            telefone = st.text_input("Telefone *", placeholder="(66) 99928-3411")
        with c2:
            cidade = st.text_input("Cidade *", placeholder="Rondonópolis")
            uf = st.text_input("UF *", max_chars=2, placeholder="MT")
            endereco = st.text_input("Endereço / Rodovia")
            contato = st.text_input("Nome do Contato na Fazenda")

        status = st.selectbox("Status", ["Ativo","Prospect","Inativo"])
        obs = st.text_area("Observação", height=80)

        salvar = st.form_submit_button("💾 Salvar Cliente", type="primary", use_container_width=True)

        if salvar:
            if not nome or not telefone or not cidade or not uf:
                st.error("Preencha os campos com *")
            else:
                id_gerado = datetime.now().strftime("%y%m%d%H%M%S")
                data = datetime.now().strftime("%d/%m/%Y %H:%M")
                linha = [id_gerado, data, nome, tipo, doc, telefone, cidade, uf.upper(), endereco, contato, status]
                ws_clientes.append_row(linha)
                st.success(f"✅ Cliente {nome} salvo com sucesso!")
                st.balloons()

elif menu == "🏭 Cadastrar Fornecedor":
    st.title("🏭 Cadastrar Fornecedor")

    with st.form("form_fornec", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome / Empresa *", placeholder="Ex: Nutrição Animal LTDA")
            tipo = st.selectbox("Tipo *", ["Insumos","Ração/Concentrado","Medicamentos","Maquinário","Transporte","Outro"])
            doc = st.text_input("CNPJ")
            telefone = st.text_input("Telefone *", placeholder="(11) 99999-9999")
        with c2:
            cidade = st.text_input("Cidade *")
            uf = st.text_input("UF *", max_chars=2)
            endereco = st.text_input("Endereço")
            produto = st.text_input("Produto/Serviço Principal")

        status = st.selectbox("Status", ["Ativo","Em Avaliação","Inativo"])

        salvar = st.form_submit_button("💾 Salvar Fornecedor", type="primary", use_container_width=True)

        if salvar:
            if not nome or not telefone or not cidade or not uf:
                st.error("Preencha os campos com *")
            else:
                id_gerado = datetime.now().strftime("%y%m%d%H%M%S")
                data = datetime.now().strftime("%d/%m/%Y %H:%M")
                linha = [id_gerado, data, nome, tipo, doc, telefone, cidade, uf.upper(), endereco, produto, status]
                ws_fornec.append_row(linha)
                st.success(f"✅ Fornecedor {nome} salvo!")
                st.balloons()

else: # Ver Cadastros
    st.title("📋 Cadastros")
    aba = st.radio("Ver:", ["Clientes","Fornecedores"], horizontal=True)

    if aba == "Clientes":
        dados = ws_clientes.get_all_records()
        if dados:
            df = pd.DataFrame(dados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 Baixar Clientes CSV", df.to_csv(index=False), "clientes.csv", use_container_width=True)
        else:
            st.info("Nenhum cliente cadastrado ainda")
    else:
        dados = ws_fornec.get_all_records()
        if dados:
            df = pd.DataFrame(dados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 Baixar Fornecedores CSV", df.to_csv(index=False), "fornecedores.csv", use_container_width=True)
        else:
            st.info("Nenhum fornecedor cadastrado ainda")
