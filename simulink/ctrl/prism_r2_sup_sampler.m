function s = prism_r2_sup_sampler(t, y, fl, prm, smp)
%#codegen
%PRISM_R2_SUP_SAMPLER  R2 보호 상태기계 표본화 실행기(TB09, MATLAB Function 블록의 진입 함수).
%
%   5 µs마다(제어기와 같은 표본 시점, 제어기보다 먼저) ctrl/prism_r2_supervisor.m을 한 번 계산하고 그 밖에는 직전 출력을 유지한다.
%   입력  t 시각, y [i_p v_s v_bus i_h v_link], fl [게이트 구동기 고장 신호, 비교기 차단 래치](한 간격 지연),
%         prm 상태기계 파라미터(TB.sup_prm), smp [dt Np]
%   출력  s 상태기계 지령 12개(prism_r2_supervisor.m 참조)

persistent sh
if isempty(sh)
    sh = zeros(12, 1);
end
k = round(t/smp(1));
if mod(k, round(smp(2))) == 0
    sh = prism_r2_supervisor(t, y, fl, prm);
end
s = sh;
end
