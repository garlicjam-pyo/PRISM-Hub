%% tb_a_array.m -- Stage A 어레이 스위칭 모델 (위상 벡터화, 자기발진 ZC 타이밍)
%  WP3-1 몬테카를로 / TB-A2 어레이 분담 / TB-A3 프리차지 / TB-A4 위상 셰딩
%  실행: >> tb_a_array          (수 분)
clear; clc;
B.Cfly=7.8125e-6; B.Lr=1.441e-7; B.Rds=6e-3; B.ESR=1.5e-3; B.RL=1e-3; B.Rmisc=1.5e-3;
B.Vf=0.9; B.Eoss=24e-6; B.Qg_E=2e-6; B.tdead=100e-9; B.tdet=20e-9; B.ithr=0.5;
fr0 = 1/(2*pi*sqrt(B.Lr*B.Cfly));

%% WP3-1 몬테카를로 (단상, C±5%, L±10%, R±10%)
rng(0); nMC=20; zcs=zeros(nMC,3); pl=zeros(nMC,3);
for k=1:nMC
    tol=struct('C',0.05,'L',0.10,'R',0.10);
    paired_rng=rng;
    [r,~]=prism_sim_array(B,fr0,1,788,46.875,400e-6,'fixed',0.98,tol,0,50,340,[],[],[]); zcs(k,1)=r.zcs; pl(k,1)=r.Ploss;
    rng(paired_rng);
    [r,~]=prism_sim_array(B,fr0,1,788,46.875,400e-6,'zcp',1.0,tol,0,50,340,[],[],[]);   zcs(k,2)=r.zcs; pl(k,2)=r.Ploss;
    rng(paired_rng);
    [r,~]=prism_sim_array(B,fr0,1,788,-46.875,400e-6,'zcp',1.0,tol,0,50,340,[],[],[]); zcs(k,3)=r.zcs; pl(k,3)=r.Ploss;
end
fprintf('WP3-1 fixed 0.98fr: ZCS max %.1f%%  loss mean %.1f W  fail %d/%d\n',max(zcs(:,1))*100,mean(pl(:,1)),sum(zcs(:,1)>0.05),nMC);
fprintf('WP3-1 self-osc   : ZCS max %.1f%%  loss mean %.1f W  fail %d/%d\n',max(zcs(:,2))*100,mean(pl(:,2)),sum(zcs(:,2)>0.05),nMC);
fprintf('WP3-1 reverse    : ZCS max %.1f%%  loss mean %.1f W  fail %d/%d\n',max(zcs(:,3))*100,mean(pl(:,3)),sum(zcs(:,3)>0.05),nMC);
assert(all(zcs(:,2:3)<.05,'all'),'ZCS regression in paired forward/reverse MC');

%% TB-A2 8위상 375 A, ±10 % 난수
rng(3); [r,w]=prism_sim_array(B,fr0,8,788,375,400e-6,'zcp',1.0,struct('C',0.1,'L',0.1,'R',0.1),0,60,340,[],[],[]);
mod=sum(reshape(r.Iavg,2,4),1);
fprintf('TB-A2: module dev %% = %s | Vbus %.1f ripple %.2f V | loss %.0f W | ZCS max %.1f%%\n', mat2str(round((mod-mean(mod))/mean(mod)*100,1)), r.Vbus, r.ripple, sum(r.Ploss_ph), max(r.zcs_ph)*100);

%% TB-A3 프리차지 (20 ohm, C_in 100 uF, 무부하, 스위칭 중)
[r,w]=prism_sim_array(B,fr0,8,788,0,400e-6,'zcp',1.0,[],20,2300,170,0,0,100e-6);
i95=find(w.vb>=0.95*394,1); fprintf('TB-A3: peak |i| %.1f A, t95 %.1f ms\n', max(abs(w.i(:))), w.t(i95)*1e3);

%% TB-A4 위상 셰딩 3 kW
[r1,~]=prism_sim_array(B,fr0,8,788,7.5,400e-6,'zcp',1.0,[],0,40,340,[],[],[],[1 1 0 0 0 0 0 0]);
[r8,~]=prism_sim_array(B,fr0,8,788,7.5,400e-6,'zcp',1.0,[],0,40,340,[],[],[],ones(1,8));
fprintf('TB-A4 3 kW: 1 module %.1f W (eta %.2f%%) | 8 phases %.1f W (eta %.2f%%)\n', sum(r1.Ploss_ph(1:2)), 3e3/(3e3+sum(r1.Ploss_ph(1:2)))*100, sum(r8.Ploss_ph), 3e3/(3e3+sum(r8.Ploss_ph))*100);

%% ------------------------------------------------------------------ 함수
