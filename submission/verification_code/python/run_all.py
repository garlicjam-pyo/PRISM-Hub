"""모든 Python 검증을 근거 번호 순서로 실행한다.

  python run_all.py            전체(2코어 기준 약 1–1.5시간)
  python run_all.py E3 E4      일부만

E2-c(Python·MATLAB 대조)는 MATLAB/Octave에서 matlab/E2_two_stage_crosscheck.m 을 먼저 실행해야 하므로
MATLAB 결과 파일이 있을 때만 실행한다.
"""
import subprocess
import sys
import time

from common import RESULTS

STEPS = [
    ("E1", ["E1_stage_a_zcs.py"]),
    ("E2", ["E2a_model_consistency.py", "E2b_reference_matrix.py"]),
    ("E3", ["E3_steady_state.py"]),
    ("E4", ["E4_requirements.py"]),
    ("E5", ["E5_E7_controller.py"]),          # E5·E6·E7을 함께 계산한다
    ("E8", ["E8_load_admission.py"]),
    ("E9", ["E9_design_alternatives.py"]),
    ("E10", ["E10_stage_c_cllc.py"]),
]

if __name__ == "__main__":
    want = set(sys.argv[1:])
    t0 = time.time()
    for eid, scripts in STEPS:
        if want and eid not in want and not (eid == "E5" and want & {"E6", "E7"}):
            continue
        for s in scripts:
            print(f"\n==== {s} ====", flush=True)
            subprocess.run([sys.executable, s], check=True)
        if eid == "E2" and (RESULTS / "E2" / "reference_matrix_matlab.json").exists():
            print("\n==== E2c_compare_matlab.py ====", flush=True)
            subprocess.run([sys.executable, "E2c_compare_matlab.py"], check=True)
    print(f"\n전체 {time.time() - t0:.0f} s")
