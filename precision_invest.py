"""
PrecisionInvest Alpha Terminal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Professional momentum-based equity analysis and backtesting engine.
Data: yfinance | Benchmark: S&P 500 (^GSPC)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import streamlit_authenticator as stauth

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. PAGE CONFIG & THEME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="PrecisionInvest Alpha Terminal",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── AUTHENTICATION ──
try:
    authenticator = stauth.Authenticate(
        st.secrets["credentials"].to_dict(),
        st.secrets["cookie"]["name"],
        st.secrets["cookie"]["key"],
        st.secrets["cookie"]["expiry_days"],
    )

    authenticator.login()
    
    if st.session_state["authentication_status"] is False:
        st.error("Username/password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password")

    if not st.session_state.get("authentication_status"):
        st.stop()
        
    authenticator.logout(location="sidebar")
except KeyError:
    # Fallback if secrets are not configured yet (e.g., local testing before setup)
    pass

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #0e1117; }

    /* — Metric Cards — */
    .stMetric {
        background-color: #161b22;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }

    /* — Tab Styling — */
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 8px;
        color: #8b949e;
        padding: 10px 24px;
        font-weight: 600;
        border: 1px solid #30363d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #238636 !important;
        color: white !important;
        border-color: #2ea043 !important;
    }

    /* — Status Banner — */
    .regime-banner {
        padding: 28px 35px;
        border-radius: 14px;
        text-align: center;
        font-weight: 800;
        font-size: 28px;
        letter-spacing: 1.5px;
        margin-bottom: 20px;
        border: 2px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .regime-bull {
        background: linear-gradient(135deg, #238636 0%, #2ea043 50%, #3fb950 100%);
        color: white;
    }
    .regime-bear {
        background: linear-gradient(135deg, #8b1a1a 0%, #da3633 50%, #f85149 100%);
        color: white;
    }

    /* — Checklist Card — */
    .check-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }
    .check-pass { border-left: 4px solid #3fb950; }
    .check-fail { border-left: 4px solid #f85149; }
    .check-title { font-weight: 700; font-size: 15px; color: #c9d1d9; }
    .check-detail { font-size: 13px; color: #8b949e; margin-top: 4px; }

    /* — Phase Card — */
    .phase-card {
        background: #161b22;
        border-radius: 14px;
        padding: 24px;
        border: 1px solid #30363d;
        border-top: 4px solid #388bfd;
        min-height: 180px;
    }
    .phase-title { font-size: 20px; font-weight: 700; color: #58a6ff; }
    .phase-desc { font-size: 14px; color: #8b949e; margin-top: 10px; line-height: 1.7; }

    /* — Score Summary — */
    .score-box {
        background: #1c2128;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #30363d;
        margin-top: 16px;
    }
    .score-num { font-size: 48px; font-weight: 800; }
    .score-label { font-size: 14px; color: #8b949e; margin-top: 6px; }

    /* — Warning Box — */
    .warn-box {
        background: #2d1b00;
        border: 1px solid #d29922;
        border-left: 5px solid #d29922;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #e3b341;
        font-size: 14px;
    }
    .bear-warn-box {
        background: #211111;
        border: 1px solid #da3633;
        border-left: 5px solid #da3633;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #f85149;
        font-size: 14px;
    }

    /* — Disclaimer — */
    .disclaimer {
        font-size: 13px;
        color: #8b949e;
        margin-top: 50px;
        border: 1px solid #da3633;
        padding: 22px;
        border-radius: 12px;
        background-color: #211111;
        line-height: 1.7;
    }

    /* — Expander — */
    div[data-testid="stExpander"] {
        border: 1px solid #30363d;
        background-color: #161b22;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. CORE ENGINE FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sp500_wiki():
    """Fetches S&P 500 ticker list from Wikipedia."""
    try:
        # We use a reliable, automatically updated open-source GitHub dataset instead of Wikipedia 
        # to prevent Streamlit Cloud from being blocked as a bot.
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        csv_text = requests.get(url, headers=headers, timeout=10).text
        df = pd.read_csv(io.StringIO(csv_text))
        
        tickers = [t.replace(".", "-") for t in df["Symbol"].tolist()]
        sectors = dict(zip(tickers, df["GICS Sector"]))
        names = dict(zip(tickers, df["Security"]))
        
        return tickers, sectors, names
    except Exception as e:
        import streamlit as st
        st.warning(f"⚠️ Lokale S&P 500 Liste konnte nicht geladen werden ({str(e)}). Verwende Notfall-Liste (12 Ticker).")
        fetch_sp500_wiki.clear() # Clear cache so it tries again next time
        fallback = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META",
                     "TSLA", "BRK-B", "JPM", "V", "UNH", "LLY"]
        return fallback, {}, {}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_benchmark(period="5y"):
    """Downloads S&P 500 benchmark data."""
    data = yf.download("^GSPC", period=period, progress=False, auto_adjust=True)["Close"]
    if isinstance(data, pd.DataFrame):
        data = data.iloc[:, 0]
    return data.dropna()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_vix():
    """Downloads VIX data."""
    try:
        data = yf.download("^VIX", period="1y", progress=False, auto_adjust=True)["Close"]
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        return data.dropna()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def get_company_info(ticker):
    """Returns company name and sector from yfinance info."""
    try:
        t = yf.Ticker(ticker)
        inf = t.info
        return {
            "Name": inf.get("longName", ticker),
            "Sector": inf.get("sector", "N/A"),
        }
    except Exception:
        return {"Name": ticker, "Sector": "N/A"}


def calc_mansfield_rs(stock_prices, benchmark_prices, window=50):
    """
    Mansfield Relative Strength Score.
    RS = (Price/Benchmark) / SMA(Price/Benchmark, window) - 1
    """
    combined = pd.concat([stock_prices, benchmark_prices], axis=1).ffill().dropna()
    if combined.empty or len(combined) < window:
        return pd.Series(dtype=float)
    combined.columns = ["Stock", "BM"]
    ratio = combined["Stock"] / combined["BM"].replace(0, np.nan)
    rs = (ratio / ratio.rolling(window=window).mean()) - 1
    return rs


def calc_correlation_matrix(prices_df, tickers):
    """Compute correlation matrix for a list of tickers."""
    available = [t for t in tickers if t in prices_df.columns]
    if len(available) < 2: return pd.DataFrame()
    returns = prices_df[available].pct_change().dropna()
    return returns.corr()


def calc_rsi(prices, window=14):
    """Standard RSI calculation."""
    if len(prices) < window + 1:
        return pd.Series([50.0] * len(prices), index=prices.index)
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.ffill().fillna(50.0)


def get_market_regime(bm_prices):
    """Returns BULL or BEAR based on price vs SMA 200."""
    if len(bm_prices) < 200:
        return "BULL", True
    sma200 = bm_prices.rolling(200).mean().iloc[-1]
    current = bm_prices.iloc[-1]
    is_bull = current > sma200
    return ("BULL" if is_bull else "BEAR"), is_bull


def get_weinstein_phase(bm_prices):
    """Weinstein Market Phases 1-4."""
    if len(bm_prices) < 200:
        return "N/A", "Nicht genügend Daten", "#8b949e"

    sma50 = bm_prices.rolling(50).mean().iloc[-1]
    sma200 = bm_prices.rolling(200).mean().iloc[-1]
    curr = bm_prices.iloc[-1]

    if curr > sma50 and sma50 > sma200:
        return ("Phase 2 — Markup 🚀",
                "Starker Aufwärtstrend. Momentum-Strategien maximieren. Positionsgröße hoch halten.",
                "#3fb950")
    elif curr < sma50 and curr > sma200:
        return ("Phase 3 — Distribution ⚠️",
                "Verteilungsphase am Top. Volatilität steigt. Stops eng ziehen, neue Positionen reduzieren.",
                "#d29922")
    elif curr < sma50 and curr < sma200:
        return ("Phase 4 — Markdown 🔴",
                "Bärenmarkt aktiv. 80% Cash-Quote zum Kapitalschutz. Nur Absicherungen handeln.",
                "#f85149")
    else:
        return ("Phase 1 — Basing 📈",
                "Bodenbildung erkennbar. Auf RS-Ausbrüche neuer Leader achten. Watchlist aufbauen.",
                "#58a6ff")


def calc_sortino(returns_pct, ann_factor):
    """Sortino Ratio — penalizes only downside volatility."""
    r = returns_pct / 100
    downside = r[r < 0]
    down_std = downside.std() if len(downside) > 1 else 0.0001
    return (r.mean() / down_std) * ann_factor if down_std > 0 else 0


def calc_calmar(total_return_pct, max_dd_pct, n_years):
    """Calmar Ratio — return / max drawdown."""
    if max_dd_pct == 0 or n_years == 0:
        return 0
    ann_ret = ((1 + total_return_pct / 100) ** (1 / n_years) - 1) * 100
    return ann_ret / abs(max_dd_pct)


def monthly_returns_heatmap(equity_series):
    """Create monthly returns DataFrame for heatmap display."""
    monthly = equity_series.resample("ME").last().pct_change() * 100
    monthly = monthly.dropna()
    df = pd.DataFrame({
        "Year": monthly.index.year,
        "Month": monthly.index.month,
        "Return": monthly.values,
    })
    pivot = df.pivot_table(values="Return", index="Year", columns="Month", aggfunc="first")
    pivot.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return pivot


def monte_carlo_simulation(returns_pct, capital, n_sims=300, n_periods=12):
    """Monte Carlo forward projection based on historical return distribution."""
    r = returns_pct.values / 100
    mu, sigma = r.mean(), r.std()
    paths = np.zeros((n_sims, n_periods + 1))
    paths[:, 0] = capital
    for t in range(1, n_periods + 1):
        rand_returns = np.random.normal(mu, sigma, n_sims)
        paths[:, t] = paths[:, t - 1] * (1 + rand_returns)
    return paths


@st.cache_data(ttl=3600, show_spinner="Breadth-Daten werden berechnet...")
def calc_breadth_cached(period="1y"):
    """Market Breadth: % of S&P 500 stocks trading above their SMA 50."""
    tickers, _, _ = fetch_sp500_wiki()
    above = 0
    total = 0
    batch_size = 50

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        try:
            data = yf.download(batch, period=period, progress=False, auto_adjust=True)["Close"]
            if isinstance(data, pd.Series):
                data = data.to_frame()
            for col in data.columns:
                prices = data[col].dropna()
                if len(prices) >= 50:
                    sma50 = prices.rolling(50).mean().iloc[-1]
                    if prices.iloc[-1] > sma50:
                        above += 1
                    total += 1
        except Exception:
            continue

    return (above / total * 100) if total > 0 else 50.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## 🎯 PrecisionInvest")
    st.caption("Alpha Terminal v2.0")
    st.divider()

    st.markdown("### ⚙️ Backtest-Parameter")
    bt_capital = st.number_input("Startkapital (USD)", value=10000, min_value=1000, step=1000)
    bt_years = st.slider("Zeitraum (Jahre)", 1, 10, 3)
    bt_positions = st.slider("Anzahl Positionen (Top RS)", 1, 15, 1)

    hold_map = {
        "Wöchentlich": "W",
        "Alle 2 Wochen": "2W",
        "Monatlich": "ME",
        "Alle 2 Monate": "2ME",
    }
    hold_choice = st.selectbox("Rebalancing-Intervall", list(hold_map.keys()), index=0)
    hold_freq = hold_map[hold_choice]

    sl_pct = st.slider("Stop-Loss %", 5, 30, 10)
    trailing_sl = st.checkbox("Trailing Stop-Loss", value=True,
                              help="Stop-Loss zieht mit steigenden Kursen nach")
    tp_pct = st.slider("Take-Profit % (0=Off)", 0, 100, 0,
                       help="Automatisch Gewinn realisieren bei X%. 0 = deaktiviert.")
    rs_window = st.slider("RS Zeitfenster (Tage)", 10, 200, 50,
                          help="50 Tage ist der Standard für Mansfield RS.")

    st.divider()
    st.caption("Handelskosten: 0.12% pro Rotation")
    st.caption("Bear-Exposure: 20% (80% Cash)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. DATA LOADING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.spinner("🔄 Terminal-Daten werden synchronisiert..."):
    bm_prices = fetch_benchmark("5y")
    
    if bm_prices is None or bm_prices.empty:
        st.error("⚠️ Fehler: Konnte keine Marktdaten von Yahoo Finance abrufen. Streamlit Cloud IPs werden manchmal von Yahoo blockiert. Bitte lade die Seite in ein paar Minuten neu.")
        st.stop()
        
    vix_data = fetch_vix()

regime_label, is_bull = get_market_regime(bm_prices)
phase_label, phase_advice, phase_color = get_weinstein_phase(bm_prices)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

banner_class = "regime-bull" if is_bull else "regime-bear"
banner_icon = "🟢 BULLISH" if is_bull else "🔴 BEARISH"
st.markdown(
    f'<div class="regime-banner {banner_class}">MARKET STATUS: {banner_icon}</div>',
    unsafe_allow_html=True,
)

# Quick metrics row
mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    sp_price = bm_prices.iloc[-1]
    sp_change = (bm_prices.iloc[-1] / bm_prices.iloc[-2] - 1) * 100 if len(bm_prices) > 1 else 0
    st.metric("S&P 500", f"{sp_price:,.0f}", f"{sp_change:+.2f}%")
with mc2:
    vix_val = vix_data.iloc[-1] if not vix_data.empty else 0
    st.metric("VIX", f"{vix_val:.1f}", "Niedrig" if vix_val < 20 else ("Erhöht" if vix_val < 30 else "Hoch"))
with mc3:
    sma200_val = bm_prices.rolling(200).mean().iloc[-1] if len(bm_prices) >= 200 else 0
    dist = ((sp_price / sma200_val) - 1) * 100 if sma200_val > 0 else 0
    st.metric("Abstand SMA 200", f"{dist:+.1f}%", "Über SMA" if dist > 0 else "Unter SMA")
with mc4:
    ret_12m = ((bm_prices.iloc[-1] / bm_prices.iloc[-252] - 1) * 100) if len(bm_prices) >= 252 else 0
    st.metric("12M Rendite S&P", f"{ret_12m:+.1f}%", "Positiv" if ret_12m > 0 else "Negativ")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab1, tab2, tab3 = st.tabs([
    "📊 Markt-Status Dashboard",
    "🔭 Momentum Scanner",
    "🧪 Advanced Backtest Engine",
])


# ──────────────────────────────────────────────────────────
# TAB 1: MARKT-STATUS DASHBOARD
# ──────────────────────────────────────────────────────────
with tab1:
    st.markdown("### 🧠 Weinstein Marktphase")

    pc1, pc2 = st.columns([2, 1])
    with pc1:
        st.markdown(
            f"""<div class="phase-card" style="border-top-color: {phase_color};">
                <div class="phase-title">{phase_label}</div>
                <div class="phase-desc">{phase_advice}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with pc2:
        regime_pass = is_bull
        vix_pass = (vix_val < 25) if not vix_data.empty else False
        mom_pass = ret_12m > 0
        score = sum([regime_pass, vix_pass, mom_pass])

        if regime_pass and mom_pass:
            score_color = "#3fb950"
        elif score >= 2:
            score_color = "#d29922"
        else:
            score_color = "#f85149"

        st.markdown(
            f"""<div class="score-box">
                <div class="score-num" style="color: {score_color};">{score}<span style="font-size:24px; color:#8b949e;">/4*</span></div>
                <div class="score-label">Market Conditions Score<br><span style="font-size:11px;">*Breadth wird separat geladen</span></div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("### ✅ Market Conditions Checklist")

    chk1, chk2 = st.columns(2)

    with chk1:
        cls1 = "check-pass" if regime_pass else "check-fail"
        icon1 = "✅" if regime_pass else "❌"
        st.markdown(
            f"""<div class="check-card {cls1}">
                <div class="check-title">{icon1} Regime-Check (SMA 200)</div>
                <div class="check-detail">S&P 500 {'über' if regime_pass else 'unter'} dem 200-Tage-Durchschnitt.
                <br>Kurs: {sp_price:,.0f} | SMA 200: {sma200_val:,.0f}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        cls3 = "check-pass" if vix_pass else "check-fail"
        icon3 = "✅" if vix_pass else "❌"
        vix_status = f"VIX bei {vix_val:.1f}" if not vix_data.empty else "VIX nicht verfügbar"
        st.markdown(
            f"""<div class="check-card {cls3}">
                <div class="check-title">{icon3} VIX-Check (&lt;25)</div>
                <div class="check-detail">{vix_status}. {'Volatilität niedrig — günstiges Umfeld.' if vix_pass else 'Erhöhte Volatilität — Vorsicht geboten.'}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with chk2:
        cls4 = "check-pass" if mom_pass else "check-fail"
        icon4 = "✅" if mom_pass else "❌"
        st.markdown(
            f"""<div class="check-card {cls4}">
                <div class="check-title">{icon4} Momentum-Check (12M-Rendite &gt; 0)</div>
                <div class="check-detail">12-Monats-Rendite: {ret_12m:+.1f}%. {'Aufwärtsmomentum intakt.' if mom_pass else 'Kein positives Momentum.'}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        breadth_placeholder = st.empty()
        with breadth_placeholder.container():
            st.markdown(
                """<div class="check-card" style="border-left: 4px solid #8b949e;">
                    <div class="check-title">⏳ Breadth-Check (&gt;50% über SMA 50)</div>
                    <div class="check-detail">Klicke den Button unten, um die Marktbreite zu berechnen.<br>Scannt alle ~500 S&P 500 Aktien.</div>
                </div>""",
                unsafe_allow_html=True,
            )

    if st.button("📊 Breadth-Check starten (scannt ~500 Aktien)", key="breadth_btn"):
        breadth_val = calc_breadth_cached()
        breadth_pass = breadth_val > 50
        cls2 = "check-pass" if breadth_pass else "check-fail"
        icon2 = "✅" if breadth_pass else "❌"
        with breadth_placeholder.container():
            st.markdown(
                f"""<div class="check-card {cls2}">
                    <div class="check-title">{icon2} Breadth-Check (&gt;50% über SMA 50)</div>
                    <div class="check-detail">{breadth_val:.1f}% der S&P 500 Aktien über SMA 50.
                    <br>{'Breite Marktbeteiligung — gesunder Trend.' if breadth_pass else 'Schwache Breite — Trend wird von wenigen Aktien getragen.'}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        final_score = score + (1 if breadth_pass else 0)
        st.markdown(f"**Aktualisierter Score: {final_score}/4**")

    if not is_bull:
        st.markdown(
            """<div class="bear-warn-box">
                🔴 <b>BEAR-REGIME AKTIV</b> — Automatische Exposure-Reduktion auf 20%.
                80% Cash-Reserve zum Kapitalschutz. Nur die stärksten Leader handeln.
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<div class="disclaimer">
            ⚠️ <b>RECHTLICHER HINWEIS</b>: Diese Informationen stellen keine Anlageberatung dar.
            Investitionen in Wertpapiere sind mit Risiken verbunden, einschließlich des vollständigen Kapitalverlusts.
            Vergangene Performance ist kein Indikator für zukünftige Ergebnisse.
            Konsultieren Sie einen lizenzierten Finanzberater vor jeder Anlageentscheidung.
            © {datetime.now().year} PrecisionInvest Alpha Terminal.
        </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────
# TAB 2: MOMENTUM SCANNER
# ──────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🔭 S&P 500 Momentum Scanner")
    st.markdown(
        "Scannt alle S&P 500 Aktien und rankt sie nach **Mansfield Relative Strength** "
        "gegenüber dem S&P 500 Index. Die Top 15 Leader werden angezeigt."
    )

    if st.button("🚀 S&P 500 Full Scan starten", key="scan_btn", type="primary"):
        with st.spinner("Scanning S&P 500... (Batch-Download, ~30-60 Sekunden)"):
            tickers, sector_map, name_map = fetch_sp500_wiki()
            bm_scan = fetch_benchmark("2y")
            results = []
            batch_size = 50

            progress_bar = st.progress(0, text="Starte Scan...")
            total_batches = (len(tickers) + batch_size - 1) // batch_size

            for batch_idx in range(0, len(tickers), batch_size):
                batch = tickers[batch_idx : batch_idx + batch_size]
                progress = min((batch_idx // batch_size + 1) / total_batches, 1.0)
                progress_bar.progress(
                    progress,
                    text=f"Batch {batch_idx // batch_size + 1}/{total_batches} "
                         f"({batch[0]}...{batch[-1]})",
                )

                try:
                    data = yf.download(
                        batch, period="2y", progress=False, auto_adjust=True
                    )["Close"]
                    if isinstance(data, pd.Series):
                        data = data.to_frame(name=batch[0])

                    for ticker in batch:
                        if ticker not in data.columns:
                            continue
                        prices = data[ticker].dropna()
                        if len(prices) < 60:
                            continue

                        bm_aligned = bm_scan.reindex(prices.index).ffill().dropna()
                        prices_aligned = prices.reindex(bm_aligned.index).ffill().dropna()

                        if len(prices_aligned) < rs_window:
                            continue

                        rs = calc_mansfield_rs(prices_aligned, bm_aligned, window=rs_window)
                        rsi = calc_rsi(prices_aligned)

                        if not rs.empty and rs.iloc[-1] > 0:
                            results.append({
                                "Ticker": ticker,
                                "Name": name_map.get(ticker, ticker),
                                "Sektor": sector_map.get(ticker, "N/A"),
                                "RS Score": round(rs.iloc[-1], 4),
                                "RSI(14)": round(rsi.iloc[-1], 1),
                            })
                except Exception:
                    continue

            progress_bar.empty()

            if results:
                df_results = (
                    pd.DataFrame(results)
                    .sort_values(by="RS Score", ascending=False)
                    .head(15)
                    .reset_index(drop=True)
                )

                st.markdown("#### 🏆 Top 15 Momentum Leader")
                st.dataframe(
                    df_results.style
                    .background_gradient(subset=["RS Score"], cmap="RdYlGn")
                    .format({"RS Score": "{:.4f}", "RSI(14)": "{:.1f}"}),
                    width="stretch",
                    hide_index=True,
                    height=560,
                )

                top_tickers_str = ", ".join(df_results["Ticker"].tolist())
                st.markdown("#### 📋 Top-Ticker für Copy-Paste")
                st.code(top_tickers_str, language="text")

                avg_rs = df_results["RS Score"].mean()
                avg_rsi = df_results["RSI(14)"].mean()
                st.markdown(
                    f"**Ø RS Score:** {avg_rs:.4f} | **Ø RSI:** {avg_rsi:.1f} | "
                    f"**Leader-Sektoren:** {', '.join(df_results['Sektor'].value_counts().head(3).index.tolist())}"
                )

                st.markdown("---")
                st.markdown("#### 🔗 Correlation Matrix (Top 15)")
                top_tickers_list = df_results["Ticker"].tolist()
                
                # Download prices for the selected top tickers
                corr_prices = yf.download(top_tickers_list, period="6mo", progress=False, auto_adjust=True)["Close"]
                if isinstance(corr_prices, pd.Series):
                    corr_prices = corr_prices.to_frame(name=top_tickers_list[0])
                
                corr = calc_correlation_matrix(corr_prices, top_tickers_list)
                if not corr.empty:
                    fig_corr = go.Figure(data=go.Heatmap(
                        z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
                        colorscale=[[0,'#1a5cff'],[0.5,'#0a0f1a'],[1,'#f85149']],
                        text=np.round(corr.values, 2), texttemplate="%{text}",
                        textfont={"size":10,"family":"Inter"}, zmid=0,
                        colorbar=dict(title="Corr")
                    ))
                    fig_corr.update_layout(
                        template="plotly_dark", height=500,
                        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                        font=dict(family="Inter"), margin=dict(l=0, r=0, t=10, b=0)
                    )
                    st.plotly_chart(fig_corr, width="stretch")
            else:
                st.warning("Keine Leader mit positivem RS Score gefunden. Marktumfeld prüfen.")

    st.markdown(
        f"""<div class="disclaimer">
            ⚠️ <b>RECHTLICHER HINWEIS</b>: Diese Informationen stellen keine Anlageberatung dar.
            Investitionen in Wertpapiere sind mit Risiken verbunden, einschließlich des vollständigen Kapitalverlusts.
            Vergangene Performance ist kein Indikator für zukünftige Ergebnisse.
            © {datetime.now().year} PrecisionInvest Alpha Terminal.
        </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────
# TAB 3: ADVANCED BACKTEST ENGINE
# ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 🧪 Advanced Backtest Engine")

    with st.expander("📖 Methodologie", expanded=False):
        st.markdown(f"""
        **🔬 RS-Momentum — Enhanced Backtest**

        **Prinzip:** Top-{bt_positions} RS-Aktien gleichgewichtet. Bull=100%, Bear=20%.
        **Stop-Loss:** {sl_pct}% {'(Trailing)' if trailing_sl else '(Fix)'} | **Take-Profit:** {"Off" if tp_pct == 0 else f"{tp_pct}%"}
        **Kosten:** 0.12% pro Trade | **Rebalancing:** {hold_choice} | **RS-Window:** {rs_window} Tage

        **Features:** Trailing SL, Take-Profit, Sortino/Calmar Ratio, Monthly Heatmap, Monte Carlo Simulation
        """)

    if st.button("🧪 Backtest starten", key="bt_btn", type="primary"):
        with st.spinner("📊 Backtesting läuft... Historische Daten werden verarbeitet..."):
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=bt_years * 365)
            prefetch_start = start_date - timedelta(days=450)

            # Download S&P 500 tickers
            tickers_bt, sector_map_bt, name_map_bt = fetch_sp500_wiki()

            # Download all data in batches
            all_price_frames = []
            batch_size = 50
            bt_progress = st.progress(0, text="Daten werden geladen...")
            total_bt_batches = (len(tickers_bt) + batch_size - 1) // batch_size

            for bi in range(0, len(tickers_bt), batch_size):
                batch = tickers_bt[bi : bi + batch_size]
                prog = min((bi // batch_size + 1) / total_bt_batches, 1.0)
                bt_progress.progress(prog, text=f"Lade Batch {bi // batch_size + 1}/{total_bt_batches}")

                try:
                    batch_data = yf.download(
                        batch,
                        start=prefetch_start.strftime("%Y-%m-%d"),
                        end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                        progress=False,
                        auto_adjust=True
                    )["Close"]
                    if isinstance(batch_data, pd.Series):
                        batch_data = batch_data.to_frame(name=batch[0])
                    all_price_frames.append(batch_data)
                except Exception:
                    continue

            bt_progress.empty()

            if not all_price_frames:
                st.error("Keine Daten verfügbar. Bitte Internetverbindung prüfen.")
                st.stop()

            bt_prices = pd.concat(all_price_frames, axis=1).ffill()

            # Get benchmark for the same period
            bm_bt = yf.download(
                "^GSPC",
                start=prefetch_start.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True
            )["Close"]
            if isinstance(bm_bt, pd.DataFrame):
                bm_bt = bm_bt.iloc[:, 0]
            bm_bt = bm_bt.dropna()

            # Align indexes
            common_idx = bt_prices.index.intersection(bm_bt.index)
            bt_prices = bt_prices.loc[common_idx]
            bm_bt = bm_bt.loc[common_idx]

            # Calculate RS scores for all tickers
            st.info("📈 RS Scores werden berechnet...")
            rs_dict = {}
            for t in bt_prices.columns:
                p = bt_prices[t].dropna()
                if len(p) < 60:
                    continue
                rs_series = calc_mansfield_rs(p, bm_bt.reindex(p.index).ffill(), window=rs_window)
                if not rs_series.empty:
                    rs_dict[t] = rs_series
            rs_history = pd.concat(rs_dict, axis=1).ffill()

            # Generate rebalancing dates
            actual_start = start_date.strftime("%Y-%m-%d")
            rebal_dates = (
                bt_prices.loc[actual_start:]
                .groupby(pd.Grouper(freq=hold_freq))
                .apply(lambda x: x.index[-1] if not x.empty else None)
                .dropna()
            )

            if not rebal_dates.empty and bt_prices.index[-1] not in rebal_dates.values:
                rebal_dates = pd.concat(
                    [rebal_dates, pd.Series([bt_prices.index[-1]], index=[bt_prices.index[-1]])]
                ).sort_values().drop_duplicates()

            # ── BACKTEST LOOP ──
            capital = bt_capital
            capital_history = []
            trade_log = []
            first_date = None
            ma200 = bm_bt.rolling(200).mean()
            trading_cost = 0.0012  # 0.12%
            sl_cnt, tp_cnt = 0, 0
            tsl_peak_tracker = {}  # Track peaks across periods for trailing SL

            for i in range(len(rebal_dates) - 1):
                cur_date = rebal_dates.iloc[i]
                nxt_date = rebal_dates.iloc[i + 1]

                if cur_date not in rs_history.index or cur_date not in ma200.index:
                    continue

                # Market regime check
                cur_ma200 = ma200.loc[cur_date]
                is_bull_period = bm_bt.loc[cur_date] > cur_ma200 if pd.notna(cur_ma200) else True
                exposure = 1.0 if is_bull_period else 0.2

                # Rank stocks by RS
                cur_rs = rs_history.loc[cur_date].dropna().sort_values(ascending=False)
                top_n = cur_rs.head(bt_positions)

                if len(top_n) < bt_positions:
                    continue
                if first_date is None:
                    first_date = cur_date

                selected = top_n.index.tolist()
                current_tickers = set(selected)
                period_returns = []
                trade_details = []

                for ticker in selected:
                    if ticker not in bt_prices.columns:
                        continue

                    buy_price = bt_prices.loc[cur_date, ticker]
                    if pd.isna(buy_price) or buy_price <= 0:
                        continue

                    # Get daily prices for SL/TP check
                    period_prices = bt_prices.loc[cur_date:nxt_date, ticker].dropna()
                    if period_prices.empty:
                        continue

                    # Path simulation with Trailing SL + Take Profit
                    exit_price = period_prices.iloc[-1]
                    exit_status = "OK"

                    # Carry over peak from previous period if same ticker held continuously
                    max_p = max(buy_price, tsl_peak_tracker.get(ticker, buy_price)) if trailing_sl else buy_price

                    for day_price in period_prices:
                        # Update trailing peak
                        if trailing_sl and day_price > max_p:
                            max_p = day_price

                        # Stop-Loss check
                        sl_price = max_p * (1 - sl_pct / 100) if trailing_sl else buy_price * (1 - sl_pct / 100)
                        if day_price <= sl_price:
                            exit_price = sl_price
                            exit_status = "🚨TSL" if trailing_sl else "🚨SL"
                            sl_cnt += 1
                            break

                        # Take-Profit check
                        if tp_pct > 0 and day_price >= buy_price * (1 + tp_pct / 100):
                            exit_price = buy_price * (1 + tp_pct / 100)
                            exit_status = "🎯TP"
                            tp_cnt += 1
                            break

                    # Update peak tracker
                    if exit_status == "OK":
                        tsl_peak_tracker[ticker] = max_p
                    else:
                        tsl_peak_tracker.pop(ticker, None)

                    # Apply trading cost
                    pos_size = (capital * exposure) / bt_positions
                    net_return = pos_size * 0.9988 * (exit_price / buy_price)
                    period_returns.append(net_return)

                    stock_pct = (exit_price / buy_price - 1) * 100
                    tsl_info = f" TSL@{sl_price:.2f}" if trailing_sl else ""
                    trade_details.append(
                        f"{ticker} (In:{buy_price:.2f} Out:{exit_price:.2f}{tsl_info} | "
                        f"{'🟢' if stock_pct > 0 else '🔴'}{stock_pct:+.1f}%, {exit_status})"
                    )

                # Clean tracker: remove tickers no longer in portfolio
                tsl_peak_tracker = {k: v for k, v in tsl_peak_tracker.items() if k in current_tickers}

                if not period_returns:
                    continue

                prev_capital = capital
                capital = sum(period_returns) + (capital * (1 - exposure))

                strat_pct = (capital / prev_capital - 1) * 100
                bm_period_pct = (bm_bt.loc[nxt_date] / bm_bt.loc[cur_date] - 1) * 100

                capital_history.append({
                    "Date": nxt_date,
                    "Strategy": capital,
                    "Market": (bm_bt.loc[nxt_date] / bm_bt.loc[first_date]) * bt_capital,
                    "StratPct": strat_pct,
                    "MktPct": bm_period_pct,
                })

                trade_log.append({
                    "Start": cur_date.date(),
                    "End": nxt_date.date(),
                    "Regime": "BULL" if is_bull_period else "BEAR",
                    "Trades": " | ".join(trade_details),
                    "Strat%": strat_pct,
                    "S&P500%": bm_period_pct,
                    "Alpha%": strat_pct - bm_period_pct,
                    "Value": capital,
                })

            # ── RESULTS ──
            if capital_history:
                res_df = pd.DataFrame(capital_history).set_index("Date")
                log_df = pd.DataFrame(trade_log)
                perf = res_df["StratPct"]

                # Metrics calculations
                total_return = (capital / bt_capital - 1) * 100
                market_return = (res_df["Market"].iloc[-1] / bt_capital - 1) * 100
                alpha = total_return - market_return

                def max_drawdown(series):
                    peak = series.cummax()
                    dd = (series - peak) / peak
                    return dd.min() * 100

                dd_strat = max_drawdown(res_df["Strategy"])
                dd_market = max_drawdown(res_df["Market"])

                # Risk-adjusted metrics
                ann_map = {"W": 52, "2W": 26, "ME": 12, "2ME": 6}
                ann_f = np.sqrt(ann_map.get(hold_freq, 12))
                sharpe = (perf.mean() / 100 / (perf.std() / 100)) * ann_f if perf.std() > 0 else 0
                vol = (perf.std() / 100) * ann_f * 100
                sortino = calc_sortino(perf, ann_f)
                n_years_actual = max((res_df.index[-1] - res_df.index[0]).days / 365.25, 0.1)
                calmar = calc_calmar(total_return, dd_strat, n_years_actual)

                # Win/loss stats
                num_g = sum(1 for p in perf if p > 0)
                num_r = sum(1 for p in perf if p < 0)
                win_s, max_win_s = 0, 0
                for p in perf:
                    win_s = win_s + 1 if p > 0 else 0
                    max_win_s = max(max_win_s, win_s)
                streak, max_streak = 0, 0
                for p in perf:
                    streak = streak + 1 if p < 0 else 0
                    max_streak = max(max_streak, streak)
                w_rate = (num_g / len(perf) * 100) if len(perf) > 0 else 0

                # ── DISPLAY METRICS ROW 1 ──
                st.markdown("---")
                st.markdown("### 📊 Backtest-Ergebnisse")

                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Final Capital", f"{capital:,.0f}$", f"{total_return:+.1f}%")
                m2.metric("Alpha", f"{alpha:+.1f}%", f"Index: {market_return:+.1f}%")
                m3.metric("Max Drawdown", f"{dd_strat:.1f}%", f"Idx: {dd_market:.1f}%", delta_color="inverse")
                m4.metric("Sharpe", f"{sharpe:.2f}", "Annualized")
                m5.metric("Sortino", f"{sortino:.2f}", "⬆️ Nur Downside-Risk")
                m6.metric("Calmar", f"{calmar:.2f}", "Return / MaxDD")

                # ── DISPLAY METRICS ROW 2 ──
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                s1.metric("Win Rate", f"{w_rate:.0f}%", f"{num_g}G / {num_r}R")
                s2.metric("Volatility", f"{vol:.1f}%", "Ann.")
                s3.metric("Best Streak", f"{max_win_s}", "🟢 Perioden")
                s4.metric("Worst Streak", f"{max_streak}", "🔴 Perioden")
                s5.metric("Stop-Losses", f"{sl_cnt}", "🚨 ausgelöst")
                s6.metric("Take-Profits", f"{tp_cnt}", "🎯 realisiert")

                # Warning if bear regime was active
                bear_periods = log_df[log_df["Regime"] == "BEAR"]
                if not bear_periods.empty:
                    st.markdown(
                        f"""<div class="warn-box">
                            ⚠️ <b>Risiko-Management aktiv:</b> In {len(bear_periods)} von {len(log_df)} Perioden
                            war das Bear-Regime aktiv (S&P 500 &lt; SMA 200). Exposure wurde automatisch
                            auf 20% reduziert (80% Cash-Reserve).
                        </div>""",
                        unsafe_allow_html=True,
                    )

                # ── EQUITY CURVE ──
                st.markdown("### 📈 Equity-Kurve")
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(
                    x=res_df.index, y=res_df["Strategy"], name="Strategy",
                    line=dict(color="#3fb950", width=3),
                    fill="tonexty", fillcolor="rgba(63,185,80,0.05)",
                ))
                fig_eq.add_trace(go.Scatter(
                    x=res_df.index, y=res_df["Market"], name="S&P 500",
                    line=dict(color="#8b949e", dash="dash", width=1.5),
                ))

                for _, row in bear_periods.iterrows():
                    fig_eq.add_vrect(
                        x0=str(row["Start"]), x1=str(row["End"]),
                        fillcolor="rgba(248,81,73,0.08)",
                        line_width=0,
                        annotation_text="BEAR",
                        annotation_position="top left",
                        annotation_font_size=9,
                        annotation_font_color="#f85149",
                    )

                fig_eq.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#0e1117",
                    height=450,
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(gridcolor="#1c2128", title="Portfolio-Wert ($)"),
                    xaxis=dict(gridcolor="#1c2128"),
                    hovermode="x unified",
                    font=dict(family="Inter"),
                )
                st.plotly_chart(fig_eq, width="stretch")

                # ── DRAWDOWN + ROLLING VOL ──
                col_dd, col_vol = st.columns(2)
                dd_s_series = (res_df["Strategy"] - res_df["Strategy"].cummax()) / res_df["Strategy"].cummax() * 100
                dd_m_series = (res_df["Market"] - res_df["Market"].cummax()) / res_df["Market"].cummax() * 100

                fig_dd = go.Figure()
                fig_dd.add_trace(go.Scatter(x=res_df.index, y=dd_s_series, name="Strategy DD",
                    line=dict(color="#f85149", width=1.5), fill="tozeroy", fillcolor="rgba(248,81,73,0.1)"))
                fig_dd.add_trace(go.Scatter(x=res_df.index, y=dd_m_series, name="S&P DD",
                    line=dict(color="#6e7681", dash="dash", width=1)))
                fig_dd.update_layout(title="📉 Drawdowns", template="plotly_dark", height=280,
                    paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font=dict(family="Inter"),
                    margin=dict(l=0, r=0, t=40, b=0))
                col_dd.plotly_chart(fig_dd, width="stretch")

                rw = max(3, ann_map.get(hold_freq, 12))
                rv_s = perf.rolling(rw, min_periods=2).std().fillna(0) / 100 * ann_f * 100
                rv_m = res_df["MktPct"].rolling(rw, min_periods=2).std().fillna(0) / 100 * ann_f * 100
                fig_v = go.Figure()
                fig_v.add_trace(go.Scatter(x=res_df.index, y=rv_s, name="Strategy Vol", line=dict(color="#ffa726", width=1.5)))
                fig_v.add_trace(go.Scatter(x=res_df.index, y=rv_m, name="S&P Vol", line=dict(color="#6e7681", dash="dash", width=1)))
                fig_v.update_layout(title="🌪 Rolling Volatility", template="plotly_dark", height=280,
                    paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font=dict(family="Inter"),
                    margin=dict(l=0, r=0, t=40, b=0))
                col_vol.plotly_chart(fig_v, width="stretch")

                # ── MONTHLY RETURNS HEATMAP ──
                st.markdown("### 📅 Monthly Returns Heatmap")
                try:
                    heatmap_data = monthly_returns_heatmap(res_df["Strategy"])
                    if not heatmap_data.empty:
                        fig_hm = go.Figure(data=go.Heatmap(
                            z=heatmap_data.values,
                            x=heatmap_data.columns.tolist(),
                            y=heatmap_data.index.astype(str).tolist(),
                            colorscale=[[0, "#c93535"], [0.5, "#161b22"], [1, "#2ea043"]],
                            text=np.round(heatmap_data.values, 1),
                            texttemplate="%{text}%",
                            textfont={"size": 11, "family": "Inter"},
                            zmid=0,
                            colorbar=dict(title="Return %"),
                        ))
                        fig_hm.update_layout(
                            template="plotly_dark",
                            height=max(200, len(heatmap_data) * 50),
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                            font=dict(family="Inter"),
                            margin=dict(l=0, r=0, t=10, b=0),
                        )
                        st.plotly_chart(fig_hm, width="stretch")
                except Exception as e:
                    st.caption(f"Heatmap n/a: {e}")

                # ── MONTE CARLO SIMULATION ──
                period_name = {
                    "Wöchentlich": "Wochen", "Alle 2 Wochen": "2-Wochen-Intervalle",
                    "Monatlich": "Monate", "Alle 2 Monate": "2-Monats-Intervalle",
                }.get(hold_choice, "Perioden")
                st.markdown(f"### 🎲 Monte Carlo Simulation (12 {period_name} Forward)")
                try:
                    mc_paths = monte_carlo_simulation(perf, capital, n_sims=300, n_periods=12)
                    fig_mc = go.Figure()
                    for path in mc_paths[:200]:
                        fig_mc.add_trace(go.Scatter(
                            y=path, mode="lines",
                            line=dict(color="rgba(63,185,80,0.06)", width=0.5),
                            showlegend=False,
                        ))
                    p5 = np.percentile(mc_paths, 5, axis=0)
                    p50 = np.percentile(mc_paths, 50, axis=0)
                    p95 = np.percentile(mc_paths, 95, axis=0)
                    fig_mc.add_trace(go.Scatter(y=p5, mode="lines", name="5th %",
                        line=dict(color="#f85149", dash="dash", width=1.5)))
                    fig_mc.add_trace(go.Scatter(y=p50, mode="lines", name="Median",
                        line=dict(color="#3fb950", width=2.5)))
                    fig_mc.add_trace(go.Scatter(y=p95, mode="lines", name="95th %",
                        line=dict(color="#1a5cff", dash="dash", width=1.5)))
                    fig_mc.update_layout(
                        template="plotly_dark", height=350,
                        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                        font=dict(family="Inter"),
                        xaxis_title="Period", yaxis_title="Capital $",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    )
                    st.plotly_chart(fig_mc, width="stretch")
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("🔴 Worst Case (5%)", f"${p5[-1]:,.0f}", f"{(p5[-1]/capital-1)*100:+.1f}%")
                    mc2.metric("📊 Median", f"${p50[-1]:,.0f}", f"{(p50[-1]/capital-1)*100:+.1f}%")
                    mc3.metric("🟢 Best Case (95%)", f"${p95[-1]:,.0f}", f"{(p95[-1]/capital-1)*100:+.1f}%")
                except Exception as e:
                    st.caption(f"Monte Carlo n/a: {e}")

                # ── CURRENT SELECTION ──
                if not rebal_dates.empty and len(rebal_dates) >= 2:
                    last_rb = rebal_dates.iloc[-2]
                    latest_rs_date = rs_history.index[-1] if not rs_history.empty else last_rb
                    
                    if last_rb in ma200.index and pd.notna(ma200.loc[last_rb]):
                        is_bull_now = bm_bt.loc[last_rb] > ma200.loc[last_rb]
                    else:
                        is_bull_now = True
                        
                    if latest_rs_date in rs_history.index:
                        curr_rank_now = rs_history.loc[latest_rs_date].dropna().sort_values(ascending=False).head(bt_positions)
                        st.markdown("---")
                        st.subheader(f"🎯 Aktuelle Ausrichtung (Rebalancing: {last_rb.date()}, RS-Stand: {latest_rs_date.date()})")
                        rc = "#3fb950" if is_bull_now else "#f85149"
                        rt = "BULL (100%)" if is_bull_now else "BEAR (20% / 80% Cash)"
                        st.markdown(f"**Regime:** <span style='color:{rc};font-weight:bold;'>{rt}</span>", unsafe_allow_html=True)
                        
                        if not curr_rank_now.empty:
                            cd = []
                            for ct in curr_rank_now.index:
                                score_rb = rs_history.loc[last_rb, ct] if last_rb in rs_history.index and ct in rs_history.columns else np.nan
                                score_now = curr_rank_now[ct]
                                cd.append({
                                    "Ticker": ct,
                                    "Name": get_company_info(ct).get("Name", ct),
                                    "RS Score (Rebalancing)": score_rb,
                                    "RS Score (Aktuell)": score_now
                                })
                            st.table(pd.DataFrame(cd).style.format(subset=['RS Score (Rebalancing)', 'RS Score (Aktuell)'], formatter="{:.2f}"))

                # ── TRADE LOG ──
                st.markdown("### 📝 Trade Log")
                st.dataframe(
                    log_df.sort_values("End", ascending=False)
                    .style
                    .map(
                        lambda x: "background-color:#238636;color:white" if str(x) == "BULL"
                        else "background-color:#da3633;color:white" if str(x) == "BEAR" else "",
                        subset=["Regime"],
                    )
                    .map(
                        lambda x: "color:#3fb950;font-weight:bold" if isinstance(x, float) and x > 0
                        else "color:#f85149" if isinstance(x, float) and x < 0 else "",
                        subset=["Alpha%"],
                    )
                    .format({"Strat%": "{:+.2f}%", "S&P500%": "{:+.2f}%", "Alpha%": "{:+.2f}%", "Value": "{:,.0f}"}),
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.error(
                    "Backtest konnte nicht ausgeführt werden. "
                    "Nicht genügend Daten oder RS-Scores für den gewählten Zeitraum."
                )

    # Disclaimer for Tab 3
    st.markdown(
        f"""<div class="disclaimer">
            ⚠️ <b>RECHTLICHER HINWEIS</b>: Diese Informationen stellen keine Anlageberatung dar.
            Investitionen in Wertpapiere sind mit Risiken verbunden, einschließlich des vollständigen Kapitalverlusts.
            Vergangene Performance ist kein Indikator für zukünftige Ergebnisse.
            Die simulierten Ergebnisse berücksichtigen Handelskosten von 0.12% pro Rotation, jedoch keine Steuern.
            Konsultieren Sie einen lizenzierten Finanzberater vor jeder Anlageentscheidung.
            © {datetime.now().year} PrecisionInvest Alpha Terminal.
        </div>""",
        unsafe_allow_html=True,
    )
