function s = prism_r2_supervisor(t, y, fl, prm)
%#codegen
%PRISM_R2_SUPERVISOR  R2 창 조정 모듈의 측정 기반 보호 상태기계(TB09, 검증 코드 E17 r2_run의 상태기계와 같은 논리).
%
%  5 µs마다(호출 측 표본기) 측정값과 고장 신호로 운전 상태를 정하고, 제어기·게이트·바이패스·제동 저항·부하 분리 명령을 낸다.
%  상태 번호
%    0 바이패스          바이패스 닫힘, H-브리지·DAB 정지(버스 = V_A)
%    1 준비(PREP)        바이패스 + H-브리지(영벡터 또는 전류 조향: 바이패스 전류 → 0)
%    2 열림 대기         바이패스 열림, H-브리지 영벡터(또는 조향) → t_wait 뒤 제어 시작
%    3 창 조정           채택 제어기(기준 V_A → V_W 램프 뒤 V_W)
%    4 끔 램프 / 5 끔 유지(기준 = V_A 추정, |v_s| ≤ 2 V가 50 µs 이어지면) / 6 영벡터(또는 직렬전압 조향) → 바이패스
%    7 DAB 고장 유지     H-브리지는 계속 조정, DAB 정지, 링크 제동 저항으로 링크 ≤ 110 V, 400 V 부하 분리 대기
%    8 DAB 고장 램프     기준 → V_A(1 ms) → V_A 추정 추종, |v_s| ≤ 2 V가 50 µs 이어지면 → 6 → 강등
%    9 H-브리지 고장 유지  H-브리지 꺼짐(다이오드 정류), DAB 보조 루프가 링크전압으로 버스를 V_W에 붙잡음 + 제동 저항
%   10 링크 붕괴         링크 기준을 20 V/ms로 0 V까지 → 직렬전압이 다이오드 전압까지 줄어듦.
%                        링크 ≤ VL_SOFT, 또는 정체(기준 0 도달 뒤 T_STALL 동안 DV_STALL도 안 내려가고 링크 ≤ VL_STALL), 또는 T_COL_MAX → 11
%   11 소프트 바이패스   바이패스 저항을 10 Ω에서 로그 램프로 낮추되(제한 없으면 T_SOFT에 3.3 mΩ), 경로전류가 투입 시작값 + DI_SOFT를
%                        넘으면 표본마다 K_UP배로 되올린다(경로전류 조절). 3.3 mΩ에 이르거나 T_SOFT_MAX가 지나면 → 12
%   12 강등              바이패스 닫힘, Stage B 정지(버스 = V_A)
%   13 이중 고장         DAB 고장 중 H-브리지 차단: Stage A 협조 정지가 필요(이 모델 밖)
%
%  (2026-10-24 TB09 1차 결과로 추가: 회로에서는 링크 붕괴가 3.5–22 V에서 멈췄고, 남은 직렬전압을 로그 램프로 닫자 경로전류가
%   177 A까지 올랐다. 그래서 정체 감지와 경로전류 조절을 넣었다. 같은 논리를 검증 코드 E17에도 넣었다.)
%
%  입력  t    시각 [s]
%        y    측정 [i_p v_s v_bus i_h v_link]
%        fl   [게이트 구동기 고장 신호(H-브리지 개방), 하드웨어 비교기 차단 래치]
%        prm  파라미터 벡터(TB09_init.m의 TB.sup_prm, 번호는 아래 코드 주석)
%  출력  s = [V_ref; 재초기화; 브리지 모드(0 제어 PWM, 1 영벡터, 2 차단, 3 조향 PWM); 조향 변조율;
%             DAB 모드(0 제어기, 1 보조 지령, 2 정지); 보조 링크전류 지령; 바이패스 소프트 저항 [Ω]; 바이패스 주 스위치(1/0);
%             제동 저항 게이트(1/0); 400 V 부하 분리(1/0); 상태 번호; 고장 검출(0 없음, 1 구동기, 2 비교기, 3 링크 창, 4 버스 창)]

