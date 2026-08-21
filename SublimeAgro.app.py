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
.stButton>button { background-color: #4caf50; color: white; border-radius: 10px; width: 100%; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def conecta_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

try:
    sh = conecta_gsheets()
    df_vendas = pd.DataFrame(sh.worksheet("Vendas").get_all_records())
except Exception as e:
    st.error(f"Conecte a planilha nos Secrets: {e}")
    st.stop()

with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    menu = st.radio("Menu", ["Dashboard", "Vendas", "Cadastrar Venda"])
    st.divider()
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;background:#1a2e1f;border:1px solid #2a4a32;padding:12px;border-radius:12px;">
        <div style="background:#4caf50;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;font-size:18px;">IM</div>
        <div><b style="color:#e8f5e9;">Igor Melo</b><br><span style="color:#4caf50;font-size:12px;">Admin • Online 🟢</span></div>
    </div>
    """, unsafe_allow_html=True)

# ... resto do código do dashboard que te mandei ...
