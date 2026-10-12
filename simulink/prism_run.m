function prism_run(fname, varargin)
%PRISM_RUN  작업 함수를 실행하고 명령창 출력과 오류를 logs/<fname>.log에 기록한다.
%
%   prism_run('build_TB01')            % 테스트벤치 빌드
%   prism_run('run_TB01')              % 시뮬레이션 + 후처리
%
%   - 패키지 폴더(이 파일 위치)와 ctrl, lib, tools, tb 하위 폴더를 경로에 더한다.
%   - 실행이 끝나면(성공·실패 모두) logs/<fname>.done 표시 파일을 남겨 완료 여부를 밖에서 확인할 수 있게 한다.
%   - 오류가 나도 MATLAB 세션은 멈추지 않고 보고서를 로그에 남긴다.
%   로그 문구는 문자 인코딩 문제를 피하려고 영문으로 쓴다(코드 주석은 한글).

root = fileparts(mfilename('fullpath'));
addpath(root, fullfile(root, 'ctrl'), fullfile(root, 'lib'), fullfile(root, 'tools'));
addpath(genpath(fullfile(root, 'tb')));
% 밖에서 고친 파일을 확실히 다시 읽도록 패키지 함수를 메모리에서 지운다(자기 자신은 제외).
rehash path;
pk = [dir(fullfile(root, '*.m')); dir(fullfile(root, 'lib', '*.m')); dir(fullfile(root, 'ctrl', '*.m')); ...
      dir(fullfile(root, 'tools', '*.m')); dir(fullfile(root, 'tb', '**', '*.m'))];
for k = 1:numel(pk)
    nm = erase(pk(k).name, '.m');
    if ~any(strcmp(nm, {'prism_run', 'prism_watch'})), clear(nm); end
end
logdir = fullfile(root, 'logs');
if ~exist(logdir, 'dir'), mkdir(logdir); end
logf  = fullfile(logdir, [fname '.log']);
donef = fullfile(logdir, [fname '.done']);
if exist(logf, 'file'),  delete(logf);  end
if exist(donef, 'file'), delete(donef); end

diary(logf);
t0 = tic;
fprintf('[prism_run] %s start %s\n', fname, char(datetime('now')));
ok = false;
try
    feval(fname, varargin{:});
    ok = true;
catch err
    fprintf('[prism_run] ERROR\n%s\n', getReport(err, 'extended', 'hyperlinks', 'off'));
end
fprintf('[prism_run] %s %s (%.1f s)\n', fname, ternary(ok, 'finished', 'FAILED'), toc(t0));
diary off;

fid = fopen(donef, 'w');
fprintf(fid, '%s %s\n', ternary(ok, 'OK', 'FAIL'), char(datetime('now')));
fclose(fid);
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
