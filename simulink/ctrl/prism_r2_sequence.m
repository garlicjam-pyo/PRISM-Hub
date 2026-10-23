function s = prism_r2_sequence(t, prm)
%#codegen
%PRISM_R2_SEQUENCE  R2 창 조정 Stage B 모듈의 운전 모드·기준전압 시퀀서(TB08).
%
%  창 조정 모듈은 V_A가 창 기준 V_W를 넘을 때만 버스를 V_W로 조정하고, 그 밖에서는 바이패스 스위치로 직렬 포트를
%  단락한 채 정지한다. 모드 전환과 고장 강등은 정해진 순서로 진행한다(검증 코드 E19와 같은 순서).
%  이 함수는 시험 시나리오의 시각표를 따라 그 순서를 만든다(측정값으로 판단하는 상태기계는 E17의 범위).
%
%  모드 번호
%    0 제어        : 채택 제어기가 H-브리지·DAB를 구동(창 조정)
%    1 DAB 고장    : 제어기는 계속 동작하지만 DAB 게이트 8개를 끈다(링크 전력 교환 없음)
%    2 영벡터      : H-브리지 하측 두 소자를 켜 직렬 포트를 L_h로 단락(v_s ≈ 0), DAB 정지
%    3 바이패스    : 바이패스 스위치 켬, H-브리지·DAB 전 소자 끔
%    4 바이패스 + 영벡터 : 바이패스와 H-브리지 영벡터가 경로전류를 나눠 흘림(켜기 전 준비 상태)
%  모드 2–4에서는 제어기를 무충격 재초기화 상태로 둔다(적분기가 지령 = 경로전류가 되도록 매 표본 다시 맞춘다).
%
%  입력  t    시각 [s]
%        prm  [t_ramp0 t_ramp1 v_from v_to t_nodab t_zero t_byp t_open t_ctrl mode_init]
%             기준전압: t < t_ramp0 이면 v_from, t_ramp0–t_ramp1 사이 직선, t ≥ t_ramp1 이면 v_to
%             모드: t ≥ t_byp → 3, t ≥ t_zero → 2, t ≥ t_nodab → 1, t ≥ t_ctrl → 0, t ≥ t_open → 2, 그 전 → mode_init
%             (쓰지 않는 시각은 1e30)
%  출력  s    [버스 기준전압 V_ref; 제어기 재초기화(1/0); 모드 번호]

t0 = prm(1); t1 = prm(2); vf = prm(3); vt = prm(4);
if t < t0
    vref = vf;
elseif t >= t1
    vref = vt;
else
    vref = vf + (vt - vf)*(t - t0)/(t1 - t0);
end
if t >= prm(7)
    mode = 3;
elseif t >= prm(6)
    mode = 2;
elseif t >= prm(5)
    mode = 1;
elseif t >= prm(9)
    mode = 0;
elseif t >= prm(8)
    mode = 2;
else
    mode = prm(10);
end
rst = double(mode >= 2);
s = [vref; rst; mode];
end
