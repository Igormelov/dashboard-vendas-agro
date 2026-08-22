import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="SUBLIME Agro - Clientes", layout="wide", page_icon="🌱")

st.markdown("""
<style>
.stApp {background:#212121!important}
h1,h2,h3,p,label,span {color:#e0e0e0!important}
[data-testid="stSidebar"] {background:#1a1a1a!important; border-right:1px solid #333}
div[data-testid="stVerticalBlock"] {gap:0!important}
div[data-testid="stHorizontalBlock"] {gap:0!important; padding:0!important; margin:0!important; align-items:center!important}
div[data-testid="column"] {padding:0 8px!important; display:flex; align-items:center; height:38px}
div[data-testid="stButton"] button {height:22px!important; min-height:22px!important; width:28px!important; padding:0!important; margin:0!important; border-radius:6px!important; border:1px solid #3a3a3a!important; background:#2e2e2e!important; color:#bbb!important}
div[data-testid="stButton"] button:hover {background:#3a3a3a!important; color:white!important}

/* CONTAINER MAIS ABAIXO */
.tabela-wrapper {margin-top:28px}
.tabela-container {
    border:1px solid #3a3a3a;
    border-radius:8px;
    overflow:hidden;
    background:#1e1e1e;
}
.tabela-header {
    display:flex; align-items:center; background:#1a1a1a; color:#8a8a8a;
    height:38px; padding:0 8px; font-size:11px; font-weight:600; letter-spacing:0.5px; text-transform:uppercase;
    border-bottom:1px solid #3a3a3a;
}
.row {
    display:flex; align-items:center; height:38px; /* altura fixa = alinhado perfeito no meio da linha */
    background:#212121;
    border-bottom:1px solid #2f2f2f;
}
.row:hover {background:#2a2a2a}
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
ws = sh.worksheet("Clientes")

@st.cache_data(ttl=30)
def carregar():
    return pd.DataFrame(ws.get_all_records()) if ws.get_all_records() else pd.DataFrame()

df = carregar()

@st.dialog("Detalhes do Cliente", width="large")
def modal_cliente(cliente):
    st.markdown(f"<h3 style='color:white; margin:0'>{cliente.get('Nome','')}</h3>", unsafe_allow_html=True)
    st.divider()
    c1,c2 = st.columns(2)
    for i,(k,v) in enumerate(cliente.items()):
        if str(v).strip()=="": v="-"
        (c1 if i%2==0 else c2).markdown(f"**{k}:** {v}")
    if st.button("Fechar", use_container_width=True, key="fecharmodal"):
        st.rerun()

with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.radio("Menu", ["Clientes"], label_visibility="collapsed")

busca_col, novo_col = st.columns([4,1])
with busca_col:
    busca = st.text_input("", placeholder="🔍 Buscar por nome, código, CPF/CNPJ, cidade...", label_visibility="collapsed")
with novo_col:
    st.button("＋ Novo Cliente", use_container_width=True)

df_f = df.copy()
if not df_f.empty and busca:
    b = busca.lower()
    df_f = df_f[df_f.astype(str).apply(lambda x: x.str.lower().str.contains(b, na=False)).any(axis=1)]

# TABELA MAIS ABAIXO
st.markdown('<div class="tabela-wrapper"><div class="tabela-container">', unsafe_allow_html=True)
st.markdown("""
<div class="tabela-header">
    <div style="width:80px; padding-left:8px">Código</div>
    <div style="flex:1.5">Nome</div>
    <div style="width:180px">CPF/CNPJ</div>
    <div style="width:180px">Cidade</div>
    <div style="width:150px">Telefone</div>
    <div style="width:40px"></div>
</div>
""", unsafe_allow_html=True)

if df_f.empty:
    st.markdown("<div style='padding:30px; text-align:center; color:#777; height:38px; display:flex; align-items:center; justify-content:center'>Nenhum cliente encontrado</div>", unsafe_allow_html=True)
else:
    col_id = "ID" if "ID" in df_f.columns else df_f.columns[0]
    col_nome = "Nome" if "Nome" in df_f.columns else df_f.columns[1]
    col_doc = "CPF_CNPJ" if "CPF_CNPJ" in df_f.columns else "CPF/CNPJ" if "CPF/CNPJ" in df_f.columns else None
    col_cidade = "Cidade" if "Cidade" in df_f.columns else None
    col_tel = "Telefone" if "Telefone" in df_f.columns else None

    for idx, row in df_f.head(200).iterrows():
        id_val = str(row.get(col_id,""))[:8]
        nome_val = str(row.get(col_nome,""))[:55]
        doc_val = str(row.get(col_doc,"")) if col_doc else ""
        cidade_val = str(row.get(col_cidade,"")) if col_cidade else ""
        tel_val = str(row.get(col_tel,"")) if col_tel else ""

        ca, cb, cc, cd, ce, cf = st.columns([0.8, 3.5, 1.8, 1.8, 1.5, 0.4])
        with ca:
            st.markdown(f"<div style='color:#8a8a8a; font-size:12px; width:100%'>{id_val}</div>", unsafe_allow_html=True)
        with cb:
            st.markdown(f"<div style='color:white; font-size:13px; font-weight:500; width:100%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis'>{nome_val}</div>", unsafe_allow_html=True)
        with cc:
            st.markdown(f"<div style='color:#c0c0c0; font-size:12px; width:100%'>{doc_val}</div>", unsafe_allow_html=True)
        with cd:
            st.markdown(f"<div style='color:#c0c0c0; font-size:12px; width:100%'>{cidade_val}</div>", unsafe_allow_html=True)
        with ce:
            st.markdown(f"<div style='color:#c0c0c0; font-size:12px; width:100%'>{tel_val}</div>", unsafe_allow_html=True)
        with cf:
            if st.button("⋮", key=f"b_{id_val}_{idx}_v16"):
                modal_cliente(row)

        st.markdown('<div style="border-bottom:1px solid #3a3a3a"></div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)
