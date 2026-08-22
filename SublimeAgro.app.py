import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import re

st.set_page_config(page_title="SUBLIME Agro - Vendas", layout="wide", page_icon="🌿")

# CSS COMPACTO + SIDEBAR IGUAL FOTO
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1a3323!important; border-right: none!important; padding-top: 0!important; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0!important; }
.stApp { background-color: #0f1a12; }
.block-container { padding-top: 1rem!important; max-width: 95%!important;}
h1 { font-size: 1.4rem!important; color: #e8f5e9!important; margin-bottom: 0.5rem!important;}
p, label, span { font-size: 12px!important; color: #e8f5e9!important; }
div[data-testid="stTextInput"] input { height: 30px!important; font-size: 12px!important; background: #1a2e1f!important; border: 1px solid #2a4a32!important; color: white!important;}
div[data-testid="InputInstructions"] { display: none!important; }
[data-testid="stForm"] small { display: none!important; }
.stButton>button { background: #2d5a35; color: white; border-radius: 8px; height: 32px!important; font-size: 12px!important; border: 1px solid #3a6b42; width: 100%; text-align: left; padding-left: 12px!important;}
.stButton>button:hover { background: #3a6b42; color: white; border-color: #4caf50;}
.stButton>button[kind="primary"] { background: #4caf50!important; text-align: center!important; font-weight: bold; justify-content: center;}

/* ESTILO DO SIDEBAR DA FOTO */
.sidebar-header { background: white; padding: 14px 16px; margin: -10px -16px 0 -16px; display: flex; align-items: center; gap: 10px; }
.menu-title { color: #7fb88a; font-size: 11px!important; font-weight: bold; letter-spacing: 1px; margin: 18px 0 6px 14px;}
.menu-active { background: #5a8a65!important; border-radius: 8px; margin: 0 8px; }
.menu-header { padding: 10px 12px; color: white; font-weight: 700; font-size: 13px!important; display: flex; justify-content: space-between; align-items: center;}
.footer-bar { position: fixed; bottom: 0; left: 0; width: 100%; max-width: 21rem; background: #132a1a; padding: 12px 16px; display: flex; justify-content: space-between; color: #8fb996; font-size: 12px!important; border-top: 1px solid #1e3d27;}
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

# SIDEBAR IGUAL FOTO
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div style="border:2px solid #2e7d32; border-radius:12px; padding:5px; width:38px; height:38px; display:flex; align-items:center; justify-content:center; font-size:22px;">🌱</div>
        <div style="line-height:1"><b style="color:#1b3a2a; font-size:19px;">SUBLIME</b><br><b style="color:#1b3a2a; font-size:15px;">Agro</b></div>
        <div style="background:#e8f5e9; color:#2e7d32; font-size:10px; font-weight:bold; padding:3px 8px; border-radius:12px; margin-left:auto; border:1px solid #a5d6a7;">V3</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="menu-title">MENU</div>', unsafe_allow_html=True)

    st.markdown('<div class="menu-active"><div class="menu-header">👥 CLIENTES <span>▼</span></div></div>', unsafe_allow_html=True)
    col = st.columns([1, 10])[1]
    with col:
        if st.button("• Lista", key="c_lista", use_container_width=True): set_menu("Lista")
        # Ativo com bolinha verde igual foto
        label_cad = "• Cadastrar Cliente ●" if st.session_state.menu_ativo=="Cadastrar Cliente" else "• Cadastrar Cliente"
        if st.button(label_cad, key="c_cad", use_container_width=True): set_menu("Cadastrar Cliente")
        if st.button("• Importar Planilha", key="c_imp", use_container_width=True): set_menu("Importar Planilha")
        if st.button("• Mapa Personalizado", key="c_mapa", use_container_width=True): set_menu("Mapa Personalizado")

    st.markdown('<div style="margin-top:8px"><div class="menu-header">🚚 FORNECEDORES <span>›</span></div></div>', unsafe_allow_html=True)
    col2 = st.columns([1,10])[1]
    with col2:
        if st.button("• Lista", key="f_lista", use_container_width=True): set_menu("Fornecedores Lista")
        if st.button("• Cadastrar Fornecedor", key="f_cad", use_container_width=True): set_menu("Cadastrar Fornecedor")
        if st.button("• Mapa Fornecedores", key="f_mapa", use_container_width=True): set_menu("Mapa Fornecedores")

    st.markdown('<div style="margin-top:8px"><div class="menu-header">📦 PRODUTOS <span>›</span></div></div>', unsafe_allow_html=True)
    col3 = st.columns([1,10])[1]
    with col3:
        if st.button("• Lista", key="p_lista", use_container_width=True): set_menu("Produtos Lista")
        if st.button("• Cadastrar Produto", key="p_cad", use_container_width=True): set_menu("Cadastrar Produto")

    st.markdown('<div style="margin-top:8px"><div class="menu-header">⚙️ CONFIGURAÇÕES <span>›</span></div></div>', unsafe_allow_html=True)
    col4 = st.columns([1,10])[1]
    with col4:
        if st.button("• Limpar Cache", key="cfg1", use_container_width=True): st.cache_resource.clear(); st.toast("Cache limpo!")
        if st.button("• Aparência", key="cfg2", use_container_width=True): set_menu("Aparência")

    st.markdown('<div style="height:80px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer-bar"><span>v3.1.4</span><span>⎆ Sair</span></div>', unsafe_allow_html=True)

menu = st.session_state.menu_ativo

# CONTEÚDO
if menu=="Lista":
    st.title("👨‍🌾 Clientes - Lista")
    st.dataframe(df_clientes, use_container_width=True, height=600)

elif menu=="Cadastrar Cliente":
    st.title("➕ Cadastrar Cliente")

    st.markdown("**📄 Upload Sintegra (opcional)**")
    arquivo = st.file_uploader("Arraste o PDF", type=["pdf"], label_visibility="collapsed")
    if arquivo:
        try:
            import PyPDF2
            texto="".join([p.extract_text() or "" for p in PyPDF2.PdfReader(arquivo).pages])
            up=texto.upper()
            dados={}
            m=re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
            if m: dados["cpf_cnpj"]=m.group(1)
            m2=re.search(r'INSCRI[ÇC][AÃ]O ESTADUAL[^0-9]*([0-9\.\-]{8,15})', up)
            if m2: dados["ie"]=m2.group(1)
            m3=re.search(r'RAZ[AÃ]O SOCIAL[:\s\-]*([A-Z0-9\s\.\-\/&]+?)(?:\s{2,}|NOME FANTASIA|CNPJ)', up)
            if m3: dados["nome"]=m3.group(1).strip().title()[:80]
            st.session_state.sintegra_dados=dados
            if dados: st.success(f"✅ Encontrado: {dados}")
        except Exception as e: st.error(str(e))

    st.divider()
    c_cep, c_btn = st.columns([4,1])
    with c_cep: cep_input=st.text_input("CEP *", placeholder="78048-000", value=st.session_state.cep_last, label_visibility="collapsed", key="cep_final")
    with c_btn: buscar=st.button("🔍 Buscar CEP", use_container_width=True)
    if buscar and cep_input:
        d=buscar_cep(cep_input)
        if d:
            st.session_state.cep_data={"endereco":d.get("logradouro",""), "cidade":d.get("localidade",""), "estado":d.get("uf",""), "complemento":d.get("complemento","")}
            st.session_state.cep_last=cep_input
            st.toast(f"✅ {d.get('logradouro')}, {d.get('localidade')}")
            st.rerun()
        else: st.error("CEP não encontrado")

    c1,c2,c3=st.columns(3)
    with c1:
        nome=st.text_input("Nome / Razão Social *", value=st.session_state.sintegra_dados.get("nome",""), key="nome_f")
        telefone=st.text_input("Telefone", key="tel_f")
        cpf=st.text_input("CPF / CNPJ", value=st.session_state.sintegra_dados.get("cpf_cnpj",""), key="cpf_f")
    with c2:
        ie=st.text_input("IE", value=st.session_state.sintegra_dados.get("ie",""), key="ie_f")
        fazenda=st.text_input("Fazenda", key="faz_f")
        cidade=st.text_input("Cidade", value=st.session_state.cep_data.get("cidade",""), key="cid_f")
    with c3:
        endereco=st.text_input("Endereço", value=st.session_state.cep_data.get("endereco",""), key="end_f")
        numero=st.text_input("Nº", key="num_f")
        complemento=st.text_input("Complemento", value=st.session_state.cep_data.get("complemento",""), key="comp_f")
    estado=st.text_input("UF", value=st.session_state.cep_data.get("estado",""), max_chars=2, key="uf_f")

    # SÓ SALVA NO CLIQUE - ENTER NÃO SALVA
    if st.button("Salvar Cliente 🌿", type="primary", use_container_width=True):
        if not nome: st.error("Nome obrigatório")
        else:
            novo_id=len(df_clientes)+1 if not df_clientes.empty else 1
            ws_clientes.append_row([novo_id, nome, telefone, cidade, estado.upper(), fazenda, cpf, cep_input, endereco, numero, complemento, ie, datetime.now().strftime("%Y-%m-%d")])
            st.session_state.sintegra_dados={}
            st.success(f"Cliente {nome} salvo com sucesso!"); st.balloons()
            st.rerun()

elif menu=="Produtos Lista":
    st.title("📦 Produtos")
    st.dataframe(df_produtos, use_container_width=True)

elif menu=="Fornecedores Lista":
    st.title("🚚 Fornecedores")
    st.info("Lista de fornecedores - em desenvolvimento")

else:
    st.title(menu)
    st.info(f"Módulo {menu} - já está no menu igual da foto, pronto para implementar!")
