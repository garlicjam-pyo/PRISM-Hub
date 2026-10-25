function check_gate_transition()
%CHECK_GATE_TRANSITION  EPS 지령 계단에서 게이트 생성기의 직류 편류(TB11 → TB12 근거). MATLAB·Octave 공용.
%
%   TB11 사례 A의 5.215 ms 주기에는 지령표 칸 전환으로 EPS 지령이 (φ, D1) = (−0.029, 0.278) → (0.199, 0.379)로 한 번에
%   바뀌었고, 회로 DAB 첨두가 88.5 A(정상 주기 66.6 A)였다. 이 스크립트는 게이트 생성기만 떼어 내 이상 스위칭(데드타임 동안
%   이전 상태 유지, 출력용량 없음)과 누설 인덕터(14.68 µH, 20 mΩ)로 같은 계단을 계산한다(버스 432 V, 링크 67.5 V).
%     e: ctrl/prism_gate_stageB_e.m(TB10·TB11) — D1을 상향 에지에서 한 주기 잡음
%     f: ctrl/prism_gate_stageB_f.m(TB12)      — 레그 2 반 이동 + 위상·D1 변화율 상한
%   출력: 계단 앞 주기 첨두, 계단 뒤 주기별 첨두(n·max|i_L|)와 주기 평균 전류(직류 편류, 링크 쪽 환산).
%   이상 모델에는 데드타임 감쇠가 없어 편류가 R/L(0.73 ms)로만 줄어든다. 회로에서는 수 주기 안에 줄어든다.
%   실행: cd ref; check_gate_transition

here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', 'ctrl'));
dt = 5e-9; Np = 1000; T = 5e-6; prm = [dt Np 10 20 T];
n = 4.6; L = 14.67975e-6; R = 0.02; vb = 432; vl = 67.5;
a = [-0.029 0.278]; b = [0.199 0.379];
gens = {'prism_gate_stageB_e', 'prism_gate_stageB_f'};
for g = 1:2
    f = str2func(gens{g});
    clear(gens{g});
    N = 70*Np; i = 0; l1 = 0; l2 = 1; s1 = 0; s2 = 1;
    pkp = zeros(70, 1); mp = zeros(70, 1); acc = 0; pk = 0;
    for k = 0:N-1
        t = k*dt; per = floor(k/Np);
        if per < 40, e = a; else, e = b; end                 % 40주기째에 계단
        gg = f(t, [0; 0], 0, prm, [0 0 0], [1; e(1); e(2)]);
        gP = gg(5:8); gS = gg(9:12);
        if gP(1), l1 = 1; elseif gP(2), l1 = 0; end
        if gP(3), l2 = 1; elseif gP(4), l2 = 0; end
        if gS(1), s1 = 1; elseif gS(2), s1 = 0; end
        if gS(3), s2 = 1; elseif gS(4), s2 = 0; end
        i = i + (vb*(l1 - l2) - n*vl*(s1 - s2) - R*i)/L*dt;
        pk = max(pk, abs(i)); acc = acc + i;
        if mod(k + 1, Np) == 0
            pkp(per + 1) = n*pk; mp(per + 1) = n*acc/Np; pk = 0; acc = 0;
            if per == 20 || per == 30, i = i - mp(per + 1)/n; end   % 시작 과도의 편류를 지운다(계단 전)
        end
    end
    fprintf('%s: 계단 전 첨두 %.1f A | 계단 뒤 첨두 %s A | 주기 평균 %s A | 30주기 뒤 첨두 %.1f A\n', gens{g}, pkp(39), ...
        sprintf('%.1f ', pkp(40:50)), sprintf('%.1f ', mp(40:50)), pkp(70));
end
end
