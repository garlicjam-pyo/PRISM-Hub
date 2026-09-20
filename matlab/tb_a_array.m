%% tb_a_array.m -- Stage A 어레이 스위칭 모델 (위상 벡터화, 자기발진 ZC 타이밍)
%  WP3-1 몬테카를로 / TB-A2 어레이 분담 / TB-A3 프리차지 / TB-A4 위상 셰딩
%  실행: >> tb_a_array          (수 분)
clear; clc;
B.Cfly=7.8125e-6; B.Lr=1.441e-7; B.Rds=6e-3; B.ESR=1.5e-3; B.RL=1e-3; B.Rmisc=1.5e-3;
B.Vf=0.9; B.Eoss=24e-6; B.Qg_E=2e-6; B.tdead=100e-9; B.tdet=20e-9; B.ithr=0.5;
fr0 = 1/(2*pi*sqrt(B.Lr*B.Cfly));

%% WP3-1 몬테카를로 (단상, C±5%, L±10%, R±10%)
rng(0); nMC=20; zcs=zeros(nMC,2); pl=zeros(nMC,2);
for k=1:nMC
    tol=struct('C',0.05,'L',0.10,'R',0.10);
    [r,~]=sim_array(B,fr0,1,788,46.875,400e-6,'fixed',0.98,tol,0,50,340,[],[],[]); zcs(k,1)=r.zcs; pl(k,1)=r.Ploss;
    [r,~]=sim_array(B,fr0,1,788,46.875,400e-6,'zcp',1.0,tol,0,50,340,[],[],[]);   zcs(k,2)=r.zcs; pl(k,2)=r.Ploss;
end
fprintf('WP3-1 fixed 0.98fr: ZCS max %.1f%%  loss mean %.1f W  fail %d/%d\n',max(zcs(:,1))*100,mean(pl(:,1)),sum(zcs(:,1)>0.05),nMC);
fprintf('WP3-1 self-osc   : ZCS max %.1f%%  loss mean %.1f W  fail %d/%d\n',max(zcs(:,2))*100,mean(pl(:,2)),sum(zcs(:,2)>0.05),nMC);

%% TB-A2 8위상 375 A, ±10 % 난수
rng(3); [r,w]=sim_array(B,fr0,8,788,375,400e-6,'zcp',1.0,struct('C',0.1,'L',0.1,'R',0.1),0,60,340,[],[],[]);
mod=sum(reshape(r.Iavg,2,4),1);
fprintf('TB-A2: module dev %% = %s | Vbus %.1f ripple %.2f V | loss %.0f W | ZCS max %.1f%%\n', mat2str(round((mod-mean(mod))/mean(mod)*100,1)), r.Vbus, r.ripple, sum(r.Ploss_ph), max(r.zcs_ph)*100);

%% TB-A3 프리차지 (20 ohm, C_in 100 uF, 무부하, 스위칭 중)
[r,w]=sim_array(B,fr0,8,788,0,400e-6,'zcp',1.0,[],20,2300,170,0,0,100e-6);
i95=find(w.vb>=0.95*394,1); fprintf('TB-A3: peak |i| %.1f A, t95 %.1f ms\n', max(abs(w.i(:))), w.t(i95)*1e3);

%% TB-A4 위상 셰딩 3 kW
[r1,~]=sim_array(B,fr0,8,788,7.5,400e-6,'zcp',1.0,[],0,40,340,[],[],[],[1 1 0 0 0 0 0 0]);
[r8,~]=sim_array(B,fr0,8,788,7.5,400e-6,'zcp',1.0,[],0,40,340,[],[],[],ones(1,8));
fprintf('TB-A4 3 kW: 1 module %.1f W (eta %.2f%%) | 8 phases %.1f W (eta %.2f%%)\n', sum(r1.Ploss_ph(1:2)), 3e3/(3e3+sum(r1.Ploss_ph(1:2)))*100, sum(r8.Ploss_ph), 3e3/(3e3+sum(r8.Ploss_ph))*100);