persistent st t_st t_det det shed_cmd shed sw_since vb_since rv0 rv1 rt1 rtype qb amode vl0 t0 tsoft0 Rs main brk mst gsince ip_s0 stall_t stall_v
VW = prm(1); upper = prm(2); H = prm(3); R = prm(4); Rh = prm(5); Cs = prm(6); Lh = prm(7); itau = prm(8);
Clink = prm(9); VD = prm(10); t_ev = prm(11); ev = prm(12); pol = prm(13); prep = prm(14); cls = prm(15);
t_prep = prm(16); t_wait = prm(17); RAMP = prm(18); HOLD = prm(19); ZERO = prm(20); t_shed = prm(21);
RATE = prm(22); VL_SOFT = prm(23); T_SOFT = prm(24); R_SOFT0 = prm(25); R_ON = prm(26); T_COL_MAX = prm(27);
VL_LO = prm(28); VL_HI = prm(29); T_SW = prm(30); VB_SW = prm(31); T_VB = prm(32);
KP_B = prm(33); KI_B = prm(34); QB_MAX = prm(35); W_L = prm(36); TAU_ST = prm(37); R_OPEN = prm(38);
P_r = prm(39); link_max = prm(40); turns = prm(41); phmax = prm(42); fs = prm(43); Ldab = prm(44); vbat = prm(45);
st0 = prm(46); Ts = prm(47); VS_GATE = prm(48); T_GATE = prm(49); T_GATE_MAX = prm(50);
VL_STALL = prm(51); T_STALL = prm(52); DV_STALL = prm(53); DI_SOFT = prm(54); K_UP = prm(55); T_SOFT_MAX = prm(56);
K_DN = (R_SOFT0/R_ON)^(Ts/T_SOFT);                    % 제한에 안 걸리면 10 Ω → 3.3 mΩ를 T_SOFT에 지나는 표본당 비율

ip = y(1); vs = y(2); vb = y(3); ih = y(4); vl = y(5);
if isempty(st)
    st = st0; t_st = 0; t_det = -1; det = 0; shed_cmd = -1; shed = 0; sw_since = -1; vb_since = -1;
    rv0 = VW; rv1 = VW; rt1 = 0; rtype = 0; qb = 0; amode = 0; vl0 = 100; t0 = 0; tsoft0 = 0;
    if st0 == 3, Rs = R_OPEN; main = 0; else, Rs = R_OPEN; main = 1; end
    brk = 0; mst = 0; gsince = -1; ip_s0 = 0; stall_t = -1; stall_v = 0;
end
va_m = vbat/2 - R*ip;                                  % V_A 추정(배터리 전압 센서 − 경로 강하)
gwin = (st == 5 && t - t_st >= HOLD - 1e-12) || (st == 8 && t - t_st >= RAMP + HOLD - 1e-12);
if gwin && abs(vs) <= VS_GATE                          % 영벡터 진입 조건: 최소 유지 뒤 |v_s| ≤ 2 V가 50 µs 이어짐
    if gsince < 0, gsince = t; end
else
    gsince = -1;
end
gate_ok = gsince >= 0 && t - gsince >= T_GATE - 1e-12;
bridge_dead = fl(1) > 0.5 || fl(2) > 0.5;
% ---- 고장 검출 --------------------------------------------------------------------------------
if t_det < 0
    if fl(1) > 0.5, t_det = t; det = 1; end
    if fl(2) > 0.5, t_det = t; det = 2; end
    if t_det < 0 && (st == 3 || st == 4 || st == 5)
        if vl < VL_LO || vl > VL_HI
            if sw_since < 0, sw_since = t; end
            if t - sw_since >= T_SW - 1e-12, t_det = t; det = 3; end
        else
            sw_since = -1;
        end
        if abs(vb - vref_at(t, rtype, rv0, rv1, rt1, RAMP, VW, va_m)) > VB_SW
            if vb_since < 0, vb_since = t; end
            if t - vb_since >= T_VB - 1e-12, t_det = t; det = 4; end
        else
            vb_since = -1;
        end
    end
elseif fl(2) > 0.5 && det == 3 && st ~= 13 && st ~= 12 && st >= 6 && st <= 8
    st = 13; t_st = t;                                  % DAB 고장 강등 중 하드웨어 차단 → 이중 고장
