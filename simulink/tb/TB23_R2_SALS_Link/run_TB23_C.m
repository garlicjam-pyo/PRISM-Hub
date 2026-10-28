function run_TB23_C()
%RUN_TB23_C  TB23 사례 C만 다시 실행한다(2026-10-28).
%   1차 실행에서 사례 C(Stage C 회생 차단 없음)의 회로 부하 블록에 차단 끔이 전달되지 않았다(블록 파라미터에 켬·끔이 없어
%   감발 비트로 차단이 시작됨 → 사실상 사례 D와 같은 조건). ref/make_ref_TB23.py에서 끔을 시작 지연 t_sc = 10⁹ s로 나타내게 고친 뒤
%   사례 C만 다시 계산한다. 1차 결과(사례 C 파일과 1차 전체 요약)는 results/run1_C/에 복사해 둔다.
%   이 함수가 끝나면 TB23_summary.*에는 사례 C만 남으므로, 다섯 사례의 최종 요약은 per-case 요약에서 다시 모은다(README).
here = fileparts(mfilename('fullpath'));
res = fullfile(here, 'results'); old = fullfile(res, 'run1_C');
if ~exist(old, 'dir'), mkdir(old); end
f = dir(fullfile(res, 'TB23_C_930V_R1_noblock_*'));
for k = 1:numel(f), copyfile(fullfile(res, f(k).name), fullfile(old, f(k).name)); end
copyfile(fullfile(res, 'TB23_summary.txt'), fullfile(old, 'TB23_summary_run1.txt'));
copyfile(fullfile(res, 'TB23_summary.json'), fullfile(old, 'TB23_summary_run1.json'));
run_TB23(3);
end
