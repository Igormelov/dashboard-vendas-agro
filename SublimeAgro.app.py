import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="SUBLIME Agro - Clientes", layout="wide", page_icon="🌱")

# COR DE FUNDO IGUAL DA SUA PRINT #212121
st.markdown("""
<style>
.stApp {background:#212121!important}
h1,h2,h3,p,label,span {color:#e0e0e0!important}
[data-testid="stSidebar"] {background:#1a1a1a!important; border-right:1px solid #333}

/* Tabela estilo Bling da sua print */
.tabela-header {
    display:flex; background:#1a1a1a; color:#9e9e9e;
    padding:12px 16px; font-size:13px; font-weight:500;
    border-bottom:1px solid #333; border-top:1px solid #333;
}
.tabela-row {
    display:flex; background:#212121; color:#e0e0e0;
    padding:14px 16px; font-size:14px; align-items:center;
    border-bottom:1px solid #2e2e2e; transition:0.2s;
}
.tabela-row:hover {background:#2a2a2a}
.col-codigo {width:80px; color:#9e9e9e}
.col-nome {flex:1.5; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.col-doc {width:180px}
.col-cidade {width:180px}
.col-tel {width:160px}
.col-acao {width:40px; text-align:right}
.btn-acao {background:none; border:none; color:#9e9e9e; cursor:pointer; font-size:18px}
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
    st.markdown(f"""
    <div style="background:#2a2a2a; padding:16px; border-radius:8px; border:1px solid #333">
    <h3 style="color:white; margin-top:0">{cliente.get('Nome','')} </h3>
    </div>
    """, unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    for i, (k,v) in enumerate(cliente.items()):
        if str(v).strip() == "": v = "-"
        if i%2==0:
            with c1: st.markdown(f"**{k}:** {v}")
        else:
            with c2: st.markdown(f"**{k}:** {v}")

    st.divider()
    if st.button("Fechar", use_container_width=True):
        st.rerun()

# Sidebar só Clientes
with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.radio("Menu", ["Clientes"], label_visibility="collapsed")

# Busca estilo Bling
c_busca, c_novo = st.columns([4,1])
with c_busca:
    busca = st.text_input("", placeholder="🔍 Buscar por nome, código, CPF/CNPJ, cidade...", label_visibility="collapsed")
with c_novo:
    if st.button("＋ Novo Cliente", type="primary", use_container_width=True):
        st.session_state['novo'] = True

df_f = df.copy()
if not df_f.empty and busca:
    b = busca.lower()
    df_f = df_f[df_f.astype(str).apply(lambda x: x.str.lower().str.contains(b, na=False)).any(axis=1)]

# Header da tabela igual sua print
st.markdown("""
<div class="tabela-header">
    <div class="col-codigo">Código</div>
    <div class="col-nome">Nome</div>
    <div class="col-doc">CPF/CNPJ</div>
    <div class="col-cidade">Cidade</div>
    <div class="col-tel">Telefone</div>
    <div class="col-acao"></div>
</div>
""", unsafe_allow_html=True)

if df_f.empty:
    st.markdown("<div style='padding:40px; text-align:center; color:#9e9e9e'>Nenhum cliente encontrado</div>", unsafe_allow_html=True)
else:
    # Detecta colunas
    col_id = "ID" if "ID" in df_f.columns else df_f.columns[0]
    col_nome = "Nome" if "Nome" in df_f.columns else "Nome/Fazenda"
    col_doc = "CPF_CNPJ" if "CPF_CNPJ" in df_f.columns else "CPF/CNPJ"
    col_cidade = "Cidade" if "Cidade" in df_f.columns else "CIDADE" if "CIDADE" in df_f.columns else None
    col_tel = "Telefone" if "Telefone" in df_f.columns else None

    for idx, row in df_f.head(100).iterrows():
        id_val = row.get(col_id, "")
        nome_val = row.get(col_nome, "")
        doc_val = row.get(col_doc, "") if col_doc in row else ""
        cidade_val = row.get(col_cidade, "") if col_cidade and col_cidade in row else ""
        tel_val = row.get(col_tel, "") if col_tel and col_tel in row else ""

        # Linha com colunas + botão 3 pontinhos
        c1,c2,c3,c4,c5,c6 = st.columns([0.8, 3.5, 1.8, 1.8, 1.5, 0.4])
        with c1: st.markdown(f"<div style='color:#9e9e9e; font-size:14px; padding-top:6px'>{id_val}</div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div style='color:white; font-size:14px; padding-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis' title='{nome_val}'>{nome_val}</div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div style='color:#e0e0e0; font-size:14px; padding-top:6px'>{doc_val}</div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div style='color:#e0e0e0; font-size:14px; padding-top:6px'>{cidade_val}</div>", unsafe_allow_html=True)
        with c5: st.markdown(f"<div style='color:#e0e0e0; font-size:14px; padding-top:6px'>{tel_val}</div>", unsafe_allow_html=True)
        with c6:
            if st.button("⋮", key=f"btn_{id_val}_{idx}", help="Ver detalhes"):
                st.session_state['cliente_sel'] = row
                modal_cliente(row)
        st.markdown("<div style='border-bottom:1px solid #2e2e2e; margin:2px 0'></div>", unsafe_allow_html=True)

# Se clicou via session_state
if 'cliente_sel' in st.session_state and st.session_state['cliente_sel'] is not None:
    pass
