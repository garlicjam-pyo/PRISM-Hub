%% tb_c1_cllc.m -- TB-C1: 대칭 CLLC 400->48 V 스위칭 ODE (이상 동기정류, 1차 환산)
clear; clc;
n=25/3; Vin=400; fr=250e3; Lr1=11.0e-6; Cr1=36.8e-9; Lm=66e-6; Lr2=Lr1; Cr2=Cr1; Co=470e-6; Coss=100e-12; td=50e-9;
r=simc(3000,fr,Vin,400,400); fprintf('nominal: Vo %.2f gain %.4f Ipri_rms %.2f Isec_rms %.1f Im_pk %.2f ZVS margin %.1fx\n',r.Vo,r.gain,r.Ipri,r.Isec,r.Im,r.zvs);
fha=@(fn,Q,m) 1./sqrt((1+(1/m)*(1-1./fn.^2)).^2+(Q*(fn-1./fn)).^2);
for Po=[300 1500 3000]
    RL=48^2/Po; Rac=8*n^2*RL/pi^2; Q=2*pi*fr*Lr1/Rac;
    for fn=[0.9 0.97 1 1.03 1.1]
        rr=simc(Po,fn*fr,Vin,300,400); fprintf('Po %4d fn %.2f: gain sim %.3f FHA %.3f Vo %.2f\n',Po,fn,rr.gain,fha(fn,Q,6),rr.Vo);
    end
end
for V=[392 400 408], rr=simc(3000,fr,V,300,400); fprintf('Vin %d: Vo %.2f\n',V,rr.Vo); end
function r=simc(Po,fs,Vin,ncyc,Nstep)
    n=25/3; Lr1=11.0e-6; Cr1=36.8e-9; Lm=66e-6; Lr2=Lr1; Cr2=Cr1; Co=470e-6; Coss=100e-12; td=50e-9;
    RL=48^2/Po; T=1/fs; dt=T/Nstep; N=ncyc*Nstep; ndead=round(td/dt); half=Nstep/2; ginv=1/(1/Lr1+1/Lm+1/Lr2);
    x=[0;0;0;0;0;48]; log=zeros(N,6);
    f=@(x,vp) fcn(x,vp,Lr1,Cr1,Lm,Lr2,Cr2,Co,RL,n,ginv);
    for k=0:N-1
        m=mod(k,Nstep); if m<half, vp=Vin*(m>=ndead); else, vp=-Vin*((m-half)>=ndead); end
        k1=f(x,vp); k2=f(x+0.5*dt*k1,vp); k3=f(x+0.5*dt*k2,vp); k4=f(x+dt*k3,vp); x=x+dt/6*(k1+2*k2+2*k3+k4); log(k+1,:)=x';
    end
    idx=(ncyc-10)*Nstep+1:N; L=log(idx,:);
    r.Vo=mean(L(:,6)); r.gain=r.Vo*n/Vin; r.Ipri=rms(L(:,1)); r.Isec=rms(L(:,4))*n; r.Im=max(abs(L(:,3)));
    sw=idx(mod(idx-1,Nstep)==half-1 | mod(idx-1,Nstep)==Nstep-1); isw=mean(abs(log(sw,1)));
    r.zvs=isw*td/(2*Coss*Vin);
end
function dx=fcn(x,vp,Lr1,Cr1,Lm,Lr2,Cr2,Co,RL,n,ginv)
    ir1=x(1); vc1=x(2); im=x(3); ir2=x(4); vc2=x(5); Vo=x(6);
    if abs(ir2)>1e-6, vs2=sign(ir2)*n*Vo; else, vs2=0; end
    vm=((vp-vc1)/Lr1+(vc2+vs2)/Lr2)*ginv;
    dx=[(vp-vc1-vm)/Lr1; ir1/Cr1; vm/Lm; (vm-vc2-vs2)/Lr2; ir2/Cr2; (abs(ir2)*n-Vo/RL)/Co];
end
