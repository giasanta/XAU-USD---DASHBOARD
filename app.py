#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 10:54:00 2025

@author: giannarcos
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from fredapi import Fred


# 🔑 Inserisci qui la tua API Key personale ricevuta da FRED
FRED_API_KEY = "c0d08af81537f58d97f45c1e1f6e83b0"

fred = Fred(api_key=FRED_API_KEY)


def get_cpi_from_fred():
    try:
        # Serie CPI mensile (indice generale)
        cpi_data = fred.get_series("CPIAUCSL")
        latest_date = cpi_data.index[-1]                     # Data ultimo valore
        previous = cpi_data[-13]                             # Valore 12 mesi fa
        latest = cpi_data[-1]                                # Ultimo valore
        cpi_yoy = ((latest - previous) / previous) * 100
        return round(cpi_yoy, 2), latest_date.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Errore nel recupero CPI da FRED: {e}")
        return None, None

st.set_page_config(page_title="XAU/USD Dashboard", layout="wide")
investing_events = []

st.title("📊 XAU/USD Daily Dashboard")


def get_price(ticker):
    try:
        data = yf.download(ticker, period="1d", interval="1m")
        if not data.empty and "Close" in data.columns:
            last_price = data["Close"].dropna().iloc[-1]
            return round(float(last_price), 2)
    except Exception as e:
        print(f"Errore nel recupero di {ticker}: {e}")
    return None

# Recupero prezzi attuali
gold_spot = get_price("XAUUSD=X")
dxy = get_price("DX-Y.NYB")
us10y = get_price("^TNX")

# Recupero CPI attuale
cpi = get_cpi_from_fred()

def get_nfp_from_fred():
    try:
        nfp = fred.get_series("PAYEMS")  # All Employees: Total Nonfarm
        latest = int(nfp[-1])
        previous = int(nfp[-2])
        diff = latest - previous
        return latest, diff
    except Exception as e:
        print(f"Errore nel recupero NFP: {e}")
        return None, None

def get_unemployment_from_fred():
    try:
        urate = fred.get_series("UNRATE")
        latest = round(urate[-1], 2)
        return latest
    except Exception as e:
        print(f"Errore nel recupero Unemployment Rate: {e}")
        return None
    
def get_cot_net_position_from_csv():
    try:
        df = pd.read_csv("cot_gold.csv")
        latest = df.iloc[-1]
        long = int(latest["Noncommercial Long"])
        short = int(latest["Noncommercial Short"])
        net = long - short
        date = latest["Date"]  # Assicurati che la colonna si chiami "Date"
        return net, date
    except Exception as e:
        print(f"Errore nel file COT: {e}")
        return None, None



import feedparser
from textblob import TextBlob

def get_important_news():
    url = "https://news.google.com/rss/search?q=gold+OR+XAUUSD+OR+Federal+Reserve+OR+Trump+OR+geopolitical+OR+inflation+OR+interest+rates&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    filtered_news = []

    for entry in feed.entries[:15]:  # analizziamo le ultime 15 notizie
        title = entry.title.lower()
        summary = entry.summary.lower()
        full_text = f"{title} {summary}"

        relevance = 0
        category = "Altro"
        rationale = "Non riconosciuta come notizia ad alto impatto."

        # Peso iniziale per keyword forti
        if "powell" in full_text or "federal reserve" in full_text:
            relevance += 30
            category = "Politica monetaria"
            rationale = "Coinvolge la Fed o Powell."
        if "rate hike" in full_text or "interest rates" in full_text:
            relevance += 25
            category = "Tassi"
            rationale = "Riguarda politica dei tassi."
        if "inflation" in full_text or "cpi" in full_text:
            relevance += 20
            category = "Inflazione"
            rationale = "Inflazione impatta le mosse della Fed."
        if "geopolitical" in full_text or "conflict" in full_text or "iran" in full_text or "gaza" in full_text:
            relevance += 20
            category = "Geopolitica"
            rationale = "Crisi internazionale: possibile spinta su oro."
        if "gold" in full_text or "safe haven" in full_text:
            relevance += 10
            category = "Mercato oro"
            rationale = "Riferimento diretto al ruolo dell’oro."

        sentiment = TextBlob(full_text).sentiment.polarity
        if sentiment < -0.2:
            relevance += 10
            rationale += " Il tono è negativo (paura/rischio)."

        if relevance >= 30:
            filtered_news.append({
                "title": entry.title,
                "summary": entry.summary,
                "link": entry.link,
                "category": category,
                "rationale": rationale,
                "relevance": relevance,
                "sentiment": sentiment
            })

    return filtered_news





