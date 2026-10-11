function E11_controller_crosscheck(groups)
% E11_CONTROLLER_CROSSCHECK  [E11] 채택 제어기(연산 지연 보상)의 MATLAB 독립 구현 교차검증
%
%  목적   E5-E7의 채택 설계 결과는 Python 구현 하나에서만 나왔다. 같은 조건을 독립 구현
%         (prism_stage_b_batch.m: 플랜트·제어기·판정, prism_gain_acker.m: 이득 설계)으로 다시 계산해
%         판정과 지표를 대조한다. 비교 설계도 같은 코드로 다시 계산해 설계 간 차이도 확인한다.
%  입력   ../results/E11/cases_*.json  (python/E11_controller_crosscheck.py export 가 생성)
%         조건(전압, 부하, 플랜트 파라미터, 적분간격)만 공유하고 이득은 여기서 다시 계산한다.
%  방법   사례를 벡터로 묶어 한 번에 적분(시간 방향 순차, 사례 방향 벡터화). 판정은
%         Tier-1: 전압 품질 6항목 + 포트 한계 + 경로·필터 <= 90 A + 내부 진동 검사
%         Tier-2: 완료 + 포트 한계 + <= 93.75 A + 버스 384-416 V + 최종 +-4 V + 내부 진동 검사
%  실행   >> cd matlab ; E11_controller_crosscheck            (전체, Octave 약 1-2시간)
%         >> E11_controller_crosscheck({'grid'})              (일부 그룹)
%  결과   ../results/E11/matlab_gain.json, matlab_<그룹>_<설계>.json
%         이후 python/E11_controller_crosscheck.py compare 로 Python 결과와 대조한다.

if nargin<1
    groups={'grid','delay_adopted','delay_reference','corners','corners_lh5','sequences'};
end
here=fileparts(mfilename('fullpath')); folder=fullfile(here,'..','results','E11');
meta=jsondecode(fileread(fullfile(folder,'cases_meta.json')));
cp=meta.control;
% 이득: 아커만 공식으로 독립 계산(채택: 감쇠비 0.95, 비교: 0.7, 같은 설계점 788 V, 5 kW)
Ka=prism_gain_acker(788,5000,cp,meta.adopted.zeta,meta.adopted.poles(:)');
Kr=prism_gain_acker(788,5000,meta.reference.control,0.7,[1 1/3 2.5]);
fprintf('이득(채택) %s\n이득(비교) %s\n',mat2str(Ka,10),mat2str(Kr,10));
fprintf('Python 대비 상대오차: 채택 %.1e, 비교 %.1e\n',max(abs((Ka-meta.adopted.K_python(:)')./meta.adopted.K_python(:)')), ...
        max(abs((Kr-meta.reference.K(:)')./meta.reference.K(:)')));
write_json(fullfile(folder,'matlab_gain.json'),struct('K_adopted',Ka,'K_reference',Kr,'tool',['GNU Octave/MATLAB ' version]));

lim=meta.limits;
opt=struct('duration',meta.duration,'step',meta.step,'T1_A',lim.T1_A,'T2_A',lim.T2_A, ...
           'T2_band',lim.T2_band(:)','tail_ih',lim.tail_ih_pp_A,'tail_m',lim.tail_m_pp);
ctlA=struct('K',Ka,'cp',cp,'predict',true,'n_sub',5);
ctlR=struct('K',Kr,'cp',meta.reference.control,'predict',false,'n_sub',5);
plan={ 'grid',{'adopted',ctlA;'reference',ctlR};
       'delay_adopted',{'adopted',ctlA};
       'delay_reference',{'reference',ctlR};
       'corners',{'adopted',ctlA};
       'corners_lh5',{'adopted',ctlA};
       'sequences',{'adopted',ctlA} };
for g=1:size(plan,1)
    name=plan{g,1}; if ~any(strcmp(groups,name)), continue; end
    cs=jsondecode(fileread(fullfile(folder,['cases_' name '.json'])));
    if iscell(cs), cs=[cs{:}]; end
    C=build_cases(cs); opt.dt=cs(1).dt; assert(all([cs.dt]==opt.dt),'그룹 안에서 적분간격이 다름');
    designs=plan{g,2};
    for d=1:size(designs,1)
        tic; R=prism_stage_b_batch(C,designs{d,2},opt); el=toc;
        out=sprintf('matlab_%s',name); if isempty(strfind(name,designs{d,1})), out=[out '_' designs{d,1}]; end
        write_json(fullfile(folder,[out '.json']),struct('rows',R,'design',designs{d,1},'dt',opt.dt));
        fprintf('%-28s %4d건, 통과 %4d, 최대 전류 %.2f A, 에너지 잔차 %.1e W  (%.0f s)\n',out,numel(R), ...
                sum([R.pass_]),max(max([R.path_peak],[R.bridge_peak])),max([R.energy_residual_max]),el);
    end
end
end

function C=build_cases(cs)
% 사례 구조체 배열 -> 벡터 필드
C.vbat=[cs.vbat]; C.power0=[cs.power0]; C.power1=[cs.power1]; C.profile=[cs.profile]; C.tier=[cs.tier];
f=fieldnames(cs(1).plant);
for j=1:numel(f)
    v=arrayfun(@(c) double(c.plant.(f{j})),cs); C.p.(f{j})=v(:)';
end
end

function write_json(path,s)
fid=fopen(path,'w'); assert(fid>=0,'파일을 열 수 없음');
fprintf(fid,'%s',jsonencode(s)); fclose(fid);
end
