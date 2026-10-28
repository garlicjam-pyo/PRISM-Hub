function [gb, fl] = prism_r2_gate_b(t, g, sup, meas, prm)
%#codegen
%PRISM_R2_GATE_B  R2 보호 상태기계의 게이트 재정의(TB09, 적분 간격마다 실행): 하드웨어 비교기, 고장 주입, 모드별 게이트.
%
%  입력  g     게이트 생성기 출력 [A상측 A하측 B상측 B하측 | P1–P4 | S1–S4] (ctrl/prism_gate_stageB.m)
%        sup   상태기계 지령 [브리지 모드(0 제어 PWM, 1 영벡터, 2 차단, 3 조향 PWM); DAB 모드(0 제어기, 1 보조, 2 정지);
%              바이패스 주 스위치; 제동 저항 게이트; 상태 번호]
%        meas  [i_p i_h v_link v_s v_bus]
%        prm   [dt T_HW I_HW VL_HW VS_HW 상한 고장종류(0 없음, 1 H-브리지 개방, 2 DAB 정지) 고장시각 T_GDF (두 번째 고장 시각)]
%              (TB23) 10번째 값이 있으면 그 시각에 비교기 차단 래치를 강제로 켠다(DAB 고장 강등 중 H-브리지 차단 → 이중 고장)
%  출력  gb    [H-브리지 4 | DAB 8 | 바이패스 주 스위치 | 제동 저항]
%        fl    [게이트 구동기 고장 신호(H-브리지 개방, T_GDF 뒤); 하드웨어 비교기 차단 래치]
%  하드웨어 비교기는 H-브리지가 동작하는 동안(차단·고장 전) 연속 감시한다: |i_p|·|i_h| > I_HW, v_link > VL_HW,
%  |v_s| > VS_HW, 그리고 정상 조정 상태(1–5)에서 v_bus > 부품 등급 상한. 조건이 T_HW 동안 이어지면 브리지를 끄고 래치한다.

persistent since trip
if isempty(trip), since = -1; trip = 0; end
T_HW = prm(2); I_HW = prm(3); VL_HW = prm(4); VS_HW = prm(5); upper = prm(6);
ftype = prm(7); t_f = prm(8); T_GDF = prm(9);
bmode = round(sup(1)); dmode = round(sup(2)); st = round(sup(5));
hb_fault = ftype == 1 && t >= t_f;
dab_fault = ftype == 2 && t >= t_f;
ip = meas(1); ih = meas(2); vl = meas(3); vs = meas(4); vb = meas(5);
if trip < 0.5 && ~hb_fault && bmode ~= 2
    normal = st >= 1 && st <= 5;
    cond = abs(ip) > I_HW || abs(ih) > I_HW || vl > VL_HW || abs(vs) > VS_HW || (normal && vb > upper);
    if cond
        if since < 0, since = t; end
        if t - since >= T_HW - 1e-15, trip = 1; end
    else
        since = -1;
    end
end
if numel(prm) >= 10 && t >= prm(10)
    trip = 1;                                     % (TB23) 두 번째 고장 주입
end
gb = [g(:); 0; 0];
if trip > 0.5 || hb_fault || bmode == 2
    gb(1:4) = 0;
elseif bmode == 1
    gb(1:4) = [0; 1; 0; 1];                       % 영벡터: H-브리지 하측 두 소자
end
if dab_fault || dmode == 2
    gb(5:12) = 0;
end
gb(13) = double(sup(3) > 0.5);
gb(14) = double(sup(4) > 0.5);
fl = [double(hb_fault && t >= t_f + T_GDF); trip];
end
