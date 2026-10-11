%% run_all_matlab.m -- MATLAB 검증 스크립트를 순서대로 실행한다.
%  E2_two_stage_crosscheck는 Python의 E2a·E2b 결과(../results/E2/*_cases.json)가 먼저 있어야 한다.
%  실행   >> cd matlab ; run_all_matlab
E1_stage_a_zcs;           % [E1] Stage A 스위칭 ODE (수 분)
E2_two_stage_crosscheck;  % [E2] Stage B 평균모델 독립 구현 대조 (MATLAB 수 분, Octave 약 1시간)
E10_stage_c_cllc;         % [E10] Stage C CLLC 스위칭 ODE (수 분)
E11_controller_crosscheck;% [E11] 채택 제어기 교차검증 (python E11 export 후, MATLAB 수 분, Octave 약 10분)
