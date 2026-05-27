import os

folders = [
    "pages",
    "modules",
    "assets",
    ".streamlit"
]

files = {
    "app.py": "",
    "modules/supabase_client.py": "",
    ".streamlit/secrets.toml": ""
}

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file_path, content in files.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("フォルダ構成を自動生成しました！")
