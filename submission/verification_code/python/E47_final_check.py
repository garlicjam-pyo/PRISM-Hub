"""[E47] 최종 제출 판정(2026-11-07, 검토 커밋 d747199) 대응: 검증기 우회 경로 보완의 오류 주입 확인, 출판 기준 사본과의 S2 재판정,
충전 중 과도시험의 분모·부하 스텝 재집계, TB28 결합 회로 기록, 줄바꿈 정규화 해시, 가치 지도 그림 (a) 축 이름.

■ 왜 필요한가(사용자 지시 2026-11-07 00:04: 최종 판정서를 바탕으로 다시 검토)
  판정서는 원고의 시험 범위 표기(15·25 kW, 충전 과도 분모·부하 스텝, 고장 강등 문단)와 검증기의 남은 우회 경로
  (양쪽 같은 행 복제, 주파수 NaN, 양쪽 같은 변경, 공통 키만 보는 비교, 차이가 있어도 종료 0)를 지적했다.
  E1–E46의 등록 판정과 원시 결과는 바꾸지 않는다.

■ 코드 보완(이 커밋, 실행 전)
  E45 fcheck_judge: 사례·표본 이름이 양쪽 모두 고유해야 하고 주파수는 유한 수여야 한다. fcheck_s2: 기준은 날짜별 보관 사본
  (validation/2026-11-06-review3/E44/cfly.json)이며 줄바꿈 정규화 SHA-256이 등록값과 같아야 한다. dstrict 두 판정은 필수(gate).
  E44 _diff_tree: 키가 한쪽에만 있거나 배열 길이가 다르면 차이로 센다. D-R0은 필수(gate), E44 실행 끝에 종료 코드.
  common: sha256_file_lf(CRLF → LF 정규화 해시), input_record에 sha256_lf, PRISM_RESULTS_DIR(결과 폴더 바꾸기, 오류 주입용).
  E18 그림 (a): 세로축 '비조정 부하 버스 전압 [V]'(경로 강하 포함 값을 그리므로).

■ 판정 기준(실행 전에 고정, 이 커밋. 결과를 본 뒤 바꾸지 않는다)
 (inj) 오류 주입(복사본에만 적용). 비교 함수 fcheck_judge(해시 검사 없이)로: 양쪽 같은 행 삭제(행 수로 실패), 양쪽 같은 행
      복제(한 행을 다른 행의 사본으로 바꿔 개수 유지 → 이름 중복으로 실패), F-b 제어 주파수 NaN, 제어 주파수 20 kHz, 새 결과 한쪽
      첨두 +10 A → 모두 실패. 전체 S2(fcheck_s2, 기준 사본 해시 포함)로: 정상 → 통과, 기준 사본과 새 결과 양쪽 같은 첨두 +10 A →
      해시 불일치로 실패. E44 _diff_tree: 키 삭제·배열 길이 변경을 차이로 잡고 같은 값은 차이 0.
      판정 INJ(gate): 모든 경우가 기대대로이고, 복제 경우의 실패 사유에 ‘중복’, 양쪽 첨두 경우에 ‘해시’가 있어야 한다.
 (dsx) E45 dstrict를 결과 폴더 복사본에서 자식 프로세스로 실행: 그대로면 종료 0, 한 쌍(E43 loss)의 키 하나를 지우면 종료 1.
      판정 DSX(gate): 둘 다 기대대로.
 (s2) 저장된 E45 cfly_refactor(validation/2026-11-06-review4)를 해시 확인한 기준 사본과 fcheck_s2로 다시 판정. 판정 S2v2(gate): 통과.
 (cnt) 저장 자료 재집계(판정 없음): E36 e16_concurrent의 Tier-1·Tier-2 건수를 632 V 진단·사양 640–920 V·추가 지연 정보 시험으로
      나누고 부하 스텝(P0 → P1) 목록을 적는다. TB28 네 사례의 부하·충전 명령과 저장 요약(V_A·버스 1 µs 최고, 48 V 최저·최고)을 적는다.
 (hash) TB28 입력 CSV 세 개의 원시 바이트 해시와 줄바꿈 정규화 해시를 적고, LF·CRLF 두 형태에서 정규화 해시가 같은지 확인
      (판정 HS(gate): 같음). E46 power.json에 기록된 원시 해시가 어느 형태와 같은지 적는다.
 (fig) 그림 7-1을 E46 fig와 같은 계산으로 다시 그린다(축 이름만 바뀜, 판정 없음). 값(fig.json)이 E46과 같은지 적는다.

■ 실행   python E47_final_check.py inj dsx s2 cnt hash fig
■ 결과   results/E47/*.json. 필수 판정(gate)이 실패하면 종료 코드 1.
"""
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import common
from common import save_json, load_json, verdict, sha256_file, sha256_file_lf

