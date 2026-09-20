%% build_rsc_phase.m -- Simulink/Simscape Electrical 모델 자동 생성: rsc_phase + TB-A1 하네스
%  사용: >> prism_design_params;  >> build_rsc_phase
%  결과: models/rsc_phase_tb.slx (블록 배치·파라미터·배선). 라이브러리 블록 경로/파라미터명은
%  R2025a 기준이며 버전에 따라 다를 수 있으므로, 실패한 항목은 명령창에 "수동 처리 목록"으로 출력한다.
%  생성 후 반드시 4.3.1의 넷리스트(아래 주석)와 대조하여 배선을 확인할 것.
%
%  넷리스트 (노드: VIN, A, B, VOUT, GND)
%    S1: D=VIN, S=A      S2: D=A,   S=VOUT
%    S3: D=VOUT, S=B     S4: D=B,   S=GND
%    Lr: A -> N1 ;  Cfly: N1 -> B  (Lr와 Cfly 직렬, 방향 무관)
%    Rmisc: 경로 직렬 (Lr 앞)
%    Vsrc: VIN-GND ;  Cout: VOUT-GND ;  Rload: VOUT-GND ;  Isens: VOUT 경로
if ~exist('P','var'), error('먼저 prism_design_params 를 실행하세요.'); end
mdl = 'rsc_phase_tb'; if bdIsLoaded(mdl), close_system(mdl,0); end
new_system(mdl); open_system(mdl);
set_param(mdl,'StopTime','2e-3','SolverType','Variable-step','Solver','ode23t', ...
              'RelTol','1e-5','MaxStep','5e-9');
manual = {};   % 수동 처리 목록
addb = @(lib,name,pos) add_block(lib,[mdl '/' name],'Position',pos,'MakeNameUnique','on');
setp = @(name,varargin) set_param([mdl '/' name],varargin{:});

% ---- 1. 전기 소자 ----------------------------------------------------------
blk.Vsrc  = addb('fl_lib/Electrical/Electrical Sources/DC Voltage Source','Vbat',[50 300 80 330]);
blk.gnd   = addb('fl_lib/Electrical/Electrical Elements/Electrical Reference','GND',[50 420 80 440]);
blk.Cfly  = addb('fl_lib/Electrical/Electrical Elements/Capacitor','Cfly',[330 250 360 280]);
blk.Lr    = addb('fl_lib/Electrical/Electrical Elements/Inductor','Lr',[330 190 360 220]);
blk.Rm    = addb('fl_lib/Electrical/Electrical Elements/Resistor','Rmisc',[330 130 360 160]);
blk.Cout  = addb('fl_lib/Electrical/Electrical Elements/Capacitor','Cout',[600 300 630 330]);
blk.Rload = addb('fl_lib/Electrical/Electrical Elements/Resistor','Rload',[660 300 690 330]);
blk.Isen  = addb('fl_lib/Electrical/Electrical Sensors/Current Sensor','I_out',[540 200 570 230]);
blk.Vsen  = addb('fl_lib/Electrical/Electrical Sensors/Voltage Sensor','V_out',[720 300 750 330]);
blk.Icsen = addb('fl_lib/Electrical/Electrical Sensors/Current Sensor','I_C',[330 310 360 340]);
blk.solv  = addb('nesl_utility/Solver Configuration','Solver',[50 500 80 530]);
% MOSFET: 경로 후보를 순서대로 시도
mosCand = {'ee_lib/Semiconductors & Converters/Semiconductors/MOSFET (Ideal, Switching)', ...
           'ee_lib/Semiconductors & Converters/Semiconductors/MOSFET'};
mosNames = {'S1','S2','S3','S4'}; mosPos = {[200 80 240 120],[200 380 240 420],[460 80 500 120],[460 380 500 420]};
for k=1:4
    ok=false;
    for c=1:numel(mosCand)
        try, blk.(mosNames{k}) = addb(mosCand{c},mosNames{k},mosPos{k}); ok=true; break; catch, end
    end
    if ~ok, manual{end+1} = sprintf('MOSFET %s: 라이브러리 경로를 찾지 못함 -> 수동 추가',mosNames{k}); end %#ok<AGROW>
end

% ---- 2. 파라미터 (P 구조체에서) -------------------------------------------
A = P.A;
pars = { 'Vbat','v0','788'; 'Cfly','c',num2str(A.Cfly); 'Cfly','r',num2str(A.ESRc); ...
         'Lr','l',num2str(A.Lr); 'Lr','r',num2str(A.RL); 'Rmisc','R',num2str(A.Rmisc); ...
         'Cout','c','400e-6'; 'Cout','r','2e-3'; 'Rload','R',num2str(400/A.Iph) };
for k=1:size(pars,1)
    try, setp(pars{k,1},pars{k,2},pars{k,3}); catch, manual{end+1} = sprintf('%s.%s = %s (수동 설정)',pars{k,:}); end %#ok<AGROW>
end
for k=1:4
    if isfield(blk,mosNames{k})
        mp = { 'Ron',num2str(A.Rds); 'Goff','1e-6'; 'Vth','5'; 'diode_param','2'; 'Vf_diode','0.9' };
        for j=1:size(mp,1)
            try, setp(mosNames{k},mp{j,1},mp{j,2}); catch, manual{end+1}=sprintf('%s.%s = %s (수동 설정: 온저항 6 mohm, 바디다이오드 Vf 0.9 V, Coss 150 pF 병렬 캡 추가)',mosNames{k},mp{j,1},mp{j,2}); end %#ok<AGROW>
        end
    end
