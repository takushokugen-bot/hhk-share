import streamlit as st
from supabase import create_client, Client
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib.font_manager as fm

# ============================
# 日本語フォント設定（完全体）
# ============================

font_path = "fonts/ipaexg.ttf"  # ← 弦のフォルダと完全一致

# フォントを強制登録（Cloud で必須）
fm.fontManager.addfont(font_path)

# フォントプロパティ取得
jp_font = fm.FontProperties(fname=font_path)

# Matplotlib に適用
plt.rcParams["font.family"] = jp_font.get_name()
plt.rcParams["axes.unicode_minus"] = False

# Seaborn にも適用
sns.set(font=jp_font.get_name())

# ============================
# Supabase 接続
# ============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📊 HHK（ヒヤリハット）分析ダッシュボード")

# ============================
# データ取得
# ============================

reports = (
    supabase.table("hhk_reports")
    .select("id, reported_at, description, reporter, company, photo_url, locations(name), categories(name)")
    .order("reported_at", desc=True)
    .execute()
    .data
)

if not reports:
    st.info("まだ投稿がありません。")
    st.stop()

# ============================
# DataFrame 化
# ============================

df = pd.DataFrame([
    {
        "ID": r["id"],
        "発生日時": pd.to_datetime(r["reported_at"]),
        "場所": r["locations"]["name"] if r["locations"] else "（未設定）",
        "カテゴリ": r["categories"]["name"] if r["categories"] else "（未設定）",
        "内容": r["description"] if r["description"] else "（未入力）",
        "投稿者": r["reporter"] if r["reporter"] else "（未入力）",
        "会社名": r["company"] if r["company"] else "（未入力）",
    }
    for r in reports
])

df["時間帯"] = df["発生日時"].dt.hour

# 日本語曜日マップ
weekday_map = {
    "Monday": "月",
    "Tuesday": "火",
    "Wednesday": "水",
    "Thursday": "木",
    "Friday": "金",
    "Saturday": "土",
    "Sunday": "日",
}

df["曜日"] = df["発生日時"].dt.day_name().map(weekday_map)
df["月"] = df["発生日時"].dt.to_period("M").astype(str)

# ============================
# フィルタ
# ============================

st.subheader("🔍 フィルタ")

col1, col2, col3 = st.columns(3)
with col1:
    location_filter = st.selectbox("場所", ["すべて"] + sorted(df["場所"].unique().tolist()))
with col2:
    category_filter = st.selectbox("カテゴリ", ["すべて"] + sorted(df["カテゴリ"].unique().tolist()))
with col3:
    company_filter = st.selectbox("会社名", ["すべて"] + sorted(df["会社名"].unique().tolist()))

start_date = st.date_input("開始日", df["発生日時"].min().date())
end_date = st.date_input("終了日", df["発生日時"].max().date())

filtered = df.copy()

if location_filter != "すべて":
    filtered = filtered[filtered["場所"] == location_filter]
if category_filter != "すべて":
    filtered = filtered[filtered["カテゴリ"] == category_filter]
if company_filter != "すべて":
    filtered = filtered[filtered["会社名"] == company_filter]

filtered = filtered[
    (filtered["発生日時"].dt.date >= start_date) &
    (filtered["発生日時"].dt.date <= end_date)
]

filtered = filtered.replace("", "（未設定）").fillna("（未設定）")

st.write(f"📌 抽出件数：{len(filtered)} 件")

if filtered.empty:
    st.warning("この条件ではデータがありません。")
    st.stop()

# ============================
# 月次KPI
# ============================

monthly_counts = (
    filtered.groupby("月")["ID"]
    .count()
    .reset_index()
    .sort_values("月")
)

# ============================
# カード風説明
# ============================

def card(text: str):
    st.markdown(
        f"""
        <div style="
            background-color:#f8f9fa;
            padding:15px;
            border-radius:10px;
            border:1px solid #d0d3d8;
            margin-bottom:10px;
            color:#000000;
            font-size:0.9rem;">
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================
# グラフ描画
# ============================

def plot_bar(data, x, title):
    if data.empty:
        st.info(f"{title}：データがありません。")
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.countplot(data=data, x=x, ax=ax)
    ax.set_title(title)
    plt.xticks(rotation=90)
    st.pyplot(fig)
    return fig

# ============================
# 基本グラフ
# ============================

st.subheader("📈 基本グラフ")

colA, colB = st.columns([2, 1])
with colA:
    fig_time = plot_bar(filtered, "時間帯", "時間帯別件数")
with colB:
    card("🕒 **時間帯別件数**：危険が集中する時間帯を可視化します。")

colA, colB = st.columns([2, 1])
with colA:
    fig_week = plot_bar(filtered, "曜日", "曜日別件数")
with colB:
    card("📅 **曜日別件数**：曜日ごとの傾向を把握できます。")

colA, colB = st.columns([2, 1])
with colA:
    fig_loc = plot_bar(filtered, "場所", "場所別件数")
with colB:
    card("📍 **場所別件数**：危険が多い場所を特定できます。")

colA, colB = st.columns([2, 1])
with colA:
    fig_cat = plot_bar(filtered, "カテゴリ", "カテゴリ別件数")
with colB:
    card("🏷 **カテゴリ別件数**：危険の種類の傾向を把握できます。")

# ============================
# 会社別
# ============================

st.subheader("🏢 会社別件数")

colA, colB = st.columns([2, 1])
with colA:
    fig_company = plot_bar(filtered, "会社名", "会社別件数")
with colB:
    card("🏢 **会社別件数**：協力会社ごとの危険傾向を比較できます。")

# ============================
# ヒートマップ
# ============================

st.subheader("🔥 ヒートマップ（赤系）")

pivot_week = filtered.pivot_table(index="曜日", columns="時間帯", aggfunc="size", fill_value=0)
pivot_loc = filtered.pivot_table(index="場所", columns="時間帯", aggfunc="size", fill_value=0)

if not pivot_week.empty:
    fig_heat_week, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot_week, cmap="Reds", annot=True, fmt="d", ax=ax)
    ax.set_title("曜日 × 時間帯 ヒートマップ")
    st.pyplot(fig_heat_week)

if not pivot_loc.empty:
    fig_heat_loc, ax2 = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot_loc, cmap="Reds", annot=True, fmt="d", ax=ax2)
    ax2.set_title("場所 × 時間帯 ヒートマップ")
    st.pyplot(fig_heat_loc)