EID = "E47"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VAL = ROOT / "validation"


def _vj(*parts):
    return json.loads(VAL.joinpath(*parts).read_text(encoding="utf-8"))


# ======================================================================================================
# (inj)
# ======================================================================================================
def inj():
    import E45_review4_response as E45
    import E44_review3_response as E44
    base_path = VAL.joinpath(*E45.FCHECK_BASE)
    base = json.loads(base_path.read_text(encoding="utf-8"))
    new0 = _vj("2026-11-06-review4", "E45", "cfly_refactor.json")
    tag, part = "F-a_45.00uF", "transient"
    peak_key = next(k for k in new0[tag][part][0] if "peak" in k and isinstance(new0[tag][part][0][k], (int, float)))
    tmp = Path(tempfile.mkdtemp(prefix="e47_"))
    cases = []

    def run(name, new, bpath=base_path, expect=False, judge_only=None, must=None):
        if judge_only is not None:
            ok, det = E45.fcheck_judge(judge_only, new); via = "fcheck_judge"
        else:
            ok, det = E45.fcheck_s2(new, bpath); via = "fcheck_s2"
        reason_ok = must is None or any(must in str(x) for x in det["problems"])
        cases.append(dict(case=name, via=via, S2=ok, expected=expect, reason_required=must, reason_ok=reason_ok,
                          problems=det["problems"][:4], diffs={k: v["n"] for k, v in det["diffs"].items() if v["n"]}))

    try:
        run("정상", copy.deepcopy(new0), expect=True)
        # 양쪽 같은 행 삭제(비교 함수)
        b1 = copy.deepcopy(base); n1 = copy.deepcopy(new0)
        del b1[tag][part][3]; del n1[tag][part][3]
        run("양쪽 같은 행 삭제", n1, judge_only=b1, must="행 수")
        # 양쪽 같은 행 복제(개수 유지, 비교 함수)
        b2 = copy.deepcopy(base); n2 = copy.deepcopy(new0)
        b2[tag][part][3] = copy.deepcopy(b2[tag][part][2]); n2[tag][part][3] = copy.deepcopy(n2[tag][part][2])
        run("양쪽 같은 행 복제", n2, judge_only=b2, must="중복")
        # 주파수 NaN, 20 kHz, 한쪽 첨두 +10 A(비교 함수)
        n3 = copy.deepcopy(new0); n3["F-b_42.75uF"]["f_control_Hz"] = float("nan"); run("제어 주파수 NaN", n3, judge_only=base, must="f_control_Hz")
        n4 = copy.deepcopy(new0); n4["F-b_42.75uF"]["f_control_Hz"] = 20000.0; run("제어 주파수 20 kHz", n4, judge_only=base, must="f_control_Hz")
        n5 = copy.deepcopy(new0); n5[tag][part][0][peak_key] += 10.0; run("새 결과 첨두 +10 A", n5, judge_only=base)
        # 양쪽 같은 첨두 +10 A
        b6 = copy.deepcopy(base); n6 = copy.deepcopy(new0)
        b6[tag][part][0][peak_key] += 10.0; n6[tag][part][0][peak_key] += 10.0
        p6 = tmp / "b_peak.json"; p6.write_text(json.dumps(b6, ensure_ascii=False, indent=1), encoding="utf-8")
        run("양쪽 같은 첨두 +10 A", n6, p6, must="해시")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # E44 _diff_tree 키 삭제·길이
    a = dict(x=1.0, y=[1, 2], z=dict(w=0.5))
    dt = dict(key_del=len(E44._diff_tree(a, dict(y=[1, 2], z=dict(w=0.5)))) > 0,
              len_change=len(E44._diff_tree(a, dict(x=1.0, y=[1, 2, 3], z=dict(w=0.5)))) > 0,
              same=len(E44._diff_tree(a, json.loads(json.dumps(a)))) == 0)
    ok = all(c["S2"] == c["expected"] and c["reason_ok"] for c in cases) and all(dt.values())
    save_json(EID, "inj", dict(cases=cases, diff_tree=dt, peak_key=peak_key))
    for c in cases:
        print("  %-16s [%s] S2=%s(기대 %s, 사유 %s) %s" % (c["case"], c["via"], c["S2"], c["expected"], c["reason_ok"], c["problems"] or c["diffs"]))
    print("  E44 _diff_tree:", dt)
    verdict("(inj INJ) 오류 주입 일곱 경우와 _diff_tree 세 경우가 기대대로", ok, gate=True)


