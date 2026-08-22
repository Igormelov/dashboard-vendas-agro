import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests, time, urllib.parse
import streamlit.components.v1 as components

st.set_page_config(page_title="SUBLIME Agro FREE", layout="wide", page_icon="🌱")

st.markdown("""<style>.stApp{background:#0f2315!important} h1,h2,h3,p,label{color:white!important}</style>""", unsafe_allow_html=True)

@st.cache_resource
def conecta():
    scope=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds_dict=dict(st.secrets["gcp_service_account"])
    if "\\n" in creds_dict["private_key"]:
        creds_dict["private_key"]=creds_dict["private_key"].replace("\\n","\n")
    creds=Credentials.from_service_account_info(creds_dict, scopes=scope)
    client=gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

sh=conecta()
HEADERS=["ID","Nome","Tipo","Telefone","Cidade","Estado","Endereco","Fonte","Data","Status"]
try: ws=sh.worksheet("Prospects")
except:
    ws=sh.add_worksheet(title="Prospects", rows=2000, cols=len(HEADERS))
    ws.append_row(HEADERS)

def get_latlon(cidade, estado):
    try:
        url=f"https://nominatim.openstreetmap.org/search?q={cidade},{estado},Brasil&format=json&limit=1"
        r=requests.get(url, headers={"User-Agent":"SUBLIME"}, timeout=10)
        if r.json(): return float(r.json()[0]["lat"]), float(r.json()[0]["lon"])
    except: pass
    return None,None

def buscar_free(cidade, estado, termos):
    """Busca 100% free - Photon + Nominatim + Overpass Kumi"""
    resultados=[]
    # 1. Photon (mais estável que Overpass)
    for termo in termos:
        try:
            q=f"{termo} {cidade} {estado}"
            # Photon
            url=f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=20&lang=pt"
            r=requests.get(url, timeout=10)
            if r.status_code==200:
                for f in r.json().get("features",[]):
                    props=f.get("properties",{})
                    resultados.append({
                        "Nome": props.get("name", termo.title()),
                        "Tipo": termo,
                        "Endereco": f"{props.get('street','')} {props.get('city','')} {props.get('state','')}",
                        "Telefone": props.get("phone",""),
                        "Cidade": cidade, "Estado": estado,
                        "Fonte": "Photon/OSM",
                        "Lat": f["geometry"]["coordinates"][1],
                        "Lon": f["geometry"]["coordinates"][0]
                    })
            time.sleep(0.5)
        except: continue

    # 2. Overpass Kumi (backup)
    lat,lon=get_latlon(cidade,estado)
    if lat:
        try:
            query=f"""[out:json][timeout:20];(node["shop"="agrarian"](around:30000,{lat},{lon});node["landuse"="farmyard"](around:30000,{lat},{lon});way["landuse"="farmyard"](around:30000,{lat},{lon}););out center 50;"""
            r=requests.post("https://overpass.kumi.systems/api/interpreter", data={"data":query}, timeout=20)
            if r.status_code==200:
                for el in r.json().get("elements",[]):
                    tags=el.get("tags",{})
                    if tags.get("name"):
                        resultados.append({
                            "Nome": tags["name"], "Tipo": "Fazenda OSM",
                            "Endereco": f"{cidade}-{estado}", "Telefone": tags.get("phone",""),
                            "Cidade": cidade, "Estado": estado, "Fonte": "Overpass Kumi",
                            "Lat": el.get("lat"), "Lon": el.get("lon")
                        })
        except: pass
    return resultados

with st.sidebar:
    st.markdown('<div style="background:white;padding:10px;border-radius:10px;text-align:center"><b>🌿 SUBLIME Agro</b><br><span style="background:#c5e8c8;padding:2px 6px;border-radius:5px;font-size:11px">100% FREE</span></div>', unsafe_allow_html=True)
    menu=st.radio("Menu", ["🔍 Prospectar Cidade", "🗺️ Mapa Google (Grátis)", "📋 Meus Prospects"])

if menu=="🔍 Prospectar Cidade":
    st.title("🔍 Prospecção 100% Grátis - Sem Cartão")
    c1,c2=st.columns(2)
    with c1: cidade=st.text_input("Cidade", "Rondonópolis")
    with c2: estado=st.text_input("UF", "MT", max_chars=2)

    tipos=st.multiselect("Buscar", ["confinamento","fazenda","fabrica de racao","cooperativa","agropecuaria","frigorifico"], default=["fazenda","confinamento","fabrica de racao"])

    if st.button("🚀 Buscar Agora - FREE", type="primary", use_container_width=True):
        with st.spinner(f"Varrendo {cidade} sem API paga..."):
            res=buscar_free(cidade,estado,tipos)
            if res:
                df=pd.DataFrame(res).drop_duplicates(subset=["Nome"])
                df=df[df["Nome"].str.len()>3]
                st.success(f"✅ {len(df)} encontrados - 100% grátis!")
                st.dataframe(df[["Nome","Tipo","Endereco","Telefone","Fonte"]], use_container_width=True)

                if st.button(f"💾 Salvar {len(df)} no Sheets"):
                    for _,r in df.iterrows():
                        ws.append_row([datetime.now().strftime("%H%M%S"), r["Nome"], r["Tipo"], r["Telefone"], r["Cidade"], r["Estado"], r["Endereco"], r["Fonte"], datetime.now().strftime("%Y-%m-%d"), "Novo"])
                    st.balloons(); st.success("Salvo!")
            else:
                st.error("Nada no OSM. Use a aba Mapa Google.")

elif menu=="🗺️ Mapa Google (Grátis)":
    st.title("🗺️ Google Maps Dentro do App - Modo Manual Grátis")
    st.markdown("Esse é o jeito grátis que funciona igual sua print - você vê o telefone e clica pra salvar")

    c1,c2,c3=st.columns([2,1,1])
    with c1: cidade=st.text_input("Cidade Maps", "Rondonópolis", key="cm")
    with c2: estado=st.text_input("UF Maps", "MT", key="um")
    with c3: tipo=st.selectbox("O que ver", ["fazendas de gado","confinamento","fabrica de racao","cooperativa agricola"])

    lat,lon=get_latlon(cidade,estado)
    if lat:
        query_url=urllib.parse.quote(f"{tipo} em {cidade} {estado}")
        maps_url=f"https://www.google.com/maps/search/{query_url}/@{lat},{lon},11z"
        components.iframe(maps_url, height=550)
        st.info("👆 Navegue no mapa acima. Quando achar um com telefone (66) 999..., copie e salve abaixo:")

        with st.form("save_manual"):
            c1,c2=st.columns(2)
            with c1:
                nome=st.text_input("Nome visto no mapa (ex: FAZENDA MORRO DA LUA)")
                tel=st.text_input("Telefone visto")
            with c2:
                end=st.text_input("Endereço")
                tipo_f=st.text_input("Tipo", value=tipo)
            if st.form_submit_button("💾 Salvar do Mapa - Grátis"):
                if nome:
                    ws.append_row([datetime.now().strftime("%H%M%S"), nome, tipo_f, tel, cidade, estado, end, "Google Maps Manual FREE", datetime.now().strftime("%Y-%m-%d"), "Novo"])
                    st.success(f"{nome} salvo!")

else:
    st.title("📋 Prospects")
    df=pd.DataFrame(ws.get_all_records())
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar CSV", df.to_csv(index=False), "prospects.csv")
    else: st.info("Vazio")
