import streamlit as st
from supabase import create_client, Client
from datetime import datetime
from modules.font import *

# ============================
# Supabase 接続
# ============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📝 HHK（ヒヤリハット）投稿フォーム")

# ============================
# マスタ取得
# ============================

locations = supabase.table("locations").select("id, name").execute().data
categories = supabase.table("categories").select("id, name").execute().data
companies = supabase.table("companies").select("id, name").execute().data

location_names = ["（未選択）"] + [l["name"] for l in locations]
category_names = ["（未選択）"] + [c["name"] for c in categories]
company_names = ["（未選択）"] + [c["name"] for c in companies]

# ============================
# 入力フォーム
# ============================

reported_at = st.datetime_input("発生日時", datetime.now())
location = st.selectbox("場所（必須）", location_names)
category = st.selectbox("カテゴリ（必須）", category_names)
company = st.selectbox("会社名（必須）", company_names)
description = st.text_area("内容（必須）")
reporter = st.text_input("投稿者名（任意）")
photo = st.file_uploader("写真（任意）", type=["jpg", "png"])

# ============================
# 投稿処理
# ============================

if st.button("📤 投稿する"):

    errors = []

    if location == "（未選択）":
        errors.append("場所は必須です。")

    if category == "（未選択）":
        errors.append("カテゴリは必須です。")

    if company == "（未選択）":
        errors.append("会社名は必須です。")

    if not description.strip():
        errors.append("内容は必須です。")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    # ID 取得
    location_id = next((l["id"] for l in locations if l["name"] == location), None)
    category_id = next((c["id"] for c in categories if c["name"] == category), None)

    # ============================
    # 写真アップロード（完全版）
    # ============================

    photo_url = None
    if photo:
        file_bytes = photo.getvalue()
        file_path = f"{datetime.now().timestamp()}_{photo.name}"

        supabase.storage.from_("hhk_photos").upload(
            file_path,
            file_bytes,
            {"content-type": photo.type}
        )

        photo_url = supabase.storage.from_("hhk_photos").get_public_url(file_path)

    # ============================
    # DB へ登録
    # ============================

    supabase.table("hhk_reports").insert({
        "reported_at": reported_at.isoformat(),
        "location_id": location_id,
        "category_id": category_id,
        "company": company,
        "description": description,
        "reporter": reporter,
        "photo_url": photo_url,
    }).execute()

    st.success("投稿が完了しました！")
    st.balloons()
