"""Check independently integrated MATLAB/Python two-stage results."""
import json
from pathlib import Path

folder=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22-integration'
py=json.loads((folder/'two_stage_python.json').read_text(encoding='utf-8'))
mat=json.loads((folder/'two_stage_matlab.json').read_text(encoding='utf-8'))
errors={}
for a,b in zip(py['cases'],mat['cases'],strict=True):
    assert a['name']==b['name']
    for key in ['completed','within_port_limits','voltage_quality_pass','violations']:
        assert a[key]==b[key],(a['name'],key)
    differences={key:abs(a[key]-b[key]) for key in ['droop','vbus_end','vbus_max','vlink_min',
                 'vlink_max','path_peak','bridge_peak','link_peak','series_peak','dab_power_peak','modulation_peak','end_time']}
    assert max(differences.values())<1e-6,(a['name'],differences)
    errors[a['name']]=max(differences.values())
result=dict(status='PASS',max_absolute_metric_error=max(errors.values()),by_case=errors,
            note='Same gains, independent equilibrium and plant implementations; not physical validation')
(folder/'two_stage_cross_language.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
