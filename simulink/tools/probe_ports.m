function probe_ports()
%PROBE_PORTS  여러 포트를 가진 Simscape 블록의 포트 이름·종류를 순서대로 기록한다(결선 도우미 작성용).
blks = { ...
    'fl_lib/Electrical/Electrical Elements/Switch'
    'fl_lib/Electrical/Electrical Elements/Diode'
    'fl_lib/Electrical/Electrical Elements/Capacitor'
    'fl_lib/Electrical/Electrical Elements/Ideal Transformer'
    'fl_lib/Electrical/Electrical Sources/DC Voltage Source'
    'fl_lib/Electrical/Electrical Sources/Controlled Current Source'
    'fl_lib/Electrical/Electrical Sources/Controlled Voltage Source'
    'fl_lib/Electrical/Electrical Sensors/Current Sensor'
    'fl_lib/Electrical/Electrical Sensors/Voltage Sensor'
    };
load_system('fl_lib');
mdl = 'probe_tmp2';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
for k = 1:numel(blks)
    h = add_block(blks{k}, sprintf('%s/b%d', mdl, k));
    pp = simscape.connectionPortProperties(h);
    fprintf('== %s\n', blks{k});
    for j = 1:numel(pp)
        try, ty = char(string(pp(j).Type)); catch, ty = class(pp(j).Type); end
        fprintf('  %d name=%s label=%s type=%s class=%s\n', j, char(pp(j).Name), char(string(pp(j).Label)), ty, class(pp(j).Type));
    end
end
close_system(mdl, 0);
end
