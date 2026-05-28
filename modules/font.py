import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns

# ============================
# 日本語フォント強制適用（完全版）
# ============================

font_path = "fonts/ipaexg.ttf"

# フォントを Matplotlib に強制登録
fm.fontManager.addfont(font_path)

jp_font = fm.FontProperties(fname=font_path)

plt.rcParams["font.family"] = jp_font.get_name()
plt.rcParams["axes.unicode_minus"] = False

sns.set(font=jp_font.get_name())
