import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SUBLIME Agro - Clientes", layout="wide", page_icon="🌱")

st.markdown("""
<style>
.stApp {background:#0f2315}
h1,h2,h3,p,label {color:white!important}
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

# Usa a aba Clientes que já existe (com seus headers atuais)
ws = sh.worksheet("Clientes")

@st.cache_data(ttl=30)
def carregar_dados():
    dados = ws.get_all_records()
    return pd.DataFrame(dados) if dados else pd.DataFrame()

df = carregar_dados()

# Modal de detalhes
@st.dialog("📋 Detalhes do Cliente", width="large")
def mostrar_detalhes(cliente):
    c1,c2 = st.columns(2)
    for col in cliente.index:
        val = cliente[col]
        if pd.isna(val) or str(val).strip() == "":
            val = "-"
        # Coloca 2 colunas
        if list(cliente.index).index(col) % 2 == 0:
            with c1: st.markdown(f"**{col}:** {val}")
        else:
            with c2: st.markdown(f"**{col}:** {val}")

    st.divider()
    tel = str(cliente.get("Telefone","")).replace(" ","").replace("(","").replace(")","").replace("-","")
    if tel:
        st.link_button(f"📱 WhatsApp: {cliente.get('Telefone')}", f"https://wa.me/55{tel}", use_container_width=True)

    if st.button("Fechar", use_container_width=True):
        st.rerun()

with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.caption("Cadastro v1.0 - Zero")
    st.markdown("**Menu**")
    st.radio("", ["Clientes"], label_visibility="collapsed")

st.title("👥 Clientes")

# Busca
busca = st.text_input("🔍 Buscar cliente", placeholder="Digite nome, CPF/CNPJ, telefone...", label_visibility="collapsed")

df_filtrado = df.copy()
if not df_filtrado.empty and busca:
    b = busca.lower()
    # busca em todas as colunas de texto
    mask = df_filtrado.astype(str).apply(lambda x: x.str.lower().str.contains(b, na=False)).any(axis=1)
    df_filtrado = df_filtrado[mask]

# Métricas
if not df.empty:
    m1,m2 = st.columns(2)
    m1.metric("Total de Clientes", len(df))
    m2.metric("Filtrados", len(df_filtrado))
    st.divider()

# TABELA SIMPLIFICADA: só ID, Nome, CPF/CNPJ e Telefone
if df_filtrado.empty:
    st.info("Nenhum cliente encontrado" if not df.empty else "Nenhum cliente cadastrado")
else:
    # Detecta nome das colunas (seu sheet tem Nome e CPF_CNPJ)
    col_id = "ID" if "ID" in df_filtrado.columns else df_filtrado.columns[0]
    col_nome = "Nome" if "Nome" in df_filtrado.columns else "Nome/Fazenda" if "Nome/Fazenda" in df_filtrado.columns else df_filtrado.columns[1]
    col_doc = "CPF_CNPJ" if "CPF_CNPJ" in df_filtrado.columns else "CPF/CNPJ" if "CPF/CNPJ" in df_filtrado.columns else None
    col_tel = "Telefone" if "Telefone" in df_filtrado.columns else None

    cols_mostrar = [c for c in [col_id, col_nome, col_doc, col_tel] if c and c in df_filtrado.columns]
    df_tabela = df_filtrado[cols_mostrar].copy()

    # Adiciona coluna de ação
    st.dataframe(df_tabela, use_container_width=True, hide_index=True, height=450)

    # Seleção para abrir detalhes
    st.markdown("#### 👆 Clique para ver detalhes")
    opcoes = [f"{row[col_id]} - {row[col_nome]}" for _, row in df_filtrado.iterrows()]
    selecionado = st.selectbox("Selecione o cliente", ["Selecione..."] + opcoes, label_visibility="collapsed")

    if selecionado!= "Selecione...":
        id_selecionado = selecionado.split(" - ")[0]
        cliente = df_filtrado[df_filtrado[col_id].astype(str) == id_selecionado].iloc[0]
        mostrar_detalhes(cliente)
