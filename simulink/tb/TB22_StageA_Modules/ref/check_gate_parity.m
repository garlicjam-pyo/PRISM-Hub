%CHECK_GATE_PARITY  4모듈 게이트(ctrl/prism_gate_stageA_zcpm.m)가 검증 코드 E28(model_stage_a.mgr_step + 영교차 추종
%   + 방향 반전 처리)과 같은 논리인지 확인한다. make_ref_TB22.py가 남긴 사례 MC(800 V 충전 시작·종료, 사전 기동)의
%   간격별 게이트 입력 전류(데드타임 소멸 처리 전)와 충전 요청을 넣고, 게이트가 내는 위상별 구간·동작 모듈 수·모듈 모드를
%   파이썬 모델의 값과 간격마다 비교한다. MATLAB·Octave 공용.
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', 'ctrl'));
d = fullfile(here, 'gate_parity');
prm = load(fullfile(d, 'prm.txt')); off = load(fullfile(d, 'off.txt')); S = csvread(fullfile(d, 'seq.csv'));
n = size(S, 1); en = ones(1, 8);
clear prism_gate_stageA_zcpm
st = zeros(n, 8); na = zeros(n, 1); mm = zeros(n, 4);
for k = 1:n
    [~, so, mg] = prism_gate_stageA_zcpm(S(k, 1), S(k, 2:9)', prm, S(k, 23), en, off);
    st(k, :) = so'; na(k) = mg(1); mm(k, :) = mg(2:5)';
end
dst = sum(st ~= S(:, 10:17)); dna = sum(na ~= S(:, 18)); dmm = sum(mm ~= S(:, 19:22));
verd = 'FAIL'; if sum(dst) + dna + sum(dmm) == 0, verd = 'PASS'; end
fid = fopen(fullfile(here, 'check_gate_parity.txt'), 'w');
for f = [1 fid]
    fprintf(f, 'gate parity (case MC, %d steps): mismatch phases [%s], active modules %d, module modes [%s] -> %s\n', ...
        n, num2str(dst), dna, num2str(dmm), verd);
end
fclose(fid);
