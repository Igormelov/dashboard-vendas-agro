import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

st.set_page_config(page_title="SUBLIME Agro - Prospecção", layout="wide", page_icon="🌱", initial_sidebar_state="expanded")

# --- CONEXÃO ---
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

# --- FUNÇÕES DE PROSPECÇÃO ---
def get_coordenadas(cidade, estado):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={cidade},{estado},Brasil&format=json&limit=1"
        r = requests.get(url, headers={"User-Agent":"SUBLIME Agro"}, timeout=10)
        if r.status_code == 200 and r.json():
            d = r.json()[0]
            return float(d["lat"]), float(d["lon"])
    except: pass
    return None, None

def buscar_osm(lat, lon, raio=30000):
    """Busca no OpenStreetMap via Overpass"""
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Tags que nos interessam para agro
    query = f"""
    [out:json][timeout:25];
    (
      node["landuse"="farmyard"](around:{raio},{lat},{lon});
      way["landuse"="farmyard"](around:{raio},{lat},{lon});
      node["industrial"="agricultural"](around:{raio},{lat},{lon});
      node["shop"="agrarian"](around:{raio},{lat},{lon});
      node["craft"="agricultural"](around:{raio},{lat},{lon});
      node["company"="agriculture"](around:{raio},{lat},{lon});
      node["name"~"confinamento|fazenda|agropecuaria|ração|racao|cooperativa",i](around:{raio},{lat},{lon});
    );
    out center 100;
    """
    try:
        r = requests.post(overpass_url, data={"data": query}, timeout=30)
        if r.status_code == 200:
            return r.json().get("elements", [])
    except Exception as e:
        st.error(f"Erro Overpass: {e}")
    return []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
    <div style="background:white; padding:12px; border-radius:12px; text-align:center; margin-bottom:10px;">
        <div style="font-weight:900; font-size:20px; color:#1a2a4a;">🌿 SUBLIME Agro</div>
        <div style="font-size:12px; background:#c5e8c8; display:inline-block; padding:2px 8px; border-radius:6px; color:#1a4a2a; font-weight:700;">PROSPECÇÃO</div>
    </div>
    """, unsafe_allow_html=True)
    menu = st.radio("Menu", ["🔍 Prospectar Cidade", "📋 Meus Prospects", "🗺️ Mapa"])

# --- TELA 1: PROSPECTAR ---
if menu == "🔍 Prospectar Cidade":
    st.title("🔍 Prospectar Clientes por Cidade")
    st.markdown("Escolha uma cidade e vamos buscar confinamentos, fazendas, fábricas de ração e cooperativas automaticamente.")

    c1, c2, c3 = st.columns([2,1,1])
    with c1: cidade = st.text_input("Cidade", "Rondonópolis")
    with c2: estado = st.text_input("UF", "MT", max_chars=2)
    with c3: raio = st.selectbox("Raio de busca", [10, 20, 30, 50], index=2, format_func=lambda x: f"{x} km")

    tipos = st.multiselect("O que buscar?",
        ["Confinamentos", "Fazendas de Gado", "Fábricas de Ração", "Cooperativas", "Lojas Agropecuárias", "Frigoríficos"],
        default=["Confinamentos", "Fazendas de Gado", "Fábricas de Ração"])

    if st.button("🚀 Buscar Potenciais Clientes", type="primary", use_container_width=True):
        with st.spinner(f"Varrendo {cidade}-{estado}..."):
            lat, lon = get_coordenadas(cidade, estado)
            if not lat:
                st.error("Cidade não encontrada. Tente Cidade + Estado ex: Rondonopolis, MT")
            else:
                st.info(f"📍 Centro de {cidade}: {lat:.4f}, {lon:.4f} | Raio {raio}km")
                elementos = buscar_osm(lat, lon, raio*1000)

                resultados = []
                for el in elementos:
                    tags = el.get("tags", {})
                    nome = tags.get("name", "Sem nome")
                    if len(nome) < 3: continue
                    resultados.append({
                        "Nome": nome,
                        "Tipo": tags.get("landuse", tags.get("shop", tags.get("industrial", "Agro"))),
                        "Endereco": f"{tags.get('addr:street','')} {tags.get('addr:housenumber','')}".strip(),
                        "Telefone": tags.get("phone", tags.get("contact:phone","")),
                        "Cidade": cidade,
                        "Estado": estado.upper(),
                        "Fonte": "OpenStreetMap",
                        "Lat": el.get("lat") or el.get("center",{}).get("lat"),
                        "Lon": el.get("lon") or el.get("center",{}).get("lon"),
                    })

                if resultados:
                    df_res = pd.DataFrame(resultados).drop_duplicates(subset=["Nome"])
                    st.success(f"✅ Encontrados {len(df_res)} potenciais clientes!")
                    st.dataframe(df_res, use_container_width=True)

                    # Salvar no Sheets
                    if st.button(f"💾 Salvar {len(df_res)} no Google Sheets"):
                        existentes = pd.DataFrame(ws.get_all_records())
                        novos = 0
                        for _, row in df_res.iterrows():
                            ws.append_row([
                                len(existentes)+novos+1,
                                row["Nome"], row["Tipo"], row["Telefone"],
                                row["Cidade"], row["Estado"], row["Endereco"],
                                row["Fonte"], datetime.now().strftime("%Y-%m-%d"), "Novo"
                            ])
                            novos+=1
                        st.success(f"{novos} salvos em Prospects!")
                else:
                    st.warning("Nenhum resultado no OSM. Vamos tentar via Google? (precisa de API Key)")

    st.divider()
    st.markdown("### 🔧 Como deixar 10x mais forte")
    st.info("""
    **Para trazer telefone e WhatsApp real:**
    1. Adicione no `secrets.toml`: `GOOGLE_PLACES_API_KEY = "sua_chave"`
    2. Eu já integro a busca: `confinamento em Rondonópolis MT`, `fabrica de ração em...`

    Quer que eu já implemente com Google Places? É só me mandar a API Key que eu atualizo o código.
    """)

elif menu == "📋 Meus Prospects":
    st.title("📋 Prospects Salvos")
    df = pd.DataFrame(ws.get_all_records())
    if df.empty:
        st.info("Nenhum prospect salvo ainda. Vá em Prospectar Cidade.")
    else:
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar CSV", df.to_csv(index=False), "prospects.csv")

else:
    st.title("🗺️ Mapa de Prospects")
    df = pd.DataFrame(ws.get_all_records())
    if df.empty:
        st.info("Sem dados para mapa")
    else:
        # Placeholder para mapa
        st.map(pd.DataFrame({"lat": [-16.47], "lon": [-54.63]}))
        st.caption("Mapa completo entra quando tivermos lat/lon dos prospects")
