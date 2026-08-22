import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SUBLIME Agro - Clientes", layout="wide", page_icon="🌱")

st.markdown("""
<style>
.stApp {background:#0f2315}
h1,h2,h3,p,label {color:white !important}
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div {background:#1a3a24 !important; color:white !important}
div[data-testid="stForm"] {background:#1a3a24; border-radius:15px; padding:20px; border:1px solid #2a5a35}
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

HEADERS = ["ID","Data","Nome/Fazenda","Tipo","CPF/CNPJ","Telefone","Cidade","UF","Endereco","Contato","Status"]

def get_or_create_ws():
    try:
        ws = sh.worksheet("Clientes")
    except:
        ws = sh.add_worksheet(title="Clientes", rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)
    return ws

ws = get_or_create_ws()

with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.caption("Cadastro v1.0 - Zero")
    st.markdown("**Menu**")
    menu = st.radio("", ["Clientes"], label_visibility="collapsed")

# --- TELA CLIENTES COM BUSCA ---
st.title("👥 Clientes")

# Carrega dados
@st.cache_data(ttl=30)
def carregar_dados():
    dados = ws.get_all_records()
    return pd.DataFrame(dados) if dados else pd.DataFrame(columns=HEADERS)

df = carregar_dados()

# Barra de busca
c1,c2,c3 = st.columns([3,1,1])
with c1:
    busca = st.text_input("🔍 Buscar cliente", placeholder="Digite nome, fazenda, cidade, telefone...", label_visibility="collapsed")
with c2:
    filtro_tipo = st.selectbox("Tipo", ["Todos"] + ["Fazenda de Gado","Confinamento","Fábrica de Ração","Cooperativa","Frigorífico","Produtor Rural","Outro"], label_visibility="collapsed")
with c3:
    filtro_status = st.selectbox("Status", ["Todos","Ativo","Prospect","Inativo"], label_visibility="collapsed")

# Aplica filtros
df_filtrado = df.copy()
if not df_filtrado.empty:
    if busca:
        busca_lower = busca.lower()
        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: busca_lower in str(row["Nome/Fazenda"]).lower() or busca_lower in str(row["Cidade"]).lower() or busca_lower in str(row["Telefone"]).lower() or busca_lower in str(row["CPF/CNPJ"]).lower(), axis=1)]
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]

# Métricas
m1,m2,m3 = st.columns(3)
m1.metric("Total", len(df))
m2.metric("Filtrados", len(df_filtrado))
m3.metric("Ativos", len(df[df["Status"]=="Ativo"]) if not df.empty and "Status" in df.columns else 0)

st.divider()

# Lista
if df_filtrado.empty:
    if df.empty:
        st.info("📭 Nenhum cliente cadastrado ainda. Clique em 'Novo Cliente' abaixo.")
    else:
        st.warning(f"Nenhum resultado para '{busca}'")
else:
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True, height=400)

# Formulário de cadastro expansível
with st.expander("➕ Novo Cliente", expanded=df.empty):
    with st.form("form_cliente", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome / Fazenda *")
            tipo = st.selectbox("Tipo *", ["Fazenda de Gado","Confinamento","Fábrica de Ração","Cooperativa","Frigorífico","Produtor Rural","Outro"])
            doc = st.text_input("CPF / CNPJ")
            telefone = st.text_input("Telefone *", placeholder="(66) 99999-9999")
        with c2:
            cidade = st.text_input("Cidade *")
            uf = st.text_input("UF *", max_chars=2)
            endereco = st.text_input("Endereço / Rodovia")
            contato = st.text_input("Contato na Fazenda")

        status = st.selectbox("Status", ["Ativo","Prospect","Inativo"])
        
        salvar = st.form_submit_button("💾 Salvar Cliente", type="primary", use_container_width=True)
        if salvar:
            if not nome or not telefone or not cidade or not uf:
                st.error("Preencha Nome, Telefone, Cidade e UF")
            else:
                id_gerado = datetime.now().strftime("%y%m%d%H%M%S")
                data = datetime.now().strftime("%d/%m/%Y %H:%M")
                linha = [id_gerado, data, nome, tipo, doc, telefone, cidade, uf.upper(), endereco, contato, status]
                ws.append_row(linha)
                st.cache_data.clear()
                st.success(f"✅ {nome} salvo!")
                st.rerun()
