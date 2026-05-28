import streamlit as st
from supabase import create_client, Client
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from modules.font import *   # ← フォント設定は必ず最後に import

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
    .select("id, reported_at, description, reporter, company, locations(name), categories(name)")
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
        "年": pd.to_datetime(r["reported_at"]).year,
        "月": pd.to_datetime(r["reported_at"]).month,
        "時間帯": pd.to_datetime(r["reported_at"]).hour,
        "曜日": pd.to_datetime(r["reported_at"]).day_name(),
        "場所": r["locations"]["name"] if r["locations"] else "",
        "カテゴリ": r["categories"]["name"] if r["categories"] else "",
        "会社名": r["company"] if r["company"] else "（未入力）",
    }
    for r in reports
])

# ============================
# フィルタ UI
# ============================

st.subheader("🔍 フィルタ")

col1, col2, col3 = st.columns(3)
with col1:
    year_filter = st.selectbox("年", ["すべて"] + sorted(df["年"].unique().tolist()))
with col2:
    month_filter = st.selectbox("月", ["すべて"] + sorted(df["月"].unique().tolist()))
with col3:
    company_filter = st.selectbox("会社名", ["すべて"] + sorted(df["会社名"].unique().tolist()))

filtered = df.copy()

if year_filter != "すべて":
    filtered = filtered[filtered["年"] == year_filter]
if month_filter != "すべて":
    filtered = filtered[filtered["月"] == month_filter]
if company_filter != "すべて":
    filtered = filtered[filtered["会社名"] == company_filter]

st.write(f"📌 抽出件数：{len(filtered)} 件")

# ============================
# グラフ1：会社別件数
# ============================

st.subheader("🏢 会社別件数")

fig1, ax1 = plt.subplots(figsize=(6, 4))
sns.countplot(data=filtered, x="会社名", ax=ax1)
ax1.set_xlabel("会社名")
ax1.set_ylabel("件数")
st.pyplot(fig1)

# ============================
# グラフ2：カテゴリ別件数
# ============================

st.subheader("📦 カテゴリ別件数")

fig2, ax2 = plt.subplots(figsize=(6, 4))
sns.countplot(data=filtered, x="カテゴリ", ax=ax2)
ax2.set_xlabel("カテゴリ")
ax2.set_ylabel("件数")
st.pyplot(fig2)

# ============================
# グラフ3：曜日 × 時間帯 ヒートマップ
# ============================

st.subheader("🕒 曜日 × 時間帯 ヒートマップ")

pivot = filtered.pivot_table(
    index="曜日",
    columns="時間帯",
    values="ID",
    aggfunc="count",
    fill_value=0
)

fig3, ax3 = plt.subplots(figsize=(10, 6))
sns.heatmap(pivot, cmap="Blues", annot=True, fmt="d", ax=ax3)
ax3.set_xlabel("時間帯")
ax3.set_ylabel("曜日")
st.pyplot(fig3)
