function prism_watch(action)
%PRISM_WATCH  작업 대기열 감시기: queue/ 폴더의 *.job 파일을 읽어 패키지 함수를 차례로 실행한다.
%
%   prism_watch          % 감시 시작(3초마다 확인)
%   prism_watch('stop')  % 감시 중지
%
%   *.job 파일 내용은 실행할 함수 이름 한 줄이다(예: build_TB01). 영문·숫자·밑줄만 허용하고,
%   이 패키지 경로 안에 있는 함수만 실행한다(임의 명령 실행 방지). 실행은 prism_run을 거치므로
%   결과는 logs/<함수>.log, 완료 표시는 logs/<함수>.done에 남는다.
%   처리한 작업 파일은 queue/done/으로 옮긴다. 화면이 잠겨도 MATLAB이 켜져 있으면 계속 동작한다.

if nargin < 1, action = 'start'; end
root = fileparts(mfilename('fullpath'));
old = timerfindall('Tag', 'prism_watch');
if ~isempty(old), stop(old); delete(old); end
if strcmp(action, 'stop')
    fprintf('prism_watch stopped\n');
    return
end
q = fullfile(root, 'queue');
if ~exist(fullfile(q, 'done'), 'dir'), mkdir(fullfile(q, 'done')); end
t = timer('Tag', 'prism_watch', 'Period', 3, 'ExecutionMode', 'fixedSpacing', ...
    'BusyMode', 'drop', 'TimerFcn', @(~, ~) poll(root, q));
start(t);
fprintf('prism_watch started: %s\n', q);
end

function poll(root, q)
jobs = dir(fullfile(q, '*.job'));
if isempty(jobs), return; end
[~, order] = sort([jobs.datenum]);
j = jobs(order(1));
src = fullfile(q, j.name);
try
    name = strtrim(fileread(src));
catch
    return
end
movefile(src, fullfile(q, 'done', [char(datetime('now', 'Format', 'yyyyMMdd_HHmmss')) '_' j.name]));
if isempty(regexp(name, '^[A-Za-z][A-Za-z0-9_]*$', 'once'))
    fprintf('prism_watch: rejected job "%s"\n', name);
    return
end
addpath(root, fullfile(root, 'ctrl'), fullfile(root, 'lib'), fullfile(root, 'tools'));
addpath(genpath(fullfile(root, 'tb')));      % 새로 추가된 테스트벤치 폴더도 찾도록 매번 갱신
loc = which(name);
if isempty(loc) || ~startsWith(loc, root)
    fprintf('prism_watch: "%s" is not a function in this package\n', name);
    return
end
fprintf('prism_watch: running %s\n', name);
prism_run(name);
end