end
sw_states = (st >= 1 && st <= 8);
if t_det >= 0 && shed_cmd < 0 && va_m > upper - 2 && st ~= 0
    shed_cmd = t;
end
if shed_cmd >= 0 && t - shed_cmd >= t_shed - 1e-12
    shed = 1;
end
% ---- 강등 경로 선택 ----------------------------------------------------------------------------
if (det == 1 || det == 2 || det == 4) && sw_states && st ~= 13
    if pol == 1                                          % 즉시 바이패스(비교용)
        main = 1; Rs = R_OPEN; st = 12; t_st = t;
    elseif pol == 2                                      % 바로 붕괴(비교용)
        amode = 1; t0 = t; vl0 = vl; st = 10; t_st = t;
    else
        st = 9; t_st = t; amode = 0; qb = 0;
    end
elseif det == 3 && (st == 3 || st == 4 || st == 5)
    if pol == 2 && shed_cmd >= 0                         % 제동 저항으로 유지
        st = 7; t_st = t;
    else
        rv0 = vref_at(t, rtype, rv0, rv1, rt1, RAMP, VW, va_m); rv1 = va_m; rt1 = t; rtype = 1; st = 8; t_st = t;
    end
end
% ---- 링크 붕괴 정체 감지(기준이 0에 닿은 뒤) ------------------------------------------------------------
stalled = false;
if st == 10 && t - t_st >= vl0/RATE - 1e-12
    if stall_t < 0 || stall_v - vl >= DV_STALL
        stall_t = t; stall_v = vl;
    end
    stalled = (t - stall_t >= T_STALL - 1e-12) && vl <= VL_STALL;
end
% ---- 정상 순서와 강등 진행 --------------------------------------------------------------------------
if st == 0 && ev == 1 && t >= t_ev && vbat/2 >= VW + H
    st = 1; t_st = t;
elseif st == 1 && t - t_st >= t_prep - 1e-12
    main = 0; Rs = R_OPEN; st = 2; t_st = t;
elseif st == 2 && t - t_st >= t_wait - 1e-12
    rv0 = va_m; rv1 = VW; rt1 = t; rtype = 1; st = 3; t_st = t;
elseif st == 3 && ev == 2 && t >= t_ev && t_det < 0 && vbat/2 <= VW - H
    rv0 = vref_at(t, rtype, rv0, rv1, rt1, RAMP, VW, va_m); rv1 = va_m; rt1 = t; rtype = 1; st = 4; t_st = t;
elseif st == 4 && t - t_st >= RAMP - 1e-12
    rtype = 2; st = 5; t_st = t;                         % 램프 뒤에는 기준이 V_A 추정을 따라간다
elseif st == 5 && t - t_st >= HOLD - 1e-12 && (gate_ok || t - t_st >= T_GATE_MAX - 1e-12)
    st = 6; t_st = t;
elseif st == 7 && shed > 0.5
    rv0 = vref_at(t, rtype, rv0, rv1, rt1, RAMP, VW, va_m); rv1 = va_m; rt1 = t; rtype = 1; st = 8; t_st = t;
elseif st == 8 && t - t_st >= RAMP - 1e-12 && rtype ~= 2
    rtype = 2;
elseif st == 8 && t - t_st >= RAMP + HOLD - 1e-12 && (gate_ok || t - t_st >= RAMP + T_GATE_MAX - 1e-12)
    st = 6; t_st = t;
elseif st == 6 && t - t_st >= ZERO - 1e-12
    main = 1; Rs = R_OPEN;
    if t_det >= 0, st = 12; else, st = 0; end
    t_st = t;
elseif st == 9 && (shed_cmd < 0 || shed > 0.5)
    amode = 1; t0 = t; vl0 = vl; st = 10; t_st = t;
elseif st == 10 && (vl <= VL_SOFT || stalled || t - t_st >= T_COL_MAX - 1e-12)
    if pol == 5
        main = 1; Rs = R_OPEN; st = 12;
    else
        tsoft0 = t; ip_s0 = ip; Rs = R_SOFT0; st = 11;
    end
    t_st = t;
