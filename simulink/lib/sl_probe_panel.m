function sl_probe_panel(sys, x0, y0, scopes, logs)
%SL_PROBE_PANEL  계측부: 태그로 받은 신호를 Scope와 To Workspace로 보낸다.
%
%   scopes : {'Scope 이름', {'태그1','태그2',...}; ...}   한 Scope에 여러 신호를 위아래 칸으로 표시
%   logs   : {'태그', '작업공간 변수 이름'; ...}          후처리용 저장(배열, 간격마다 1점)
%            세 번째 열을 주면 솎음 간격(예: 'TB.Np' → 제어주기마다 1점)
%
%   Scope는 시각 확인용이고, 판정은 To Workspace 데이터로 run 스크립트가 계산한다.

y = y0;
for k = 1:size(scopes, 1)
    nm = scopes{k, 1}; tags = scopes{k, 2}; n = numel(tags);
    hgt = max(60, 40*n);
    for j = 1:n
        add_block('simulink/Signal Routing/From', sprintf('%s/%s_from%d', sys, nm, j), ...
            'Position', [x0, y + 40*(j-1), x0 + 110, y + 40*(j-1) + 20], 'GotoTag', tags{j});
    end
    sc = [sys '/' nm];
    add_block('simulink/Sinks/Scope', sc, 'Position', [x0 + 170, y, x0 + 220, y + hgt - 20], ...
        'NumInputPorts', num2str(n));
    try
        cfg = get_param(sc, 'ScopeConfiguration');
        cfg.LayoutDimensions = [n, 1];
        cfg.Title = strrep(nm, '_', ' ');
        cfg.OpenAtSimulationStart = false;
        cfg.DataLogging = false;
        cfg.ShowLegend = true;
    catch
    end
    for j = 1:n
        add_line(sys, sprintf('%s_from%d/1', nm, j), sprintf('%s/%d', nm, j), 'autorouting', 'smart');
    end
    y = y + hgt + 30;
end
for k = 1:size(logs, 1)
    tg = logs{k, 1}; var = logs{k, 2};
    dec = '1';
    if size(logs, 2) >= 3 && ~isempty(logs{k, 3}), dec = logs{k, 3}; end
    add_block('simulink/Signal Routing/From', sprintf('%s/log_from_%s', sys, var), ...
        'Position', [x0, y, x0 + 110, y + 20], 'GotoTag', tg);
    add_block('simulink/Sinks/To Workspace', sprintf('%s/log_%s', sys, var), ...
        'Position', [x0 + 170, y, x0 + 260, y + 20], 'VariableName', var, 'SaveFormat', 'Array', ...
        'MaxDataPoints', 'inf', 'Decimation', dec, 'SampleTime', '-1');
    add_line(sys, sprintf('log_from_%s/1', var), sprintf('log_%s/1', var));
    y = y + 35;
end
end
