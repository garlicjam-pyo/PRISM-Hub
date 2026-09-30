function result = E2_two_stage_crosscheck()
% E2_TWO_STAGE_CROSSCHECK  [E2] Stage B 평균모델의 MATLAB 독립 구현으로 Python 사례를 재계산한다.
%
%  목적   Python 구현의 코드 오류가 판정을 바꾸지 않았음을 보이기 위해, 같은 사례를 독립 구현
%         (prism_two_stage_case.m)으로 다시 적분하고 결과를 저장한다(보고서 5.3절).
%  입력   ../results/E2/two_stage_cases.json   (python/E2a_model_consistency.py가 생성, 12개 사례)
%         ../results/E2/reference_cases.json   (python/E2b_reference_matrix.py가 생성, 80개 조건)
%  판정   - 12개 사례: 에너지 잔차 < 1e-7 W, 정상 사례 10개 통과, 실패 사례 2개가 실패로 판정
%         - 80개 조건: 모든 조건에서 같은 이득·같은 제어기 공칭값, 공칭 41개 통과,
%           통과·실패 판정이 Python의 expected_pass와 같을 것
%  실행   >> cd matlab ; E2_two_stage_crosscheck
%         이후 python/E2c_compare_matlab.py 로 지표를 수치 대조한다.
%  결과   ../results/E2/two_stage_matlab.json, ../results/E2/reference_matrix_matlab.json

here=fileparts(mfilename('fullpath')); folder=fullfile(here,'..','results','E2');

%% (1) 12개 동적 사례 (운전점별 설계 이득, 모델 검산용)
cases=jsondecode(fileread(fullfile(folder,'two_stage_cases.json')));
for j=1:numel(cases)
    r=prism_two_stage_case(cases(j)); rows(j)=r; %#ok<AGROW>
    assert(r.energy_residual_max<1e-7,'에너지 보존 검산 실패');
    fprintf('%-24s 강하 %8.4f V, 경로 피크 %8.3f A, 포트 한계 %d, 전압 품질 %d\n',r.name,r.droop,r.path_peak,r.within_port_limits,r.voltage_quality_pass);
end
assert(all([rows(1:10).within_port_limits]) && all([rows(1:10).voltage_quality_pass]),'정상 사례 실패');
assert(~rows(11).within_port_limits && ~rows(11).voltage_quality_pass,'과부하 사례가 실패로 판정되지 않음');
assert(~rows(12).within_port_limits && rows(12).voltage_quality_pass,'지령 포화 100 A 사례 판정 불일치');
out.scope='MATLAB 독립 중점법 적분; 이득은 Python과 공유'; out.matlab_version=version; out.cases=rows;
write_json(fullfile(folder,'two_stage_matlab.json'),out);
fprintf('  -> 저장: results/E2/two_stage_matlab.json\n');

%% (2) 비교 설계 제어기 80개 조건
cases=jsondecode(fileread(fullfile(folder,'reference_cases.json')));
clear rows
for j=1:numel(cases)
    assert(isequal(cases(j).K,cases(1).K),'조건마다 이득이 다름');
    assert(isequal(cases(j).control_parameters,cases(1).control_parameters),'제어기 공칭값이 다름');
    r=prism_two_stage_case(cases(j));
    assert(r.requirements_pass==cases(j).expected_pass,'Python과 판정 불일치');
    if strcmp(cases(j).group,'nominal'), assert(r.requirements_pass,'공칭 조건 실패'); end
    r.group=cases(j).group; rows(j)=r; %#ok<AGROW>
    fprintf('%-32s 판정 %d, 강하 %.4f V, 경로 %.3f A, 회복 %.1f us\n',r.name,r.requirements_pass,r.droop,r.path_peak,r.recovery_s*1e6);
end
result.scope='MATLAB 독립 구현, 고정 이득 1개와 제어기 공칭값'; result.matlab_version=version; result.cases=rows;
write_json(fullfile(folder,'reference_matrix_matlab.json'),result);
fprintf('  -> 저장: results/E2/reference_matrix_matlab.json (%d개 조건 판정 일치)\n',numel(rows));
end

function write_json(path,s)
f=fopen(path,'w'); assert(f>=0,'파일을 열 수 없음');
fwrite(f,jsonencode(s,'PrettyPrint',true),'char'); fclose(f);
end
