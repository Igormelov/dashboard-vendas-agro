import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests, time, urllib.parse
import folium
from streamlit_folium import st_folium

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
    return -16.4708, -54.6386

def buscar_free(cidade, estado, termos):
    resultados=[]
    for termo in termos:
        try:
            q=f"{termo} {cidade} {estado}"
            url=f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=20&lang=pt"
            r=requests.get(url, timeout=10)
            if r.status_code==200:
                for f in r.json().get("features",[]):
                    props=f.get("properties",{})
                    if props.get("name"):
                        resultados.append({
                            "Nome": props.get("name"), "Tipo": termo,
                            "Endereco": f"{props.get('street','')} {props.get('city','')}",
                            "Telefone": props.get("phone",""),
                            "Cidade": cidade, "Estado": estado, "Fonte": "Photon",
                            "Lat": f["geometry"]["coordinates"][1], "Lon": f["geometry"]["coordinates"][0]
                        })
            time.sleep(0.5)
        except: continue
    return resultados

with st.sidebar:
    st.markdown('<div style="background:white;padding:10px;border-radius:10px;text-align:center"><b>🌿 SUBLIME Agro</b><br><span style="background:#c5e8c8;padding:2px 6px;border-radius:5px;font-size:11px">v5.1 FIX</span></div>', unsafe_allow_html=True)
    menu=st.radio("Menu", ["🔍 Prospectar Cidade", "🗺️ Mapa que FUNCIONA", "📋 Meus Prospects"])

if menu=="🔍 Prospectar Cidade":
    st.title("🔍 Prospecção 100% Grátis")
    c1,c2=st.columns(2)
    with c1: cidade=st.text_input("Cidade", "Rondonópolis")
    with c2: estado=st.text_input("UF", "MT", max_chars=2)
    tipos=st.multiselect("Buscar", ["confinamento","fazenda","fabrica de racao","cooperativa","agropecuaria"], default=["fazenda","confinamento"])
    if st.button("🚀 Buscar Agora", type="primary", use_container_width=True):
        with st.spinner(f"Varrendo {cidade}..."):
            res=buscar_free(cidade,estado,tipos)
            if res:
                df=pd.DataFrame(res).drop_duplicates(subset=["Nome"])
                st.success(f"✅ {len(df)} encontrados!")
                st.dataframe(df[["Nome","Tipo","Endereco","Fonte"]], use_container_width=True)
                # Mapa com os resultados
                lat,lon=get_latlon(cidade,estado)
                m=folium.Map(location=[lat,lon], zoom_start=11)
                for _,r in df.iterrows():
                    if r["Lat"]: folium.Marker([r["Lat"], r["Lon"]], popup=r["Nome"], icon=folium.Icon(color="green")).add_to(m)
                st_folium(m, height=400, use_container_width=True)

                if st.button(f"💾 Salvar {len(df)}"):
                    for _,r in df.iterrows():
                        ws.append_row([datetime.now().strftime("%H%M%S"), r["Nome"], r["Tipo"], r["Telefone"], r["Cidade"], r["Estado"], r["Endereco"], r["Fonte"], datetime.now().strftime("%Y-%m-%d"), "Novo"])
                    st.balloons()
            else: st.warning("Nada encontrado. Tente o Mapa.")

elif menu=="🗺️ Mapa que FUNCIONA":
    st.title("🗺️ Mapa - Corrigido (OpenStreetMap + Google em nova aba)")
    st.warning("Google bloqueia dentro do app (sua print com ícone quebrado é por isso). Agora uso OSM dentro + botão pro Google.")

    c1,c2,c3=st.columns([2,1,1])
    with c1: cidade=st.text_input("Cidade", "Rondonópolis", key="cm")
    with c2: estado=st.text_input("UF", "MT", key="um")
    with c3: tipo=st.selectbox("Buscar", ["fazendas de gado","confinamento","fabrica de racao","cooperativa agricola"])

    lat,lon=get_latlon(cidade,estado)

    # Botão que abre Google Maps de verdade (igual sua primeira print)
    query_url=urllib.parse.quote(f"{tipo} em {cidade} {estado}")
    gmaps_link=f"https://www.google.com/maps/search/{query_url}/@{lat},{lon},11z"

    st.link_button(f"🔗 ABRIR GOOGLE MAPS - {tipo} em {cidade} (igual sua 1ª print)", gmaps_link, type="primary", use_container_width=True)
    st.caption("Isso abre o Google Maps real em nova aba, com telefone (66) 99928-3411 igual você viu na Fazenda Morro da Lua")

    # Mapa que FUNCIONA dentro do Streamlit
    st.markdown("### Mapa dentro do app (OpenStreetMap - funciona)")
    m=folium.Map(location=[lat,lon], zoom_start=11)
    folium.Marker([lat,lon], popup=f"{cidade}-{estado}", icon=folium.Icon(color="red", icon="star")).add_to(m)
    # Busca e plota
    res=buscar_free(cidade,estado,[tipo])
    for r in res[:15]:
        folium.Marker([r["Lat"], r["Lon"]], popup=f"{r['Nome']}", icon=folium.Icon(color="green", icon="leaf")).add_to(m)

    st_folium(m, height=500, use_container_width=True)

    with st.form("manual"):
        st.markdown("**Viu no Google Maps? Salva aqui:**")
        c1,c2=st.columns(2)
        with c1: nome=st.text_input("Nome (ex: FAZENDA MORRO DA LUA)"); tel=st.text_input("Telefone")
        with c2: end=st.text_input("Endereço"); tipo_f=st.text_input("Tipo", value=tipo)
        if st.form_submit_button("💾 Salvar"):
            if nome:
                ws.append_row([datetime.now().strftime("%H%M%S"), nome, tipo_f, tel, cidade, estado, end, "Google Maps Manual", datetime.now().strftime("%Y-%m-%d"), "Novo"])
                st.success("Salvo!")

else:
    st.title("📋 Prospects")
    df=pd.DataFrame(ws.get_all_records())
    if not df.empty: st.dataframe(df, use_container_width=True)
