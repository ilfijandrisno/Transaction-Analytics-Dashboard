
# streamlit_app_v2.py
# Versi dashboard dengan 4 tab periodik dan filter dinamis sesuai period
# Pastikan file 'transactions_dummy.csv' ada di folder yang sama

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
from itertools import count
from plotly import graph_objects as go

st.set_page_config(page_title="Synthetic Transactions Dashboard", layout="wide")
pio.templates.default = "plotly_white"

@st.cache_data
def load_data():
    df = pd.read_csv("data/transactions_dummy.csv", parse_dates=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["quarter"] = df["date"].dt.quarter
    return df

MONTH_NAMES = {i: pd.Timestamp(2000, i, 1).strftime("%b") for i in range(1,13)}

# ---- Number format (EN): 1,234,567 ; 1,234,567.89 ; short 10.25 M ----
def fmt_en(x: float) -> str:
    """Thousands with commas. No decimals if integer; else up to 2 decimals (trim zeros)."""
    try:
        xv = float(x)
    except Exception:
        return str(x)
    s = f"{xv:,.2f}"
    # jika bulat -> hilangkan desimal
    if s.endswith("00"):
        return f"{int(round(xv)):,}"
    # jika ada pecahan -> pangkas trailing zero
    return s.rstrip("0").rstrip(".")

def fmt_rp(x: float) -> str:
    return f"Rp{fmt_en(x)}"

def fmt_int(x) -> str:
    try:
        return f"{int(x):,}"
    except Exception:
        return str(x)

def fmt_short(x: float) -> str:
    """K/M/B/T with exactly 2 decimals and NO space (e.g., 214.69k, 10.25M)."""
    n = float(x)
    if abs(n) >= 1e12:
        return f"{n/1e12:,.2f}T"
    if abs(n) >= 1e9:
        return f"{n/1e9:,.2f}B"
    if abs(n) >= 1e6:
        return f"{n/1e6:,.2f}M"
    if abs(n) >= 1e3:
        return f"{n/1e3:,.2f}k"
    return fmt_en(n)

def format_number_short(value):
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value/1_000:.2f}k"
    else:
        return f"{value:.0f}"
    
def set_bar_text_per_trace(fig, values):
    """Pasang label di atas bar.
    - Single-trace: panjang text = jumlah bar
    - Multi-trace (tiap kategori 1 trace): text per-trace 1 nilai
    """
    labels = [fmt_short(v) for v in values]

    if len(fig.data) == 1:
        tr = fig.data[0]
        tr.text = labels                     # <- satu label per bar
        tr.texttemplate = "%{text}"
        tr.textposition = "outside"
        tr.cliponaxis = False
        tr.textfont = dict(color="#111827")
        return

    for i, tr in enumerate(fig.data):
        tr.text = [labels[i]] if i < len(labels) else []
        tr.texttemplate = "%{text}"
        tr.textposition = "outside"
        tr.cliponaxis = False
        tr.textfont = dict(color="#111827")

def kpi_css():
    st.markdown("""
    <style>
    .kpi-card{padding:16px;border-radius:16px;background:#ffffff;
              box-shadow:0 2px 12px rgba(2,6,23,.06);border:1px solid #eef2f7}
    .kpi-title{font-size:12px;color:#64748b;margin:0}
    .kpi-value{font-size:24px;font-weight:700;margin:4px 0 0 0;color:#0f172a}
    </style>
    """, unsafe_allow_html=True)

def kpi_card(title, value):
    st.markdown(f"""
    <div class="kpi-card">
      <p class="kpi-title">{title}</p>
      <p class="kpi-value">{value}</p>
    </div>
    """, unsafe_allow_html=True)

