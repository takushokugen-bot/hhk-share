import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns

font_path = "fonts/ipaexg.ttf"
jp_font = fm.FontProperties(fname=font_path)

plt.rcParams["font.family"] = jp_font.get_name()
plt.rcParams["axes.unicode_minus"] = False

sns.set(font=jp_font.get_name())
