import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import time

st.set_page_config(page_title="SUBLIME Agro - Prospecção", layout="wide", page_icon="🌱", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background: #0f2315!important; }
[data-testid="stHeader"] { background: #0f2315!important; }
h1, h2, h3, p, label { color: white!important; }
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background: #1e3a26!important; color: white!important; border: 1.5px solid #2e6b3a!important;
}
</style>
""", unsafe_allow_html=True)

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
HEADERS = ["ID","Nome","Tipo","Telefone","Cidade","Estado","Endereco","Fonte","Data_Prospeccao","Status"]
try:
    ws = sh.worksheet("Prospects")
except:
    ws = sh.add_worksheet(title="Prospects", rows=2000, cols=len(HEADERS))
    ws.append_row(HEADERS)

def get_coordenadas(cidade, estado):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={cidade},{estado},Brasil&format=json&limit=1"
        r = requests.get(url, headers={"User-Agent":"SUBLIME-Agro/1.0"}, timeout=10)
        if r.status_code == 200 and r.json():
            d = r.json()[0]
            return float(d["lat"]), float(d["lon"])
    except: pass
    return None, None

def buscar_overpass_com_retry(lat, lon, raio):
    endpoints = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    query = f"""
    [out:json][timeout:25];
    (
      node["landuse"="farmyard"](around:{raio},{lat},{lon});
      way["landuse"="farmyard"](around:{raio},{lat},{lon});
      node["shop"="agrarian"](around:{raio},{lat},{lon});
      node["industrial"="agricultural"](around:{raio},{lat},{lon});
      node["name"~"confinamento|fazenda|agro|racao|cooperativa",i](around:{raio},{lat},{lon});
    );
    out center 80;
    """
    for endpoint in endpoints:
        try:
            r = requests.post(endpoint, data={"data": query}, timeout=30, headers={"User-Agent":"SUBLIME-Agro/1.0"})
            if r.status_code == 200:
                return r.json().get("elements", [])
        except:
            time.sleep(1)
            continue
    return []

def buscar_nominatim_texto(cidade, estado, termos):
    """Fallback: busca textual direta"""
    resultados = []
    for termo in termos:
        try:
            q = f"{termo} {cidade} {estado}"
            url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=15&addressdetails=1"
            r = requests.get(url, headers={"User-Agent":"SUBLIME-Agro/1.0"}, timeout=10)
            if r.status_code == 200:
                for item in r.json():
                    resultados.append({
                        "Nome": item.get("display_name","").split(",")[0],
                        "Tipo": termo,
                        "Endereco": item.get("display_name",""),
                        "Telefone": "",
                        "Cidade": cidade,
                        "Estado": estado,
                        "Fonte": "Nominatim",
                        "Lat": item.get("lat"),
                        "Lon": item.get("lon"),
                        "_raw": item
                    })
            time.sleep(1) # respeita limite nominatim
        except: continue
    return resultados

with st.sidebar:
    st.markdown("""
    <div style="background:white; padding:12px; border-radius:12px; text-align:center; margin-bottom:10px;">
        <div style="font-weight:900; font-size:20px; color:#1a2a4a;">🌿 SUBLIME Agro</div>
        <div style="font-size:12px; background:#c5e8c8; display:inline-block; padding:2px 8px; border-radius:6px; color:#1a4a2a; font-weight:700;">PROSPECÇÃO v4.5</div>
    </div>
    """, unsafe_allow_html=True)
    menu = st.radio("Menu", ["🔍 Prospectar Cidade", "📋 Meus Prospects"])

if menu == "🔍 Prospectar Cidade":
    st.title("🔍 Prospectar Clientes")
    st.markdown("Escolha uma cidade e vamos buscar confinamentos, fazendas, fábricas de ração e cooperativas automaticamente.")

    c1, c2, c3 = st.columns([2,1,1])
    with c1: cidade = st.text_input("Cidade", "Rondonópolis")
    with c2: estado = st.text_input("UF", "MT", max_chars=2)
    with c3: raio = st.selectbox("Raio", [10,20,30,50], index=2, format_func=lambda x: f"{x} km")

    tipos = st.multiselect("O que buscar?",
        ["Confinamento", "Fazenda", "Fabrica Racao", "Cooperativa", "Agropecuaria", "Frigorifico"],
        default=["Confinamento", "Fazenda", "Fabrica Racao"])

    if st.button("🚀 Buscar Potenciais Clientes", type="primary", use_container_width=True):
        lat, lon = get_coordenadas(cidade, estado)
        if not lat:
            st.error("Cidade não encontrada")
        else:
            st.info(f"📍 Centro de {cidade}: {lat:.4f}, {lon:.4f} | Raio {raio}km")

            with st.spinner("Tentando Overpass (3 servidores)..."):
                elementos = buscar_overpass_com_retry(lat, lon, raio*1000)

            resultados = []
            if elementos:
                for el in elementos:
                    tags = el.get("tags", {})
                    nome = tags.get("name", "Fazenda sem nome")
                    resultados.append({
                        "Nome": nome,
                        "Tipo": tags.get("landuse","Agro"),
                        "Endereco": f"{tags.get('addr:street','')} {cidade}-{estado}",
                        "Telefone": tags.get("phone",""),
                        "Cidade": cidade, "Estado": estado.upper(),
                        "Fonte": "Overpass", "Lat": el.get("lat"), "Lon": el.get("lon")
                    })

            # Se Overpass falhar, usa busca por texto (que funcionou no seu caso)
            if not resultados:
                st.warning("Overpass instável, usando busca textual (fallback) - mais lento mas funciona")
                resultados = buscar_nominatim_texto(cidade, estado, tipos)

            if resultados:
                df_res = pd.DataFrame(resultados).drop_duplicates(subset=["Nome"])
                st.success(f"✅ {len(df_res)} potenciais clientes encontrados!")
                st.dataframe(df_res[["Nome","Tipo","Endereco","Telefone","Fonte"]], use_container_width=True)

                if st.button(f"💾 Salvar {len(df_res)} no Sheets", type="primary"):
                    for _, row in df_res.iterrows():
                        ws.append_row([
                            datetime.now().strftime("%Y%m%d%H%M%S"),
                            row["Nome"], row["Tipo"], row["Telefone"],
                            row["Cidade"], row["Estado"], row["Endereco"],
                            row["Fonte"], datetime.now().strftime("%Y-%m-%d"), "Novo"
                        ])
                    st.success("Salvos!"); st.balloons()
            else:
                st.error("Nenhum resultado. Tente outra cidade ou aumente o raio.")

elif menu == "📋 Meus Prospects":
    st.title("📋 Prospects Salvos")
    df = pd.DataFrame(ws.get_all_records())
    if df.empty:
        st.info("Nenhum prospect ainda")
    else:
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar CSV", df.to_csv(index=False), "prospects.csv")
