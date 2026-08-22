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

/* ZERA O GAP */
div[data-testid="stVerticalBlock"] {gap:0!important}
div[data-testid="stHorizontalBlock"] {gap:0!important; padding:0!important; margin:0!important}
div[data-testid="column"] {padding:0!important}

/* BOTÃO NOVO CLIENTE - CORRIGIDO, NÃO QUEBRA */
div[data-testid="stButton"] button[kind="primary"] {
    white-space:nowrap!important; height:36px!important; min-height:36px!important;
    background:#2e2e2e!important; border:1px solid #3a3a3a!important; color:white!important;
    border-radius:8px!important; width:100%!important;
}
div[data-testid="stButton"] button:not([kind="primary"]) {
    height:24px!important; min-height:24px!important; width:28px!important;
    padding:0!important; border-radius:6px!important;
    background:#2e2e2e!important; border:1px solid #3a3a3a!important; color:#aaa!important;
}

/* LINHA PADRÃO */
.linha {height:38px; display:flex; align-items:center; border-bottom:1px solid #3a3a3a;}
.linha-header {background:#1a1a1a; color:#8a8a8a; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;}
.linha-dado {background:#212121; color:#e0e0e0;}
.linha-dado:hover {background:#2a2a2a}
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
    if st.button("Fechar", use_container_width=True):
        st.rerun()

with st.sidebar:
    st.markdown("### 🌱 SUBLIME Agro")
    st.radio("Menu", ["Clientes"], label_visibility="collapsed")

# BUSCA + BOTÃO - MESMA LINHA, SEM QUEBRAR
col_busca, col_btn = st.columns([4, 1])
with col_busca:
    busca = st.text_input("", placeholder="🔍 Buscar por nome, código, CPF/CNPJ, cidade...", label_visibility="collapsed")
with col_btn:
    st.button("＋ Novo Cliente", type="primary", use_container_width=True)

df_f = df.copy()
if not df_f.empty and busca:
    b = busca.lower()
    df_f = df_f[df_f.astype(str).apply(lambda x: x.str.lower().str.contains(b, na=False)).any(axis=1)]

# CONTAINER ENQUADRADO MAIS ABAIXO
st.markdown('<div style="margin-top:22px; border:1px solid #3a3a3a; border-radius:8px; overflow:hidden; background:#1e1e1e">', unsafe_allow_html=True)

# CABEÇALHO USANDO O MESMO GRID DAS LINHAS - ALINHADO PERFEITO
h1,h2,h3,h4,h5,h6 = st.columns([0.8, 3.2, 1.8, 1.8, 1.4, 0.5])
with h1: st.markdown('<div class="linha linha-header" style="padding-left:12px">CÓDIGO</div>', unsafe_allow_html=True)
with h2: st.markdown('<div class="linha linha-header">NOME</div>', unsafe_allow_html=True)
with h3: st.markdown('<div class="linha linha-header">CPF/CNPJ</div>', unsafe_allow_html=True)
with h4: st.markdown('<div class="linha linha-header">CIDADE</div>', unsafe_allow_html=True)
with h5: st.markdown('<div class="linha linha-header">TELEFONE</div>', unsafe_allow_html=True)
with h6: st.markdown('<div class="linha linha-header"></div>', unsafe_allow_html=True)

if df_f.empty:
    st.markdown('<div style="padding:20px; text-align:center; color:#777; background:#212121">Nenhum cliente</div>', unsafe_allow_html=True)
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

        c1,c2,c3,c4,c5,c6 = st.columns([0.8, 3.2, 1.8, 1.8, 1.4, 0.5])
        with c1: st.markdown(f'<div class="linha linha-dado" style="padding-left:12px; color:#8a8a8a; font-size:12px">{id_val}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="linha linha-dado" style="color:white; font-size:13px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">{nome_val}</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="linha linha-dado" style="color:#c0c0c0; font-size:12px">{doc_val}</div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="linha linha-dado" style="color:#c0c0c0; font-size:12px">{cidade_val}</div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="linha linha-dado" style="color:#c0c0c0; font-size:12px">{tel_val}</div>', unsafe_allow_html=True)
        with c6:
            # 3 PONTINHOS ALINHADO NO CENTRO DA LINHA
            st.markdown('<div class="linha linha-dado" style="justify-content:center">', unsafe_allow_html=True)
            if st.button("⋮", key=f"btn_{id_val}_{idx}_v17"):
                modal_cliente(row)
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
