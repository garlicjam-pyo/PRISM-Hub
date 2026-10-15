function run_TB04(caseList, opts)
%RUN_TB04  TB04 폐루프 사례를 실행하고 검증 모델(E12 스위칭 ODE)과 Tier-1 기준으로 판정한다.
%
%   run_TB04                     % 두 사례 모두
%   run_TB04({'A_640V_15to25kW'})
%   run_TB04(caseList, struct('dt', 2.5e-9))   % 적분 간격(= 게이트 시간 분해능)을 바꿔 실행. 결과 파일 이름에 _dt2.5ns
%   run_TB04(caseList, struct('dt', 2.5e-9, 'Coss_d', 20e-12))   % 소자 출력용량(DAB C_oss_d, H-브리지 C_oss_h) 민감도
%
%   판정(사례마다)
%     (1) Tier-1(Simscape 회로 자체): 5 µs 주기 평균 버스전압 400±8 V, 마지막 1 ms 주기 평균 리플 ≤ 0.1 V,
%         경로·필터 순시 전류 ≤ 98 A, 링크전류 주기 평균 ≤ 80 A·링크전력 ≤ 8 kW, 링크전압 90–110 V, |v_s| ≤ 90 V
%     (2) 검증 모델과 일치: 계단 전 정상(0.8–1.0 ms)과 끝(3.8–4.0 ms) 평균 — 버스 0.2 V, 경로·필터 1 A,
%         계단 뒤 최저 버스전압 0.5 V, 최대 경로·필터 순시 전류 max(2 A, 3 %), 주기 평균 버스전압 궤적 RMS 0.2 V
%         링크전압·링크전류의 일치는 사례 A(SPS 영역)에서 판정(링크 0.5 V, 링크전류 1.5 A + 3 %),
%         사례 B(DAB 저전류 구간)는 정보로 기록한다(TB03: 데드타임 영역 전달 특성이 C_oss에 민감)
%   결과: results/TB04_<사례>_summary.txt·json, TB04_<사례>_response.png, TB04_<사례>_step_zoom.png, 회로도 그림
%   판정·그림 코드는 lib/tb_stageB_evaluate.m(TB04B와 공용)

if nargin < 1 || isempty(caseList), caseList = {'A_640V_15to25kW', 'B_788V_0to10kW'}; end
if nargin < 2, opts = struct(); end
tag = '';                                           % 결과 파일 이름에 붙일 변경 사항 표시
if isfield(opts, 'dt') && abs(opts.dt - 5e-9) > 1e-12, tag = [tag sprintf('_dt%gns', 1e9*opts.dt)]; end
if isfield(opts, 'Coss_d'), tag = [tag sprintf('_Cossd%gpF', 1e12*opts.Coss_d)]; end
if isfield(opts, 'Coss_h'), tag = [tag sprintf('_Cossh%gpF', 1e12*opts.Coss_h)]; end
if isempty(fieldnames(opts))
    evalin('base', 'clear TB04_opts');
else
    assignin('base', 'TB04_opts', opts);            % TB04_init이 읽는다(dt는 prism_hub_params, C_oss는 TB.B)
end
here = fileparts(mfilename('fullpath'));
mdl  = 'TB04_StageB_ClosedLoop';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
load_system(fullfile(here, [mdl '.slx']));
allPass = true;
for c = 1:numel(caseList)
    cn = caseList{c};
    assignin('base', 'TB04_case', cn);
    run(fullfile(here, 'TB04_init.m'));
    tic; out = sim(mdl); wall = toc;
    S = tb_stageB_evaluate(out, TB, fullfile(here, 'ref'), cn, resDir, wall, tag, 'TB04');
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
evalin('base', 'clear TB04_case TB04_opts');
if ~isempty(tag), fprintf('TB04%s overall: %s\n', tag, ternary(allPass, 'PASS', 'FAIL')); return; end
sl_export_png({mdl, [mdl '/StageB_Regulator'], [mdl '/StageB_Regulator/HBridge'], [mdl '/Controller_StageB'], [mdl '/Gate_StageB']}, resDir);
fprintf('TB04 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
