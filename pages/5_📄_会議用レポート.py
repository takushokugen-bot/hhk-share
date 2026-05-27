import streamlit as st
from supabase import create_client, Client
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches
from io import BytesIO
import datetime as dt

# ============================
# Supabase 接続
# ============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📄 会議用レポート出力（Word）")

# ============================
# 期間指定
# ============================

today = dt.date.today()
start_date = st.date_input("開始日", today.replace(day=1))
end_date = st.date_input("終了日", today)

# ============================
# データ取得
# ============================

reports = (
    supabase.table("hhk_reports")
    .select("id, reported_at, description, reporter, company, locations(name), categories(name)")
    .order("reported_at")
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

df = df[
    (df["発生日時"].dt.date >= start_date) &
    (df["発生日時"].dt.date <= end_date)
]

if df.empty:
    st.warning("この期間のデータはありません。")
    st.stop()

# ============================
# KPI 計算
# ============================

df["日付"] = df["発生日時"].dt.date

first_day_this_month = today.replace(day=1)
first_day_last_month = (first_day_this_month - dt.timedelta(days=1)).replace(day=1)
last_day_last_month = first_day_this_month - dt.timedelta(days=1)

this_month_df = df[df["日付"] >= first_day_this_month]
this_month_count = len(this_month_df)

last_month_df = df[
    (df["日付"] >= first_day_last_month) &
    (df["日付"] <= last_day_last_month)
]
last_month_count = len(last_month_df)

if last_month_count == 0:
    mom = "N/A"
else:
    mom = f"{((this_month_count - last_month_count) / last_month_count) * 100:.1f}%"

# ============================
# グラフ生成
# ============================

def plot_bar(data, x, title):
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.countplot(data=data, x=x, ax=ax)
    ax.set_title(title)
    plt.xticks(rotation=90)
    return fig

def plot_heatmap(pivot, title):
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot, cmap="Reds", annot=True, fmt="d", ax=ax)
    ax.set_title(title)
    return fig

def fig_to_png_bytes(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf

df["時間帯"] = df["発生日時"].dt.hour
df["曜日"] = df["発生日時"].dt.day_name()

fig_time = plot_bar(df, "時間帯", "時間帯別件数")
fig_week = plot_bar(df, "曜日", "曜日別件数")
fig_loc = plot_bar(df, "場所", "場所別件数")
fig_cat = plot_bar(df, "カテゴリ", "カテゴリ別件数")
fig_company = plot_bar(df, "会社名", "会社別件数")

pivot_week = df.pivot_table(index="曜日", columns="時間帯", aggfunc="size", fill_value=0)
pivot_loc = df.pivot_table(index="場所", columns="時間帯", aggfunc="size", fill_value=0)

fig_heat_week = plot_heatmap(pivot_week, "曜日 × 時間帯 ヒートマップ")
fig_heat_loc = plot_heatmap(pivot_loc, "場所 × 時間帯 ヒートマップ")

# ============================
# Word レポート生成
# ============================

def build_doc(df_export):
    doc = Document()

    doc.add_heading("HHK（ヒヤリハット）振り返りレポート", level=1)
    doc.add_paragraph(f"期間：{start_date} ～ {end_date}")
    doc.add_paragraph("")

    # KPI
    doc.add_heading("1. KPI（重要指標）", level=2)
    doc.add_paragraph(f"今月の件数：{this_month_count} 件")
    doc.add_paragraph(f"先月の件数：{last_month_count} 件")
    doc.add_paragraph(f"先月比：{mom}")
    doc.add_paragraph("")

    # 集計サマリ
    doc.add_heading("2. 集計サマリ", level=2)
    doc.add_paragraph(f"総件数：{len(df_export)} 件")

    # 場所別
    by_loc = df_export.groupby("場所")["ID"].count().reset_index().sort_values("ID", ascending=False)
    doc.add_paragraph("■ 場所別件数")
    for _, row in by_loc.iterrows():
        doc.add_paragraph(f"- {row['場所']}：{row['ID']} 件", style="List Bullet")
    doc.add_paragraph("")

    # カテゴリ別
    by_cat = df_export.groupby("カテゴリ")["ID"].count().reset_index().sort_values("ID", ascending=False)
    doc.add_paragraph("■ カテゴリ別件数")
    for _, row in by_cat.iterrows():
        doc.add_paragraph(f"- {row['カテゴリ']}：{row['ID']} 件", style="List Bullet")
    doc.add_paragraph("")

    # 会社別（追加）
    by_company = df_export.groupby("会社名")["ID"].count().reset_index().sort_values("ID", ascending=False)
    doc.add_paragraph("■ 会社別件数")
    for _, row in by_company.iterrows():
        doc.add_paragraph(f"- {row['会社名']}：{row['ID']} 件", style="List Bullet")
    doc.add_paragraph("")

    # グラフ
    doc.add_heading("3. グラフ", level=2)
    for title, fig in [
        ("時間帯別件数", fig_time),
        ("曜日別件数", fig_week),
        ("場所別件数", fig_loc),
        ("カテゴリ別件数", fig_cat),
        ("会社別件数", fig_company),
    ]:
        doc.add_paragraph(f"■ {title}")
        doc.add_picture(fig_to_png_bytes(fig), width=Inches(6))

    # ヒートマップ
    doc.add_heading("4. ヒートマップ", level=2)
    doc.add_paragraph("■ 曜日 × 時間帯")
    doc.add_picture(fig_to_png_bytes(fig_heat_week), width=Inches(6))

    doc.add_paragraph("■ 場所 × 時間帯")
    doc.add_picture(fig_to_png_bytes(fig_heat_loc), width=Inches(6))

    # 個別事例
    doc.add_heading("5. 個別事例一覧", level=2)
    for _, row in df_export.sort_values("発生日時").iterrows():
        doc.add_paragraph(f"[ID {row['ID']}] {row['発生日時']}")
        doc.add_paragraph(f"場所：{row['場所']} / カテゴリ：{row['カテゴリ']}")
        doc.add_paragraph(f"会社：{row['会社名']}")
        doc.add_paragraph(f"内容：{row['内容']}")
        doc.add_paragraph(f"投稿者：{row['投稿者']}")
        doc.add_paragraph("-" * 40)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ============================
# ダウンロード
# ============================

doc_bytes = build_doc(df)
st.download_button(
    label="📥 Wordレポートをダウンロード",
    data=doc_bytes,
    file_name=f"HHKレポート_{start_date}_{end_date}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
