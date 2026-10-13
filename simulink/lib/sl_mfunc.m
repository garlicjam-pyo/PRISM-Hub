function h = sl_mfunc(sys, name, pos, srcFile)
%SL_MFUNC  MATLAB Function 블록을 만들고 코드 파일 내용을 그대로 넣는다.
%
%   h = sl_mfunc(sys, 'StageA_Gate', [x1 y1 x2 y2], 'prism_gate_stageA.m')
%
%   h = sl_mfunc(sys, 'Controller', pos, {'prism_ctrl_sampler.m', 'prism_stageB_controller.m'})
%       여러 파일을 주면 차례로 이어 붙인다(첫 파일이 블록의 진입 함수, 나머지는 지역 함수).
%   코드를 파일 참조가 아니라 블록 안에 복사해 넣으므로 모델 파일만으로 동작한다(제출물 자족성).
%   원본은 ctrl/ 폴더의 .m 파일이며, 빌드할 때마다 최신 원본으로 다시 채운다.

h = add_block('simulink/User-Defined Functions/MATLAB Function', [sys '/' name], 'Position', pos);
rt = sfroot;
ch = rt.find('-isa', 'Stateflow.EMChart', 'Path', [sys '/' name]);
if isempty(ch)
    error('sl_mfunc:chart', 'MATLAB Function chart not found: %s/%s', sys, name);
end
if ischar(srcFile), srcFile = {srcFile}; end
code = '';
for k = 1:numel(srcFile)
    code = [code fileread(which(srcFile{k})) newline]; %#ok<AGROW>
end
ch.Script = code;
end
