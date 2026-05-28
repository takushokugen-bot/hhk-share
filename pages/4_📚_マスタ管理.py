from modules.font import *
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ============================
# Supabase 接続
# ============================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 マスタ管理（場所・カテゴリ・会社）")

# ============================
# 共通関数
# ============================

def load_master(table):
    """Supabase からマスタ一覧を取得"""
    res = supabase.table(table).select("id, name").order("id").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "name"])

def add_master(table, name):
    """マスタ追加"""
    supabase.table(table).insert({"name": name}).execute()

def delete_master(table, id_):
    """マスタ削除"""
    supabase.table(table).delete().eq("id", id_).execute()

def update_master(table, id_, new_name):
    """マスタ更新"""
    supabase.table(table).update({"name": new_name}).eq("id", id_).execute()

# ============================
# UI：タブ切り替え
# ============================

tab1, tab2, tab3 = st.tabs(["📍 場所マスタ", "🏷 カテゴリマスタ", "🏢 会社マスタ"])

# ============================
# 📍 場所マスタ
# ============================

with tab1:
    st.subheader("📍 場所マスタ一覧")

    df_loc = load_master("locations")
    st.dataframe(df_loc, use_container_width=True)

    st.markdown("---")

    # 追加
    st.subheader("➕ 場所を追加")
    new_loc = st.text_input("場所名を入力")
    if st.button("追加する", key="add_loc"):
        if new_loc.strip():
            add_master("locations", new_loc.strip())
            st.success("追加しました")
            st.rerun()
        else:
            st.warning("場所名を入力してください")

    st.markdown("---")

    # 編集
    st.subheader("✏ 場所名を編集")
    if not df_loc.empty:
        edit_id = st.selectbox("編集するIDを選択", df_loc["id"].tolist())
        new_name = st.text_input("新しい場所名")
        if st.button("更新する", key="edit_loc"):
            if new_name.strip():
                update_master("locations", edit_id, new_name.strip())
                st.success("更新しました")
                st.rerun()
            else:
                st.warning("新しい名前を入力してください")

    st.markdown("---")

    # 削除
    st.subheader("🗑 場所を削除")
    if not df_loc.empty:
        del_id = st.selectbox("削除するIDを選択", df_loc["id"].tolist(), key="del_loc")
        if st.button("削除する", key="delete_loc"):
            delete_master("locations", del_id)
            st.success("削除しました")
            st.rerun()

# ============================
# 🏷 カテゴリマスタ
# ============================

with tab2:
    st.subheader("🏷 カテゴリマスタ一覧")

    df_cat = load_master("categories")
    st.dataframe(df_cat, use_container_width=True)

    st.markdown("---")

    # 追加
    st.subheader("➕ カテゴリを追加")
    new_cat = st.text_input("カテゴリ名を入力")
    if st.button("追加する", key="add_cat"):
        if new_cat.strip():
            add_master("categories", new_cat.strip())
            st.success("追加しました")
            st.rerun()
        else:
            st.warning("カテゴリ名を入力してください")

    st.markdown("---")

    # 編集
    st.subheader("✏ カテゴリ名を編集")
    if not df_cat.empty:
        edit_cat_id = st.selectbox("編集するIDを選択", df_cat["id"].tolist())
        new_cat_name = st.text_input("新しいカテゴリ名")
        if st.button("更新する", key="edit_cat"):
            if new_cat_name.strip():
                update_master("categories", edit_cat_id, new_cat_name.strip())
                st.success("更新しました")
                st.rerun()
            else:
                st.warning("新しい名前を入力してください")

    st.markdown("---")

    # 削除
    st.subheader("🗑 カテゴリを削除")
    if not df_cat.empty:
        del_cat_id = st.selectbox("削除するIDを選択", df_cat["id"].tolist(), key="del_cat")
        if st.button("削除する", key="delete_cat"):
            delete_master("categories", del_cat_id)
            st.success("削除しました")
            st.rerun()

# ============================
# 🏢 会社マスタ（NEW）
# ============================

with tab3:
    st.subheader("🏢 会社マスタ一覧")

    df_company = load_master("companies")
    st.dataframe(df_company, use_container_width=True)

    st.markdown("---")

    # 追加
    st.subheader("➕ 会社を追加")
    new_company = st.text_input("会社名を入力")
    if st.button("追加する", key="add_company"):
        if new_company.strip():
            add_master("companies", new_company.strip())
            st.success("追加しました")
            st.rerun()
        else:
            st.warning("会社名を入力してください")

    st.markdown("---")

    # 編集
    st.subheader("✏ 会社名を編集")
    if not df_company.empty:
        edit_company_id = st.selectbox("編集するIDを選択", df_company["id"].tolist())
        new_company_name = st.text_input("新しい会社名")
        if st.button("更新する", key="edit_company"):
            if new_company_name.strip():
                update_master("companies", edit_company_id, new_company_name.strip())
                st.success("更新しました")
                st.rerun()
            else:
                st.warning("新しい名前を入力してください")

    st.markdown("---")

    # 削除
    st.subheader("🗑 会社を削除")
    if not df_company.empty:
        del_company_id = st.selectbox("削除するIDを選択", df_company["id"].tolist(), key="del_company")
        if st.button("削除する", key="delete_company"):
            delete_master("companies", del_company_id)
            st.success("削除しました")
            st.rerun()
