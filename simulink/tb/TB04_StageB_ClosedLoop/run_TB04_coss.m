function run_TB04_coss()
%RUN_TB04_COSS  TB04 잔류 리플 원인 점검: DAB 소자 출력용량(C_oss_d)에 따른 사례 A 정상상태 버스 리플.
%
%   게이트 시간 분해능을 2.5 → 1.25 ns로 줄여도 사례 A(25 kW)의 마지막 1 ms 리플은 0.11–0.12 V에 머문다
%   (run_TB04_resolution). 검증 모델(E12)과 회로의 남은 차이 중 가장 큰 것은 DAB 소자 출력용량이다
%   (검증 모델에는 없음, TB03: 데드타임 전이와 변압기 직류 편류 감쇠가 C_oss에 민감).
%   같은 사례를 적분 간격 2.5 ns에서 C_oss_d 20 pF, 500 pF로 다시 계산해 리플이 C_oss_d를 따라가는지 본다.
%   결과: results/TB04_A_640V_15to25kW_dt2.5ns_Cossd*pF_*, results/TB04_coss.txt

here = fileparts(mfilename('fullpath'));
resDir = fullfile(here, 'results');
run_TB04({'A_640V_15to25kW'}, struct('dt', 2.5e-9, 'Coss_d', 20e-12));
run_TB04({'A_640V_15to25kW'}, struct('dt', 2.5e-9, 'Coss_d', 500e-12));
rows = {'_dt2.5ns_Cossd20pF', 20; '_dt2.5ns', 100; '_dt2.5ns_Cossd500pF', 500};
fid = fopen(fullfile(resDir, 'TB04_coss.txt'), 'w');
hdr = sprintf('case A_640V_15to25kW, dt 2.5 ns\n%-12s %12s %14s %16s %10s\n', 'Coss_d[pF]', 'ripple[V]', 'min vbus[V]', 'final il diff[A]', 'verdict');
fprintf('%s', hdr); fprintf(fid, '%s', hdr);
for k = 1:size(rows, 1)
    f = fullfile(resDir, ['TB04_A_640V_15to25kW' rows{k, 1} '_summary.json']);
    if ~exist(f, 'file'), continue; end
    S = jsondecode(fileread(f));
    c = S.compare;
    mv = c(strcmp({c.metric}, 'min v_bus after step [V]'));
    fl = c(strcmp({c.metric}, 'final mean link current [A]'));
    s = sprintf('%-12g %12.4f %14.3f %16.3f %10s\n', rows{k, 2}, S.ripple_last1ms_V, mv.simscape, fl.simscape - fl.model, S.verdict);
    fprintf('%s', s); fprintf(fid, '%s', s);
end
fclose(fid);
end
