import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="SUBLIME Agro - Zerando", layout="wide")
st.warning("⚠️ MODO LIMPEZA TOTAL - Vai apagar tudo")

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

if st.button("🔴 CONFIRMAR - APAGAR TUDO E ZERAR", type="primary"):
    for ws in sh.worksheets():
        try:
            sh.del_worksheet(ws)
        except:
            pass
    
    HEADERS_CLIENTES = ["ID","Nome","Telefone","Cidade","Estado","Fazenda","CPF_CNPJ","CEP","Endereco","Numero","Complemento","IE","Data_Cadastro"]
    ws = sh.add_worksheet(title="Clientes", rows=1000, cols=len(HEADERS_CLIENTES))
    ws.append_row(HEADERS_CLIENTES)
    
    st.success("✅ Tudo apagado e zerado! Agora só tem a aba Clientes limpa.")
    st.balloons()
