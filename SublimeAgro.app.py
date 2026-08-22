import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime
import requests
import re

st.set_page_config(page_title="SUBLIME Agro - Vendas", layout="wide", page_icon="🌿")

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0f1a12; border-right: 1px solid #2a4a32; }
[data-testid="stSidebar"] * { font-size: 14px!important; }
.stApp { background-color: #0f1a12; }
.block-container { padding-top: 1rem!important; padding-bottom: 0rem!important; max-width: 95%!important;}
h1 { font-size: 1.45rem!important; margin: 0 0 0.4rem 0!important; color: #e8f5e9!important;}
h2 { font-size: 1.1rem!important; margin: 0.6rem 0 0.3rem 0!important; color: #e8f5e9!important;}
h3 { font-size: 0.95rem!important; color: #e8f5e9!important;}
p, span, label, div[data-testid="stMarkdownContainer"] p { font-size: 12px!important; color: #e8f5e9!important; }
label { margin-bottom: 1px!important; font-size: 11px!important; opacity: 0.9; }
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] div,
div[data-testid="stNumberInput"] input {
    font-size: 12px!important; height: 30px!important; min-height: 30px!important;
    padding: 2px 8px!important; background-color: #1a2e1f!important;
    border: 1px solid #2a4a32!important; color: #e8f5e9!important;
}
div[data-testid="stTextInput"], div[data-testid="stSelectbox"], div[data-testid="stNumberInput"] { margin-bottom: -14px!important; }
.stButton>button {
    background-color: #4caf50; color: white; border-radius: 8px;
    width: 100%; font-weight: bold; border: none;
    font-size: 12px!important; height: 32px!important; padding: 3px!important;
}
div[data-testid="stMetric"] { background-color: #1a2e1f; border: 1px solid #2a4a32; border-radius: 10px; padding: 6px 10px!important;}
div[data-testid="stMetricLabel"] { font-size: 10px!important; }
div[data-testid="stMetricValue"] { font-size: 15px!important; }
[data-testid="stFileUploader"] section { padding: 6px!important; min-height: 60px!important;}
[data-testid="stFileUploader"] * { font-size: 11px!important; }
hr { margin: 0.4rem 0!important; }
div[data-testid="InputInstructions"] { display: none!important; }
[data-testid="stForm"] small { display: none!important; }
</style>
""", unsafe_allow_html=True)

def normaliza(df):
    df.columns = [c.strip() for c in df.columns]
    return df

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
            data=r.json()
            if "erro" not in data: return data
    except: return None
    return None

sh = conecta_gsheets()

# CORREÇÃO DO ERRO DA SUA PRINT - NÃO TENTA CRIAR ABA DUPLICADA
def get_or_create_ws(nome, headers):
    try:
        # Tenta listar todas as abas primeiro
        for ws in sh.worksheets():
            if ws.title == nome:
                return ws
        # Se não achou, cria
        ws = sh.add_worksheet(title=nome, rows=1000, cols=len(headers))
        ws.append_row(headers)
        return ws
    except Exception as e:
        # Se der qualquer erro de API, tenta pegar de novo
        try:
            return sh.worksheet(nome)
        except:
            st.error(f"Erro ao acessar aba {nome}: {e}")
            st.stop()

def carrega_df_seguro(ws, headers):
    try:
        vals = ws.get_all_values()
        if len(vals) <= 1:
            return pd.DataFrame(columns=headers)
        # Usa primeira linha como header, mas normaliza
        df = pd.DataFrame(vals[1:], columns=[c.strip() for c in vals[0]])
        # Se faltam colunas, adiciona vazias
        for h in headers:
            if h not in df.columns:
                df[h] = ""
        return df
    except:
        return pd.DataFrame(columns=headers)

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

with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    menu = st.radio("Menu", ["Dashboard","Vendas","Cadastrar Venda","Clientes","Novo Cliente"], label_visibility="collapsed", index=4)
    st.divider()
    st.markdown("""<div style="display:flex;align-items:center;gap:12px;background:#1a2e1f;border:1px solid #2a4a32;padding:10px;border-radius:12px;">
    <div style="background:#4caf50;width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;">IM</div>
    <div><b style="font-size:13px;">Igor Melo</b><br><span style="color:#4caf50;font-size:11px;">Admin • Online 🟢</span></div></div>""", unsafe_allow_html=True)

if menu=="Dashboard":
    st.title("Dashboard de Vendas 🌿")
    st.dataframe(df_vendas, use_container_width=True, height=500)

elif menu=="Vendas":
    st.title("Todas as Vendas")
    st.dataframe(df_vendas, use_container_width=True, height=500)

elif menu=="Cadastrar Venda":
    st.title("Nova Venda 🚀")
    lista = df_clientes["Nome"].tolist() if not df_clientes.empty and "Nome" in df_clientes.columns else []
    sel = st.selectbox("Cliente *", ["Selecione..."]+lista+["Cliente Avulso"])
    cidade_auto=estado_auto=""
    if sel not in ["Selecione...","Cliente Avulso",""] and not df_clientes.empty and "Nome" in df_clientes.columns:
        d=df_clientes[df_clientes["Nome"]==sel]
        if not d.empty: cidade_auto=d.iloc[0].get("Cidade",""); estado_auto=d.iloc[0].get("Estado","")
    with st.form("venda"):
        c1,c2=st.columns(2)
        with c1:
            produto=st.selectbox("Produto", df_produtos["Nome"].tolist() if not df_produtos.empty and "Nome" in df_produtos.columns else ["Soja Premium"])
            qtd=st.number_input("Qtd",1)
            cidade=st.text_input("Cidade", value=cidade_auto)
            estado=st.text_input("UF", value=estado_auto, max_chars=2)
        with c2:
            vendedor=st.selectbox("Vendedor", ["Igor Melo","Ana Costa","Bruno Silva","Carlos Lima"])
            status=st.selectbox("Status", ["Pago","Pendente"])
        if st.form_submit_button("Salvar Venda 🌿"):
            ws_vendas.append_row([len(df_vendas)+1, datetime.now().strftime("%Y-%m-%d"), sel, produto, qtd, 0,0, cidade, estado.upper(), vendedor, status])
            st.success("Venda salva!"); st.rerun()

elif menu=="Clientes":
    st.title("👨‍🌾 Clientes Cadastrados")
    st.dataframe(df_clientes, use_container_width=True, height=500)

elif menu=="Novo Cliente":
    st.markdown("### ➕ Novo Cliente")
    st.markdown("#### 📄 Upload Sintegra")
    st.caption("Arraste o PDF do Sintegra aqui (opcional)")
    arquivo = st.file_uploader("Upload Sintegra", type=["pdf"], label_visibility="collapsed")
    if arquivo is not None:
        with st.spinner("Lendo Sintegra..."):
            try:
                import PyPDF2
                texto=""
                reader=PyPDF2.PdfReader(arquivo)
                for p in reader.pages: texto+=p.extract_text() or ""
                texto_upper=texto.upper()
                dados={}
                m_cnpj=re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
                if m_cnpj: dados["cpf_cnpj"]=m_cnpj.group(1)
                m_ie=re.search(r'INSCRI[ÇC][AÃ]O ESTADUAL[^0-9]*([0-9\.\-]{8,15})', texto_upper)
                if m_ie: dados["ie"]=m_ie.group(1).strip()
                m_r=re.search(r'RAZ[AÃ]O SOCIAL[:\s\-]*([A-Z0-9\s\.\-\/&]+?)(?:\s{2,}|NOME FANTASIA|CNPJ)', texto_upper)
                if m_r and len(m_r.group(1).strip())>5: dados["nome"]=m_r.group(1).strip().title()[:80]
                st.session_state.sintegra_dados=dados
                if dados: st.success(f"✅ Encontrado: {dados}")
            except Exception as e: st.error(f"Erro: {e}")

    st.divider()
    st.markdown("#### Endereço - CEP com Lupa")
    c_cep, c_btn = st.columns([4,1])
    with c_cep: cep_input=st.text_input("CEP *", placeholder="78250-000", value=st.session_state.cep_last, key="cep_input_novo", label_visibility="collapsed")
    with c_btn: buscar=st.button("🔍 Buscar CEP", use_container_width=True)
    if buscar and cep_input:
        dcep=buscar_cep(cep_input)
        if dcep:
            st.session_state.cep_data["endereco"]=dcep.get("logradouro","")
            st.session_state.cep_data["cidade"]=dcep.get("localidade","")
            st.session_state.cep_data["estado"]=dcep.get("uf","")
            st.session_state.cep_data["complemento"]=dcep.get("complemento","")
            st.session_state.cep_last=cep_input
            st.toast(f"Endereço: {dcep.get('logradouro')}", icon="✅")
            st.rerun()
        else: st.error("CEP não encontrado")

    # SEM FORM - ENTER NÃO SALVA MAIS
    c1,c2,c3 = st.columns(3)
    with c1:
        nome=st.text_input("Nome Completo / Razão Social *", value=st.session_state.sintegra_dados.get("nome",""), key="nome_cli")
        telefone=st.text_input("Telefone", placeholder="(65) 9 9999-9999", key="tel_cli")
        cpf=st.text_input("CPF / CNPJ", value=st.session_state.sintegra_dados.get("cpf_cnpj",""), key="cpf_cli")
    with c2:
        ie=st.text_input("IE", value=st.session_state.sintegra_dados.get("ie",""), key="ie_cli")
        fazenda=st.text_input("Fazenda", key="faz_cli")
        cidade=st.text_input("Cidade", value=st.session_state.cep_data.get("cidade",""), key="cid_cli")
    with c3:
        endereco=st.text_input("Endereço", value=st.session_state.cep_data.get("endereco",""), key="end_cli")
        numero=st.text_input("Nº", placeholder="123", key="num_cli")
        complemento=st.text_input("Complemento", value=st.session_state.cep_data.get("complemento",""), key="comp_cli")
    estado=st.text_input("UF", value=st.session_state.cep_data.get("estado",""), max_chars=2, key="uf_cli")

    if st.button("Salvar Cliente 🌿", type="primary"):
        if not nome: st.error("Nome obrigatório")
        else:
            novo_id=len(df_clientes)+1 if not df_clientes.empty else 1
            ws_clientes.append_row([novo_id, nome, telefone, cidade, estado.upper(), fazenda, cpf, cep_input, endereco, numero, complemento, ie, datetime.now().strftime("%Y-%m-%d")])
            st.session_state.sintegra_dados={}
            st.success(f"Cliente {nome} salvo!"); st.balloons()
            st.rerun()