# ======================================================================================================
# (dsx)
# ======================================================================================================
DSX_PAIRS = [("E38", "l1_e15_comparison"), ("E38", "l1_e25_comparison"), ("E38", "l1_e18_A25R_value_map"), ("E41", "fair"),
             ("E42", "cases"), ("E42", "cells"), ("E43", "loss"), ("E44", "r0_l1_e15_comparison"), ("E44", "r0_l1_e25_comparison"),
             ("E44", "r0_l1_e18_A25R_value_map"), ("E44", "r0_e41_fair"), ("E44", "r0_e42_cases"), ("E44", "r0_e42_cells"),
             ("E44", "r0_e43_loss")]


def dsx():
    out = {}
    for label, mutate in (("그대로", False), ("E43 loss 키 하나 삭제", True)):
        tmp = Path(tempfile.mkdtemp(prefix="e47dsx_"))
        try:
            for eid, name in DSX_PAIRS:
                (tmp / eid).mkdir(exist_ok=True)
                shutil.copy(common.RESULTS / eid / (name + ".json"), tmp / eid / (name + ".json"))
            removed = None
            if mutate:
                f = tmp / "E43" / "loss.json"; d = json.loads(f.read_text(encoding="utf-8"))
                removed = next(iter(d)); del d[removed]
                f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            env = dict(os.environ, PRISM_RESULTS_DIR=str(tmp))
            r = subprocess.run([sys.executable, str(HERE / "E45_review4_response.py"), "dstrict"], env=env, capture_output=True, text=True)
            out[label] = dict(exit=r.returncode, removed_key=removed, tail=r.stdout.strip().splitlines()[-3:])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    ok = out["그대로"]["exit"] == 0 and out["E43 loss 키 하나 삭제"]["exit"] == 1
    save_json(EID, "dsx", out)
    for k, v in out.items():
        print("  %s: 종료 %d %s" % (k, v["exit"], v["tail"]))
    verdict("(dsx DSX) dstrict: 그대로 종료 0, 키 삭제 종료 1", ok, gate=True)


# ======================================================================================================
# (s2)
# ======================================================================================================
def s2():
    import E45_review4_response as E45
    new = _vj("2026-11-06-review4", "E45", "cfly_refactor.json")
    ok, det = E45.fcheck_s2(new)
    save_json(EID, "s2", dict(S2=ok, rows=det["rows"], problems=det["problems"], diffs={k: v["n"] for k, v in det["diffs"].items()},
                              base=det["base"]))
    verdict("(s2 S2v2) 보관 E45 cfly_refactor 56행이 해시 확인한 기준 사본과 같음", ok,
            json.dumps(dict(rows=det["rows"], problems=det["problems"]), ensure_ascii=False), gate=True)


