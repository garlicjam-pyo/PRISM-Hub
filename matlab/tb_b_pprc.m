%% tb_b_pprc.m -- TB-B2/TB-S1: PPRC 직렬 경로 평균값 모델, 상태궤환+적분 설계, 60 A 스텝 비교
%  필요: Control System Toolbox (place).  실행: >> tb_b_pprc
%  플랜트 x=[i_p; v_ser; v_bus; i_dab], u=DAB 전류 지령, w=i_load(정전력)
%    di_p/dt   = (Vbat/2 - (R_A+R_p) i_p + v_ser - v_bus)/L
%    dv_ser/dt = (i_dab - i_p)/C_ser
%    dv_bus/dt = (i_p - w)/C_bus
%    di_dab/dt = (u - i_dab)/tau      (+ 전송지연 d, 샘플 Ts, 포화 +-100 A)
%  제어: u = -Kx*x - Kq*q + i_ff,  dq/dt = v_ref - v_bus
clear; clc;
Vbat=788; R_A=10.2e-3; R_p=3e-3; tau=10e-6; d=5e-6; Ts=5e-6;
L=1.5e-6; Cs=100e-6; Cb=400e-6;

%% 1. 극배치 설계 (f_bw = 8 kHz)
K = design_sf(L,Cs,Cb,8e3,R_A,R_p,tau);
fprintf('K = [%.3f %.3f %.3f %.3f | Kq %.0f]\n',K);

%% 2. TB-S1: 60 A 스텝, 제어 방식 비교
cases = {'B0',struct(); 'B1',struct('ff','B1'); 'B2',struct('ff','B2'); ...
         'ARL(20%,+50us)',struct('ff','ARL','pred_err',0.2,'t_err',50e-6); ...
         'ARL+preboost8V',struct('ff','ARL','pred_err',0.2,'t_err',50e-6,'pre_boost',8)};
figure('Name','TB-S1'); hold on; grid on;
for c=1:size(cases,1)
    r = sim_path(K,L,Cs,Cb,60,cases{c,2},Vbat,R_A,R_p,tau,d,Ts);
    fprintf('%-16s droop %.2f V  overshoot %.2f V  rec %s us  i_dab pk %.0f A\n', cases{c,1}, r.droop, r.over, num2str(r.rec*1e6,'%.0f'), r.ipk);
    m = r.t>=0.8e-3 & r.t<=1.6e-3; plot((r.t(m)-1e-3)*1e6, r.vb(m), 'DisplayName', cases{c,1});
end
yline(392,'r--'); xlabel('t - t_{step} (\mus)'); ylabel('V_{bus} (V)'); legend; title('TB-S1 60 A CPL step');

%% 3. 스텝 크기 스윕 (포화 절벽)
for dI = [25 60 80 87 95 105]
    r = sim_path(K,L,Cs,Cb,dI,struct(),Vbat,R_A,R_p,tau,d,Ts);
    fprintf('dI=%3d A: droop %.1f V  rec %s\n', dI, r.droop, num2str(r.rec*1e6,'%.0f'));
end

%% 4. 커패시터 축소 (뱅크별 재설계)
for s = [0.5 1 2]
    Ks = design_sf(L,Cs*s,Cb*s,8e3,R_A,R_p,tau);
    r0 = sim_path(Ks,L,Cs*s,Cb*s,60,struct(),Vbat,R_A,R_p,tau,d,Ts);
    r2 = sim_path(Ks,L,Cs*s,Cb*s,60,struct('ff','B2'),Vbat,R_A,R_p,tau,d,Ts);
    fprintf('s=%.2f: B0 droop %.1f V  B2 %.1f V  (unstable: %d)\n', s, r0.droop, r2.droop, r0.unstable);
end

%% ----------------------------------------------------------------- 함수
function K = design_sf(L,Cs,Cb,fbw,R_A,R_p,tau)
    A=[-(R_A+R_p)/L 1/L -1/L 0; -1/Cs 0 0 1/Cs; 1/Cb 0 0 0; 0 0 0 -1/tau]; B=[0;0;0;1/tau];
    Aa=blkdiag(A,0); Aa(5,3)=-1; Ba=[B;0];
    w=2*pi*fbw; z=0.7;
    p=[-z*w+1i*w*sqrt(1-z^2), -z*w-1i*w*sqrt(1-z^2), -w, -w/3, -min(2.5*w,2*pi*30e3)];
    K=place(Aa,Ba,p);
end

function r = sim_path(K,L,Cs,Cb,dI,opt,Vbat,R_A,R_p,tau,d,Ts)
    ff=''; pe=0; te=0; pb=0; if isfield(opt,'ff'), ff=opt.ff; end
    if isfield(opt,'pred_err'), pe=opt.pred_err; end; if isfield(opt,'t_err'), te=opt.t_err; end; if isfield(opt,'pre_boost'), pb=opt.pre_boost; end
    dt=0.1e-6; tend=2.5e-3; tstep=1e-3; tlead=1e-3; n=round(tend/dt); t=(0:n-1)'*dt; P0=5e3; Isat=100;
    ip=P0/400; vs=400-(Vbat/2-R_A*ip); vb=400; idab=ip;
    q=-(ip+K(1:4)*[ip;vs;vb;idab])/K(5);
    nd=round(d/dt); dbuf=ip*ones(nd+1,1); cmd=ip; kc=round(Ts/dt);
    vbl=zeros(n,1); idl=zeros(n,1);
    for k=0:n-1
        tt=t(k+1); Pload=P0+400*dI*(tt>=tstep); iload=Pload/vb;
        if mod(k,kc)==0
            switch ff
                case 'B1',  iff=(P0+400*dI*(tt-20e-6>=tstep))/vb - P0/400;
                case 'B2',  iff=dI*(tt>=tstep-(tau+d));
                case 'ARL', iff=dI*(1-pe)*(tt>=tstep-(tau+d)+te);
                otherwise,  iff=0;
            end
            vr=400; if pb>0 && tt<tstep, vr=400+pb*min(1,max(0,(tt-(tstep-tlead))/(tlead*0.5))); end
            cmd=min(Isat,max(-Isat, -K(1:4)*[ip;vs;vb;idab] - K(5)*q + iff));
            q=q+Ts*(vr-vb);
        end
        dbuf=[cmd; dbuf(1:end-1)]; u=dbuf(end);
        dip=(Vbat/2-(R_A+R_p)*ip+vs-vb)/L; dvs=(idab-ip)/Cs; dvb=(ip-iload)/Cb; did=(u-idab)/tau;
        ip=ip+dt*dip; vs=vs+dt*dvs; vb=vb+dt*dvb; idab=idab+dt*did;
        vbl(k+1)=vb; idl(k+1)=idab;
    end
    m=t>=tstep; r.droop=400-min(vbl(m)); r.over=max(vbl)-400; r.ipk=max(abs(idl));
    ok=abs(vbl-400)<=4; r.rec=NaN;
    for k=round(tstep/dt):n, if all(ok(k:end)), r.rec=t(k)-tstep; break; end, end
    tail=vbl(t>tend-0.5e-3); r.unstable=(max(tail)-min(tail)>2) || any(isnan(tail));
    r.t=t; r.vb=vbl; r.idab=idl;
end
