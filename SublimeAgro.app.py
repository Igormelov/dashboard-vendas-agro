import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime
import requests

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
    if len(cep)!= 8:
        return None
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if "erro" not in data:
                return data
    except:
        return None
    return None

sh = conecta_gsheets()

def get_or_create_ws(nome, headers):
    try:
        ws = sh.worksheet(nome)
        # Se já existe mas está sem as colunas novas, não recria, só usa
        existing = ws.row_values(1)
        # Se faltar colunas novas, adiciona no cabeçalho (upgrade automático)
        for h in headers:
            if h not in existing:
                # Adiciona nova coluna no final do header
                pass # Vamos lidar no append, mas mantém simples
        return ws
    except:
        ws = sh.add_worksheet(title=nome, rows=1000, cols=len(headers))
        ws.append_row(headers)
        return ws

# ATUALIZADO com campos de endereço
HEADERS_CLIENTES = ["ID","Nome","Telefone","Cidade","Estado","Fazenda","CPF_CNPJ","CEP","Endereco","Numero","Complemento","Data_Cadastro"]

ws_vendas = get_or_create_ws("Vendas", ["ID","Data","Cliente","Produto","Quantidade","Valor_Unit","Valor_Total","Cidade","Estado","Vendedor","Status"])
ws_produtos = get_or_create_ws("Produtos", ["ID","Nome","Preco","Estoque"])
ws_clientes = get_or_create_ws("Clientes", HEADERS_CLIENTES)

df_vendas = normaliza(pd.DataFrame(ws_vendas.get_all_records()))
df_produtos = normaliza(pd.DataFrame(ws_produtos.get_all_records()))
df_clientes = normaliza(pd.DataFrame(ws_clientes.get_all_records()))

# Session state para CEP
if "cep_data" not in st.session_state:
    st.session_state.cep_data = {"endereco": "", "cidade": "", "estado": "", "complemento": ""}
if "cep_last" not in st.session_state:
    st.session_state.cep_last = ""

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    menu = st.radio("Menu", ["Dashboard", "Vendas", "Cadastrar Venda", "Clientes", "Novo Cliente"], label_visibility="collapsed", index=4)
    st.divider()
    st.markdown("""<div style="display:flex;align-items:center;gap:12px;background:#1a2e1f;border:1px solid #2a4a32;padding:12px;border-radius:12px;">
    <div style="background:#4caf50;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;">IM</div>
    <div><b>Igor Melo</b><br><span style="color:#4caf50;font-size:12px;">Admin • Online 🟢</span></div></div>""", unsafe_allow_html=True)

if menu == "Dashboard":
    st.title("Dashboard de Vendas 🌿")
    if not df_vendas.empty:
        df_vendas['Valor_Total'] = pd.to_numeric(df_vendas['Valor_Total'], errors='coerce').fillna(0)
        total = df_vendas['Valor_Total'].sum()
        c1,c2,c3 = st.columns(3)
        c1.metric("Faturamento Total", f"R$ {total:,.2f}")
        c2.metric("Total de Vendas", len(df_vendas))
        c3.metric("Ticket Médio", f"R$ {total/len(df_vendas):,.2f}")
    else:
        st.warning("Sem vendas ainda")

elif menu == "Vendas":
    st.title("Todas as Vendas")
    st.dataframe(df_vendas, use_container_width=True)

