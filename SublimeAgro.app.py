import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime

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

sh = conecta_gsheets()

def get_or_create_ws(nome, headers):
    try:
        ws = sh.worksheet(nome)
    except:
        ws = sh.add_worksheet(title=nome, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws

ws_vendas = get_or_create_ws("Vendas", ["ID","Data","Cliente","Produto","Quantidade","Valor_Unit","Valor_Total","Cidade","Estado","Vendedor","Status"])
ws_produtos = get_or_create_ws("Produtos", ["ID","Nome","Preco","Estoque"])
ws_clientes = get_or_create_ws("Clientes", ["ID","Nome","Telefone","Cidade","Estado","Fazenda","CPF_CNPJ","Data_Cadastro"])

df_vendas = normaliza(pd.DataFrame(ws_vendas.get_all_records()))
df_produtos = normaliza(pd.DataFrame(ws_produtos.get_all_records()))
df_clientes = normaliza(pd.DataFrame(ws_clientes.get_all_records()))

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    menu = st.radio("Menu", ["Dashboard", "Vendas", "Cadastrar Venda", "Clientes", "Novo Cliente"], label_visibility="collapsed")
    st.divider()
    st.markdown("""<div style="display:flex;align-items:center;gap:12px;background:#1a2e1f;border:1px solid #2a4a32;padding:12px;border-radius:12px;">
    <div style="background:#4caf50;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;">IM</div>
    <div><b>Igor Melo</b><br><span style="color:#4caf50;font-size:12px;">Admin • Online 🟢</span></div></div>""", unsafe_allow_html=True)

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("Dashboard de Vendas 🌿")
    if not df_vendas.empty:
        df_vendas['Valor_Total'] = pd.to_numeric(df_vendas['Valor_Total'], errors='coerce').fillna(0)
        total = df_vendas['Valor_Total'].sum()
        qtd = len(df_vendas)
        ticket = total / qtd if qtd > 0 else 0
        c1,c2,c3 = st.columns(3)
        c1.metric("Faturamento Total", f"R$ {total:,.2f}")
        c2.metric("Total de Vendas", qtd)
        c3.metric("Ticket Médio", f"R$ {ticket:,.2f}")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Vendas por Estado")
            fig = px.bar(df_vendas.groupby("Estado")["Valor_Total"].sum().reset_index(), x="Estado", y="Valor_Total", color="Estado", template="plotly_dark")
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Vendas por Produto")
            fig2 = px.pie(df_vendas, names="Produto", values="Valor_Total", hole=0.4, template="plotly_dark")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Sem vendas ainda")

elif menu == "Vendas":
    st.title("Todas as Vendas")
    st.dataframe(df_vendas, use_container_width=True)

elif menu == "Cadastrar Venda":
    st.title("Nova Venda 🚀")
    st.info("Selecione o cliente e a cidade/estado serão preenchidos automaticamente.")

    # 1. Seleciona o cliente FORA do form para atualizar em tempo real
    lista_clientes = df_clientes["Nome"].tolist() if not df_clientes.empty else []
    cliente_selecionado = st.selectbox("Cliente *", ["Selecione..."] + lista_clientes + ["Cliente Avulso"])

    # Busca dados do cliente
    cidade_auto = ""
    estado_auto = ""
    fazenda_auto = ""
    if cliente_selecionado not in ["Selecione...", "Cliente Avulso", ""] and not df_clientes.empty:
        dados_cli = df_clientes[df_clientes["Nome"] == cliente_selecionado]
        if not dados_cli.empty:
            cidade_auto = dados_cli.iloc[0].get("Cidade", "")
            estado_auto = dados_cli.iloc[0].get("Estado", "")
            fazenda_auto = dados_cli.iloc[0].get("Fazenda", "")
            st.success(f"Cliente: {cliente_selecionado} | Fazenda: {fazenda_auto} | {cidade_auto}-{estado_auto}")

    with st.form("venda"):
        c1,c2 = st.columns(2)
        with c1:
            produto = st.selectbox("Produto", df_produtos["Nome"].tolist() if not df_produtos.empty else ["Soja Premium"])
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            # Cidade e Estado já vêm preenchidos mas podem ser editados
            cidade = st.text_input("Cidade", value=cidade_auto)
            estado = st.text_input("Estado (UF)", value=estado_auto, max_chars=2)
        with c2:
            vendedor = st.selectbox("Vendedor", ["Igor Melo","Ana Costa","Bruno Silva","Carlos Lima"])
            status = st.selectbox("Status", ["Pago","Pendente"])
            obs = st.text_input("Fazenda / Obs", value=fazenda_auto)

        valor_unit = 0
        if not df_produtos.empty:
            row = df_produtos[df_produtos["Nome"]==produto]
            if not row.empty:
                try: valor_unit = float(str(row.iloc[0]["Preco"]).replace("R$","").replace(",","."))
                except: valor_unit = 0
        st.write(f"**Valor Unit: R$ {valor_unit:,.2f} | Total: R$ {valor_unit*qtd:,.2f}**")

        if st.form_submit_button("Salvar Venda 🌿"):
            if cliente_selecionado == "Selecione...":
                st.error("Selecione um cliente!")
            else:
                ws_vendas.append_row([len(df_vendas)+1, datetime.now().strftime("%Y-%m-%d"), cliente_selecionado, produto, qtd, valor_unit, valor_unit*qtd, cidade, estado.upper(), vendedor, status])
                st.success(f"Venda para {cliente_selecionado} salva!")
                st.balloons()
                st.rerun()

elif menu == "Clientes":
    st.title("👨‍🌾 Clientes Cadastrados")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total de Clientes", len(df_clientes))
    c2.metric("Cidades Atendidas", df_clientes["Cidade"].nunique() if not df_clientes.empty else 0)
    c3.metric("Estados", df_clientes["Estado"].nunique() if not df_clientes.empty else 0)
    st.divider()
    if df_clientes.empty:
        st.info("Nenhum cliente ainda. Vá em Novo Cliente para cadastrar.")
    else:
        busca = st.text_input("🔍 Buscar cliente por nome ou fazenda")
        if busca:
            df_f = df_clientes[df_clientes.apply(lambda r: busca.lower() in str(r).lower(), axis=1)]
            st.dataframe(df_f, use_container_width=True)
        else:
            st.dataframe(df_clientes.sort_values("ID", ascending=False), use_container_width=True)

elif menu == "Novo Cliente":
    st.title("➕ Novo Cliente")
    with st.form("cliente"):
        c1,c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo *")
            telefone = st.text_input("Telefone / WhatsApp", placeholder="(65) 9 9999-9999")
            cpf = st.text_input("CPF / CNPJ")
        with c2:
            fazenda = st.text_input("Nome da Fazenda")
            cidade = st.text_input("Cidade")
            estado = st.text_input("Estado (UF)", max_chars=2)
        if st.form_submit_button("Salvar Cliente 🌿"):
            if not nome:
                st.error("Nome é obrigatório")
            else:
                novo_id = len(df_clientes)+1
                ws_clientes.append_row([novo_id, nome, telefone, cidade, estado.upper(), fazenda, cpf, datetime.now().strftime("%Y-%m-%d")])
                st.success(f"Cliente {nome} cadastrado com sucesso!")
                st.balloons()
                st.rerun()
