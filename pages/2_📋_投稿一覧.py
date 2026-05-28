from modules.font import *
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time

# ============================
# Supabase 接続
# ============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📋 投稿一覧（ページネーション＋自動更新付き）")

# ============================
# 自動リロード設定
# ============================

auto_refresh = st.checkbox("🔄 5秒ごとに自動更新する", value=False)
if auto_refresh:
    st.caption("5秒ごとに最新データを取得します。")
    time.sleep(5)
    st.rerun()

# ============================
# ページネーション設定
# ============================

PAGE_SIZE = 50
if "page" not in st.session_state:
    st.session_state.page = 0

# ============================
# データ取得（← company を追加）
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
# DataFrame 化（← 会社名を追加）
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
        "内容": r["description"],
        "投稿者": r["reporter"],
        "会社名": r["company"] if r["company"] else "（未入力）",  # ← 追加
        "写真URL": r["photo_url"],
    }
    for r in reports
])

# ============================
# フィルタ UI（必要なら会社名フィルタも追加可能）
# ============================

st.subheader("🔍 フィルタ")

col1, col2, col3, col4 = st.columns(4)
with col1:
    year_filter = st.selectbox("年", ["すべて"] + sorted(df["年"].unique().tolist()))
with col2:
    month_filter = st.selectbox("月", ["すべて"] + sorted(df["月"].unique().tolist()))
with col3:
    hour_filter = st.selectbox("時間帯", ["すべて"] + sorted(df["時間帯"].unique().tolist()))
with col4:
    weekday_filter = st.selectbox("曜日", ["すべて"] + sorted(df["曜日"].unique().tolist()))

col5, col6 = st.columns(2)
with col5:
    location_filter = st.selectbox("場所", ["すべて"] + sorted(df["場所"].unique().tolist()))
with col6:
    category_filter = st.selectbox("カテゴリ", ["すべて"] + sorted(df["カテゴリ"].unique().tolist()))

# ============================
# フィルタ適用
# ============================

filtered = df.copy()

if year_filter != "すべて":
    filtered = filtered[filtered["年"] == year_filter]
if month_filter != "すべて":
    filtered = filtered[filtered["月"] == month_filter]
if hour_filter != "すべて":
    filtered = filtered[filtered["時間帯"] == hour_filter]
if weekday_filter != "すべて":
    filtered = filtered[filtered["曜日"] == weekday_filter]
if location_filter != "すべて":
    filtered = filtered[filtered["場所"] == location_filter]
if category_filter != "すべて":
    filtered = filtered[filtered["カテゴリ"] == category_filter]

total = len(filtered)
st.write(f"📌 抽出件数：{total} 件")

# ============================
# ページネーション適用
# ============================

max_page = max((total - 1) // PAGE_SIZE, 0)

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    if st.button("⬅ 前のページ", disabled=(st.session_state.page <= 0)):
        st.session_state.page -= 1
        st.rerun()
with col_p2:
    st.write(f"ページ：{st.session_state.page + 1} / {max_page + 1}")
with col_p3:
    if st.button("次のページ ➡", disabled=(st.session_state.page >= max_page)):
        st.session_state.page += 1
        st.rerun()

start = st.session_state.page * PAGE_SIZE
end = start + PAGE_SIZE
page_df = filtered.iloc[start:end]

# ============================
# 表形式で一覧表示（削除ボタン付き）
# ============================

st.subheader("📊 投稿テーブル（削除可能）")

for _, row in page_df.iterrows():
    colA, colB = st.columns([8, 1])

    with colA:
        st.write(
            f"**ID:** {row['ID']}  \n"
            f"**日時:** {row['発生日時']}  \n"
            f"**場所:** {row['場所']}  \n"
            f"**カテゴリ:** {row['カテゴリ']}  \n"
            f"**内容:** {row['内容']}  \n"
            f"**投稿者:** {row['投稿者']}  \n"
            f"**会社名:** {row['会社名']}"  # ← 追加
        )

    with colB:
        if st.button("🗑 削除", key=f"delete_{row['ID']}"):
            supabase.table("hhk_reports").delete().eq("id", row["ID"]).execute()
            st.success("削除しました")
            st.rerun()

# ============================
# 写真表示
# ============================

st.subheader("🖼 写真表示")

for _, row in page_df.iterrows():
    if st.button(f"写真を見る（ID:{row['ID']}）", key=f"view_{row['ID']}"):
        url = row["写真URL"]
        if isinstance(url, str) and url.startswith("http"):
            st.image(url, width=350)
        else:
            st.info("写真はありません。")
