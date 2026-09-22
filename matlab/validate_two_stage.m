function result = validate_two_stage()
% Independent finite-link plant integration using exported, identical gains.
% Run python/validate_two_stage.py first. This is not a switching model.
root=fileparts(fileparts(mfilename('fullpath')));
folder=fullfile(root,'validation','2026-09-22-integration');
cases=jsondecode(fileread(fullfile(folder,'two_stage_cases.json')));
for j=1:numel(cases)
    r=prism_two_stage_case(cases(j));
    rows(j)=r; %#ok<AGROW>
    assert(r.energy_residual_max<1e-7,'Energy balance mismatch');
    fprintf('%s: droop %.6f V, path peak %.6f A, port limits %d, voltage quality %d\n',r.name,r.droop,r.path_peak,r.within_port_limits,r.voltage_quality_pass);
end
assert(all([rows(1:10).within_port_limits]) && all([rows(1:10).voltage_quality_pass]));
assert(~rows(11).within_port_limits && ~rows(11).voltage_quality_pass);
assert(~rows(12).within_port_limits && rows(12).voltage_quality_pass);
result.scope='Independent MATLAB midpoint integration; shared controller gains from Python';
result.matlab_version=version; result.cases=rows;
result.status='PASS: scoped regression including expected engineering failures';
f=fopen(fullfile(folder,'two_stage_matlab.json'),'w');
cleanup=onCleanup(@() fclose(f)); fwrite(f,jsonencode(result,PrettyPrint=true),'char');
end