def agg_trend(dff, period):
    import pandas as pd
    if dff is None or dff.empty:
        return pd.DataFrame(columns=["Period","GMV","Fee","Txn","success"])

    if period == "Weekly":
        # 1) Agregasi per ISO week
        g = (dff.groupby("week")
                .agg(GMV=("amount","sum"),
                     Fee=("fee_amount","sum"),
                     Txn=("amount","size"),
                     success=("status", lambda s: (s == "SUCCESS").mean()))
             ).reset_index().sort_values("week")

        # 2) Map week -> W1..W5 (minggu ke-6 ikut W5)
        weeks_sorted = g["week"].sort_values().unique().tolist()
        labels = ["W1", "W2", "W3", "W4", "W5"]
        week_to_w = {w: labels[min(i, 4)] for i, w in enumerate(weeks_sorted)}
        g["Period"] = g["week"].map(week_to_w)

        # 3) AGREGASI ULANG per Period (karena W5 bisa berisi >1 minggu)
        gg = g.copy()
        gg["success_num"] = gg["success"] * gg["Txn"]  # untuk rata-rata berbobot

        gg = (gg.groupby("Period", as_index=False)
                .agg(GMV=("GMV","sum"),
                     Fee=("Fee","sum"),
                     Txn=("Txn","sum"),
                     success_num=("success_num","sum")))

        gg["success"] = gg["success_num"] / gg["Txn"]
        gg = gg.drop(columns=["success_num"])

        # 4) Pastikan urutan kategori W1..W5 rapi
        import pandas as pd
        period_order = labels[:len(gg)]
        gg["Period"] = pd.Categorical(gg["Period"], categories=labels, ordered=True)
        gg = gg.sort_values("Period").reset_index(drop=True)

        return gg

    elif period == "Monthly":
        g = (dff.groupby("month")
                .agg(GMV=("amount","sum"),
                     Fee=("fee_amount","sum"),
                     Txn=("amount","size"),
                     success=("status", lambda s: (s=="SUCCESS").mean()))
             ).reset_index().sort_values("month")
        g["Period"] = g["month"].map(MONTH_NAMES)

    elif period == "Quarterly":
        g = (dff.groupby("quarter")
                .agg(GMV=("amount","sum"),
                     Fee=("fee_amount","sum"),
                     Txn=("amount","size"),
                     success=("status", lambda s: (s=="SUCCESS").mean()))
             ).reset_index().sort_values("quarter")
        g["Period"] = "Q" + g["quarter"].astype(str)

    else:  # Yearly
        g = (dff.groupby("year")
                .agg(GMV=("amount","sum"),
                     Fee=("fee_amount","sum"),
                     Txn=("amount","size"),
                     success=("status", lambda s: (s=="SUCCESS").mean()))
             ).reset_index().sort_values("year")
        g["Period"] = g["year"].astype(str)

    return g



def filter_control(label: str, options: list[str], key: str) -> list[str]:
    """
    Dropdown ringkas dengan (All). 
    - (All) => return semua options
    - (Custom...) => muncul multiselect kedua
    - Pilih satu item => return [item]
    """
    pick = st.selectbox(
        label,
        ["(All)", "(Custom...)"] + options,
        index=0,
        key=f"{key}_select",
    )
    if pick == "(All)":
        return options
    if pick == "(Custom...)":
        return st.multiselect(
            f"{label} — pilih item",
            options,
            default=options,
            key=f"{key}_custom",
        )
    # single value
    return [pick]

def add_full_number_hover(fig, series, is_int=False):
    """Attach full-number hover text; works for single-trace & multi-trace (color='category')."""
    import numpy as np
    vals = [(f"{int(v):,}" if is_int else fmt_en(v)) for v in series.tolist()]

    # Single trace: cukup vektor
    if len(fig.data) == 1:
        fig.update_traces(
            customdata=np.array(vals, dtype=object).reshape(-1, 1),
            hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>"
        )
        return fig

    # Multi-trace (satu bar per trace): set customdata per trace
    for i, tr in enumerate(fig.data):
        v = vals[i] if i < len(vals) else ""
        tr.customdata = [[v]]
        tr.hovertemplate = "<b>%{x}</b><br>%{customdata}<extra></extra>"
    return fig

