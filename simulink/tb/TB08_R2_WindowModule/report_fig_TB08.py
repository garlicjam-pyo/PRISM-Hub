"""TB08 보고서 그림: 바이패스 전환 순시 파형((a) DAB 고장 강등의 바이패스 투입, (b) 켬 전환의 바이패스 열림).

results/TB08_zoom_D_1008V_dabfault_25kW.csv(순시, 10 ns)와 results/TB08_E_930V_enable_25kW_periods.csv(5 µs 주기 평균)를
읽어 docs/fig/tb08_bypass_transitions.png를 만든다. 실행: python report_fig_TB08.py
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fp = [f for f in fm.findSystemFonts() if 'NotoSansCJK-Regular' in f or 'NotoSansCJK-Medium' in f]
if fp:
    fm.fontManager.addfont(fp[0]); plt.rcParams['font.family'] = fm.FontProperties(fname=fp[0]).get_name()
plt.rcParams['axes.unicode_minus'] = False
import os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results') + os.sep
D = np.loadtxt(R + 'TB08_zoom_D_1008V_dabfault_25kW.csv', delimiter=',')
E = np.loadtxt(R + 'TB08_E_930V_enable_25kW_periods.csv', delimiter=',')
c_byp, c_p, c_h, c_lim = '#1f4e9c', '#c8502a', '#7a7a7a', '#b00020'
fig, ax = plt.subplots(1, 2, figsize=(11, 4.0), gridspec_kw=dict(wspace=0.28))
t = D[:, 0]*1e6; k = (t >= -3) & (t <= 12)
a = ax[0]
a.plot(t[k], D[k, 1], color=c_byp, lw=1.8, label='바이패스 전류')
a.plot(t[k], D[k, 2], color=c_p, lw=1.4, label='경로전류')
a.plot(t[k], D[k, 3], color=c_h, lw=1.4, ls='--', label='필터전류(H-브리지)')
a.axvline(0, color='k', lw=0.8, ls=':')
a.annotate('투입 직후 −173 A\n(소자당 87 A, 펄스 정격의 0.26배)\n폭 약 1 µs, 17 µJ', xy=(0.05, -173), xytext=(2.0, -150),
           fontsize=9, arrowprops=dict(arrowstyle='->', lw=0.8))
a.set_xlabel('바이패스 투입 뒤 시간 [µs]'); a.set_ylabel('전류 [A]')
a.set_title('(a) DAB 고장 강등, 1008 V·25 kW: 바이패스 투입', fontsize=10.5)
a.set_ylim(-190, 75); a.grid(alpha=0.3); a.legend(loc='center right', fontsize=8.5, frameon=False, ncol=1)
tm = E[:, 0]*1e3; k = (tm >= 0.4) & (tm <= 1.4)
b = ax[1]
b.plot(tm[k], E[k, 2], color=c_p, lw=1.6, label='경로전류(5 µs 평균)')
b.plot(tm[k], E[k, 3], color=c_h, lw=1.4, ls='--', label='필터전류(5 µs 평균)')
b.axhline(90, color=c_lim, lw=1.0, ls='-.'); b.text(1.38, 86.5, '전환 한계 90 A', color=c_lim, fontsize=8.5, ha='right')
for x, s, dx, ha in [(0.5, '바이패스 열림', -0.012, 'right'), (0.7, '제어 시작', 0.012, 'left')]:
    b.axvline(x, color='k', lw=0.8, ls=':'); b.text(x + dx, 97, s, fontsize=8.5, va='top', ha=ha)
b.annotate('19.6 kHz 출렁임, 최대 73 A', xy=(0.69, 73.3), xytext=(0.85, 78), fontsize=9, arrowprops=dict(arrowstyle='->', lw=0.8))
b.set_xlabel('시간 [ms]'); b.set_ylabel('전류 [A]')
b.set_title('(b) 켬, 930 V·25 kW: 바이패스 열림 뒤 전류 이전', fontsize=10.5)
b.set_ylim(20, 100); b.grid(alpha=0.3); b.legend(loc='lower right', fontsize=8.5, frameon=False)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'docs', 'fig', 'tb08_bypass_transitions.png'), dpi=160, bbox_inches='tight')
