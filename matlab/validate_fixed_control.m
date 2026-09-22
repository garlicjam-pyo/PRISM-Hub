function result = validate_fixed_control()
% Run Python validate_fixed_control.py first. Same fixed gains in every case.
root=fileparts(fileparts(mfilename('fullpath')));
% Verify the shared-kernel refactor against the archived twelve-case result.
legacy_folder=fullfile(root,'validation','2026-09-22-integration');
legacy_cases=jsondecode(fileread(fullfile(legacy_folder,'two_stage_cases.json')));
legacy_result=jsondecode(fileread(fullfile(legacy_folder,'two_stage_matlab.json')));
for j=1:numel(legacy_cases)
    r=prism_two_stage_case(legacy_cases(j)); a=legacy_result.cases(j);
    assert(abs(r.droop-a.droop)<1e-6 && abs(r.path_peak-a.path_peak)<1e-6);
    assert(r.within_port_limits==a.within_port_limits && r.voltage_quality_pass==a.voltage_quality_pass);
end
folder=fullfile(root,'validation','2026-09-22-fixed-control');
cases=jsondecode(fileread(fullfile(folder,'cases.json')));
for j=1:numel(cases)
    assert(isequal(cases(j).K,cases(1).K),'Gains changed between cases');
    assert(isequal(cases(j).control_parameters,cases(1).control_parameters),'Nominal controller parameters changed');
    r=prism_two_stage_case(cases(j));
    assert(r.requirements_pass==cases(j).expected_pass,'Python/MATLAB requirement disagreement');
    if strcmp(cases(j).group,'nominal'), assert(r.requirements_pass,'Nominal requirement failed'); end
    r.group=cases(j).group; rows(j)=r; %#ok<AGROW>
    fprintf('%s: pass %d, droop %.6f V, path %.6f A, recovery %.3f us\n',r.name,r.requirements_pass,r.droop,r.path_peak,r.recovery_s*1e6);
end
result.scope='Independent MATLAB plant integration with one common gain and nominal controller parameters';
result.legacy_cases_checked=numel(legacy_cases);
result.matlab_version=version; result.cases=rows;
result.status='PASS: nominal requirements and cross-language classifications';
f=fopen(fullfile(folder,'matlab_results.json'),'w');
cleanup=onCleanup(@() fclose(f)); fwrite(f,jsonencode(result,PrettyPrint=true),'char');
end
