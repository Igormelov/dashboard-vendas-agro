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
div[data-testid="stVerticalBlock"] {gap: 0.2rem!important}
div[data-testid="stHorizontalBlock"] {gap: 0rem!important; padding:0!important; margin:0!important}
div[data-testid="column"] {padding:2px 6px!important}
div[data-testid="stButton"] button {height:26px!important; min-height:26px!important; padding:0 8px!important; margin:0!important; border-radius:6px!important; border:1px solid #333!important; background:#2a2a2a!important; color:#ccc!important}
div[data-testid="stButton"] button:hover {background:#333!important; color:white!important}
hr {margin:0!important}
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
    if st.button("＋ Novo Cliente", type="primary", use_container_width=True):
        st.session_state['novo'] = True

df_f = df.copy()
if not df_f.empty and busca:
    b = busca.lower()
    df_f = df_f[df_f.astype(str).apply(lambda x: x.str.lower().str.contains(b, na=False)).any(axis=1)]

# Header fixo
st.markdown("""
<div style="display:flex; background:#1a1a1a; color:#9e9e9e; padding:8px 10px; font-size:12px; border:1px solid #333; border-bottom:1px solid #333">
    <div style="width:70px">Código</div>
    <div style="flex:1.5">Nome</div>
    <div style="width:170px">CPF/CNPJ</div>
    <div style="width:160px">Cidade</div>
    <div style="width:140px">Telefone</div>
    <div style="width:35px"></div>
</div>
""", unsafe_allow_html=True)

if df_f.empty:
    st.markdown("<div style='padding:30px; text-align:center; color:#777'>Nenhum cliente encontrado</div>", unsafe_allow_html=True)
else:
    col_id = "ID" if "ID" in df_f.columns else df_f.columns[0]
    col_nome = "Nome" if "Nome" in df_f.columns else "Nome/Fazenda" if "Nome/Fazenda" in df_f.columns else df_f.columns[1]
    col_doc = "CPF_CNPJ" if "CPF_CNPJ" in df_f.columns else "CPF/CNPJ" if "CPF/CNPJ" in df_f.columns else None
    col_cidade = "Cidade" if "Cidade" in df_f.columns else None
    col_tel = "Telefone" if "Telefone" in df_f.columns else None

    for idx, row in df_f.head(200).iterrows():
        id_val = row.get(col_id, "")
        nome_val = str(row.get(col_nome, ""))[:50]
        doc_val = row.get(col_doc, "") if col_doc else ""
        cidade_val = row.get(col_cidade, "") if col_cidade else ""
        tel_val = row.get(col_tel, "") if col_tel else ""

        c_a, c_b, c_c, c_d, c_e, c_f = st.columns([0.8, 3.5, 1.8, 1.8, 1.5, 0.4])
        with c_a:
            st.markdown(f"<div style='color:#9e9e9e; font-size:13px; line-height:26px'>{id_val}</div>", unsafe_allow_html=True)
        with c_b:
            st.markdown(f"<div style='color:white; font-size:13px; line-height:26px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis' title='{nome_val}'>{nome_val}</div>", unsafe_allow_html=True)
        with c_c:
            st.markdown(f"<div style='color:#e0e0e0; font-size:13px; line-height:26px'>{doc_val}</div>", unsafe_allow_html=True)
        with c_d:
            st.markdown(f"<div style='color:#e0e0e0; font-size:13px; line-height:26px'>{cidade_val}</div>", unsafe_allow_html=True)
        with c_e:
            st.markdown(f"<div style='color:#e0e0e0; font-size:13px; line-height:26px'>{tel_val}</div>", unsafe_allow_html=True)
        with c_f:
            if st.button("⋮", key=f"btn_{id_val}_{idx}_v14"):
                modal_cliente(row)

        st.markdown("<div style='border-bottom:1px solid #252525;'></div>", unsafe_allow_html=True)
