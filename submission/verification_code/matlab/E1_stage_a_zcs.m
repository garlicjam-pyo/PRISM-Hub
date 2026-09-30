%% E1_stage_a_zcs.m -- [E1] Stage A 스위칭 ODE 시험 (MATLAB 구현)
%
%  목적   공진 부품 공차가 있어도 Stage A(2:1 RSC)가 정·역방향 모두 영전류 스위칭(ZCS)을 유지하는지,
%         그리고 정격 손실·경부하 모듈 셰딩·프리차지 돌입전류를 확인한다(보고서 6.1절, 표 6.1).
%  필요성 RSC의 효율·소형화 이점은 ZCS에 의존한다. 부품 공차(C ±5 %, L ±10 %)만으로 실제 공진주파수가
%         수 % 달라지므로 타이밍 방식이 이를 흡수해야 아키텍처가 성립한다.
%  방법   prism_sim_array.m (RK4, 주기당 340단계)
%    1) 부품 공차 표본 20개(단상 46.875 A): 같은 표본으로 고정 타이밍 0.98 f_r0 / 영교차 추종 정방향 /
%       영교차 추종 역방향을 비교(rng 상태를 저장·복원해 짝지음)
%    2) 8위상 ±375 A, 공칭과 C·L·R ±10 %(rng(3)): ZCS, 총 손실, 모듈 전류 편차
%    3) 3 kW 셰딩: 1모듈(2위상) 운전 vs 8위상 운전 손실
%    4) 프리차지: 20 ohm, 100 uF, 0 V 시작, 무부하 스위칭 기동
%  판정   ZCS = 턴오프 전류 / 피크 전류 <= 5 %. 영교차 추종은 전 표본·전 사례가 기준 이내여야 한다.
%  보고서 수치(MATLAB R2024b): 고정 16/20 초과·최대 40.1 %, 영교차 추종 0/20·최대 1.1 %,
%         8위상 466 W·모듈 편차 -3.3~+2.2 %, 셰딩 31.6 W / 120.5 W, 프리차지 15.5 A·13.2 ms
%  주의   GNU Octave의 rng는 MATLAB과 난수열이 달라 공차 표본(1·2의 공차 사례)이 다르게 뽑힌다.
%  실행   >> cd matlab ; E1_stage_a_zcs        (수 분)
%  결과   ../results/E1/stage_a_matlab.json
clear; clc;
here=fileparts(mfilename('fullpath')); outdir=fullfile(here,'..','results','E1');
if ~isfolder(outdir), mkdir(outdir); end
B.Cfly=7.8125e-6; B.Lr=1.441e-7; B.Rds=6e-3; B.ESR=1.5e-3; B.RL=1e-3; B.Rmisc=1.5e-3;
B.Vf=0.9; B.Eoss=24e-6; B.Qg_E=2e-6; B.tdead=100e-9; B.tdet=20e-9; B.ithr=0.5;
fr0 = 1/(2*pi*sqrt(B.Lr*B.Cfly));

%% 1) 부품 공차 표본 20개 (단상, C +-5 %, L +-10 %, R +-10 %)
rng(0); nMC=20; zcs=zeros(nMC,3); pl=zeros(nMC,3);
tol=struct('C',0.05,'L',0.10,'R',0.10);
for k=1:nMC
    paired_rng=rng;                                         % 같은 표본으로 세 방식을 비교
    [r,~]=prism_sim_array(B,fr0,1,788,46.875,400e-6,'fixed',0.98,tol,0,50,340,[],[],[]); zcs(k,1)=r.zcs; pl(k,1)=r.Ploss;
    rng(paired_rng);
    [r,~]=prism_sim_array(B,fr0,1,788,46.875,400e-6,'zcp',1.0,tol,0,50,340,[],[],[]);   zcs(k,2)=r.zcs; pl(k,2)=r.Ploss;
    rng(paired_rng);
    [r,~]=prism_sim_array(B,fr0,1,788,-46.875,400e-6,'zcp',1.0,tol,0,50,340,[],[],[]); zcs(k,3)=r.zcs; pl(k,3)=r.Ploss;