elif menu == "Cadastrar Venda":
    st.title("Nova Venda 🚀")
    lista_clientes = df_clientes["Nome"].tolist() if not df_clientes.empty else []
    cliente_sel = st.selectbox("Cliente *", ["Selecione..."] + lista_clientes + ["Cliente Avulso"])
    cidade_auto = estado_auto = fazenda_auto = ""
    if cliente_sel not in ["Selecione...", "Cliente Avulso", ""] and not df_clientes.empty:
        dados = df_clientes[df_clientes["Nome"]==cliente_sel]
        if not dados.empty:
            cidade_auto = dados.iloc[0].get("Cidade","")
            estado_auto = dados.iloc[0].get("Estado","")
            fazenda_auto = dados.iloc[0].get("Fazenda","")
            st.success(f"{cliente_sel} | {fazenda_auto} - {cidade_auto}/{estado_auto}")
    with st.form("venda"):
        c1,c2 = st.columns(2)
        with c1:
            produto = st.selectbox("Produto", df_produtos["Nome"].tolist() if not df_produtos.empty else ["Soja Premium"])
            qtd = st.number_input("Qtd", 1)
            cidade = st.text_input("Cidade", value=cidade_auto)
            estado = st.text_input("UF", value=estado_auto, max_chars=2)
        with c2:
            vendedor = st.selectbox("Vendedor", ["Igor Melo","Ana Costa","Bruno Silva","Carlos Lima"])
            status = st.selectbox("Status", ["Pago","Pendente"])
        if st.form_submit_button("Salvar Venda 🌿"):
            ws_vendas.append_row([len(df_vendas)+1, datetime.now().strftime("%Y-%m-%d"), cliente_sel, produto, qtd, 0, 0, cidade, estado.upper(), vendedor, status])
            st.success("Venda salva!")
            st.rerun()

elif menu == "Clientes":
    st.title("👨‍🌾 Clientes Cadastrados")
    st.dataframe(df_clientes, use_container_width=True)

elif menu == "Novo Cliente":
    st.title("➕ Novo Cliente")

    # ---- LINHA DO CEP COM LUPA ----
    st.subheader("Endereço")
    col_cep, col_lupa, col_spacer = st.columns([3,1,2])
    with col_cep:
        cep_input = st.text_input("CEP *", placeholder="78000-000", value=st.session_state.cep_last, help="Digite o CEP e clique na lupa")
    with col_lupa:
        st.write("") # espaçamento
        st.write("")
        buscar = st.button("🔍 Buscar CEP")

    if buscar and cep_input:
        with st.spinner("Buscando endereço..."):
            dados_cep = buscar_cep(cep_input)
            if dados_cep:
                st.session_state.cep_data["endereco"] = dados_cep.get("logradouro","")
                st.session_state.cep_data["cidade"] = dados_cep.get("localidade","")
                st.session_state.cep_data["estado"] = dados_cep.get("uf","")
                st.session_state.cep_data["complemento"] = dados_cep.get("complemento","")
                st.session_state.cep_last = cep_input
                st.success(f"Endereço encontrado: {dados_cep.get('logradouro')} - {dados_cep.get('bairro')}")
            else:
                st.error("CEP não encontrado. Verifique o número.")

    # ---- FORMULÁRIO COM CAMPOS NOVOS ----
    with st.form("cliente"):
        c1,c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo *")
            telefone = st.text_input("Telefone / WhatsApp", placeholder="(65) 9 9999-9999")
            cpf = st.text_input("CPF / CNPJ")
            fazenda = st.text_input("Nome da Fazenda")
        with c2:
            # Usa dados do CEP se existirem
            endereco_val = st.session_state.cep_data["endereco"]
            cidade_val = st.session_state.cep_data["cidade"]
            estado_val = st.session_state.cep_data["estado"]
            comp_val = st.session_state.cep_data["complemento"]

            endereco = st.text_input("Endereço", value=endereco_val, placeholder="Rua, Avenida...")
            numero = st.text_input("Nº", placeholder="123")
            complemento = st.text_input("Complemento", value=comp_val, placeholder="Galpão, Lote, Km...")
            cidade = st.text_input("Cidade", value=cidade_val)
            estado = st.text_input("Estado (UF)", value=estado_val, max_chars=2)

        if st.form_submit_button("Salvar Cliente 🌿"):
            if not nome:
                st.error("Nome é obrigatório")
            else:
                novo_id = len(df_clientes)+1
                # Salva na ordem do HEADERS_CLIENTES
                ws_clientes.append_row([
                    novo_id, nome, telefone, cidade, estado.upper(), fazenda, cpf,
                    cep_input, endereco, numero, complemento,
                    datetime.now().strftime("%Y-%m-%d")
                ])
                # Limpa CEP
                st.session_state.cep_data = {"endereco": "", "cidade": "", "estado": "", "complemento": ""}
                st.session_state.cep_last = ""
                st.success(f"Cliente {nome} cadastrado!")
                st.balloons()
                st.rerun()
