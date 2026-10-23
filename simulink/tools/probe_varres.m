function probe_varres()
%PROBE_VARRES  TB09 작성 전 조사: Variable Resistor(가변 저항) 블록의 경로·포트·파라미터 이름.
load_system('fl_lib');
cands = {'fl_lib/Electrical/Electrical Elements/Variable Resistor'};
for k = 1:numel(cands)
    b = cands{k};
    if ~bdIsLoaded('probe_vr'), new_system('probe_vr'); end
    h = add_block(b, sprintf('probe_vr/VR%d', k));
    fprintf('%s\n', b);
    dp = get_param(h, 'DialogParameters'); fn = fieldnames(dp);
    for j = 1:numel(fn)
        try, v = get_param(h, fn{j}); catch, v = '?'; end
        if ~ischar(v), v = mat2str(v); end
        fprintf('  param %s = %s\n', fn{j}, v);
    end
    ph = get_param(h, 'PortHandles');
    fprintf('  LConn %d RConn %d\n', numel(ph.LConn), numel(ph.RConn));
    try
        pp = simscape.connectionPortProperties(h);   % R2025a
        for j = 1:numel(pp), fprintf('  port %s\n', pp(j).Name); end
    catch e
        fprintf('  connectionPortProperties: %s\n', e.message);
    end
end
bdclose('all');
end