# 📈 GDP USA (trimestrale)

def get_gdp_growth():
    try:
        gdp_series = fred.get_series("GDPC1")  # GDP reale trimestrale (chained 2012 dollars)
        latest = gdp_series.iloc[-1]
        previous = gdp_series.iloc[-2]
        growth = ((latest - previous) / previous) * 100
        date = gdp_series.index[-1].strftime("%Y-%m-%d")
        return round(growth, 2), date
    except Exception as e:
        print(f"❌ Errore recupero GDP: {e}")
        return None, None


# 🔥 Core PCE (YoY)

def get_core_pce_yoy():
    try:
        # Core PCE - Personal Consumption Expenditures Excluding Food and Energy
        pce_series = fred.get_series("PCEPILFE")
        latest = pce_series.iloc[-1]
        previous = pce_series.iloc[-13]  # 12 mesi fa
        yoy = ((latest - previous) / previous) * 100
        date = pce_series.index[-1].strftime("%Y-%m-%d")
        return round(yoy, 2), date
    except Exception as e:
        print(f"❌ Errore recupero Core PCE: {e}")
        return None, None

# 🛍️ Retail Sales (YoY)

def get_retail_sales_yoy():
    try:
        series = fred.get_series("RSAFS")  # Retail Sales: Total (Ex Autos)
        latest = series.iloc[-1]
        previous = series.iloc[-13]
        yoy = ((latest - previous) / previous) * 100
        date = series.index[-1].strftime("%Y-%m-%d")
        return round(yoy, 2), date
    except Exception as e:
        print(f"❌ Errore recupero Retail Sales: {e}")
        return None, None


def get_investing_events_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    import time

    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        url = "https://www.investing.com/economic-calendar/"
        driver.get(url)

        time.sleep(10)

        eventi = []
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.js-event-item")

        for row in rows:
            try:
                country = row.find_element(By.CSS_SELECTOR, "td.flagCur span").get_attribute("title")
                title = row.find_element(By.CSS_SELECTOR, "td.event").text.strip()
                actual = row.find_element(By.CSS_SELECTOR, "td.act").text.strip()
                bull_icons = row.find_elements(By.CSS_SELECTOR, "td.sentiment i.grayFullBullishIcon")
                num_bulls = len(bull_icons)

                try:
                    explanation = row.find_element(By.CSS_SELECTOR, "td.event span.tooltip").get_attribute("data-tooltip")
                except:
                    explanation = ""

                if country == "United States" and num_bulls == 3:
                    eventi.append({
                        "titolo": title,
                        "valore": actual,
                        "tori": num_bulls,
                        "note": explanation
                    })

            except:
                continue

        driver.quit()
        return eventi

    except Exception as e:
        print(f"❌ Errore Selenium Investing: {e}")
        return []



# 📈 Mostra valore CPI e interpretazione
st.subheader("📈 Inflazione USA (CPI YoY)")

cpi, cpi_date = get_cpi_from_fred()

if cpi:
    col_cpi, col_cpi2 = st.columns([1, 3])
    col_cpi.metric("💡 CPI Attuale", f"{cpi}%")
    col_cpi.caption(f"📅 Ultimo aggiornamento: {cpi_date}")

    # Impatto automatico
    if cpi > 4.0:
        col_cpi2.error("🔴 Inflazione alta: probabile supporto rialzista per l'oro. (Impatto 30%)")
    elif cpi < 2.5:
        col_cpi2.success("🟢 Inflazione bassa: poco impatto sull’oro. (Impatto 5%)")
    else:
        col_cpi2.warning("🟡 Inflazione moderata: impatto medio. (Impatto 15%)")
else:
    st.warning("⚠️ Impossibile recuperare il valore CPI.")
    


# 👷‍♂️ Occupazione USA (NFP + Disoccupazione)
st.subheader("👷‍♂️ Occupazione USA (NFP + Disoccupazione)")

nfp_total, nfp_diff = get_nfp_from_fred()
unemployment = get_unemployment_from_fred()

col_nfp, col_urate = st.columns(2)

