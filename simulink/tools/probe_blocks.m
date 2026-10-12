function probe_blocks()
%PROBE_BLOCKS  빌드 스크립트 작성 전 사전 조사: 사용할 라이브러리 블록의 경로, 포트 이름, 대화상자 파라미터를 기록한다.
%
%   Simscape 블록의 포트 이름(p, n 등)과 파라미터 이름은 릴리스마다 다를 수 있으므로,
%   실제 설치(R2025a)에서 한 번 조사해 그 결과에 맞춰 결선·설정 코드를 쓴다.
%   결과는 prism_run이 logs/probe_blocks.log에 남긴다.

fprintf('MATLAB %s\n', version);
v = ver;
for k = 1:numel(v)
    if any(strcmp(v(k).Name, {'Simulink', 'Simscape', 'Simscape Electrical', 'Stateflow'}))
        fprintf('  %s %s\n', v(k).Name, v(k).Version);
    end
end
fprintf('simscape.addConnection: %d\n', exist('simscape.addConnection') > 0); %#ok<EXIST>
fprintf('simscape.connectionPortProperties: %d\n', exist('simscape.connectionPortProperties') > 0); %#ok<EXIST>

load_system('fl_lib'); load_system('nesl_utility');
try
    load_system('ee_lib'); fprintf('ee_lib loaded\n');
catch e
    fprintf('ee_lib not loaded: %s\n', e.message);
end

blks = { ...
    'fl_lib/Electrical/Electrical Elements/Resistor'
    'fl_lib/Electrical/Electrical Elements/Capacitor'
    'fl_lib/Electrical/Electrical Elements/Inductor'
    'fl_lib/Electrical/Electrical Elements/Switch'
    'fl_lib/Electrical/Electrical Elements/Diode'
    'fl_lib/Electrical/Electrical Elements/Ideal Transformer'
    'fl_lib/Electrical/Electrical Elements/Electrical Reference'
    'fl_lib/Electrical/Electrical Sources/DC Voltage Source'
    'fl_lib/Electrical/Electrical Sources/DC Current Source'
    'fl_lib/Electrical/Electrical Sources/Controlled Current Source'
    'fl_lib/Electrical/Electrical Sources/Controlled Voltage Source'
    'fl_lib/Electrical/Electrical Sensors/Current Sensor'
    'fl_lib/Electrical/Electrical Sensors/Voltage Sensor'
    'nesl_utility/Simulink-PS Converter'
    'nesl_utility/PS-Simulink Converter'
    'nesl_utility/Solver Configuration'
    'nesl_utility/Connection Port'
    };

mdl = 'probe_tmp';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
for k = 1:numel(blks)
    fprintf('\n== %s\n', blks{k});
    try
        h = add_block(blks{k}, sprintf('%s/b%d', mdl, k));
    catch e
        fprintf('  ADD FAILED: %s\n', e.message);
        % 같은 이름의 블록을 라이브러리에서 찾아 대체 경로를 제시
        [~, nm] = fileparts(blks{k});
        cand = find_system({'fl_lib', 'nesl_utility'}, 'LookUnderMasks', 'all', 'FollowLinks', 'on', 'Name', nm);
        fprintf('  candidates: %s\n', strjoin(cand', ' | '));
        continue
    end
    ph = get_param(h, 'PortHandles');
    fprintf('  PortHandles: LConn=%d RConn=%d Inport=%d Outport=%d\n', ...
        numel(ph.LConn), numel(ph.RConn), numel(ph.Inport), numel(ph.Outport));
    try
        pp = simscape.connectionPortProperties(h);
        fprintf('%s', evalc('disp(pp)'));
    catch e
        fprintf('  connectionPortProperties failed: %s\n', e.message);
    end
    dp = get_param(h, 'DialogParameters');
    if isstruct(dp)
        fn = fieldnames(dp);
        for j = 1:numel(fn)
            try
                val = get_param(h, fn{j});
                if ~ischar(val), val = mat2str(val); end
            catch
                val = '?';
            end
            fprintf('  %-28s = %s\n', fn{j}, val);
        end
    end
end
close_system(mdl, 0);

% MATLAB Function 블록 내용 주입 경로 확인(Stateflow API)
mdl2 = 'probe_mf';
if bdIsLoaded(mdl2), close_system(mdl2, 0); end
new_system(mdl2);
add_block('simulink/User-Defined Functions/MATLAB Function', [mdl2 '/F']);
rt = sfroot;
ch = rt.find('-isa', 'Stateflow.EMChart', 'Path', [mdl2 '/F']);
fprintf('\nEMChart found: %d\n', numel(ch));
if ~isempty(ch)
    ch.Script = sprintf('function y = f(u)\n%%#codegen\ny = 2*u;\n');
    fprintf('EMChart script set OK\n');
end
close_system(mdl2, 0);
end
