function files = sl_export_png(sysList, outDir)
%SL_EXPORT_PNG  모델(또는 서브시스템) 회로도를 PNG로 저장한다(문서·검토용).
%   files = sl_export_png({'TB01_StageA_RSC', 'TB01_StageA_RSC/StageA_Phase1'}, 'results')
if ~exist(outDir, 'dir'), mkdir(outDir); end
files = {};
for k = 1:numel(sysList)
    s = sysList{k};
    f = fullfile(outDir, [strrep(s, '/', '__') '.png']);
    open_system(s);
    print(['-s' s], '-dpng', '-r150', f);
    files{end+1} = f; %#ok<AGROW>
end
end
