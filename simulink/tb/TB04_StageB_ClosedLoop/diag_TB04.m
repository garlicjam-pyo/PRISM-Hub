function diag_TB04()
%DIAG_TB04  TB04 진단: 사례 A를 짧게(50 µs) 실행하고 기록 신호를 results/TB04_diag.mat로 저장한다.
%
%   전체 실행 전에 평형점에서 출발한 회로가 평형을 유지하는지(버스전압, 경로·필터 전류, 직렬전압,
%   링크 전류, 제어기 출력)를 검증 모델 파형과 비교하기 위한 진단용 실행이다.

here = fileparts(mfilename('fullpath'));
mdl  = 'TB04_StageB_ClosedLoop';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
load_system(fullfile(here, [mdl '.slx']));
assignin('base', 'TB04_case', 'A_640V_15to25kW');
run(fullfile(here, 'TB04_init.m'));
tic; out = sim(mdl, 'StopTime', '50e-6'); w = toc;
D = struct('wall', w);
nm = {'t', 'vbus', 'ip', 'ih', 'vs', 'vlink', 'ilink', 'iL', 'dg', 'uc', 'aux'};
for k = 1:numel(nm)
    D.(nm{k}) = double(squeeze(out.(nm{k})));
end
% 부하·손실 전류원 설정과 Simulink-PS 변환기 입력 처리 방식 기록
cv = {'iload_PS', 'iloss_PS'};
for k = 1:numel(cv)
    try
        D.([cv{k} '_filter']) = get_param([mdl '/' cv{k}], 'FilteringAndDerivatives');
    catch
        D.([cv{k} '_filter']) = 'n/a';
    end
end
D.TB = TB;
save(fullfile(resDir, 'TB04_diag.mat'), '-struct', 'D', '-v7');
fprintf('diag saved (%.1f s wall, %d samples), vbus end %.3f V, ip end %.2f A, ih end %.2f A, vs end %.2f V\n', ...
    w, numel(D.t), D.vbus(end), D.ip(end), D.ih(end), D.vs(end));
fprintf('PS converter input handling: iload %s, iloss %s\n', D.iload_PS_filter, D.iloss_PS_filter);
close_system(mdl, 0);
evalin('base', 'clear TB04_case');
end
