"""Diagnostic transport-delay sweep for the frozen Stage B controller.

The sweep brackets the tested delay boundary of the finite-link average model.
It is not a proof of continuous-time stability or a firmware timing budget.
"""
from dataclasses import asdict, replace
from pathlib import Path
import json

from pprc_fixed_control import NOMINAL, run


OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-22-fixed-control"
DELAYS_US = [5.0, 5.5, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0]
VOLTAGES = [640, 920]


def main():
    rows = []
    for delay_us in DELAYS_US:
        plant = replace(NOMINAL, delay=delay_us * 1e-6)
        for vbat in VOLTAGES:
            result = run(vbat, plant=plant, dt=1e-7)
            rows.append(
                dict(
                    delay_us=delay_us,
                    vbat_V=vbat,
                    requirements_pass=result["requirements_pass"],
                    droop_V=result["droop"],
                    path_peak_A=result["path_peak"],
                    bridge_peak_A=result["bridge_peak"],
                    recovery_us=None if result["recovery_s"] is None else result["recovery_s"] * 1e6,
                    failed_checks=[k for k, value in result["checks"].items() if not value],
                    violated_ports=[k for k, value in result["violations"].items() if value],
                )
            )

    all_pass = [
        delay for delay in DELAYS_US
        if all(row["requirements_pass"] for row in rows if row["delay_us"] == delay)
    ]
    any_fail = [
        delay for delay in DELAYS_US
        if any(not row["requirements_pass"] for row in rows if row["delay_us"] == delay)
    ]
    data = dict(
        status="PASS: diagnostic boundary reproduced",
        scope="Frozen gain; nominal finite-link average plant; 1 to 25 kW step; 640 and 920 V; dt=0.1 us",
        controller_parameters=asdict(NOMINAL),
        last_tested_delay_all_cases_pass_us=max(all_pass),
        first_tested_delay_any_case_fails_us=min(any_fail),
        boundary_note="Discrete tested bracket, not a certified maximum delay or hardware stability margin.",
        cases=rows,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "delay_sweep.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({k: data[k] for k in ["status", "last_tested_delay_all_cases_pass_us", "first_tested_delay_any_case_fails_us", "boundary_note"]}, indent=2))


if __name__ == "__main__":
    main()