# NFP
if nfp_total is not None:
    nfp_data = fred.get_series("PAYEMS")
    last_nfp_date = nfp_data.index[-1].strftime("%Y-%m-%d")

    col_nfp.metric("📊 NFP Totale", f"{nfp_total:,}", f"{nfp_diff:+,}")

    if nfp_diff > 200_000:
        col_nfp.error("🔴 Forte creazione di posti di lavoro: pressione ribassista sull'oro (Impatto 30%)")
    elif nfp_diff < 50_000:
        col_nfp.warning("🟡 Creazione modesta: impatto moderato (Impatto 15%)")
    elif nfp_diff < 0:
        col_nfp.success("🟢 Lavoro in calo: possibile supporto per l'oro (Impatto 25%)")
    else:
        col_nfp.info("📌 Nessun impatto rilevante.")

    col_nfp.caption(f"📅 Ultimo aggiornamento: {last_nfp_date}")

# Tasso di disoccupazione
if unemployment is not None:
    urate_data = fred.get_series("UNRATE")
    last_urate_date = urate_data.index[-1].strftime("%Y-%m-%d")

    col_urate.metric("📉 Tasso disoccupazione", f"{unemployment}%")

    if unemployment < 3.8:
        col_urate.success("🟡 Disoccupazione bassa: impatto contenuto (Impatto 10%)")
    elif unemployment >= 4.0:
        col_urate.error("🔴 Disoccupazione in aumento: rischio economico → oro potrebbe salire (Impatto 25%)")
    else:
        col_urate.info("📌 Livello stabile: impatto neutro (Impatto 10%)")

    col_urate.caption(f"📅 Ultimo aggiornamento: {last_urate_date}")
        

# 📦 ISM da file CSV (aggiornato manualmente 1 volta al mese)
st.subheader("📦 ISM Manufacturing & Services (da file)")

try:
    ism_df = pd.read_csv("ism_data.csv")

    col_ism_m, col_ism_s = st.columns(2)

    for index, row in ism_df.iterrows():
        tipo = row["Tipo"]
        valore = float(row["Valore"])
        data = row["Data"]

        if tipo.lower() == "manufacturing":
            col_ism_m.metric("🏭 ISM Manufacturing", f"{valore}")
            if valore < 45:
                col_ism_m.error("🟢 Forte contrazione: supporto oro (Impatto 30%)")
            elif valore < 50:
                col_ism_m.warning("🟡 Rallentamento: impatto moderato (15%)")
            else:
                col_ism_m.info("🔵 Espansione: possibile pressione sull’oro (10%)")

            col_ism_m.caption(f"📅 Ultimo aggiornamento: {data}")

        elif tipo.lower() == "services":
            col_ism_s.metric("🧰 ISM Services", f"{valore}")
            if valore < 45:
                col_ism_s.error("🟢 Servizi deboli: supporto oro (25%)")
            elif valore < 50:
                col_ism_s.warning("🟡 Rallentamento: impatto medio (15%)")
            else:
                col_ism_s.info("🔵 Servizi forti → impatto contenuto (10%)")

            col_ism_s.caption(f"📅 Ultimo aggiornamento: {data}")

except Exception as e:
    st.warning(f"⚠️ Errore lettura file ISM: {e}")


# 📊 COT Report da file CSV locale
st.subheader("📊 COT Report - Grandi speculatori sull'oro")

cot_net, cot_date = get_cot_net_position_from_csv()

if cot_net is not None:
    if cot_net > 100_000:
        st.success(f"🔴 Istituzionali net long di {cot_net:,} contratti → forte sentiment rialzista (Impatto 30%)")
    elif cot_net < 0:
        st.error(f"🟢 Istituzionali net short di {abs(cot_net):,} contratti → pressione ribassista (Impatto 25%)")
    else:
        st.info(f"🟡 Net position {cot_net:,} → neutralità o attesa (Impatto 10%)")

    st.caption(f"📅 Ultimo aggiornamento: {cot_date}")
else:
    st.warning("⚠️ Rapporto COT non disponibile.")
    
    
# 🔥 Core PCE (YoY)
st.subheader("🔥 Core PCE (inflazione preferita dalla Fed - YoY)")
core_pce, pce_date = get_core_pce_yoy()

if core_pce is not None:
    st.metric("📊 Core PCE YoY", f"{core_pce}%")
    if core_pce > 4.0:
        st.error("🔴 Inflazione persistente → Fed può restare aggressiva → impatto negativo sull'oro (30%)")
    elif core_pce < 2.5:
        st.success("🟢 Inflazione sotto controllo → possibile supporto oro (25%)")
    else:
        st.info("🟡 Inflazione moderata → impatto neutro o misto (15%)")

    st.caption(f"📅 Ultimo aggiornamento: {pce_date}")
else:
    st.warning("⚠️ Impossibile recuperare il Core PCE.")
    
    
# 🛍️ Retail Sales (YoY)
st.subheader("🛍️ Retail Sales USA (YoY)")
retail_yoy, retail_date = get_retail_sales_yoy()