elseif st == 11 && (Rs <= R_ON*(1 + 1e-9) || t - t_st >= T_SOFT_MAX - 1e-12)
    main = 1; Rs = R_OPEN; st = 12; t_st = t;
end
if st == 11 && t > tsoft0 + 1e-12                        % 소프트 투입(경로전류 조절)
    if ip > ip_s0 + DI_SOFT
        Rs = min(Rs*K_UP, R_SOFT0);
    else
        Rs = max(Rs/K_DN, R_ON);
    end
end
% ---- 지령 --------------------------------------------------------------------------------------
vref = vref_at(t, rtype, rv0, rv1, rt1, RAMP, VW, va_m);
rst = double(st == 0 || st == 1 || st == 2 || st == 6 || st >= 9);
steer = (st == 1 || st == 2) && prep > 0.5 || (st == 6 && cls > 0.5);
if st == 3 || st == 4 || st == 5 || st == 7 || st == 8
    bmode = 0;
elseif steer
    bmode = 3;
elseif st == 1 || st == 2 || st == 6
    bmode = 1;
else
    bmode = 2;
end
if bridge_dead, bmode = 2; end
if steer
    if st == 6, ihs = ip - Cs*vs/TAU_ST; else, ihs = ip; end
    mst = min(max((vs + Rh*ih + Lh/itau*(ihs - ih))/max(vl, 1), -0.95), 0.95);
end
% 보조 링크 루프(H-브리지 강등 9–11)
icmd_aux = 0; vlr = vl;
if st >= 9 && st <= 11
    if amode == 0
        e = vb - VW;
        qb = min(max(qb + Ts*KI_B*e, -QB_MAX), QB_MAX);
        ff = vbat/2 - (R + Rh)*ip - 2*VD - VW;
        vlr = min(max(ff + KP_B*e + qb, 0), 110);
    else
        vlr = max(vl0 - RATE*(t - t0), 0);
    end
    sps = max(vb, 0)*turns*phmax*(1 - phmax/pi)/(2*pi*fs*Ldab);
    lim = min([link_max, sps, P_r/max(vl, 1e-3)]);
    icmd_aux = min(max(-abs(ih) + Clink*W_L*(vlr - vl), -lim), lim);
end
if st >= 9 && st <= 11
    dmode = 1;
elseif st == 3 || st == 4 || st == 5 || st == 7 || st == 8
    dmode = 0;
else
    dmode = 2;
end
if det == 3, dmode = 2; end                              % DAB 고장: DAB 게이트는 고장 주입으로 이미 꺼져 있음
% 제동 저항(정책 4·5, DAB 정책 2). H-브리지 강등 유지(9) 중에는 링크 과전압 보호만(110 V), 붕괴·소프트 투입(10·11) 중에는
% 링크 기준 + 5 V 위에서 켠다(2026-10-24: 유지 중 기준 추종 제동은 경로전류 첨두를 키워 E17에서 W410 103 A로 불통과)
if (pol == 4 || pol == 5) && st == 9
    if vl > 110, brk = 1; elseif vl < 105, brk = 0; end
elseif (pol == 4 || pol == 5) && st >= 10 && st <= 11
    if vl > vlr + 5, brk = 1; elseif vl < vlr + 2, brk = 0; end
elseif pol == 2 && det == 3 && (st == 7 || st == 8 || st == 6)
    if vl > 110, brk = 1; elseif vl < 105, brk = 0; end
else
    brk = 0;
end
s = [vref; rst; bmode; mst; dmode; icmd_aux; Rs; main; brk; shed; st; det];
end

function v = vref_at(t, rtype, v0, v1, t1, RAMP, VW, va_m)
% 기준전압: 0 = V_W, 1 = v0 → v1 직선 램프(RAMP), 2 = V_A 추정 추종(끔·DAB 고장 램프 뒤)
if rtype < 0.5
    v = VW;
elseif rtype < 1.5
    v = v0 + (v1 - v0)*min((t - t1)/RAMP, 1);
else
    v = va_m;
end
end
