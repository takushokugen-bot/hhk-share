import streamlit as st
import requests
import textwrap
import pandas as pd
import json

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-70b-instruct"


def summarize_reports(df: pd.DataFrame, max_samples: int = 50) -> str:
    if df.empty:
        return "データがないため、要約はありません。"

    df_sample = df.sort_values("発生日時", ascending=False).head(max_samples)

    lines = []
    for _, row in df_sample.iterrows():
        lines.append(
            f"- 日時: {row['発生日時']} / 場所: {row['場所']} / カテゴリ: {row['カテゴリ']} / 会社: {row['会社名']}\n  内容: {row['内容']}"
        )

    user_prompt = textwrap.dedent(f"""
    以下は物流現場で発生したヒヤリハットの記録です。
    管理者向けに「要点」「主な原因傾向」「注意すべきポイント」を
    箇条書きで簡潔にまとめてください。

    ### ヒヤリハット一覧
    {chr(10).join(lines)}
    """)

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "あなたは安全管理の専門家です。日本語で回答してください。"},
            {"role": "user", "content": user_prompt.strip()},
        ],
        "temperature": 0.2,
        "max_tokens": 512,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(GROQ_ENDPOINT, data=json.dumps(payload), headers=headers, timeout=60)

    if resp.status_code != 200:
        return f"❌ Groq API エラー: {resp.status_code}\n{resp.text}"

    return resp.json()["choices"][0]["message"]["content"].strip()