if retail_yoy is not None:
    st.metric("🛒 Retail Sales YoY", f"{retail_yoy}%")
    if retail_yoy > 5.0:
        st.error("🔴 Consumi forti → economia solida → Fed restrittiva → pressione sull’oro (Impatto 25%)")
    elif retail_yoy < 2.0:
        st.success("🟢 Debolezza nei consumi → supporto oro (Impatto 25%)")
    else:
        st.info("🟡 Consumi stabili → impatto neutro (10–15%)")

    st.caption(f"📅 Ultimo aggiornamento: {retail_date}")
else:
    st.warning("⚠️ Impossibile recuperare le vendite al dettaglio.")
    
    

# 📈 GDP USA (trimestrale)
st.subheader("📈 PIL USA (GDP Reale - variazione trimestrale)")
gdp_growth, gdp_date = get_gdp_growth()

if gdp_growth is not None:
    st.metric("🇺🇸 Variazione GDP", f"{gdp_growth}%")
    if gdp_growth > 3.0:
        st.error("🔴 Crescita forte → la Fed potrebbe mantenere tassi alti → pressione sull'oro (Impatto 25%)")
    elif gdp_growth < 1.0:
        st.success("🟢 Crescita debole → possibile supporto all'oro (Impatto 30%)")
    else:
        st.info("🟡 Crescita moderata → impatto neutro o misto (15%)")

    st.caption(f"📅 Ultimo aggiornamento: {gdp_date}")
else:
    st.warning("⚠️ Impossibile recuperare il dato sul PIL USA.")
    
    
# 🌐 Notizie ad alto impatto filtrate (logica avanzata)
st.subheader("🌐 Notizie più rilevanti per XAU/USD (filtro AI)")

important_news = get_important_news()

if important_news:
    for news in important_news:
        with st.expander(f"📰 {news['title']}"):
            st.markdown(f"[🌍 Vedi fonte]({news['link']})")
            st.markdown(f"📌 Categoria: **{news['category']}**")
            st.markdown(f"🧠 Motivo: {news['rationale']}")
            st.markdown(f"📊 Rilevanza stimata: **{news['relevance']}%**")
            if news["sentiment"] > 0.2:
                st.success("Sentiment positivo")
            elif news["sentiment"] < -0.2:
                st.error("Sentiment negativo")
            else:
                st.info("Sentiment neutro o misto")
else:
    st.warning("⚠️ Nessuna notizia rilevante trovata.")
    
#investing 
st.subheader("📅 Eventi economici USA ad alta rilevanza (Investing.com)")

if st.button("🔄 Aggiorna eventi da Investing.com"):
    investing_events = get_investing_events_selenium()

    if investing_events:
        for ev in investing_events:
            titolo_originale = ev["titolo"]
            titolo = titolo_originale.lower()
            valore = ev["valore"]
            note = ev.get("note", "")

            st.markdown(f"🔸 **{titolo_originale}** — Risultato: `{valore}` — 🐂🐂🐂")

            if note:
                st.caption(f"🧠 Interpretazione ufficiale Investing: *{note}*")

            # Interpretazione AI ragionata
            if any(x in titolo for x in ["sussidio", "disoccupazione", "unemployment", "jobless"]):
                try:
                    num = int(valore.replace("K", "").replace(",", "").strip())
                    if num > 210:
                        st.success("🟢 Aumento richieste sussidi = rallentamento → possibile supporto oro (Impatto 25%)")
                    else:
                        st.warning("🟡 Valore stabile o basso → impatto moderato (10%)")
                except:
                    st.info("🟡 Dato non numerico → impatto neutro")

            elif "philadelphia fed" in titolo:
                if "-" in valore or valore.startswith("-"):
                    st.success("🟢 Sentiment manifatturiero negativo → rischio economico → supporto oro (30%)")
                else:
                    st.warning("🟡 Sentiment in miglioramento → impatto neutro o moderato (15%)")

            elif "retail sales" in titolo:
                if "%" in valore:
                    try:
                        perc = float(valore.replace("%", "").replace(",", "."))
                        if perc > 0.7:
                            st.error("🔴 Consumi forti → economia solida → pressione ribassista oro (Impatto 25%)")
                        elif perc < 0.2:
                            st.success("🟢 Consumi deboli → possibile supporto oro (Impatto 25%)")
                        else:
                            st.info("🟡 Crescita moderata delle vendite → impatto contenuto (15%)")
                    except:
                        st.info("🟡 Dato vendite non numerico → impatto neutro")

            elif "inflazione" in titolo or "cpi" in titolo:
                st.error("🔴 Inflazione alta → impatto forte sui tassi → pressione oro (Impatto 30%)")

            else:
                st.info("📌 Evento rilevante ma non riconosciuto direttamente. Consultare manualmente.")

            st.markdown("---")
    else:
        st.warning("⚠️ Nessun evento rilevante trovato.")
    


