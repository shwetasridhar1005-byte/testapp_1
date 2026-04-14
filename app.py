import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Global Market Dashboard", layout="wide")

st.title("🌍 Global Market Dashboard")

# -------- SYMBOL MAP --------
symbols = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW JONES": "^DJI",
    "NIKKEI 225": "^N225",
    "HANG SENG": "^HSI",
    "SHANGHAI": "000001.SS",
    "GOLD": "GC=F",
    "CRUDE OIL": "CL=F"
}

interval_map = {
    "4H": "1h",
    "1D": "1d",
    "1M": "1d",
    "1Y": "1d"
}

# -------- DATA FETCH --------
@st.cache_data
def get_data(ticker, start, end, interval):
    try:
        data = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            auto_adjust=True
        )

        if data is None or data.empty:
            return None

        # Handle multi-index
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if "Close" not in data.columns:
            return None

        data = data.dropna(subset=["Close"])
        data["Returns"] = data["Close"].pct_change()

        if data.empty:
            return None

        return data

    except:
        return None


# -------- DATE HELPER --------
def get_quick_range(option):
    end = datetime.date.today()

    mapping = {
        "1M": 30,
        "2M": 60,
        "6M": 180,
        "1Y": 365,
        "3Y": 365 * 3,
        "5Y": 365 * 5
    }

    start = end - datetime.timedelta(days=mapping[option])
    return start, end


# -------- CHART --------
def plot_chart(data, title):
    if data is None or data.empty:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name=title,
            hovertemplate="Price: %{y:.2f}<br>Date: %{x}<extra></extra>"
        )
    )

    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        dragmode=False,
        xaxis=dict(
            rangeslider=dict(visible=True),
            fixedrange=True
        ),
        yaxis=dict(fixedrange=True)
    )

    return fig


# =========================
# 📈 MARKET TRENDS
# =========================

st.header("📈 Market Trends")

quick_option = st.radio(
    "Quick Duration",
    ["1M", "2M", "6M", "1Y", "3Y", "5Y"],
    horizontal=True
)

start_date, end_date = get_quick_range(quick_option)

c1, c2 = st.columns(2)
with c1:
    start_date = st.date_input("Start Date", start_date)
with c2:
    end_date = st.date_input("End Date", end_date)

select_all = st.checkbox("Select All Indices")

if select_all:
    selected_assets = list(symbols.keys())
else:
    selected_assets = st.multiselect(
        "Select Assets",
        list(symbols.keys()),
        default=["NIFTY 50", "S&P 500", "NASDAQ"]
    )

# Grid layout (2 columns)
for i in range(0, len(selected_assets), 2):
    cols = st.columns(2)

    for j in range(2):
        if i + j < len(selected_assets):
            asset = selected_assets[i + j]

            with cols[j]:
                st.subheader(asset)

                interval_label = st.radio(
                    f"Interval - {asset}",
                    ["4H", "1D", "1M", "1Y"],
                    horizontal=True,
                    key=f"int_{asset}"
                )

                interval = interval_map[interval_label]

                data = get_data(symbols[asset], start_date, end_date, interval)
                fig = plot_chart(data, asset)

                if fig:
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config={
                            "scrollZoom": False,
                            "displayModeBar": False,
                            "doubleClick": False
                        }
                    )
                else:
                    st.warning("Data unavailable")


# =========================
# 🔗 CORRELATION ANALYZER
# =========================

st.header("🔗 Correlation Analyzer")

quick_corr = st.radio(
    "Quick Duration (Correlation)",
    ["1M", "2M", "6M", "1Y", "3Y", "5Y"],
    horizontal=True
)

start_corr, end_corr = get_quick_range(quick_corr)

c3, c4 = st.columns(2)
with c3:
    start_corr = st.date_input("Start Date (Corr)", start_corr)
with c4:
    end_corr = st.date_input("End Date (Corr)", end_corr)

select_all_corr = st.checkbox("Select All (Correlation)")

if select_all_corr:
    selected_corr_assets = list(symbols.keys())
else:
    selected_corr_assets = st.multiselect(
        "Select Assets (Correlation)",
        list(symbols.keys()),
        default=["NIFTY 50", "S&P 500", "GOLD"]
    )

if len(selected_corr_assets) > 8:
    st.warning("Max 8 assets allowed. Showing first 8.")
    selected_corr_assets = selected_corr_assets[:8]

if len(selected_corr_assets) >= 2:

    df = pd.DataFrame()

    for asset in selected_corr_assets:
        data = get_data(symbols[asset], start_corr, end_corr, "1d")
        if data is not None:
            df[asset] = data["Returns"]

    df = df.dropna()

    if not df.empty:

        corr = df.corr()

        st.subheader("📊 Correlation Table")
        st.dataframe(corr)

        st.subheader("🔥 Heatmap")

        fig = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale="RdBu",
            zmin=-1,
            zmax=1
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📉 Returns Comparison")
        st.line_chart(df)

    else:
        st.warning("Not enough overlapping data")

else:
    st.info("Select at least 2 assets")

st.info("Mobile friendly • Slider enabled • Crosshair enabled")