end
% Cfly, Cout 초기전압 = Vin/2 (프리차지 완료 가정) : 블록 "Variables" 탭에서 vc = 394 V, 우선순위 High
manual{end+1} = 'Cfly, Cout 초기전압 394 V: 블록 다이얼로그 > Variables 탭 > Capacitor voltage = 394, Priority High';

% ---- 3. 게이트 신호 (Pulse Generator -> Simulink-PS) --------------------------
T = 1/A.fs; td = A.tdead;                       % TB-A1 결과: fs = 0.98 fr (147 kHz), tdead 100 ns
pw = 50*(1-2*td/T);
gate = { 'S1', td; 'S3', td; 'S2', T/2+td; 'S4', T/2+td };
for k=1:4
    pg = addb('simulink/Sources/Pulse Generator',['PG_' gate{k,1}],[20 60+90*k 50 90+90*k]);
    setp(['PG_' gate{k,1}],'PulseType','Time based','Amplitude','10','Period',num2str(T), ...
         'PulseWidth',num2str(pw),'PhaseDelay',num2str(gate{k,2}));
    cv = addb('nesl_utility/Simulink-PS Converter',['SPS_' gate{k,1}],[90 60+90*k 120 90+90*k]);
    try, add_line(mdl,['PG_' gate{k,1} '/1'],['SPS_' gate{k,1} '/1']); catch, end
    try, add_line(mdl,['SPS_' gate{k,1} '/RConn1'],[gate{k,1} '/LConn1']); catch, manual{end+1}=sprintf('게이트 배선 %s (SPS_%s -> %s.G)',gate{k,1},gate{k,1},gate{k,1}); end %#ok<AGROW>
end

% ---- 4. 전력 배선 (포트 인덱스: LConn1=+/D 측, RConn1=-/S 측 가정) ------------
% 실패 시 수동 목록에 넷리스트 라인으로 기록
net = { 'Vbat/LConn1','S1/RConn1',   'VIN -> S1.D';
        'S1/RConn2','Rmisc/LConn1',  'S1.S(A) -> Rmisc';
        'Rmisc/RConn1','Lr/LConn1',  'Rmisc -> Lr';
        'Lr/RConn1','I_C/LConn1',    'Lr -> I_C(+)';
        'I_C/RConn1','Cfly/LConn1',  'I_C(-) -> Cfly(+)';
        'Cfly/RConn1','S3/RConn2',   'Cfly(-)(B) -> S3.S';
        'Cfly/RConn1','S4/RConn1',   'B -> S4.D';
        'S1/RConn2','S2/RConn1',     'A -> S2.D';
        'S2/RConn2','I_out/LConn1',  'S2.S(VOUT) -> I_out(+)';
        'S3/RConn1','I_out/LConn1',  'S3.D(VOUT) -> I_out(+)';
        'I_out/RConn1','Cout/LConn1','I_out(-) -> Cout(+)';
        'Cout/LConn1','Rload/LConn1','VOUT -> Rload';
        'Cout/LConn1','V_out/LConn1','VOUT -> V_out(+)';
        'Cout/RConn1','GND/LConn1',  'Cout(-) -> GND';
        'Rload/RConn1','GND/LConn1', 'Rload(-) -> GND';
        'V_out/RConn1','GND/LConn1', 'V_out(-) -> GND';
        'S4/RConn2','GND/LConn1',    'S4.S -> GND';
        'Vbat/RConn1','GND/LConn1',  'Vbat(-) -> GND';
        'Solver/RConn1','GND/LConn1','Solver -> GND' };
for k=1:size(net,1)
    try, add_line(mdl,net{k,1},net{k,2},'autorouting','on'); catch, manual{end+1}=['배선 수동: ' net{k,3} '  (' net{k,1} ' -> ' net{k,2} ')']; end %#ok<AGROW>
end

% ---- 5. 계측 출력 (PS -> Simulink -> To Workspace) ---------------------------
meas = {'I_C','iC'; 'I_out','iout'; 'V_out','vout'};
for k=1:size(meas,1)
    psc = addb('nesl_utility/PS-Simulink Converter',['PSS_' meas{k,2}],[800 100+80*k 830 130+80*k]);
    tw  = addb('simulink/Sinks/To Workspace',['TW_' meas{k,2}],[880 100+80*k 940 130+80*k]);
    setp(['TW_' meas{k,2}],'VariableName',meas{k,2},'SaveFormat','Timeseries');
    try, add_line(mdl,[meas{k,1} '/RConn2'],['PSS_' meas{k,2} '/LConn1']); catch, manual{end+1}=sprintf('센서 출력 배선: %s 물리신호 -> PSS_%s',meas{k,1},meas{k,2}); end %#ok<AGROW>
    try, add_line(mdl,['PSS_' meas{k,2} '/1'],['TW_' meas{k,2} '/1']); catch, end
end
set_param(mdl,'SignalLogging','on','SignalLoggingName','logsout');
save_system(mdl,[mdl '.slx']);
fprintf('\n=== %s 생성 완료. 수동 처리 목록 (%d건) ===\n',mdl,numel(manual)); fprintf(' - %s\n',manual{:});
fprintf('\n검증 순서: (1) 넷리스트 대조 (2) Simscape "Check model" (3) sim 후 iC 반파정현·|i_off|/Ipk<=5%% 확인.\n');
