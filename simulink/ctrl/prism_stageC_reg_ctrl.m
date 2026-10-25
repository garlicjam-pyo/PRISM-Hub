function u = prism_stageC_reg_ctrl(t, meas, prm)
%#codegen
%PRISM_STAGEC_REG_CTRL  조정형 Stage C(동기 벅 + CLLC DCX) 디지털 제어기. 검증 코드 E22 control(_avg)과 같은 알고리즘.
%
%   표본: T_s = 10 µs(벅 스위칭 주기, 삼각 반송파의 골 = 상측 켜짐 구간 가운데에서 표본 → 인덕터 평균전류).
%   이번 표본에서 계산한 듀티는 다음 표본부터 쓴다(계산 지연 1주기).
%
%   제어 구조(바깥 → 안)
%     출력전류 지령 i_x* = min( 전압 PI(48 V, 교차 1 kHz) + 부하전류 앞먹임,
%                               충전전류 루프: 부하전류 + 충전 제한 + PI(제한 − i_bat)   ← 배터리가 있을 때,
%                               전류 제한: 과도 130 A, 수요가 정격 105 A를 넘은 시간이 2 ms를 넘으면 105 A )
%     인덕터 전류 지령 i_L* = i_x*/n(DCX 전류비)
%     인덕터 전류 PI(교차 5 kHz, 비례항 지령 가중 b) + 중간전압 앞먹임 → 듀티 d = u/v_bus, 0.02 ≤ d ≤ 0.97
%     DCX 보내는 쪽: i_L* > +0.5 A → 1차(V_I → 48 V), < −0.5 A → 2차(48 V → V_I), 그 사이는 유지
%     경부하 두 브리지 구동(prm(25) = P_in > 0일 때, TB15부터): 출력 전력 지령 |i_x*·v_o| < P_in이면 모드 2(두 브리지 같은
%       위상 구동), 모드 2에서 |i_x*·v_o| > P_out(prm(26))이 되면 지령 부호의 보내는 쪽으로 돌아간다. 받는 쪽만 다이오드로 두면
%       역방향 경부하에서 받는 쪽 1차 레그 용량 때문에 DCX 이득이 오른다(검증 코드 E22 gain·both, TB14 사례 F·G).
%   누적 방지: 조건부 적분(포화 방향으로는 적분하지 않음)
%
%   입력  t     시각 [s]
%         meas  [v_bus; i_L; v_I; v_o; i_load; i_bat]  (i_bat: 충전 +, 배터리가 없으면 0)
%         prm   [T_s K_pi K_ii K_pv K_iv I_lim I_rev ff hyst d_max K_pb K_ib I_bat_max I_rated T_OL b  V_ref dt bat_on  I_v0 d0 mode0 iL0 n (P_in P_out (I_i0))]
%               (1–16 = E22 ctl 벡터와 같은 순서, 25·26번이 없으면 두 브리지 구동 안 함(TB14))
%               27번(TB17부터): 전류 PI 적분의 시작값 = (R_L + K_pi(1 − b))·i_L0. 부하가 있는 시작점에서 시작 과도를 없앤다
%               (없으면 0에서 시작: TB14–TB16, 검증 코드 E22와 같음)
%   출력  u     [d; 모드(+1 1차가 보냄, −1 2차가 보냄, 2 두 브리지 구동); i_L 지령 [A]; 선택(0 전압, 1 충전 제한, 2 상한, 3 하한)]

persistent init tn d dn Iv Ii Ib tol mode iref sel
Ts = prm(1); Kpi = prm(2); Kii = prm(3); Kpv = prm(4); Kiv = prm(5);
Ilim = prm(6); Irev = prm(7); ffon = prm(8); hyst = prm(9); dmax = prm(10);
Kpb = prm(11); Kib = prm(12); Ibmax = prm(13); Irated = prm(14); TOL = prm(15); b = prm(16);
Vref = prm(17); dt = prm(18); bat = prm(19); n = prm(24);
Pin = 0; Pout = 0;
if numel(prm) >= 26, Pin = prm(25); Pout = prm(26); end
if isempty(init)
    init = 1; tn = 0; d = prm(21); dn = prm(21); Iv = prm(20); Ii = 0; Ib = 0; tol = 0;
    mode = prm(22); iref = prm(23); sel = 0;
    if numel(prm) >= 27, Ii = prm(27); end
end
if t >= tn - 0.5*dt
    tn = tn + Ts;
    d = dn;                                          % 직전 표본에서 계산한 듀티를 지금부터 적용
    vb = meas(1); iL = meas(2); vI = meas(3); vo = meas(4); iload = meas(5);
    ib = 0;
    if bat > 0.5, ib = meas(6); end
    % ---- 바깥 루프: 출력전류 지령 ---------------------------------------------------------------
    ev = Vref - vo;
    ff = 0;
    if ffon > 0.5, ff = iload; end                   % 앞먹임은 부하전류만(배터리 전류를 넣으면 양의 되먹임)
    ixr = Kpv*ev + Iv + Kiv*ev*Ts + ff;
    sel = 0;
    if bat > 0.5                                     % 충전전류 루프
        eb = Ibmax - ib;
        ixb = iload + Ibmax + Kpb*eb + Ib;
        if ixb < ixr
            ixr = ixb; sel = 1;
            Ib = Ib + Kib*eb*Ts;
        else
            Ib = 0;
        end
    end
    dem = ixr;                                       % 제한 전 수요
    lim = Ilim;
    if tol >= TOL, lim = Irated; end                 % 과부하 시간 제한
    if ixr > lim
        ixr = lim; sel = 2;
    elseif ixr < -Irev
        ixr = -Irev; sel = 3;
    end
    if dem > Irated
        tol = tol + Ts;
    else
        tol = max(0, tol - Ts);
    end
    if sel == 0 || (sel == 2 && ev < 0) || (sel == 3 && ev > 0)
        Iv = Iv + Kiv*ev*Ts;                         % 조건부 적분
    elseif sel == 1
        Iv = min(Iv, ixr - Kpv*ev - ff);             % 충전 제한 중: 전압 적분이 지령을 따라가게
    end
    iref = ixr/n;
    pr = ixr*vo;                                     % 출력 전력 지령
    if Pin > 0 && mode == 2                          % 두 브리지 구동 중: |P*| > P_out이면 보내는 쪽 하나로
        if pr > Pout
            mode = 1;
        elseif pr < -Pout
            mode = -1;
        end
    elseif Pin > 0 && abs(pr) < Pin
        mode = 2;
    elseif iref > hyst
        mode = 1;
    elseif iref < -hyst
        mode = -1;
    end
    % ---- 안쪽 루프: 인덕터 전류 → 듀티 ---------------------------------------------------------------
    ei = iref - iL;
    uu = vI + Kpi*(b*iref - iL) + Ii + Kii*ei*Ts;
    dd = uu/vb;
    if dd > dmax
        dd = dmax;
        if ei < 0, Ii = Ii + Kii*ei*Ts; end
    elseif dd < 0.02
        dd = 0.02;
        if ei > 0, Ii = Ii + Kii*ei*Ts; end
    else
        Ii = Ii + Kii*ei*Ts;
    end
    dn = dd;
end
u = [d; mode; iref; sel];
end
