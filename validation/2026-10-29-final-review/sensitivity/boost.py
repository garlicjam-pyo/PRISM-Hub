import sys
sys.path.insert(0, '/home/claude/PRISM-Hub/submission/verification_code/python')
import E15_baseline_loss_rating as E15
for f in (50e3, 25e3, 16e3):
    print("boost 800V 375A f=%.0f kHz: %.0f W" % (f/1e3, E15.hs_converter("boost", 400., 800., 400.*375, "SiC1200", f, 6, 150000., 400.)))
# aux buck components at 800 V, 0.5 kW
for P in (500., 2500.):
    print("aux buck P=%.0f: %.1f W" % (P, E15.hs_converter("buck", 800., 400., P, "SiC1200", 50e3, 2, 25000., 400.)))