end
name={'고정 0.98 f_r      ','영교차 추종 정방향','영교차 추종 역방향'};
for j=1:3
    fprintf('1) %s: ZCS 기준 초과 %d/%d, 최대 %.1f %%, 평균 손실 %.1f W\n',name{j},sum(zcs(:,j)>0.05),nMC,max(zcs(:,j))*100,mean(pl(:,j)));
end
zz=zcs(:,2:3); assert(all(zz(:)<=.05),'영교차 추종 ZCS 기준 위반');
res.tolerance_samples=struct('zcs',zcs,'loss',pl,'n_fail_fixed',sum(zcs(:,1)>0.05),'max_fixed',max(zcs(:,1)),'max_zcp',max(zz(:)));

%% 2) 8위상 +-375 A, 공칭과 공차 +-10 %
k=0;
for direction=[1 -1]
    for tolerance=[false true]
        k=k+1; if tolerance, tl=struct('C',.1,'L',.1,'R',.1); else, tl=[]; end
        rng(3); [r,~]=prism_sim_array(B,fr0,8,788,375*direction,400e-6,'zcp',1.0,tl,0,60,340,[],[],[]);
        modc=sum(reshape(r.Iavg,2,4),1); dev=(modc-mean(modc))/mean(modc)*100;       % 모듈 = 2위상
        fprintf('2) 방향 %+d, 공차 %d: ZCS 최대 %.3f %%, Vbus %.1f V, 출력 %.1f A, 손실 %.0f W, 모듈 편차 %s %%\n', ...
            direction,tolerance,max(r.zcs_ph)*100,r.Vbus,sum(r.Iavg),sum(r.Ploss_ph),mat2str(round(dev*10)/10));
        assert(max(r.zcs_ph)<=.05,'8위상 ZCS 기준 위반');
        res.eight_phase(k)=struct('direction',direction,'tolerance',tolerance,'zcs_max',max(r.zcs_ph),'Vbus',double(r.Vbus), ...
            'Iout',sum(r.Iavg),'loss_total',sum(r.Ploss_ph),'module_dev_pct',dev);
    end
end

%% 3) 3 kW 모듈 셰딩
[r1,~]=prism_sim_array(B,fr0,8,788,7.5,400e-6,'zcp',1.0,[],0,40,340,[],[],[],[1 1 0 0 0 0 0 0]);
[r8,~]=prism_sim_array(B,fr0,8,788,7.5,400e-6,'zcp',1.0,[],0,40,340,[],[],[],ones(1,8));
P1=sum(r1.Ploss_ph(1:2)); P8=sum(r8.Ploss_ph);
fprintf('3) 3 kW: 1모듈 %.1f W (효율 %.2f %%), 8위상 %.1f W (효율 %.2f %%)\n',P1,3e3/(3e3+P1)*100,P8,3e3/(3e3+P8)*100);
res.shedding=struct('one_module_W',P1,'all_phases_W',P8);

%% 4) 프리차지 (20 ohm, C_in 100 uF, 무부하, 스위칭 중)
[r,w]=prism_sim_array(B,fr0,8,788,0,400e-6,'zcp',1.0,[],20,2300,170,0,0,100e-6);
i95=find(w.vb>=0.95*394,1); ipk=max(abs(double(w.i(:))));
fprintf('4) 프리차지: 위상 피크 %.1f A, 95 %% 도달 %.1f ms\n', ipk, w.t(i95)*1e3);
res.precharge=struct('peak_phase_current',ipk,'t95_ms',w.t(i95)*1e3);

res.tool=version;
fid=fopen(fullfile(outdir,'stage_a_matlab.json'),'w'); fprintf(fid,'%s',jsonencode(res,'PrettyPrint',true)); fclose(fid);
fprintf('  -> 저장: results/E1/stage_a_matlab.json\n');