%% ------------------------------------------------------------------ 함수
function [r,w] = sim_array(B,fr0,N,Vbat,Iload,Cbus,mode,fratio,tol,R_in,ncyc,Nstep,vC0,Vb0,C_in,en)
    if nargin<16 || isempty(en), en=ones(1,N); end
    C=B.Cfly*ones(1,N); L=B.Lr*ones(1,N); R=(2*B.Rds+B.ESR+B.RL+B.Rmisc)*ones(1,N);
    if ~isempty(tol)
        C=C.*(1+tol.C*(2*rand(1,N)-1)); L=L.*(1+tol.L*(2*rand(1,N)-1)); R=R.*(1+tol.R*(2*rand(1,N)-1));
    end
    Vf=B.Vf; td=B.tdead; fs=fratio*fr0; T=1/fs; dt=T/Nstep; n=ncyc*Nstep; ndead=round(td/dt); half=Nstep/2; ndet=round(B.tdet/dt);
    off=round((0:N-1)*(Nstep/2)/N);
    Vo0=Vbat/2; iC=zeros(1,N); if isempty(vC0), vC=Vo0*ones(1,N); else, vC=vC0*ones(1,N); end
    if isempty(Vb0), Vb=Vo0; else, Vb=Vb0; end
    if R_in>0, Vin=0; else, Vin=Vbat; end
    if isempty(C_in), C_in=100e-6; end
    t_on=0.5/fr0*(1-2*td*fr0); min_on=round(0.8*t_on/dt); max_on=round(1.12*t_on/dt);
    st=zeros(1,N); nxt=ones(1,N); tmr=-off; oncnt=zeros(1,N); armed=false(1,N); det=zeros(1,N);
    Li=zeros(n,N,'single'); Lv=zeros(n,N,'single'); Lb=zeros(n,1,'single'); Ls=zeros(n,N,'int8'); Lio=zeros(n,N,'single');
    for k=0:n-1
        if strcmp(mode,'zcp')
            start=(st==0)&(tmr>=ndead); st(start)=nxt(start); nxt(start)=3-nxt(start);
            armed(start)=false; det(start)=0; oncnt(start)=0; tmr(start)=0;
            armed=armed|((st~=0)&(abs(iC)>B.ithr*5));
            cross=(st~=0)&armed&(((st==1)&(iC<B.ithr))|((st==2)&(iC>-B.ithr)));
            det(cross)=det(cross)+1; oncnt(st~=0)=oncnt(st~=0)+1;
            stop=(st~=0)&(((oncnt>=min_on)&cross&(det>ndet))|(oncnt>=max_on));
            st(stop)=0; tmr(stop)=0; tmr(st==0)=tmr(st==0)+1; s=st;
        else
            m=mod(k-off,Nstep); s=zeros(1,N);
            s(m<half & m>=ndead)=1; s(m>=half & (m-half)>=ndead)=2;
        end
        s(~en)=0;
        [k1,io,iin]=deriv(iC,vC,Vb,s,Vin,C,L,R,Vf,Cbus,Iload);
        k2=deriv(iC+0.5*dt*k1(1,:),vC+0.5*dt*k1(2,:),Vb+0.5*dt*k1(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        k3=deriv(iC+0.5*dt*k2(1,:),vC+0.5*dt*k2(2,:),Vb+0.5*dt*k2(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        k4=deriv(iC+dt*k3(1,:),vC+dt*k3(2,:),Vb+dt*k3(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        Li(k+1,:)=iC; Lv(k+1,:)=vC; Lb(k+1)=Vb; Ls(k+1,:)=s; Lio(k+1,:)=io;
        iCn=iC+dt/6*(k1(1,:)+2*k2(1,:)+2*k3(1,:)+k4(1,:));
        vC=vC+dt/6*(k1(2,:)+2*k2(2,:)+2*k3(2,:)+k4(2,:));
        Vb=Vb+dt/6*(k1(3,1)+2*k2(3,1)+2*k3(3,1)+k4(3,1));
        blk=(s==0)&(iCn.*iC<=0); iCn(blk)=0; iC=iCn;
        if R_in>0, Vin=Vin+dt*((Vbat-Vin)/R_in-sum(iin))/C_in; end
    end
    t=(0:n-1)'*dt; w.t=t; w.i=Li; w.v=Lv; w.vb=Lb; w.st=Ls; w.io=Lio;
    msk=t>=t(end)-10*T; r.Vbus=mean(Lb(msk)); r.ripple=max(Lb(msk))-min(Lb(msk));
    for kk=1:N
        ik=double(Li(msk,kk)); sk=double(Ls(msk,kk)); tr=find(diff(sk)~=0);
        offk=tr(sk(tr)~=0 & sk(tr+1)==0); onk=tr(sk(tr)==0 & sk(tr+1)==1);
        Ipk=max(abs(ik)); if isempty(offk), ioff=0; else, ioff=max(abs(ik(offk))); end
        if numel(onk)>2, fsk=1/(mean(diff(onk))*dt); else, fsk=fs; end
        r.zcs_ph(kk)=ioff/max(Ipk,1e-6); r.Iavg(kk)=mean(double(Lio(msk,kk)));
        r.Ploss_ph(kk)=mean(ik.^2)*R(kk)+mean((sk==0).*2*Vf.*abs(ik))+4*B.Eoss*fsk+4*B.Qg_E*fsk;
    end
    r.zcs=max(r.zcs_ph); r.Ploss=sum(r.Ploss_ph);
end

function [dx,io,iin] = deriv(iC,vC,Vb,s,Vin,C,L,R,Vf,Cbus,Iload)
    di=zeros(size(iC));
    p1=s==1; p2=s==2; d=s==0;
    di(p1)=(Vin-Vb-vC(p1)-iC(p1).*R(p1))./L(p1);
    di(p2)=(Vb-vC(p2)-iC(p2).*R(p2))./L(p2);
    dp=d&(iC>1e-3); dn=d&(iC<-1e-3);
    di(dp)=(-vC(dp)-iC(dp).*R(dp)-2*Vf)./L(dp);
    di(dn)=(Vin-vC(dn)-iC(dn).*R(dn)+2*Vf)./L(dn);
    io=zeros(size(iC)); io(p1)=iC(p1); io(p2)=-iC(p2);
    iin=zeros(size(iC)); iin(p1)=iC(p1); iin(dn)=-iC(dn);
    dx=[di; iC./C; (sum(io)-Iload)/Cbus*ones(1,numel(iC))];
end