def render_dash(period:str, df:pd.DataFrame, key_prefix:str):
    kpi_css()

    # --- unique key generator for charts in this tab ---
    _cid = count(1)
    def plot(fig, name: str):
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_{name}_{next(_cid)}")

    def style_numeric(fig):
        fig.update_layout(separators=".,")      # ribuan '.', desimal ','
        fig.update_yaxes(tickformat=",.3f")     # 3 desimal
        fig.update_traces(texttemplate="%{y:,.3f}", textposition="outside", cliponaxis=False)
        return fig
    st.subheader(f"{period} Dashboard — Filters")

    cats_all = sorted(df["category"].unique().tolist())
    chs_all  = sorted(df["channel"].unique().tolist())
    regs_all = sorted(df["region"].unique().tolist())
    years_all= sorted(df["year"].unique().tolist())

    # --- WEEKLY FILTERS ---
    if period == "Weekly":
        # --- WEEKLY FILTERS ---
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
        with c1:
            year = st.selectbox("Year", years_all, index=len(years_all) - 1, key=f"{key_prefix}_year")
        months_in_year = sorted(df.loc[df["year"] == year, "month"].unique().tolist())
        with c2:
            month = st.selectbox(
                "Month",
                months_in_year,
                index=(len(months_in_year) - 1),            # ⬅️ default: bulan terakhir
                format_func=lambda m: MONTH_NAMES.get(m, ""),
                key=f"{key_prefix}_month",
            )
        with c3:
            cats = filter_control("Category", cats_all, key=f"{key_prefix}_cats")
        with c4:
            chs  = filter_control("Channel",  chs_all,  key=f"{key_prefix}_chs")
        with c5:
            regs = filter_control("Region", regs_all, key=f"{key_prefix}_regs")

        dff = df[
            (df["year"] == year)
            & (df["month"] == month)
            & (df["category"].isin(cats))
            & (df["channel"].isin(chs))
            & (df["region"].isin(regs))
        ].copy()

        if dff.empty:
            st.warning("No data for the selected filters.")
            return

    # --- MONTHLY FILTERS ---
    elif period == "Monthly":
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            year = st.selectbox("Year", years_all, index=len(years_all)-1, key=f"{key_prefix}_year")
        with c2:
            cats = filter_control("Category", cats_all, key=f"{key_prefix}_cats")
        with c3:
            chs  = filter_control("Channel",  chs_all,  key=f"{key_prefix}_chs")
        with c4:
            regs = filter_control("Region", regs_all, key=f"{key_prefix}_regs")


        # ⬇️ Filter ke bulan terpilih
        dff = df[
            (df["year"]==year) &
            (df["category"].isin(cats)) &
            (df["channel"].isin(chs)) &
            (df["region"].isin(regs))
        ].copy()

        if dff.empty:
            st.warning("No data for the selected filters.")
            return

    # --- QUARTERLY FILTERS ---
    elif period == "Quarterly":
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            year = st.selectbox("Year", years_all, index=len(years_all)-1, key=f"{key_prefix}_year")
        with c2:
            cats = filter_control("Category", cats_all, key=f"{key_prefix}_cats")
        with c3:
            chs  = filter_control("Channel",  chs_all,  key=f"{key_prefix}_chs")
        with c4:
            regs = filter_control("Region", regs_all, key=f"{key_prefix}_regs")

        # ⬇️ Filter ke quarter terpilih
        dff = df[
            (df["year"]==year) &
            (df["category"].isin(cats)) &
            (df["channel"].isin(chs)) &
            (df["region"].isin(regs))
        ].copy()

        if dff.empty:
            st.warning("No data for the selected filters.")
            return

    # --- YEARLY FILTERS ---
    else:  # Yearly
        c2, c3, c4 = st.columns([1,  1, 1])
        # ⬇️ Multi-select Year (default semua)
        with c2:
            cats = filter_control("Category", cats_all, key=f"{key_prefix}_cats")
        with c3:
            chs  = filter_control("Channel",  chs_all,  key=f"{key_prefix}_chs")
        with c4:
            regs = filter_control("Region", regs_all, key=f"{key_prefix}_regs")
    
        dff = df[
            (df["category"].isin(cats)) &
            (df["channel"].isin(chs)) &
            (df["region"].isin(regs))
        ].copy()
    
        if dff.empty:
            st.warning("No data for the selected filters.")
            return


    gmv = dff["amount"].sum()
    fee = dff["fee_amount"].sum()
    users = dff["user_id"].nunique()
    txns = len(dff)

    st.markdown(" ")
    c1,c2,c3,c4 = st.columns(4, gap="large")
    with c1: kpi_card("GMV", fmt_rp(gmv))
    with c2: kpi_card("Fee Revenue", fmt_rp(fee))
    with c3: kpi_card("Total Users", fmt_int(users))
    with c4: kpi_card("Total Transactions", fmt_int(txns))

    st.markdown("---")

    # ------- Overview -------
    st.subheader("Overview")
    trend = agg_trend(dff, period)
    co1,co2 = st.columns(2, gap="large")
    period_order = trend["Period"].tolist()
    with co1:
        fig = px.bar(trend, x="Period", y="GMV", title=f"Total Transaction Value — {period}",
                     category_orders={"Period": period_order}   # <-- pastikan urut W1..Wn
                     )
        ymax = float(trend["GMV"].max())
        fig.update_yaxes(tickformat="~s", range=[0, ymax * 1.12])

        # label di atas bar: 2 desimal (366.37M dst)
        fig.update_traces(
            text=trend["GMV"].apply(fmt_short),   # ← 2 desimal, tanpa spasi, k/M/B/T
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color="#111827")        # ⬅️ teks hitam
        )

        # hover tetap angka full
        fig.update_traces(
            customdata=trend["GMV"].apply(fmt_en),
            hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>"
        )

        plot(fig, "trend_gmv")
    with co2:
        fig = px.bar(trend, x="Period", y="Fee", title=f"Fee-based Revenue — {period}",
                     category_orders={"Period": period_order}
                     )
        fig.update_yaxes(tickformat="~s")

        fig.update_traces(
            text=trend["Fee"].apply(fmt_short),   # ← 2 desimal (4.64M, 5.90M, dst)
            texttemplate="%{text}",
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color="#111827")        # ⬅️ teks hitam
        )

        fig.update_traces(
            customdata=trend["Fee"].apply(fmt_en),
            hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>"
        )

        plot(fig, "trend_fee")

    # --- Success Rate line ---
    sr = trend.copy()                      # trend = hasil agg_trend(dff, period)
    sr["label"] = ""                       # kolom teks kosong untuk semua titik
    
    imax = sr["success"].idxmax()          # index titik tertinggi
    imin = sr["success"].idxmin()          # index titik terendah

    # Jika imax==imin (semua sama), biarkan hanya satu label
    sr.loc[imax, "label"] = f"{sr.loc[imax,'success']:.2%}"
    if imax != imin:
        sr.loc[imin, "label"] = f"{sr.loc[imin,'success']:.2%}"

    # fig = px.line(trend, x="Period", y="success", markers=True, title=f"Success Rate — {period}")
    fig = px.line(
        sr,
        x="Period",                         # pastikan sudah pakai 'Period' (W1..Wn / Jan..)
        y="success",
        text="label",                       # ⬅️ hanya max/min yang berisi teks
        markers=True,
        hover_data={  # sembunyikan kolom yang tidak mau ditampilkan
            "label": False,
            "Period": True,
            "success": True
        },
        title=f"Success Rate — {period}",
        category_orders={"Period": sr["Period"].tolist()}  # jaga urutan bila perlu
    )
    
    fig.update_layout(
        yaxis_title="Percentage",
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_traces(
        textposition="top center",          # teks di atas titik
        textfont=dict(color="#111827")      # warna teks hitam
    )
    plot(fig, "trend_sr")

    # ------- Business Mix -------
    CAT_COLORS = {
        "Airtime": "#4F46E5",             # indigo
        "Electricity Prepaid": "#06B6D4", # cyan
        "Data Bundle": "#22C55E",         # green
        "Postpaid Bills": "#F59E0B",      # amber
        "Micro-Insurance": "#EC4899",     # pink
        "Water Utility": "#64748B",       # slate
        }
    CAT_ORDER = list(CAT_COLORS.keys())

    st.subheader("Business Mix")

    cat = (dff.groupby("category")
              .agg(transactions=("amount","size"),
                   gmv=("amount","sum"),
                   fee=("fee_amount","sum"))
              .reset_index()
              .sort_values("transactions", ascending=False))

    # Row 1: Fee by Category & GMV by Category
    r1c1, r1c2 = st.columns(2, gap="large")
    with r1c1:
        fig = go.Figure(go.Bar(
            x=cat["category"],
            y=cat["fee"],
            marker_color=[CAT_COLORS[c] for c in cat["category"]],
            width=0.9  # batang lebih tebal (0..1 terhadap slot kategori)
        ))
        fig.update_layout(
            title="Fee by Category",
            bargap=0.05,              # jarak antar kategori
            showlegend=False,
            margin=dict(t=90, b=40),
            uniformtext_minsize=10,
            uniformtext_mode="hide"
        )
        peak = float(cat["fee"].max())
        fig.update_yaxes(range=[0, peak * 1.18], tickformat="~s", automargin=True)
        set_bar_text_per_trace(fig, cat["fee"])
        add_full_number_hover(fig, cat["fee"], is_int=False)
        plot(fig, "mix_fee")
    with r1c2:
        fig = go.Figure(go.Bar(
            x=cat["category"],
            y=cat["gmv"],
            marker_color=[CAT_COLORS[c] for c in cat["category"]],
            width=0.9
        ))
        fig.update_layout(
            title="GMV by Category",
            bargap=0.05,
            showlegend=False,
            margin=dict(t=90, b=40),
            uniformtext_minsize=10,
            uniformtext_mode="hide"
        )
        peak = float(cat["gmv"].max())
        fig.update_yaxes(range=[0, peak * 1.18], tickformat="~s", automargin=True)
        set_bar_text_per_trace(fig, cat["gmv"])   
        add_full_number_hover(fig, cat["gmv"], is_int=False)
        plot(fig, "mix_gmv")

    # Row 2: Txn share & Transactions by Region
    r2c1, r2c2 = st.columns(2, gap="large")
    with r2c1:
        fig = go.Figure(go.Bar(
            x=cat["category"],
            y=cat["transactions"],
            marker_color=[CAT_COLORS[c] for c in cat["category"]],
            width=0.9
        ))
        fig.update_layout(
            title="Share of Transactions by Category",
            bargap=0.05,
            showlegend=False,
            margin=dict(t=90, b=40),
            uniformtext_minsize=10,
            uniformtext_mode="hide"
        )
        peak = float(cat["transactions"].max())
        fig.update_yaxes(range=[0, peak * 1.18], tickformat="~s", automargin=True)  # headroom 18%
        set_bar_text_per_trace(fig, cat["transactions"])  
        add_full_number_hover(fig, cat["transactions"], is_int=True)
        plot(fig, "mix_txn")
    with r2c2:
        reg = (dff.groupby("region").agg(transactions=("amount","size")).reset_index())
        fig = px.pie(reg, names="region", values="transactions", hole=0.25,
                     title="Transactions by Region")
        plot(fig, "mix_region")

    # (Opsional) Row 3: GMV Share Pie per Category
    # r3c = st.container()
    # with r3c:
    #     fig = px.pie(cat, names="category", values="gmv", hole=0.25,
    #                  title="GMV Share by Category")
    #     st.plotly_chart(fig, use_container_width=True)

    # ------- Reliability & Monitoring -------
    st.subheader("Reliability & Monitoring")
    sf = (dff.groupby(["category","status"])
          .size()
          .reset_index(name="count"))
    # Teks label di atas bar (pakai pemisah ribuan)
    sf["count_txt"] = sf["count"].apply(lambda v: f"{int(v):,}")

    # Warna konsisten: SUCCESS = hijau, FAILED = merah
    STATUS_COLORS = {"SUCCESS": "#10B981", "FAILED": "#EF4444"}
    
    fig = px.bar(
        sf, 
        x="category", 
        y="count", 
        color="status", 
        text="count_txt", 
        barmode="group", 
        title="Success vs Failed by Category",
        category_orders={"status": ["SUCCESS", "FAILED"]},     # urutan legend
        color_discrete_map=STATUS_COLORS
        )
    
    # Rapikan tampilan
    fig.update_traces(
        textposition="outside",                # teks di luar bar (di atas)
        cliponaxis=False,                      # jangan terpotong di tepi
        textfont=dict(color="#111827")         # teks hitam
    )

    # Sumbu & hover
    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Total",                   # ⬅️ ganti label sumbu-Y
        legend_title_text="Status"
    )

    fig.update_yaxes(
        tickformat="~s")  

    fig.update_traces(
        customdata=sf[["status", "count"]],  # ⬅️ 2 kolom ke hover
        hovertemplate=(
            "status=%{customdata[0]}<br>"     # status asli
            "category=%{x}<br>"
            "total=%{customdata[1]:,}"        # total format ribuan
            "<extra></extra>"
        )
    )

    plot(fig, "rel_sf")

    failed = dff[dff.get("status", "").eq("FAILED")].copy()
    if failed.empty:
        st.info("Tidak ada transaksi FAILED untuk filter saat ini.")
    elif "failure_reason" not in failed.columns:
        st.info("Kolom 'failure_reason' tidak tersedia di dataset.")
    else:
        failed["failure_reason"] = failed["failure_reason"].fillna("").replace("", "Unknown")
    
        # ↓ ganti 'count' → 'Total'
        fr = (failed.groupby("failure_reason")
                    .size()
                    .reset_index(name="Total")
                    .sort_values("Total", ascending=False)
                    .head(15))
    
        if fr.empty:
            st.info("Tidak ada data 'Failure Reasons' untuk filter saat ini.")
        else:
            fr = (failed.groupby("failure_reason")
                        .size()
                        .reset_index(name="Total")
                        .sort_values("Total", ascending=False))

            fig = px.bar(
                fr,
                x="failure_reason",
                y="Total",
                title="Failure Reasons (Top)"
            )

            # Atur layout & proporsi batang
            fig.update_layout(
                xaxis_title="Failure Reason",
                yaxis_title="Total",
                bargap=0.45,   # batang lebih ramping (0..1)
                height=520,
                margin=dict(t=40, b=10)
            )

            # (opsional) bikin batang tampak lebih tinggi dan label jelas
            ymax = float(fr["Total"].max())
            fig.update_yaxes(range=[0, ymax * 1.18])
            fig.update_traces(text=fr["Total"], textposition="outside", cliponaxis=False, textfont=dict(color="#111827") )

            plot(fig, "rel_fr")

    # fr = (dff[dff["status"]=="FAILED"]
    #         .groupby("failure_reason").size()
    #         .reset_index(name="count")
    #         .sort_values("count", ascending=False))
    # fig = px.bar(fr, x="failure_reason", y="count", title="Failure Reasons (Top)")
    # plot(fig, "rel_fr")

    # ------- Users -------
    st.subheader("Users")
    per_user = (dff.groupby("user_id")
                   .agg(gmv=("amount","sum"), txns=("amount","size"))
                   .reset_index())
    colA,colB,colC = st.columns(3, gap="large")

    active_users   = per_user["user_id"].nunique()
    avg_gmv_user   = per_user["gmv"].mean()  if len(per_user)>0 else 0
    total_txns     = int(per_user["txns"].sum()) if len(per_user)>0 else 0
    avg_txn_user   = per_user["txns"].mean() if len(per_user)>0 else 0

    with colA:
        st.metric("Active Users", fmt_int(per_user['user_id'].nunique()))
    with colB:
        st.metric("Avg GMV per Active User", fmt_rp(avg_gmv_user))
    with colC:
        st.metric("Total Transactions (Users)", fmt_int(total_txns))

    # Tabel users — full width + format kolom numerik
    _tbl = per_user.sort_values("gmv", ascending=False).head(200).copy()
    _tbl["gmv"]  = _tbl["gmv"].apply(fmt_en)   # 1,234,567.89
    _tbl["txns"] = _tbl["txns"].apply(fmt_int)  # 12,345
    st.dataframe(_tbl, use_container_width=True)

    st.markdown("---")
    st.download_button("Download filtered data (CSV)",
                       data=dff.to_csv(index=False).encode("utf-8"),
                       file_name=f"filtered_{period.lower()}.csv",
                       mime="text/csv")

df = load_data()
st.title("Transaction Analytics Dashboard")
st.caption("All figures are synthetic and for demo purposes only.")

tabW, tabM, tabQ, tabY = st.tabs(["Weekly", "Monthly", "Quarterly", "Yearly"])
with tabW:
    render_dash("Weekly", df, key_prefix="W")
with tabM:
    render_dash("Monthly", df, key_prefix="M")
with tabQ:
    render_dash("Quarterly", df, key_prefix="Q")
with tabY:
    render_dash("Yearly", df, key_prefix="Y")
