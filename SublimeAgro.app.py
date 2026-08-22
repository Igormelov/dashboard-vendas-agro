import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

st.set_page_config(page_title="SUBLIME Agro V4", layout="wide", page_icon="🌱", initial_sidebar_state="expanded")

@st.cache_resource
def conecta():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "\\n" in creds_dict["private_key"]:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

sh = conecta()
ws = sh.worksheet("Clientes")
df = pd.DataFrame(ws.get_all_records())

with st.sidebar:
    st.title("🌿 SUBLIME Agro")
    menu = st.radio("MENU", ["Lista", "Cadastrar Cliente"])

if menu == "Lista":
    st.title("Clientes")
    st.dataframe(df, use_container_width=True)
else:
    st.title("Cadastrar Cliente")
    nome = st.text_input("Nome")
    telefone = st.text_input("Telefone")
    cidade = st.text_input("Cidade")
    if st.button("Salvar"):
        ws.append_row([len(df)+1, nome, telefone, cidade, "", "", "", "", "", "", "", "", datetime.now().strftime("%Y-%m-%d")])
        st.success("Salvo!")
        st.rerun()
