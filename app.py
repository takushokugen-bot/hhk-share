from modules.font import *
import streamlit as st

st.title("辰巳商会　HHK（ヒヤリハット）共有システム")
st.write("左のメニューから操作を選んでください。")

# ============================
# スマホ最適化（全ページ共通）
# ============================

st.markdown("""
<style>

/* スマホ向け最適化 */
@media (max-width: 600px) {

    /* ページ全体の余白を調整 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* ボタンを押しやすく */
    .stButton>button {
        padding: 1rem;
        font-size: 18px;
        width: 100%;
        border-radius: 8px;
    }

    /* 入力欄の文字を大きく */
    input, textarea, select {
        font-size: 18px !important;
    }

    /* セレクトボックスの高さ調整 */
    .stSelectbox>div>div {
        height: 48px;
    }

    /* 見出しをスマホ向けに */
    h1, h2, h3 {
        font-size: 1.4rem !important;
    }

    /* グラフの横スクロール防止 */
    .element-container {
        width: 100% !important;
    }
}

</style>
""", unsafe_allow_html=True)
