"""Compare completed independent MATLAB/Python regressions; run both suites first."""
from pathlib import Path
import json

folder=Path(__file__).resolve().parents[1]/'validation'/'2026-09-22'
mat=json.loads((folder/'matlab_results.json').read_text(encoding='utf-8'))
py=json.loads((folder/'python_results.json').read_text(encoding='utf-8'))
sim=json.loads((folder/'simulink_results.json').read_text(encoding='utf-8'))
differences=[]
for m,p in zip(mat['step'],py['step'],strict=True):
    assert m['Vbat']==p['Vbat']
    assert m['within_port_limits']==p['within_port_limits']
    assert m['voltage_quality_pass']==p['voltage_quality_pass']
    for key in ['droop','vbus_end','current_peak']:
        error=abs(m[key]-p[key]); assert error<1e-6,(key,error)
        differences.append(error)
assert abs(mat['rated_low_battery']['droop']-py['rated_low_battery']['droop'])<1e-6
assert all(row['zcs_max']<.05 for row in mat['stage_a']+py['stage_a'])
assert sim['max_voltage_difference_vs_euler']<1
result={'status':'PASS','max_MATLAB_Python_step_metric_difference':max(differences),
        'Simulink_Euler_max_waveform_difference_V':sim['max_voltage_difference_vs_euler'],
        'note':'Stage A tolerance samples differ between MATLAB and NumPy RNGs.'}
(folder/'cross_language_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
