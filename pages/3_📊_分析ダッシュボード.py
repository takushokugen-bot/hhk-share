from modules.font import *
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib.font_manager as fm

# ============================
# 日本語フォント設定
# ============================

jp_fonts = [
    "IPAexGothic",
    "Noto Sans CJK JP",
    "Noto Sans JP",
    "Yu Gothic",
    "MS Gothic",
]

font_found = False
for f in jp_fonts:
    try:
        fm.findfont(f, fallback_to_default=True)
        plt.rcParams["font.family"] = f
        font_found = True
        break
    except Exception:
        pass

if not font_found:
    plt.rcParams["font.family"] = "sans-serif"

plt.rcParams["axes.unicode_minus"] = False

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
df["曜日"] = df["発生日時"].dt.day_name()
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
# 月次KPI用（月情報）
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
# 基本グラフ（説明カード付き）
# ============================

st.subheader("📈 基本グラフ")

# --- 時間帯 ---
colA, colB = st.columns([2, 1])
with colA:
    fig_time = plot_bar(filtered, "時間帯", "時間帯別件数")
with colB:
    card("🕒 **時間帯別件数**：危険が集中する時間帯を可視化します。")

# --- 曜日 ---
colA, colB = st.columns([2, 1])
with colA:
    fig_week = plot_bar(filtered, "曜日", "曜日別件数")
with colB:
    card("📅 **曜日別件数**：曜日ごとの傾向を把握できます。")

# --- 場所 ---
colA, colB = st.columns([2, 1])
with colA:
    fig_loc = plot_bar(filtered, "場所", "場所別件数")
with colB:
    card("📍 **場所別件数**：危険が多い場所を特定できます。")

# --- カテゴリ ---
colA, colB = st.columns([2, 1])
with colA:
    fig_cat = plot_bar(filtered, "カテゴリ", "カテゴリ別件数")
with colB:
    card("🏷 **カテゴリ別件数**：危険の種類の傾向を把握できます。")

# ============================
# 会社別グラフ（説明カード付き）
# ============================

st.subheader("🏢 会社別件数")

colA, colB = st.columns([2, 1])
with colA:
    fig_company = plot_bar(filtered, "会社名", "会社別件数")
with colB:
    card("🏢 **会社別件数**：協力会社ごとの危険傾向を比較できます。")

# ============================
# ヒートマップ（曜日 × 時間帯 / 場所 × 時間帯）
# ============================

st.subheader("🔥 ヒートマップ（赤系）")

pivot_week = filtered.pivot_table(index="曜日", columns="時間帯", aggfunc="size", fill_value=0)
pivot_loc = filtered.pivot_table(index="場所", columns="時間帯", aggfunc="size", fill_value=0)

fig_heat_week = None
fig_heat_loc = None

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

# ============================
# 会社 × 場所 × 時間帯 ヒートマップ
# ============================

st.subheader("🔥 会社 × 場所 × 時間帯 ヒートマップ")

fig_company_heat = None

if company_filter == "すべて":
    st.info("会社名を選択すると、会社 × 場所 × 時間帯のヒートマップを表示します。")
else:
    df_company = filtered[filtered["会社名"] == company_filter]

    pivot_company = df_company.pivot_table(
        index="場所",
        columns="時間帯",
        aggfunc="size",
        fill_value=0
    )

    if pivot_company.empty:
        st.info("データがありません。")
    else:
        fig_company_heat, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(pivot_company, cmap="Reds", annot=True, fmt="d", ax=ax)
        ax.set_title(f"{company_filter}：場所 × 時間帯 ヒートマップ")
        st.pyplot(fig_company_heat)

# ============================
# Excel 出力
# ============================

