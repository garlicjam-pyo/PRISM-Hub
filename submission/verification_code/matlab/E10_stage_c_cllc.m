function res = E10_stage_c_cllc()
% E10_STAGE_C_CLLC  [E10] Stage C 대칭 CLLC 400 -> 48 V, 3 kW 스위칭 ODE (MATLAB 구현)
%
%  목적   고정이득(공진점) 운전에서 전압이득이 1에 가깝고 부하에 둔감한지, 입력 +-2 %가 출력에 그대로
%         전달되는지, 1차측 ZVS 전류가 확보되는지 확인한다(python/E10_stage_c_cllc.py와 같은 모델).
%  모델   1차측 환산 6상태 [i_r1, v_c1, i_m, i_r2', v_c2', V_o], 권선비 n = 25/3,
%         1차 50 % 구형파(데드타임 50 ns), 2차 이상 동기정류, 저항부하, RK4 주기당 400단계.
%         자화 노드 KCL로 v_m을 대수적으로 구한다.
%  판정   공진점 이득 1 +- 3 % (0.3-3 kW), ZVS 여유 = i_sw*t_d/(2*C_oss*V_in) > 1
%  실행   >> cd matlab ; E10_stage_c_cllc      (수 분)
%  결과   ../results/E10/stage_c_matlab.json
here=fileparts(mfilename('fullpath')); outdir=fullfile(here,'..','results','E10');
if ~isfolder(outdir), mkdir(outdir); end
n=25/3; Vin=400; fr=250e3; Lr1=11.0e-6;
r=simc(3000,fr,Vin,400,400);
fprintf('공칭 3 kW, fs = fr: Vo %.2f V, 이득 %.4f, 1차 실효 %.2f A, 2차 실효 %.1f A, 자화 피크 %.2f A, ZVS 여유 %.1f배\n', ...
        r.Vo,r.gain,r.Ipri,r.Isec,r.Im,r.zvs);
res.nominal=r;
% 기본파 근사(FHA) 이득, m = Lm/Lr = 6
fha=@(fn,Q,m) 1./sqrt((1+(1/m)*(1-1./fn.^2)).^2+(Q*(fn-1./fn)).^2);
k=0;
for Po=[300 1500 3000]
    RL=48^2/Po; Rac=8*n^2*RL/pi^2; Q=2*pi*fr*Lr1/Rac;
    for fn=[0.9 0.97 1 1.03 1.1]
        rr=simc(Po,fn*fr,Vin,300,400); k=k+1;
        fprintf('%4d W, fs/fr %.2f: 이득 %.3f (FHA %.3f), Vo %.2f V, ZVS 여유 %.1f배\n',Po,fn,rr.gain,fha(fn,Q,6),rr.Vo,rr.zvs);
        res.gain_table(k)=struct('Po',Po,'fn',fn,'gain_sim',rr.gain,'gain_fha',fha(fn,Q,6),'Vo',rr.Vo,'zvs_margin',rr.zvs);
    end
end
for V=[392 400 408], rr=simc(3000,fr,V,300,400); fprintf('입력 %d V: Vo %.2f V\n',V,rr.Vo); res.(sprintf('Vo_at_%d',V))=rr.Vo; end
res.tool=version;
fid=fopen(fullfile(outdir,'stage_c_matlab.json'),'w'); fprintf(fid,'%s',jsonencode(res,'PrettyPrint',true)); fclose(fid);
fprintf('  -> 저장: results/E10/stage_c_matlab.json\n');
end

function r=simc(Po,fs,Vin,ncyc,Nstep)
% ncyc 주기 적분 후 마지막 10주기로 평균 출력·이득·실효전류·ZVS 여유 계산
    n=25/3; Lr1=11.0e-6; Cr1=36.8e-9; Lm=66e-6; Lr2=Lr1; Cr2=Cr1; Co=470e-6; Coss=100e-12; td=50e-9;
    RL=48^2/Po; T=1/fs; dt=T/Nstep; N=ncyc*Nstep; ndead=round(td/dt); half=Nstep/2; ginv=1/(1/Lr1+1/Lm+1/Lr2);
    x=[0;0;0;0;0;48]; lg=zeros(N,6);
    f=@(x,vp) fcn(x,vp,Lr1,Cr1,Lm,Lr2,Cr2,Co,RL,n,ginv);
    for k=0:N-1
        m=mod(k,Nstep); if m<half, vp=Vin*(m>=ndead); else, vp=-Vin*((m-half)>=ndead); end
        k1=f(x,vp); k2=f(x+0.5*dt*k1,vp); k3=f(x+0.5*dt*k2,vp); k4=f(x+dt*k3,vp); x=x+dt/6*(k1+2*k2+2*k3+k4); lg(k+1,:)=x';
    end
    idx=(ncyc-10)*Nstep+1:N; L=lg(idx,:);
    r.Vo=mean(L(:,6)); r.gain=r.Vo*n/Vin; r.Ipri=sqrt(mean(L(:,1).^2)); r.Isec=sqrt(mean(L(:,4).^2))*n; r.Im=max(abs(L(:,3)));
    sw=idx(mod(idx-1,Nstep)==half-1 | mod(idx-1,Nstep)==Nstep-1); isw=mean(abs(lg(sw,1)));   % 스위칭 순간 1차 전류
    r.zvs=isw*td/(2*Coss*Vin);
end

function dx=fcn(x,vp,Lr1,Cr1,Lm,Lr2,Cr2,Co,RL,n,ginv)
    ir1=x(1); vc1=x(2); ir2=x(4); vc2=x(5); Vo=x(6);
    if abs(ir2)>1e-6, vs2=sign(ir2)*n*Vo; else, vs2=0; end        % 이상 동기정류
    vm=((vp-vc1)/Lr1+(vc2+vs2)/Lr2)*ginv;                          % 자화 노드 전압
    dx=[(vp-vc1-vm)/Lr1; ir1/Cr1; vm/Lm; (vm-vc2-vs2)/Lr2; ir2/Cr2; (abs(ir2)*n-Vo/RL)/Co];
end
