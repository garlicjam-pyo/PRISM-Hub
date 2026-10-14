function sl_startup_guard(sys, name, pos, initExpr, T, cpos)
%SL_STARTUP_GUARD  측정 신호의 시작 표본 보호: 처음 두 간격(t < 1.5·dt)에는 평형점 값을 내보낸다.
%
%   sl_startup_guard(sys, 'Startup_guard', [x1 y1 x2 y2], 'TB.meas0', 'TB')
%
%   Simscape 지역 해석기의 첫 출력 표본(t = 0)은 초기화 계산 중의 값이라 물리량이 아니다
%   (TB04 진단: v_bus 199.5 V, 링크전류 −3.3e7 A가 한 표본 나타난 뒤 다음 간격부터 정상).
%   디지털 제어기·게이트 생성기·손실 모델이 이 값을 표본하면 적분기와 주기 평균이 오염되므로,
%   Switch 블록으로 t ≥ T.guard_t(= 1.5·dt)일 때만 측정값을 통과시키고 그 전에는 initExpr 상수를 쓴다.
%   실제 장치에서는 ADC가 기동 직후 값을 버리는 것과 같은 처리이며, 그 뒤의 동작에는 영향이 없다.
%
%   포트: 1 = 측정 신호(스칼라 또는 벡터), 2 = 시각(Digital Clock 또는 From 't'), 3 = 초기값(이 함수가 만든다)
%   생성 블록: sys/name(Switch), sys/[name '_init'](Constant, 위치 cpos — 생략하면 Switch 왼쪽 아래)

sl_add(sys, 'simulink/Signal Routing/Switch', name, pos, ...
    'Criteria', 'u2 >= Threshold', 'Threshold', [T '.guard_t']);
if nargin < 6 || isempty(cpos)
    cpos = [pos(1) - 110, pos(4) + 15, pos(1) - 20, pos(4) + 35];
end
sl_add(sys, 'simulink/Sources/Constant', [name '_init'], cpos, 'Value', initExpr);
sl_line(sys, [name '_init/1'], [name '/3']);
end
