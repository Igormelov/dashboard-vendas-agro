import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import re

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide", page_icon="🌱")

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #1a3523!important;
    width: 268px!important;
    min-width: 268px!important;
    max-width: 268px!important;
    border-radius: 0 18px 18px 0!important;
    padding: 0!important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0!important; }
.stApp { background: #eef3ee; }
[data-testid="stSidebarNav"], header, footer, div[data-testid="InputInstructions"] { display: none!important; }

/* DIMINUI ESPAÇAMENTO ENTRE OPÇÕES - BEM ENQUADRADO */
[data-testid="stSidebar"].stVerticalBlock { gap: 0rem!important; }
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
    margin: 0!important;
    padding: 0!important;
    gap: 0!important;
}
.stButton { margin: -2px 0!important; padding: 0!important; }
.stButton>button {
    background: transparent!important;
    border: none!important;
    color: #a8c5b0!important;
    font-size: 13.5px!important;
    text-align: left!important;
    padding: 2px 0 2px 32px!important;
    height: 24px!important;
    min-height: 24px!important;
    line-height: 1.1!important;
    margin: 0!important;
    font-weight: 400!important;
    box-shadow: none!important;
}
.stButton>button:hover { color: white!important; }

.main-container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def conecta_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "\\n" in creds_dict["private_key"]:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

def buscar_cep(cep):
    cep = "".join(filter(str.isdigit, cep))
    if len(cep)!=8: return None
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
        if r.status_code==200:
            d=r.json()
            if "erro" not in d: return d
    except: return None
    return None

sh = conecta_gsheets()
def get_or_create_ws(nome, headers):
    for ws in sh.worksheets():
        if ws.title == nome: return ws
    ws = sh.add_worksheet(title=nome, rows=1000, cols=len(headers))
    ws.append_row(headers)
    return ws
def carrega_df_seguro(ws, headers):
    try:
        vals = ws.get_all_values()
        if len(vals) <= 1: return pd.DataFrame(columns=headers)
        df = pd.DataFrame(vals[1:], columns=[c.strip() for c in vals[0]])
        for h in headers:
            if h not in df.columns: df[h] = ""
        return df
    except: return pd.DataFrame(columns=headers)

HEADERS_CLIENTES = ["ID","Nome","Telefone","Cidade","Estado","Fazenda","CPF_CNPJ","CEP","Endereco","Numero","Complemento","IE","Data_Cadastro"]
HEADERS_VENDAS = ["ID","Data","Cliente","Produto","Quantidade","Valor_Unit","Valor_Total","Cidade","Estado","Vendedor","Status"]
HEADERS_PRODUTOS = ["ID","Nome","Preco","Estoque"]
ws_vendas = get_or_create_ws("Vendas", HEADERS_VENDAS)
ws_produtos = get_or_create_ws("Produtos", HEADERS_PRODUTOS)
ws_clientes = get_or_create_ws("Clientes", HEADERS_CLIENTES)
df_vendas = carrega_df_seguro(ws_vendas, HEADERS_VENDAS)
df_produtos = carrega_df_seguro(ws_produtos, HEADERS_PRODUTOS)
df_clientes = carrega_df_seguro(ws_clientes, HEADERS_CLIENTES)

if "cep_data" not in st.session_state: st.session_state.cep_data = {"endereco":"","cidade":"","estado":"","complemento":""}
if "cep_last" not in st.session_state: st.session_state.cep_last = ""
if "sintegra_dados" not in st.session_state: st.session_state.sintegra_dados = {}
if "menu_ativo" not in st.session_state: st.session_state.menu_ativo = "Cadastrar Cliente"
def set_menu(item): st.session_state.menu_ativo = item

