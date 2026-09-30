"""보고서 그림용 한글 글꼴 설정. 설치된 한글 글꼴을 순서대로 찾아 쓴다(없으면 기본 글꼴)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

COLOR = {"blue": "#1f4e79", "orange": "#c55a11", "green": "#548235", "red": "#c00000", "gray": "#7f7f7f"}


def korean():
    for path in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                 "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
        try:
            fm.fontManager.addfont(path)
        except Exception:
            pass
    names = {f.name for f in fm.fontManager.ttflist}
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP"]:
        if name in names:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams.update({"axes.unicode_minus": False, "font.size": 9, "axes.titlesize": 9.5,
                         "legend.fontsize": 8, "savefig.dpi": 220, "axes.grid": True, "grid.alpha": .3})
    return plt