# ======================================================================================================
# (cnt)
# ======================================================================================================
def cnt():
    co = _vj("2026-10-28-a25r-impact", "E36", "e16_concurrent.json")["rows"]
    res = {}
    for tier in (1, 2):
        rows = [r for r in co if r["tier"] == tier]
        info = [r for r in rows if tier == 2 and r["name"] == "delay+3.0us"]
        formal = [r for r in rows if r not in info]
        spec = [r for r in formal if r["V"] >= 640]
        steps = sorted({(r["info"]["P0"], r["info"]["P1"]) for r in rows})
        res["Tier-%d" % tier] = dict(all=len(rows), formal_incl_632=[sum(r["pass_"] for r in formal), len(formal)],
                                     spec_640_920=[sum(r["pass_"] for r in spec), len(spec)],
                                     delay_info=[sum(r["pass_"] for r in info), len(info)], steps_W=steps,
                                     voltages=sorted({r["V"] for r in rows}))
    tb = {}
    d28 = ROOT / "simulink" / "tb" / "TB28_A25R_Charging_Stop" / "results"
    for cn in ("A28_920V_pathloss", "B28_640V_pathloss_ramp", "C28_800V_module_fault", "D28_800V_charge_slow"):
        s = json.loads((d28 / ("TB28_%s_summary.json" % cn)).read_text(encoding="utf-8"))
        tb[cn] = dict(verdict=s["verdict"], vA_max_1us=s["vA_max_1us"], vbus_max_1us=s["vbus_max_1us"], vo_min=s["vo_min"], vo_max=s["vo_max"])
    tb["load_note"] = "A·B·C: 400 V 부하 20 kW + Stage C 5 kW(보조 25 kW), D: 400 V 10 kW + Stage C 5 kW(보조 15 kW), README 표"
    save_json(EID, "cnt", dict(e36_concurrent=res, tb28=tb))
    for k, v in res.items():
        print("  E36 %s: 정식(632 V 포함) %s, 사양 640–920 V %s, 지연 정보 %s, 스텝 %s" % (k, v["formal_incl_632"], v["spec_640_920"], v["delay_info"], v["steps_W"]))
    for k, v in tb.items():
        if isinstance(v, dict):
            print("  TB28 %s: %s V_A ≤ %.2f V, 버스 ≤ %.2f V, 48 V %.3f–%.3f V" % (k, v["verdict"], v["vA_max_1us"], v["vbus_max_1us"], v["vo_min"], v["vo_max"]))


# ======================================================================================================
# (hash)
# ======================================================================================================
def hash_():
    d28 = ROOT / "simulink" / "tb" / "TB28_A25R_Charging_Stop" / "results"
    pw = json.dumps(_vj("2026-11-06-review5", "E46", "power.json"), ensure_ascii=False)
    out = {}; ok = True
    import hashlib
    for cn in ("A28_920V_pathloss", "B28_640V_pathloss_ramp", "C28_800V_module_fault"):
        p = d28 / ("TB28_%s_avg1us.csv" % cn)
        b = p.read_bytes()
        lf = b.replace(b"\r\n", b"\n"); crlf = lf.replace(b"\n", b"\r\n")
        h_lf, h_crlf = hashlib.sha256(lf).hexdigest(), hashlib.sha256(crlf).hexdigest()
        n_lf, n_crlf = hashlib.sha256(lf.replace(b"\r\n", b"\n")).hexdigest(), hashlib.sha256(crlf.replace(b"\r\n", b"\n")).hexdigest()
        same = n_lf == n_crlf == sha256_file_lf(p)
        ok &= same
        out[cn] = dict(raw_worktree=sha256_file(p), worktree_crlf=b.count(b"\r\n"), sha256_lf_bytes=h_lf, sha256_crlf_bytes=h_crlf,
                       sha256_lf_normalized=sha256_file_lf(p), normalized_same=same,
                       e46_recorded_matches=("LF" if h_lf in pw else "CRLF" if h_crlf in pw else "없음"))
    save_json(EID, "hash", out)
    for k, v in out.items():
        print("  %s: 정규화 %s…, 정규화 같음 %s, E46 기록 해시 = %s 바이트" % (k, v["sha256_lf_normalized"][:12], v["normalized_same"], v["e46_recorded_matches"]))
    verdict("(hash HS) LF·CRLF 두 형태의 줄바꿈 정규화 해시가 같음", ok, gate=True)


# ======================================================================================================
# (fig)
# ======================================================================================================
def fig():
    import E46_review5_response as E46
    E46.EID = EID
    E46.save_json = lambda eid, name, obj: common.save_json(EID, name, obj)
    E46.fig()
    a, b = load_json(EID, "fig"), _vj("2026-11-06-review5", "E46", "fig.json")
    same = len(common.strict_diff(a["diff"], b["diff"])) == 0
    save_json(EID, "fig_compare", dict(values_same_as_E46=same))
    print("  그림 값이 E46과 같음:", same)


PARTS = dict(inj=inj, dsx=dsx, s2=s2, cnt=cnt, hash=hash_, fig=fig)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        if w not in PARTS:
            raise SystemExit("알 수 없는 부분: %s (가능: %s)" % (w, ", ".join(PARTS)))
    for w in want:
        print("\n==== E47 %s ====" % w, flush=True)
        PARTS[w]()
    sys.exit(common.exit_status())