with st.sidebar:
    st.markdown("""
    <div style="background:white; padding:12px 16px; border-radius:18px 18px 0 0; display:flex; align-items:center; gap:8px; margin:0;">
        <div style="width:38px; height:38px; border:2.5px solid #2e6b3a; border-radius:10px; display:flex; align-items:center; justify-content:center;">🌿</div>
        <div style="line-height:0.9">
            <div style="font-family:Arial Black; font-size:20px; font-weight:900; color:#1a2a4a;">SUBLIME</div>
            <div style="font-family:Arial Black; font-size:17px; font-weight:900; color:#1a2a4a; margin-top:-2px;">Agro</div>
        </div>
        <div style="margin-left:auto; background:#c5e8c8; color:#1a4a2a; font-size:11px; font-weight:800; padding:3px 8px; border-radius:6px;">V3</div>
    </div>
    <div style="background:#1a3523; padding:10px 14px 2px 14px;">
        <div style="color:#8ab896; font-size:11px; font-weight:700; letter-spacing:1.2px; margin-left:4px;">MENU</div>
    </div>
    """, unsafe_allow_html=True)

    # CLIENTES ATIVO
    st.markdown("""
    <div style="background:#1a3523; padding:2px 10px;">
        <div style="background:#6b9c78; border-radius:8px; padding:8px 12px; display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:6px; color:white; font-weight:800; font-size:13.5px;">👥 CLIENTES</div>
            <div style="color:white; font-size:10px;">▼</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1,20])[1]
    with col:
        if st.button("• Lista", key="c_lista"): set_menu("Lista"); st.rerun()
        if st.button("• Cadastrar Cliente", key="c_cad"): set_menu("Cadastrar Cliente"); st.rerun()
        if st.button("• Importar Planilha", key="c_imp"): set_menu("Importar Planilha"); st.rerun()
        if st.button("• Mapa Personalizado", key="c_map"): set_menu("Mapa Personalizado"); st.rerun()

    st.markdown("""
    <div style="background:#1a3523; padding:8px 10px 0 10px;">
        <div style="display:flex; align-items:center; justify-content:space-between; padding:4px 2px;">
            <div style="display:flex; align-items:center; gap:6px; color:white; font-weight:800; font-size:13.5px;">🚚 FORNECEDORES</div>
            <div style="color:#8ab896; font-size:14px;">›</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col2 = st.columns([1,20])[1]
    with col2:
        if st.button("• Lista", key="f_lista"): set_menu("Fornecedores Lista"); st.rerun()
        if st.button("• Cadastrar Fornecedor", key="f_cad"): set_menu("Cadastrar Fornecedor"); st.rerun()
        if st.button("• Mapa Fornecedores", key="f_map"): set_menu("Mapa Fornecedores"); st.rerun()

    st.markdown("""
    <div style="background:#1a3523; padding:8px 10px 0 10px;">
        <div style="display:flex; align-items:center; justify-content:space-between; padding:4px 2px;">
            <div style="display:flex; align-items:center; gap:6px; color:white; font-weight:800; font-size:13.5px;">📦 PRODUTOS</div>
            <div style="color:#8ab896; font-size:14px;">›</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col3 = st.columns([1,20])[1]
    with col3:
        if st.button("• Lista", key="p_lista"): set_menu("Produtos Lista"); st.rerun()
        if st.button("• Cadastrar Produto", key="p_cad"): set_menu("Cadastrar Produto"); st.rerun()

    st.markdown("""
    <div style="background:#1a3523; padding:8px 10px 0 10px;">
        <div style="display:flex; align-items:center; justify-content:space-between; padding:4px 2px;">
            <div style="display:flex; align-items:center; gap:6px; color:white; font-weight:800; font-size:13.5px;">⚙️ CONFIGURAÇÕES</div>
            <div style="color:#8ab896; font-size:14px;">›</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col4 = st.columns([1,20])[1]
    with col4:
        if st.button("• Limpar Cache", key="cfg1"): st.cache_resource.clear()
        if st.button("• Aparência", key="cfg2"): set_menu("Aparência"); st.rerun()

    # ITEM ATIVO COM BOLINHA E SUBLINHADO
    if st.session_state.menu_ativo=="Cadastrar Cliente":
        st.markdown("""
        <style>
        button[kind="secondary"]:nth-of-type(1) { color: white!important; font-weight: 700!important; text-decoration: underline!important; }
        </style>
        <div style="background:#1a3523; margin:-92px 0 0 32px; pointer-events:none; display:flex; align-items:center; gap:4px; color:white; font-size:13.5px; font-weight:700; text-decoration:underline; text-underline-offset:3px;">
            • Cadastrar Cliente <span style="color:#4ade80; font-size:10px; margin-left:4px;">●</span>
        </div>
        <div style="height:70px; background:#1a3523;"></div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:20px; background:#1a3523;"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1a3523; padding:10px 12px; display:flex; justify-content:space-between; border-radius:0 0 18px 18px;">
        <div style="color:#8ab896; font-size:12px;">v3.1.4</div>
        <div style="color:#c5d9c8; font-size:12px;">☰ Sair</div>
    </div>
    """, unsafe_allow_html=True)

menu = st.session_state.menu_ativo
if menu=="Lista":
    st.title("👨‍🌾 Clientes - Lista")
    st.dataframe(df_clientes, use_container_width=True, height=600)
elif menu=="Cadastrar Cliente":
    st.title("➕ Cadastrar Cliente")
    arquivo = st.file_uploader("📄 Upload Sintegra", type=["pdf"], label_visibility="collapsed")
    if arquivo:
        try:
            import PyPDF2
            texto="".join([p.extract_text() or "" for p in PyPDF2.PdfReader(arquivo).pages])
            up=texto.upper()
            dados={}
            m=re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            if m: dados["cpf_cnpj"]=m.group(1)
            st.session_state.sintegra_dados=dados
        except: pass
    c_cep, c_btn = st.columns([4,1])
    with c_cep: cep_input=st.text_input("CEP", value=st.session_state.cep_last, key="cep_f", label_visibility="collapsed", placeholder="78048-000")
    with c_btn: buscar=st.button("🔍 Buscar CEP")
    if buscar and cep_input:
        d=buscar_cep(cep_input)
        if d:
            st.session_state.cep_data={"endereco":d.get("logradouro",""), "cidade":d.get("localidade",""), "estado":d.get("uf",""), "complemento":d.get("complemento","")}
            st.session_state.cep_last=cep_input
            st.rerun()
    c1,c2,c3=st.columns(3)
    with c1:
        nome=st.text_input("Nome *", value=st.session_state.sintegra_dados.get("nome",""), key="nome_f")
        telefone=st.text_input("Telefone", key="tel_f")
        cpf=st.text_input("CPF/CNPJ", value=st.session_state.sintegra_dados.get("cpf_cnpj",""), key="cpf_f")
    with c2:
        fazenda=st.text_input("Fazenda", key="faz_f")
        cidade=st.text_input("Cidade", value=st.session_state.cep_data.get("cidade",""), key="cid_f")
        estado=st.text_input("UF", value=st.session_state.cep_data.get("estado",""), max_chars=2, key="uf_f")
    with c3:
        endereco=st.text_input("Endereço", value=st.session_state.cep_data.get("endereco",""), key="end_f")
        numero=st.text_input("Nº", key="num_f")
        complemento=st.text_input("Complemento", key="comp_f")
    if st.button("Salvar Cliente 🌿", type="primary"):
        if nome:
            ws_clientes.append_row([len(df_clientes)+1, nome, telefone, cidade, estado.upper(), fazenda, cpf, cep_input, endereco, numero, complemento, "", datetime.now().strftime("%Y-%m-%d")])
            st.success("Salvo!"); st.balloons(); st.rerun()
else:
    st.title(menu)
    st.info(f"Módulo {menu}")
