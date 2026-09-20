%% tb_s6_sals.m -- TB-S6: SALS 강건 부하 셰이핑 (1 ms LP) + 직렬 경로 평균값 모델 (상태궤환)
%  필요: Control System Toolbox (place), Optimization Toolbox (linprog). 실행: >> tb_s6_sals
clear; clc;
Vbat=788; R_A=10.2e-3; R_p=3e-3; tau=10e-6; d=5e-6; Ts=5e-6; L=1.5e-6; Cs=100e-6; Cb=400e-6; Vbus=400;
A=[-(R_A+R_p)/L 1/L -1/L 0; -1/Cs 0 0 1/Cs; 1/Cb 0 0 0; 0 0 0 -1/tau]; B=[0;0;0;1/tau];
Aa=blkdiag(A,0); Aa(5,3)=-1; Ba=[B;0]; w=2*pi*8e3; z=0.7;
K=place(Aa,Ba,[-z*w+1i*w*sqrt(1-z^2),-z*w-1i*w*sqrt(1-z^2),-w,-w/3,-2*pi*20e3]);
% 부하 정의 (A @400 V): 비지연 = 12.5 + 컴프레서(5 ms 기동, 서지 50 A 20 ms 후 25 A로 tau 50 ms) + V2L 9 A(4 ms); 지연가능 3종(6 ms 요청)
nondef=@(t) 12.5 + (t>=0.005).*((t<0.025)*50 + (t>=0.025).*25.*(1-exp(-(t-0.025)/0.05))) + 9*(t>=0.004);
defr=struct('name',{'PTC','BatHeater','V48'},'req',{17.5,17.5,3.75},'t',{0.006,0.006,0.006},'w',{1.0,0.7,0.5});
tend=0.08;
% (1) 무셰이핑 / (2) HW 150 A / (3) SALS 강건 (오차 -20 %, +5 ms)
il0=@(t,vb) (nondef(t)+sum([defr.req].*(t>=[defr.t])))*Vbus/vb;
[t,vb0]=simpath(K,L,Cs,Cb,il0,tend,100,Vbat,R_A,R_p,tau,d,Ts); fprintf('B0 no shaping: vmin %.1f\n',min(vb0));
[~,vb1]=simpath(K,L,Cs,Cb,il0,tend,150,Vbat,R_A,R_p,tau,d,Ts); fprintf('HW 150 A: vmin %.1f\n',min(vb1));
[tg,al]=sals(nondef,defr,95,15,1e-3,tend,-0.2,5e-3,[5e-3 0.25]);
ils=@(t,vb) (nondef(t)+sum(arrayfun(@(j) interp1(tg,al(:,j),t,'previous','extrap'),1:3)))*Vbus/vb;
[~,vb2]=simpath(K,L,Cs,Cb,ils,tend,100,Vbat,R_A,R_p,tau,d,Ts); fprintf('SALS robust (err -20%%/+5ms): vmin %.1f\n',min(vb2));
figure; plot(t*1e3,vb0,t*1e3,vb1,t*1e3,vb2); ylim([300 420]); grid on; xlabel('t (ms)'); ylabel('V_{bus}'); legend('B0','HW 150 A','SALS robust');
function [tg,al]=sals(nondef,defr,Imax,H,Tc,tend,pe,te,rob)
    tg=(0:Tc:tend-Tc)'; J=numel(defr); al=zeros(numel(tg),J);
    for i=1:numel(tg)
        th=tg(i)+(0:H-1)'*Tc; sh=linspace(-rob(1),rob(1),11);
        nd=max(cell2mat(arrayfun(@(s) nondef(th-te-s),sh,'UniformOutput',false)),[],2)*(1+pe)*(1+rob(2));
        c=zeros(H*J,1); lb=zeros(H*J,1); ub=zeros(H*J,1); Aub=zeros(H,H*J); bub=Imax-nd;
        for k=1:H, for j=1:J, idx=(k-1)*J+j; c(idx)=-defr(j).w*(1+0.02*(k-1)); ub(idx)=defr(j).req*(th(k)>=defr(j).t); Aub(k,idx)=1; end, end
        opts=optimoptions('linprog','Display','none'); u=linprog(c,Aub,bub,[],[],lb,ub,opts); if isempty(u), u=zeros(H*J,1); end
        al(i,:)=u(1:J)';
    end
end
function [t,vbl]=simpath(K,L,Cs,Cb,ilfn,tend,Isat,Vbat,R_A,R_p,tau,d,Ts)
    dt=0.2e-6; n=round(tend/dt); t=(0:n-1)'*dt; P0=5e3; ip=P0/400; vs=400-(Vbat/2-R_A*ip); vb=400; idab=ip;
    q=-(ip+K(1:4)*[ip;vs;vb;idab])/K(5); nd=round(d/dt); dbuf=ip*ones(nd+1,1); cmd=ip; kc=round(Ts/dt); vbl=zeros(n,1);
    for k=0:n-1
        il=ilfn(t(k+1),vb);
        if mod(k,kc)==0, uu=-K(1:4)*[ip;vs;vb;idab]-K(5)*q; cmd=min(Isat,max(-Isat,uu)); q=q+Ts*(400-vb)+0.05*(cmd-uu)/(-K(5)); end
        dbuf=[cmd;dbuf(1:end-1)]; u=dbuf(end);
        ip=ip+dt*(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; vs=vs+dt*(idab-ip)/Cs; vb=max(50,vb+dt*(ip-il)/Cb); idab=idab+dt*(u-idab)/tau; vbl(k+1)=vb;
    end
end
