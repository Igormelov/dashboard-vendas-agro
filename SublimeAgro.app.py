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
.stApp { background-color: #0f1a12; }
[data-testid="stSidebar"] { background-color: #0f1a12; border-right: 1px solid #2a4a32; }
div[data-testid="stMetric"] { background-color: #1a2e1f; border: 1px solid #2a4a32; border-radius: 14px; padding: 15px; }
h1,h2,h3,p,span,label { color: #e8f5e9!important; }
.stButton>button { background-color: #4caf50; color: white; border-radius: 10px; width: 100%; font-weight: bold; border: none; }
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
    if len(cep)!=8:
        return None
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
        if r.status_code==200:
            data=r.json()
            if "erro" not in data:
                return data
    except:
        return None
    return None

sh = conecta_gsheets()

def get_or_create_ws(nome, headers):
    try:
        ws = sh.worksheet(nome)
        return ws
    except:
        ws = sh.add_worksheet(title=nome, rows=1000, cols=len(headers))
        ws.append_row(headers)
        return ws

HEADERS_CLIENTES = ["ID","Nome","Telefone","Cidade","Estado","Fazenda","CPF_CNPJ","CEP","Endereco","Numero","Complemento","IE","Data_Cadastro"]

ws_vendas = get_or_create_ws("Vendas", ["ID","Data","Cliente","Produto","Quantidade","Valor_Unit","Valor_Total","Cidade","Estado","Vendedor","Status"])
ws_produtos = get_or_create_ws("Produtos", ["ID","Nome","Preco","Estoque"])
ws_clientes = get_or_create_ws("Clientes", HEADERS_CLIENTES)

df_vendas = normaliza(pd.DataFrame(ws_vendas.get_all_records()))
df_produtos = normaliza(pd.DataFrame(ws_produtos.get_all_records()))
df_clientes = normaliza(pd.DataFrame(ws_clientes.get_all_records()))

if "cep_data" not in st.session_state:
    st.session_state.cep_data = {"endereco":"","cidade":"","estado":"","complemento":""}
if "cep_last" not in st.session_state:
    st.session_state.cep_last = ""
if "sintegra_dados" not in st.session_state:
    st.session_state.sintegra_dados = {}

with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    menu = st.radio("Menu", ["Dashboard","Vendas","Cadastrar Venda","Clientes","Novo Cliente"], label_visibility="collapsed", index=4)
    st.divider()
    st.markdown("""<div style="display:flex;align-items:center;gap:12px;background:#1a2e1f;border:1px solid #2a4a32;padding:12px;border-radius:12px;">
    <div style="background:#4caf50;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;">IM</div>
    <div><b>Igor Melo</b><br><span style="color:#4caf50;font-size:12px;">Admin • Online 🟢</span></div></div>""", unsafe_allow_html=True)

if menu=="Dashboard":
    st.title("Dashboard de Vendas 🌿")
    if not df_vendas.empty:
        df_vendas['Valor_Total']=pd.to_numeric(df_vendas['Valor_Total'], errors='coerce').fillna(0)
        total=df_vendas['Valor_Total'].sum()
        c1,c2,c3=st.columns(3)
        c1.metric("Faturamento Total", f"R$ {total:,.2f}")
        c2.metric("Total Vendas", len(df_vendas))
        c3.metric("Ticket Médio", f"R$ {total/len(df_vendas):,.2f}" if len(df_vendas)>0 else "R$ 0")
    else:
        st.warning("Sem vendas")

elif menu=="Vendas":
    st.title("Todas as Vendas")
    st.dataframe(df_vendas, use_container_width=True)

elif menu=="Cadastrar Venda":
    st.title("Nova Venda 🚀")
    lista = df_clientes["Nome"].tolist() if not df_clientes.empty else []
    sel = st.selectbox("Cliente *", ["Selecione..."]+lista+["Cliente Avulso"])
    cidade_auto=estado_auto=""
    if sel not in ["Selecione...","Cliente Avulso",""] and not df_clientes.empty:
        d=df_clientes[df_clientes["Nome"]==sel]
        if not d.empty:
            cidade_auto=d.iloc[0].get("Cidade","")
            estado_auto=d.iloc[0].get("Estado","")
    with st.form("venda"):
        c1,c2=st.columns(2)
        with c1:
            produto=st.selectbox("Produto", df_produtos["Nome"].tolist() if not df_produtos.empty else ["Soja Premium"])
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
    st.dataframe(df_clientes, use_container_width=True)

elif menu=="Novo Cliente":
    st.title("➕ Novo Cliente")

    st.subheader("📄 Upload Sintegra")
    arquivo = st.file_uploader("Arraste o PDF do Sintegra aqui (opcional)", type=["pdf"])

    if arquivo is not None:
        with st.spinner("Lendo Sintegra..."):
            try:
                import PyPDF2
                texto=""
                reader=PyPDF2.PdfReader(arquivo)
                for p in reader.pages:
                    texto+=p.extract_text() or ""

                cnpj=re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
                ie=re.search(r'Inscri[çc][aã]o Estadual[:\s]*([0-9\.\-]+)', texto, re.I)

                dados={}
                if cnpj: dados["cpf_cnpj"]=cnpj.group(0)
                if ie: dados["ie"]=ie.group(1)

                # Tenta razão social
                m_razao=re.search(r'Raz[aã]o Social[:\s]*([^\n]+)', texto, re.I)
                if m_razao: dados["nome"]=m_razao.group(1).strip()[:80]

                st.session_state.sintegra_dados=dados
                if dados:
                    st.success(f"✅ Dados encontrados no Sintegra: {dados}")
                else:
                    st.warning("PDF lido, mas não achei CNPJ/IE automático. Preencha manual.")
            except Exception as e:
                st.error(f"Erro ao ler PDF: {e}")

    st.divider()
    st.subheader("Endereço - CEP com Lupa")
    c_cep, c_btn = st.columns([3,1])
    with c_cep:
        cep_input=st.text_input("CEP *", placeholder="78048-000", value=st.session_state.cep_last)
    with c_btn:
        st.write(""); st.write("")
        buscar=st.button("🔍 Buscar CEP")

    if buscar and cep_input:
        dcep=buscar_cep(cep_input)
        if dcep:
            st.session_state.cep_data["endereco"]=dcep.get("logradouro","")
            st.session_state.cep_data["cidade"]=dcep.get("localidade","")
            st.session_state.cep_data["estado"]=dcep.get("uf","")
            st.session_state.cep_data["complemento"]=dcep.get("complemento","")
            st.session_state.cep_last=cep_input
            st.success(f"Endereço encontrado: {dcep.get('logradouro')} - {dcep.get('bairro')}")
        else:
            st.error("CEP não encontrado")

    with st.form("cliente"):
        c1,c2=st.columns(2)
        with c1:
            nome=st.text_input("Nome Completo / Razão Social *", value=st.session_state.sintegra_dados.get("nome",""))
            telefone=st.text_input("Telefone / WhatsApp", placeholder="(65) 9 9999-9999")
            cpf=st.text_input("CPF / CNPJ", value=st.session_state.sintegra_dados.get("cpf_cnpj",""))
            ie=st.text_input("Inscrição Estadual", value=st.session_state.sintegra_dados.get("ie",""))
            fazenda=st.text_input("Nome da Fazenda")
        with c2:
            endereco=st.text_input("Endereço", value=st.session_state.cep_data.get("endereco",""))
            numero=st.text_input("Nº", placeholder="123")
            complemento=st.text_input("Complemento", value=st.session_state.cep_data.get("complemento",""))
            cidade=st.text_input("Cidade", value=st.session_state.cep_data.get("cidade",""))
            estado=st.text_input("Estado (UF)", value=st.session_state.cep_data.get("estado",""), max_chars=2)

        if st.form_submit_button("Salvar Cliente 🌿"):
            if not nome:
                st.error("Nome obrigatório")
            else:
                novo_id=len(df_clientes)+1
                ws_clientes.append_row([novo_id, nome, telefone, cidade, estado.upper(), fazenda, cpf, cep_input, endereco, numero, complemento, ie, datetime.now().strftime("%Y-%m-%d")])
                st.session_state.sintegra_dados={}
                st.success(f"Cliente {nome} salvo!"); st.balloons(); st.rerun()
