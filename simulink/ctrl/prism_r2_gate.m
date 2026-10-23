function gb = prism_r2_gate(g, mode)
%#codegen
%PRISM_R2_GATE  R2 창 조정 모듈의 게이트 재정의(TB08): 게이트 생성기 출력을 운전 모드에 맞게 바꾸고 바이패스 게이트를 더한다.
%
%  입력  g     게이트 생성기 출력 [A상측 A하측 B상측 B하측 | P1 P2 P3 P4 | S1 S2 S3 S4] (ctrl/prism_gate_stageB.m)
%        mode  운전 모드(ctrl/prism_r2_sequence.m: 0 제어, 1 DAB 고장, 2 영벡터, 3 바이패스, 4 바이패스 + 영벡터)
%  출력  gb    [g 12개(재정의 후); 바이패스 게이트]
%  영벡터는 H-브리지 두 레그의 하측 소자를 켜는 상태다(A하측·B하측). 하드웨어에서는 게이트 구동기 수준의
%  재정의에 해당하므로 제어기의 전달지연(5 µs)을 거치지 않는다.

gb = [g(:); 0];
md = round(mode);
if md == 1                       % DAB 고장: DAB 1·2차 게이트 끔
    gb(5:12) = 0;
elseif md == 2                   % 영벡터: H-브리지 하측 두 소자, DAB 끔
    gb(1:4) = [0; 1; 0; 1];
    gb(5:12) = 0;
elseif md == 3                   % 바이패스: 바이패스 켬, H-브리지·DAB 전 소자 끔
    gb(1:12) = 0;
    gb(13) = 1;
elseif md == 4                   % 바이패스 + 영벡터(켜기 전 준비 상태)
    gb(1:4) = [0; 1; 0; 1];
    gb(5:12) = 0;
    gb(13) = 1;
end
end