# Mostra i dati
col1, col2, col3 = st.columns(3)

col1.metric("🟡 XAU/USD Spot", f"${gold_spot}")
col2.metric("💵 DXY (Indice USD)", dxy)
col3.metric("📈 US 10Y Yield", f"{us10y}%")


st.caption("Versione base. Nei prossimi step aggiungeremo altri dati macro e il sistema di valutazione dell'impatto.")


# 🔮 Interpretazione giornaliera macro completa + segnale

st.subheader("📊 Interpretazione complessiva e segnale operativo")

total_score = 0
commenti = []

# CPI
if cpi:
    if cpi > 4.0:
        total_score += 30
        commenti.append("Inflazione alta → +30")
    elif cpi < 2.5:
        total_score += 5
        commenti.append("Inflazione bassa → +5")
    else:
        total_score += 15
        commenti.append("Inflazione moderata → +15")

# NFP
if nfp_diff:
    if nfp_diff > 200_000:
        total_score -= 30
        commenti.append("Forte creazione lavoro (NFP) → –30")
    elif nfp_diff < 50_000:
        total_score += 15
        commenti.append("Lavoro debole → +15")
    elif nfp_diff < 0:
        total_score += 20
        commenti.append("Lavoro in calo → +20")

# Disoccupazione
if unemployment:
    if unemployment < 3.8:
        total_score += 10
        commenti.append("Disoccupazione bassa → +10")
    elif unemployment >= 4.0:
        total_score += 25
        commenti.append("Disoccupazione in aumento → +25")

# DXY e US10Y
if dxy and us10y:
    if dxy > 104:
        total_score -= 15
        commenti.append("Dollaro forte → –15")
    if us10y > 4:
        total_score -= 15
        commenti.append("Tassi alti → –15")

# ISM
try:
    if ism_manuf and float(ism_manuf) < 50:
        total_score += 15
        commenti.append("ISM manifatturiero sotto 50 → +15")
    if ism_services and float(ism_services) < 50:
        total_score += 10
        commenti.append("ISM servizi sotto 50 → +10")
except:
    pass

# COT
if cot_net is not None:
    if cot_net > 100_000:
        total_score += 30
        commenti.append("Net Long Istituzionali >100k → +30")
    elif cot_net < 0:
        total_score -= 15
        commenti.append("Net Short Istituzionali → –15")

# Notizie Investing
if investing_events:
    for ev in investing_events:
        titolo = ev["titolo"].lower()
        note = ev.get("note", "").lower()
        if any(x in note for x in ["positivo per il dollaro", "aumenta le chance di rialzo tassi"]):
            total_score -= 10
            commenti.append(f"📰 Notizia favorevole al dollaro: {ev['titolo']} → –10")
        elif any(x in note for x in ["negativo per il dollaro", "supporta oro", "rischio recessione"]):
            total_score += 10
            commenti.append(f"📰 Notizia a supporto dell’oro: {ev['titolo']} → +10")

# 🔵 Normalizza il punteggio max a 100
if total_score > 100:
    total_score = 100
elif total_score < 0:
    total_score = 0

# 🎯 Mostra il punteggio finale
st.metric("📈 Punteggio macro totale", f"{total_score}/100")

# 🟢🟡🔴 Segnale operativo finale
if total_score >= 66:
    st.success("🟢 Pressione rialzista sull’oro → Possibile ingresso LONG")
    st.markdown("**✔️ Suggerimento operativo:** Valuta posizioni rialziste (LONG), in base alla conferma tecnica.")
elif total_score <= 35:
    st.error("🔴 Pressione ribassista sull’oro → Rischio discesa")
    st.markdown("**⚠️ Suggerimento operativo:** Evita ingressi long, valuta eventuale SHORT solo se supportato da analisi tecnica.")
else:
    st.warning("🟡 Condizione neutra → Meglio attendere")
    st.markdown("**📌 Suggerimento operativo:** Condizioni contrastanti, attendere conferma tecnica per entrare.")

# 🔍 Commento ragionato finale
st.markdown("### 🧠 Analisi dei fattori macro:")
for c in commenti:
    st.markdown(f"- {c}")
