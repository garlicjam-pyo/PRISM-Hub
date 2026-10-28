%TB23_INIT  TB23(보호 상태기계 ↔ SALS 연동, R2-W460) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   TB13과 같은 전력 회로·상태기계·EPS 지령 블록·게이트 생성기(검증 코드 E21 P3t)에 다음을 더한다.
%     - 400 V 부하 = 등급별 계약 응답 블록(ctrl/prism_sals_loads.m, TB.sals_prm 22개): 상태기계 비트 명령(접촉기 열림, SALS 감발·
%       되돌림, Stage C 회생 차단)에 메시지 지연·손실·워치독과 계약 변화율로 응답한다.
%     - 상태기계 파라미터 69개(SALS 모드, 61–69): 부하전류 추정 i_p − C_tot·dv_bus/dt로 유지(9) 끝, T_CUR_MAX면 접촉기 분리,
%       이중 고장(13)의 접촉기 분리 + SALS 감발 + Stage A 정지 + 제동 저항 과전압 보호
%     - Stage A 정지 스위치(ctrl/prism_stageA_stop.m)와 V_A 노드 커패시터 C_A 400 µF
%     - 보호 파라미터 10번째 = 두 번째 고장(비교기 차단) 시각(사례 E)
%   SALS 시간은 ks = 0.15로 줄였다(메시지 지연 5 → 0.75 ms, 접촉기 20 → 3 ms 등, ref/make_ref_TB23.py). 기준값도 같은 시간으로 계산한다.
%   사례: 기본 작업공간 변수 TB23_case(없으면 'A_930V_MX_S5'). 기준값은 ref/TB23_<사례>_init.json(검증 코드 E17·E29)
%   선택: 기본 작업공간 변수 TB23_opts(구조체) — dt

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');

if evalin('base', 'exist(''TB23_case'', ''var'')')
    caseName = evalin('base', 'TB23_case');
else
    caseName = 'A_930V_MX_S5';
end
ov = struct();
if evalin('base', 'exist(''TB23_opts'', ''var'')'), ov = evalin('base', 'TB23_opts'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB23_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P0, 't_step', 1e30, 't_end', R0.t_end);
cs.dt = 2.5e-9;                      % TB08과 같은 판정 격자
if isfield(ov, 'dt'), cs.dt = ov.dt; end
P = prism_hub_params(cs);

TB = struct();
TB.name  = 'TB23_R2_SALS_Link';
TB.case  = caseName;
TB.event = R0.event;
TB.dt    = P.sim.dt;
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.VA    = R0.vbat/2;                % Stage A 등가: 이상 V_bat/2 + 13.2 mΩ + 1.5 µH(TB04·TB08과 같음)
TB.Rpath = 0.0132;
TB.Lpath = 1.5e-6;
TB.Cb    = 400e-6;
TB.VW    = R0.VW;
TB.upper = R0.upper;
TB.Prated = R0.dab_rated_W;

% ---- Stage B 부품: TB08과 같고, 소자 역방향 도통만 꺼진 GaN 값으로 ------------------------------------------
TB.B = P.B;
TB.B.n      = R0.turns;              % 4.6:1
TB.B.Ldab   = R0.Ldab;               % 14.68 µH
TB.B.Goff   = 1e-8;
TB.B.Vf     = R0.Vd;                 % 2.0 V: 꺼진 GaN의 역방향 도통(수십 A). H-브리지가 꺼지면 다이오드 정류기가 된다
TB.B.Rd     = 1e-4;
TB.B.Goffd  = 1e-8;
TB.B.Coss_dp = 335e-12;              % DAB 1차 소자 C_o(tr)(TB04B·TB08과 같음)
TB.B.Coss_ds = 1371e-12;             % DAB 2차 소자 C_oss(tr)
TB.B.Coss_d = TB.B.Coss_dp;
TB.Rbyp_cell = R0.R_bypass/2;        % 바이패스 셀 = EPC2305 2병렬, 역직렬 셀 2개 = 3.3 mΩ
TB.Vf_byp  = 1.4;                    % 바이패스 셀 역방향 도통(EPC2305 V_SD)
TB.Rd_byp  = TB.Rbyp_cell;
TB.R_open  = 1e6;                    % 소프트 투입 가변 저항: 열림
TB.Rbrk    = R0.Rbrk;                % 링크 제동 저항 3 Ω
TB.Rdmp    = R0.Rdmp;                % 버스 RC 감쇠기 48.6 mΩ
TB.Cdmp    = R0.Cdmp;                % 1.6 mF
TB.sals_prm = R0.sals_prm(:)';      % 등급별 계약 응답 블록 파라미터 22개(시간 축소 반영)
TB.CA      = R0.C_A;                % V_A 노드 커패시터 400 µF(Stage A 정지 뒤 경로전류로 방전)
TB.RsaOn   = 1e-4;                  % Stage A 정지 스위치: 동작 0.1 mΩ, 정지 1 MΩ
TB.RsaOff  = 1e6;

% ---- 초기조건 ---------------------------------------------------------------------------------------
x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
TB.vcd0 = R0.vcd0;
TB.st0  = R0.st0;
TB.byp0 = double(R0.st0 ~= 3);       % 바이패스로 시작(켬 사례)이면 주 스위치 켬
m0 = R0.u0(1); il0 = R0.u0(2);
TB.P0 = R0.P0; TB.P1 = R0.P0; TB.t_step = 1e30; TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

% ---- 제어기(TB08과 같음) + 상태기계 + 보호 ------------------------------------------------------------------
prm = P.ctrl_prm;
prm(9)  = TB.VW;
prm(14) = TB.Prated;
prm(17) = R0.Ldab;
prm(19) = R0.turns;
TB.ctrl_prm  = prm;
TB.ctrl_tab  = P.ctrl_tab;
TB.ctrl_init = [R0.q0 0 m0 il0];
TB.smp       = [TB.dt TB.Np];
TB.delay_steps = P.delay_steps;
TB.uc0       = [m0; 0];
TB.gate_prm  = P.gateB_prm;
TB.gate_init = [m0 0 il0];
TB.loss_prm  = [TB.dt TB.Np R0.eta TB.B.Rdab];
TB.ploss0    = 0;
TB.sup_prm   = R0.sup_prm(:)';                       % 상태기계 파라미터 69개(SALS 모드, E17·E29와 같은 값)
ET = jsondecode(fileread(fullfile(refDir, 'TB23_eps_table.json')));   % EPS 지령표(j ≤ 0, 검증 코드 dab_modulation.py)
TB.eps_prm   = R0.eps_prm(:)';                       % [켬 n L_dab f_s 첨두상한 r0 dr j0 dj]
TB.eps_d     = ET.d;                                  % 1차 펄스 폭 [rad], 71 × 79
TB.eps_phi   = ET.phi;                                % 등가 위상 [rad]
TB.eps_pk    = ET.pk;                                 % 정규화 첨두(스위칭 반영, E21)
TB.pk_max    = R0.pk_max;                             % 설계 상한 1.387 × 정격점 첨두 [A](판정은 1.5배)
TB.rated_pk  = R0.rated_pk;
TB.prot_prm  = [TB.dt R0.prot_prm(:)'];             % [dt T_HW I_HW VL_HW VS_HW 상한 고장종류 고장시각 T_GDF 두번째고장시각]

TB.guard_t    = 1.5*TB.dt;
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
