import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid

from modules.font import *

# ============================
# Supabase 接続
# ============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("HHK（ヒヤリハット）投稿フォーム")

# ============================
# マスタ読み込み
# ============================

locations = supabase.table("locations").select("*").execute().data
categories = supabase.table("categories").select("*").execute().data
companies = supabase.table("companies").select("*").execute().data  # ← 会社マスタ

location_names = [loc["name"] for loc in locations]
category_names = [cat["name"] for cat in categories]
company_names = [c["name"] for c in companies] if companies else []

# ============================
# 入力フォーム
# ============================

reported_at = st.datetime_input("発生日時", datetime.now())
location_name = st.selectbox("場所", location_names)
category_name = st.selectbox("カテゴリ", category_names)

company_name = st.selectbox(
    "会社名（任意）",
    ["（未選択）"] + company_names
) if company_names else st.selectbox(
    "会社名（任意）",
    ["（未選択）"]
)

description = st.text_area("内容")
reporter = st.text_input("投稿者名（任意）")

uploaded_file = st.file_uploader("写真（任意）", type=["jpg", "jpeg", "png"])

# ============================
# 選択された場所・カテゴリのIDを取得
# ============================

location_id = next(loc["id"] for loc in locations if loc["name"] == location_name)
category_id = next(cat["id"] for cat in categories if cat["name"] == category_name)

# ============================
# 投稿ボタン
# ============================

if st.button("投稿する"):

    photo_url = None

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_ext = uploaded_file.name.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"

        supabase.storage.from_("hhk_photos").upload(
            file_name,
            file_bytes,
            {"content-type": f"image/{file_ext}"}
        )

        photo_url = supabase.storage.from_("hhk_photos").get_public_url(file_name)

    data = {
        "reported_at": reported_at.isoformat(),
        "location_id": location_id,
        "category_id": category_id,
        "description": description,
        "reporter": reporter,
        "company": None if company_name == "（未選択）" else company_name,
        "photo_url": photo_url
    }

    supabase.table("hhk_reports").insert(data).execute()
    st.success("投稿が完了しました！")
