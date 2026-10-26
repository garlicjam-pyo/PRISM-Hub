"""모든 Python 검증을 근거 번호 순서로 실행한다.

  python run_all.py            전체(2코어 기준 약 7시간, 그중 E12 약 3시간, E17 약 1.5시간)
  python run_all.py E3 E4      일부만

E2-c·E11 대조는 MATLAB/Octave에서 matlab/E2_two_stage_crosscheck.m, E11_controller_crosscheck.m 을 먼저
실행해야 하므로 MATLAB 결과 파일이 있을 때만 실행한다.
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
    ("E11", ["E11_controller_crosscheck.py"]),   # 사례 내보내기(MATLAB 실행 후 compare)
    ("E12", ["E12_switching_verification.py"]),
    ("E13", ["E13_baseline_structures.py"]),
    ("E14", ["E14_protection_startup.py"]),
    ("E15", ["E15_baseline_loss_rating.py"]),
    ("E16", ["E16_charging_integration.py"]),
    ("E18", ["E18_industry_value_map.py"]),      # E15 결과(stage_a_grid, comparison)를 읽는다
    ("E19", ["E19_r2_window_module.py"]),
    ("E17", ["E17_protection_integration.py"]),  # E12·E14·E19 모델을 쓰므로 마지막에(monitor·r2·figures)
    ("E20", ["E20_dab_fault_modulation.py"]),    # E17 상태기계를 쓴다(table·compare·figures, 약 10분)
    ("E21", ["E21_dab_switching_margin.py"]),    # 스위칭 표(모듈당 약 2분) + E17 상태기계(table·compare·figures)
    ("E22", ["E22_stage_c_regulated.py"]),       # 조정형 Stage C(design zvs gain spice both dcx control figures, 2코어 약 15분)
    ("E23", ["E23_r2_integrated.py"]),           # R2 통합(E21·E22 결과를 읽는다. base zbus degrade figures, 약 2분)
    ("E24", ["E24_stage_a_shedding.py"]),        # Stage A 경부하 위상 셰딩(design static transient deadfix figures, 2코어 약 10분)
    ("E25", ["E25_motor_boost_comparison.py"]),  # 모터 승압·800 V 부품 구조 비교(E15 결과 필요, 처음 약 2분)
    ("E26", ["E26_charging_stop.py"]),           # 충전 중 Stage A 정지·충전기 차단 협조(overload event figures, 2코어 약 2분)
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
        if eid == "E11" and (RESULTS / "E11" / "matlab_gain.json").exists():
            print("\n==== E11_controller_crosscheck.py compare ====", flush=True)
            subprocess.run([sys.executable, "E11_controller_crosscheck.py", "compare"], check=True)
    print(f"\n전체 {time.time() - t0:.0f} s")
