function h = sl_mfunc(sys, name, pos, srcFile)
%SL_MFUNC  MATLAB Function 블록을 만들고 코드 파일 내용을 그대로 넣는다.
%
%   h = sl_mfunc(sys, 'StageA_Gate', [x1 y1 x2 y2], 'prism_gate_stageA.m')
%
%   코드를 파일 참조가 아니라 블록 안에 복사해 넣으므로 모델 파일만으로 동작한다(제출물 자족성).
%   원본은 ctrl/ 폴더의 .m 파일이며, 빌드할 때마다 최신 원본으로 다시 채운다.

h = add_block('simulink/User-Defined Functions/MATLAB Function', [sys '/' name], 'Position', pos);
rt = sfroot;
ch = rt.find('-isa', 'Stateflow.EMChart', 'Path', [sys '/' name]);
if isempty(ch)
    error('sl_mfunc:chart', 'MATLAB Function chart not found: %s/%s', sys, name);
end
ch.Script = fileread(which(srcFile));
end
