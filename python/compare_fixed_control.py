"""Independent MATLAB/Python metrics and fixed-controller classifications."""
import json
from pathlib import Path

folder=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22-fixed-control'
py=json.loads((folder/'python_results.json').read_text(encoding='utf-8'))
mat=json.loads((folder/'matlab_results.json').read_text(encoding='utf-8'))
errors={}
for a,b in zip(py['cases'],mat['cases'],strict=True):
    assert a['name']==b['name']
    for key in ['completed','within_port_limits','voltage_quality_pass','violations','checks','requirements_pass']:
        assert a[key]==b[key],(a['name'],key)
    if a['recovery_s'] is None: assert b['recovery_s'] is None
    else: assert abs(a['recovery_s']-b['recovery_s'])<1e-10
    differences={k:abs(a[k]-b[k]) for k in ['droop','vbus_end','vbus_max','vlink_min','vlink_max',
        'path_peak','bridge_peak','link_peak','series_peak','dab_power_peak','modulation_peak','end_time','tail_ripple_V']}
    # Failure trajectories can amplify floating-point error; use a documented
    # looser absolute tolerance for diagnostic cases, never a different verdict.
    tolerance=1e-6 if a['group']=='nominal' else 1e-3
    assert max(differences.values())<tolerance,(a['name'],differences)
    errors[a['name']]=max(differences.values())
result=dict(status='PASS',cases=len(errors),max_absolute_metric_error=max(errors.values()),
            max_nominal_error=max(errors[r['name']] for r in py['cases'] if r['group']=='nominal'),
            by_case=errors,note='Independent integration of the same average equations, not hardware validation')
(folder/'cross_language.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print({key:value for key,value in result.items() if key!='by_case'})
