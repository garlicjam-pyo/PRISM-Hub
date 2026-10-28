function check_gate_parity_TB27()
%CHECK_GATE_PARITY_TB27  모듈 고장 처리 게이트(ctrl/prism_gate_stageA_zcpf.m)가 검증 코드 E35(A25R, model_stage_a.mgr_fault + 일반화한
%   mgr_step + 영교차 추종)과 같은 논리인지 확인한다. make_ref_TB27.py가 남긴 사례 FA(800 V 주행, 모듈 1 고장 → 모듈 2)와
%   FF(800 V 충전, 모듈 1 고장 → 3모듈)의 간격별 게이트 입력 전류(데드타임 소멸 처리 전)와 충전 요청을 넣고, 게이트가 내는
%   위상별 구간·동작 모듈 수·모듈 모드를 파이썬 모델의 값과 간격마다 비교한다.
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', 'ctrl'));
cases = {'FF27_800V_charge_m1', 'MC27_800V_charge_slow', 'MA27_540V_bus_5_15_5kW', 'SC27_800V_charge_steady'};
fid = fopen(fullfile(here, 'check_gate_parity_TB27.txt'), 'w');
allok = true;
for c = 1:numel(cases)
    d = fullfile(here, 'gate_parity', cases{c});
    prm = load(fullfile(d, 'prm.txt')); off = load(fullfile(d, 'off.txt')); S = readmatrix(fullfile(d, 'seq.csv'));
    n = size(S, 1); en = ones(1, 8);
    clear prism_gate_stageA_zcpf
    st = zeros(n, 8); na = zeros(n, 1); mm = zeros(n, 4);
    for k = 1:n
        [~, so, mg] = prism_gate_stageA_zcpf(S(k, 1), S(k, 2:9)', prm, S(k, 23), en, off);
        st(k, :) = so'; na(k) = mg(1); mm(k, :) = mg(2:5)';
    end
    dst = sum(st ~= S(:, 10:17)); dna = sum(na ~= S(:, 18)); dmm = sum(mm ~= S(:, 19:22));
    ok = sum(dst) + dna + sum(dmm) == 0; allok = allok && ok;
    verd = 'FAIL'; if ok, verd = 'PASS'; end
    for f = [1 fid]
        fprintf(f, 'gate parity (case %s, %d steps, fault module %d at step %d): mismatch phases [%s], active modules %d, module modes [%s] -> %s\n', ...
            cases{c}, n, prm(22), prm(23), num2str(dst), dna, num2str(dmm), verd);
    end
end
verd = 'FAIL'; if allok, verd = 'PASS'; end
for f = [1 fid], fprintf(f, 'gate parity overall: %s\n', verd); end
fclose(fid);
end
