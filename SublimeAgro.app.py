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
div[data-testid="stVerticalBlock"] {gap: 0.15rem!important}
div[data-testid="stHorizontalBlock"] {gap: 0rem!important; padding:0!important; margin:0!important}
div[data-testid="column"] {padding:2px 8px!important}
div[data-testid="stButton"] button {height:24px!important; min-height:24px!important; padding:0 8px!important; margin:0!important; border-radius:6px!important; border:1px solid #3a3a3a!important; background:#2e2e2e!important; color:#bbb!important}
div[data-testid="stButton"] button:hover {background:#3a3a3a!important; color:white!important; border-color:#555!important}

/* CONTAINER DA TABELA - ENQUADRADO */
.tabela-container {
    margin-top:18px; /* mais abaixo */
    border:1px solid #3a3a3a; /* borda clara ao redor */
    border-radius:8px;
    overflow:hidden;
    background:#1e1e1e;
}
.tabela-header {
    display:flex; background:#1a1a1a; color:#9e9e9e;
    padding:10px 12px; font-size:12px; font-weight:500;
    border-bottom:1px solid #3a3a3a; /* linha mais clara */
}
.linha-separadora {
    border-bottom:1px solid #3a3a3a; /* linha clara entre contatos */
}
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
    dados = ws.get_all_records()
    return pd.DataFrame(dados) if dados else pd.DataFrame()

df = carregar()

@st.dialog("Detalhes do Cliente", width="large")
def modal_cliente(cliente):
    st.markdown(f"<h3 style='color:white; margin:0'>{cliente.get('Nome','')}</h3>", unsafe_allow_html=True)
    st.divider()
    c1, c2 = st.columns(2)
    for i, (k, v) in enumerate(cliente.items()):
        if str(v).strip() == "": v = "-"
        if i % 2 == 0:
            with c1: st.markdown(f"**{k}:** {v}")
        else:
            with c2: st.markdown(f"**{k}:** {v}")
    st.divider()
    if st.button("Fechar", use_container_width=True, key="fechar_modal"):
        st.rerun()

with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.radio("Menu", ["Clientes"], label_visibility="collapsed")

col_busca, col_novo = st.columns([4, 1])
with col_busca:
    busca = st.text_input("", placeholder="🔍 Buscar por nome, código, CPF/CNPJ, cidade...", label_visibility="collapsed")
with col_novo:
    st.button("＋ Novo Cliente", use_container_width=True)

df_f = df.copy()
if not df_f.empty and busca:
    b = busca.lower()
    df_f = df_f[df_f.astype(str).apply(lambda x: x.str.lower().str.contains(b, na=False)).any(axis=1)]

# ABRE O CONTAINER ENQUADRADO
st.markdown('<div class="tabela-container">', unsafe_allow_html=True)

st.markdown("""
<div class="tabela-header">
    <div style="width:80px">Código</div>
    <div style="flex:1.5">Nome</div>
    <div style="width:180px">CPF/CNPJ</div>
    <div style="width:180px">Cidade</div>
    <div style="width:150px">Telefone</div>
    <div style="width:35px"></div>
</div>
""", unsafe_allow_html=True)

if df_f.empty:
    st.markdown("<div style='padding:30px; text-align:center; color:#777'>Nenhum cliente encontrado</div>", unsafe_allow_html=True)
else:
    col_id = "ID" if "ID" in df_f.columns else df_f.columns[0]
    col_nome = "Nome" if "Nome" in df_f.columns else df_f.columns[1]
    col_doc = "CPF_CNPJ" if "CPF_CNPJ" in df_f.columns else "CPF/CNPJ" if "CPF/CNPJ" in df_f.columns else None
    col_cidade = "Cidade" if "Cidade" in df_f.columns else None
    col_tel = "Telefone" if "Telefone" in df_f.columns else None

    for idx, row in df_f.head(200).iterrows():
        id_val = row.get(col_id, "")
        nome_val = str(row.get(col_nome, ""))[:55]
        doc_val = row.get(col_doc, "") if col_doc else ""
        cidade_val = row.get(col_cidade, "") if col_cidade else ""
        tel_val = row.get(col_tel, "") if col_tel else ""

        c_a, c_b, c_c, c_d, c_e, c_f = st.columns([0.8, 3.5, 1.8, 1.8, 1.5, 0.4])
        with c_a:
            st.markdown(f"<div style='color:#9e9e9e; font-size:13px; line-height:32px'>{id_val}</div>", unsafe_allow_html=True)
        with c_b:
            st.markdown(f"<div style='color:white; font-size:13px; line-height:32px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis' title='{nome_val}'>{nome_val}</div>", unsafe_allow_html=True)
        with c_c:
            st.markdown(f"<div style='color:#e0e0e0; font-size:13px; line-height:32px'>{doc_val}</div>", unsafe_allow_html=True)
        with c_d:
            st.markdown(f"<div style='color:#e0e0e0; font-size:13px; line-height:32px'>{cidade_val}</div>", unsafe_allow_html=True)
        with c_e:
            st.markdown(f"<div style='color:#e0e0e0; font-size:13px; line-height:32px'>{tel_val}</div>", unsafe_allow_html=True)
        with c_f:
            if st.button("⋮", key=f"btn_{id_val}_{idx}_v15"):
                modal_cliente(row)

        # LINHA MAIS CLARA AGORA
        st.markdown('<div class="linha-separadora"></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) # FECHA CONTAINER
