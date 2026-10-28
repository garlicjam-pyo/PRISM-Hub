function h = build_stageA_module(sys, name, pos, m, A, coss)
%BUILD_STAGEA_MODULE  Stage A 한 모듈(2위상 2:1 공진 스위치드 커패시터) 서브시스템을 만든다.
%
%   h = build_stageA_module(sys, 'StageA_Module1', [x1 y1 x2 y2], 1, 'TB.A')
%
%   외부 포트: VIN(배터리 +), GND(배터리 −), VOUT(V_A 노드)
%   내부: 위상 2개(build_stageA_phase)를 VIN·GND·VOUT에 병렬로 잇는다. 모듈 m의 위상 번호는 2m−1, 2m이다.
%   두 위상은 게이트 생성기에서 반주기/2(= T/4) 엇갈려 동작한다(인터리빙 → V_A 리플 저감).
%   게이트 태그 gA_P<k>_S<n>, 계측 태그 iA_P<k>(공진전류), vCf_P<k>(C_fly 전압)는 위상 서브시스템이 만든다.
%   A : 파라미터 구조체 이름(문자열, 예 'TB.A')
%   coss : (TB26, 선택) 스위치 셀 출력용량 식(예 'TB.A.Coss'). 없으면 출력용량 없음(TB06–TB24와 같음).

if nargin < 6, coss = ''; end
mod = [sys '/' name];
h = add_block('built-in/Subsystem', mod, 'Position', pos);
add_block('nesl_utility/Connection Port', [mod '/VIN'],  'Position', [30 160 60 180],  'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [mod '/GND'],  'Position', [30 520 60 540],  'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [mod '/VOUT'], 'Position', [640 340 670 360], 'Side', 'Right', 'Port', '3');
k1 = 2*m - 1; k2 = 2*m;
build_stageA_phase(mod, sprintf('StageA_Phase%d', k1), [200 100 380 260], k1, A, coss);
build_stageA_phase(mod, sprintf('StageA_Phase%d', k2), [200 380 380 540], k2, A, coss);
for k = [k1 k2]
    ph = sprintf('StageA_Phase%d', k);
    sl_pc(mod, ph, 'VIN',  'VIN',  'port');
    sl_pc(mod, ph, 'GND',  'GND',  'port');
    sl_pc(mod, ph, 'VOUT', 'VOUT', 'port');
end
sl_note(mod, sprintf(['Stage A 모듈 %d: 위상 %d·%d 병렬(목표 정격 37.5 kW)\n' ...
    '각 위상은 영교차 추종 게이트로 자기 공진전류가 0일 때 끈다(ZCS). 두 위상은 T/4 엇갈려 시작한다.'], m, k1, k2), ...
    [30 600 640 640], 'box');
set_param(h, 'BackgroundColor', 'white');
end
