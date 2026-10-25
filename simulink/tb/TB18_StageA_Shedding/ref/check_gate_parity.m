%CHECK_GATE_PARITY  셰딩 게이트(ctrl/prism_gate_stageA_zcps.m)가 검증 코드 E24(model_stage_a.shed_step + 영교차 추종)와
%   같은 논리인지 확인한다. make_ref_TB18.py가 남긴 사례 F의 간격별 게이트 입력 전류(데드타임 소멸 처리 전)를 넣고,
%   게이트가 내는 위상별 구간·셰딩 모드를 파이썬 모델의 값과 간격마다 비교한다. MATLAB·Octave 공용.
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', 'ctrl'));
d = fullfile(here, 'gate_parity');
prm = load(fullfile(d, 'prm.txt')); off = load(fullfile(d, 'off.txt')); S = csvread(fullfile(d, 'seq.csv'));
n = size(S, 1); en = [1 1 0 0 0 0 0 0];
clear prism_gate_stageA_zcps
st = zeros(n, 2); sm = zeros(n, 1);
for k = 1:n
    [~, so, sh] = prism_gate_stageA_zcps(S(k, 1), [S(k, 2); S(k, 3); zeros(6, 1)], prm, en, off);
    st(k, :) = so(1:2)'; sm(k) = sh(1);
end
d1 = sum(st(:, 1) ~= S(:, 4)); d2 = sum(st(:, 2) ~= S(:, 5)); d3 = sum(sm ~= S(:, 6));
verd = 'FAIL'; if d1 + d2 + d3 == 0, verd = 'PASS'; end
fid = fopen(fullfile(here, 'check_gate_parity.txt'), 'w');
for f = [1 fid]
    fprintf(f, 'gate parity (case F, %d steps): mismatch phase1 %d, phase2 %d, shed mode %d -> %s\n', n, d1, d2, d3, verd);
end
fclose(fid);
