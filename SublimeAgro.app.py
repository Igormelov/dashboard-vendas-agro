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
.stDataFrame { background-color: #1a2e1f; }
</style>
""", unsafe_allow_html=True)

# --- CONEXAO COM GOOGLE SHEETS (COM FIX DO ERRO PEM) ---
@st.cache_resource
def conecta_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    # FIX: corrige a chave privada
    if "\\n" in creds_dict["private_key"]:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

try:
    sh = conecta_gsheets()
    ws_vendas = sh.worksheet("Vendas")
    ws_produtos = sh.worksheet("Produtos")
    df_vendas = pd.DataFrame(ws_vendas.get_all_records())
    df_produtos = pd.DataFrame(ws_produtos.get_all_records())
except Exception as e:
    st.error(f"Erro ao conectar planilha: {e}")
    st.info("Verifique os Secrets e se compartilhou a planilha com: sublime-agro@main-depot-506212-f6.iam.gserviceaccount.com")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    menu = st.radio("Menu", ["Dashboard", "Vendas", "Cadastrar Venda"], label_visibility="collapsed")
    st.divider()
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;background:#1a2e1f;border:1px solid #2a4a32;padding:12px;border-radius:12px;">
        <div style="background:#4caf50;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;font-size:18px;">IM</div>
        <div><b style="color:#e8f5e9;">Igor Melo</b><br><span style="color:#4caf50;font-size:12px;">Admin • Online 🟢</span></div>
    </div>
    """, unsafe_allow_html=True)

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("Dashboard de Vendas 🌿")

    if df_vendas.empty:
        st.warning("Planilha de Vendas vazia. Adicione dados na aba Vendas.")
        st.stop()

    df_vendas['Valor_Total'] = pd.to_numeric(df_vendas['Valor_Total'], errors='coerce').fillna(0)
    df_vendas['Quantidade'] = pd.to_numeric(df_vendas['Quantidade'], errors='coerce').fillna(0)
    df_vendas['Data'] = pd.to_datetime(df_vendas['Data'], errors='coerce')

    total_vendas = df_vendas['Valor_Total'].sum()
    qtd_vendas = len(df_vendas)
    ticket_medio = total_vendas / qtd_vendas if qtd_vendas > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Total", f"R$ {total_vendas:,.2f}")
    col2.metric("Total de Vendas", qtd_vendas)
    col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Vendas por Estado")
        fig = px.bar(df_vendas.groupby("Estado")["Valor_Total"].sum().reset_index(), x="Estado", y="Valor_Total", color="Estado", template="plotly_dark")
        fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Vendas por Produto")
        fig2 = px.pie(df_vendas, names="Produto", values="Valor_Total", hole=0.4, template="plotly_dark")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Histórico de Vendas")
    st.dataframe(df_vendas.sort_values("Data", ascending=False), use_container_width=True)

elif menu == "Vendas":
    st.title("Todas as Vendas")
    st.dataframe(df_vendas, use_container_width=True, height=600)

elif menu == "Cadastrar Venda":
    st.title("Nova Venda")
    with st.form("nova_venda"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente")
            produto = st.selectbox("Produto", df_produtos["Nome"].tolist() if not df_produtos.empty else ["Soja Premium"])
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
        with col2:
            cidade = st.text_input("Cidade")
            estado = st.text_input("Estado (UF)", max_chars=2)
            vendedor = st.selectbox("Vendedor", ["Igor Melo", "Ana Costa", "Bruno Silva", "Carlos Lima"])
            status = st.selectbox("Status", ["Pago", "Pendente"])

        valor_unit = 0
        if not df_produtos.empty:
            prod = df_produtos[df_produtos["Nome"] == produto]
            if not prod.empty:
                valor_unit = float(prod.iloc[0]["Preco"])

        st.write(f"**Valor Unitário:** R$ {valor_unit} | **Total:** R$ {valor_unit * quantidade:,.2f}")

        if st.form_submit_button("Salvar Venda 🚀"):
            nova_linha = [len(df_vendas)+1, datetime.now().strftime("%Y-%m-%d"), cliente, produto, quantidade, valor_unit, valor_unit*quantidade, cidade, estado.upper(), vendedor, status]
            ws_vendas.append_row(nova_linha)
            st.success("Venda cadastrada com sucesso!")
            st.cache_data.clear()
            st.rerun()
