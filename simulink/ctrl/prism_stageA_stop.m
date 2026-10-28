function R = prism_stageA_stop(code, prm)
%#codegen
%PRISM_STAGEA_STOP  Stage A 협조 정지 스위치(TB23): 보호 상태기계 비트 명령 16(Stage A 정지)이면 V_A 등가 전원을 끊는다.
%
%   Stage A는 이상 전원 V_bat/2로 등가했다. 정지하면 모든 위상이 자연 턴오프로 꺼지고 V_A 노드는 출력 커패시터 C_A만 남는다
%   (검증 코드 E17 r2_run의 astop: V_A = C_A가 경로전류로 방전). 이 블록은 전원과 C_A 노드 사이 가변 저항 값을 낸다.
%   입력  code  상태기계 s(10)(SALS 모드 비트 명령), prm [R_on R_off] [Ω]
%   출력  R     R_on(동작) 또는 R_off(정지)
c = round(code);
if mod(floor(c/16), 2) >= 1
    R = prm(2);
else
    R = prm(1);
end
end