def fig_to_png_bytes(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf

def to_excel_with_charts(df_export, p_week, p_loc,
                         f_time, f_week, f_loc, f_cat,
                         f_company,
                         fh_week, fh_loc,
                         fh_company,
                         monthly_counts):

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # 1. 元データ
        df_export.to_excel(writer, index=False, sheet_name="元データ")

        # 2. 期間全体ヒートマップ
        p_week.to_excel(writer, sheet_name="曜日×時間帯")
        p_loc.to_excel(writer, sheet_name="場所×時間帯")

        # 3. 期間全体グラフ
        sheet_chart = workbook.add_worksheet("全体グラフ")

        row = 1
        col = 1

        def insert_if(fig, title):
            nonlocal row
            if fig is None:
                return
            png = fig_to_png_bytes(fig)
            sheet_chart.insert_image(row, col, title + ".png", {"image_data": png})
            row += 20

        insert_if(f_time, "時間帯別件数")
        insert_if(f_week, "曜日別件数")
        insert_if(f_loc, "場所別件数")
        insert_if(f_cat, "カテゴリ別件数")
        insert_if(f_company, "会社別件数")
        insert_if(fh_week, "曜日×時間帯ヒートマップ")
        insert_if(fh_loc, "場所×時間帯ヒートマップ")
        insert_if(fh_company, "会社×場所×時間帯ヒートマップ")

        # 4. 月別シート（サマリ → グラフ → ヒートマップ）

        for month in monthly_counts["月"].unique():

            df_month = df_export[df_export["月"] == month]
            sheet = workbook.add_worksheet(f"{month}")

            row = 1
            col = 1

            # ---- サマリ ----
            sheet.write(row, col, f"【{month} サマリ】")
            row += 2

            sheet.write(row, col, f"件数：{len(df_month)} 件")
            row += 2

            # 場所別
            sheet.write(row, col, "■ 場所別件数")
            row += 1
            by_loc_m = df_month.groupby("場所")["ID"].count().reset_index().sort_values("ID", ascending=False)
            for _, r in by_loc_m.iterrows():
                sheet.write(row, col, f"- {r['場所']}：{r['ID']} 件")
                row += 1
            row += 1

            # カテゴリ別
            sheet.write(row, col, "■ カテゴリ別件数")
            row += 1
            by_cat_m = df_month.groupby("カテゴリ")["ID"].count().reset_index().sort_values("ID", ascending=False)
            for _, r in by_cat_m.iterrows():
                sheet.write(row, col, f"- {r['カテゴリ']}：{r['ID']} 件")
                row += 1
            row += 1

            # 会社別
            sheet.write(row, col, "■ 会社別件数")
            row += 1
            by_company_m = df_month.groupby("会社名")["ID"].count().reset_index().sort_values("ID", ascending=False)
            for _, r in by_company_m.iterrows():
                sheet.write(row, col, f"- {r['会社名']}：{r['ID']} 件")
                row += 1
            row += 2

            # ---- グラフ ----
            sheet.write(row, col, f"【{month} グラフ】")
            row += 2

            fig_time_m = None
            fig_week_m = None
            fig_loc_m = None
            fig_cat_m = None
            fig_company_m = None

            if not df_month.empty:
                fig_time_m = plt.figure(figsize=(8, 4))
                sns.countplot(data=df_month, x="時間帯")
                plt.title(f"{month} 時間帯別件数")
                plt.xticks(rotation=90)

                fig_week_m = plt.figure(figsize=(8, 4))
                sns.countplot(data=df_month, x="曜日")
                plt.title(f"{month} 曜日別件数")
                plt.xticks(rotation=90)

                fig_loc_m = plt.figure(figsize=(8, 4))
                sns.countplot(data=df_month, x="場所")
                plt.title(f"{month} 場所別件数")
                plt.xticks(rotation=90)

                fig_cat_m = plt.figure(figsize=(8, 4))
                sns.countplot(data=df_month, x="カテゴリ")
                plt.title(f"{month} カテゴリ別件数")
                plt.xticks(rotation=90)

                fig_company_m = plt.figure(figsize=(8, 4))
                sns.countplot(data=df_month, x="会社名")
                plt.title(f"{month} 会社別件数")
                plt.xticks(rotation=90)

            for title, fig in [
                (f"{month} 時間帯別件数", fig_time_m),
                (f"{month} 曜日別件数", fig_week_m),
                (f"{month} 場所別件数", fig_loc_m),
                (f"{month} カテゴリ別件数", fig_cat_m),
                (f"{month} 会社別件数", fig_company_m),
            ]:
                if fig:
                    png = fig_to_png_bytes(fig)
                    sheet.insert_image(row, col, title + ".png", {"image_data": png})
                    row += 20

            # ---- ヒートマップ ----
            sheet.write(row, col, f"【{month} ヒートマップ】")
            row += 2

            pivot_week_m = df_month.pivot_table(index="曜日", columns="時間帯", aggfunc="size", fill_value=0)
            pivot_loc_m = df_month.pivot_table(index="場所", columns="時間帯", aggfunc="size", fill_value=0)

            if not pivot_week_m.empty:
                fig_hw_m, ax = plt.subplots(figsize=(10, 4))
                sns.heatmap(pivot_week_m, cmap="Reds", annot=True, fmt="d", ax=ax)
                ax.set_title(f"{month} 曜日×時間帯")
                png = fig_to_png_bytes(fig_hw_m)
                sheet.insert_image(row, col, f"{month}_heat_week.png", {"image_data": png})
                row += 20

            if not pivot_loc_m.empty:
                fig_hl_m, ax = plt.subplots(figsize=(10, 4))
                sns.heatmap(pivot_loc_m, cmap="Reds", annot=True, fmt="d", ax=ax)
                ax.set_title(f"{month} 場所×時間帯")
                png = fig_to_png_bytes(fig_hl_m)
                sheet.insert_image(row, col, f"{month}_heat_loc.png", {"image_data": png})
                row += 20

    return output.getvalue()

excel_data = to_excel_with_charts(
    filtered,
    pivot_week,
    pivot_loc,
    fig_time,
    fig_week,
    fig_loc,
    fig_cat,
    fig_company,
    fig_heat_week,
    fig_heat_loc,
    fig_company_heat,
    monthly_counts,
)

st.download_button(
    label="📥 Excel ダウンロード（グラフ・ヒートマップ・月別シート付き）",
    data=excel_data,
    file_name="HHK分析_グラフ付き.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
