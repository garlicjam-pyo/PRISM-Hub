function export_TB07_png()
%EXPORT_TB07_PNG  TB07 회로도 그림(최상위, Stage A 모듈 1, 게이트, 충전기 지령)을 results/에 다시 내보낸다.
here = fileparts(mfilename('fullpath'));
mdl = 'TB07_Integrated_Charging';
run(fullfile(here, 'TB07_init.m'));
load_system(fullfile(here, [mdl '.slx']));
sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/Gate_StageA'], [mdl '/Charger_Profile']}, fullfile(here, 'results'));
end
