%% tb_a1_rsc_phase.m  --  TB-A1: 2:1 공진형 SC 위상 셀 스위칭 시뮬레이션 (Simulink 불필요)
%  상태 x = [iC; vC; Vout]  (iC>0 : C_fly 상판으로 유입 = 충전)
%  Phase1 (S1,S3 on): L diC/dt = Vin - Vout - vC - iC*R
%  Phase2 (S2,S4 on): L diC/dt = Vout - vC - iC*R
%  Dead time (all off, 바디 다이오드):
%     iC>0 : L diC/dt = -vC - iC*R - 2Vf     (출력 노드 주변 환류, 출력 전류 0)
%     iC<0 : L diC/dt = Vin - vC - iC*R + 2Vf (입력으로 회생)
%     iC=0 : 다이오드 차단
%  출력 노드: Cout dVout/dt = iout - Vout/Rload,  iout = iC (P1), -iC (P2), 0 (dead)
%  손실: 도통 mean(iC^2)*R, 다이오드 mean(2Vf|iC|)@dead, Coss 4*Eoss*fs, 게이트 4*Qg_E*fs
%  실행: >> tb_a1_rsc_phase      (약 1~2분, 결과 표 + 그림)
clear; clc;
P.Cfly=7.8125e-6; P.Lr=1.441e-7; P.Rds=6e-3; P.ESR=1.5e-3; P.RL=1e-3; P.Rmisc=1.5e-3;
P.Vf=0.9; P.Eoss=24e-6; P.Qg_E=2e-6; P.Cout=400e-6; P.tdead=100e-9;
fr = 1/(2*pi*sqrt(P.Lr*P.Cfly));

%% 공칭점
[r,w] = sim_phase(P, fr, 788, 46.875, 1.0, 300, 680, []);
fprintf('공칭: Ipk=%.1f A, Irms=%.1f A, ZCS(off)=%.1f %%, i_on=%.2f A, swing=%.1f V, Ploss=%.1f W, eta=%.3f %%, Rout=%.1f mohm\n', ...
    r.Ipk, r.Irms, r.zcs*100, r.i_on, r.swing, r.Ploss, r.eta*100, r.Rout*1e3);
figure('Name','TB-A1 nominal'); 
subplot(3,1,1); plot((w.t-w.t(1))*1e6, w.iC); ylabel('i_C (A)'); grid on; title('TB-A1 nominal 788 V / 46.9 A / f_s=f_r');
subplot(3,1,2); plot((w.t-w.t(1))*1e6, w.vC); ylabel('v_{Cfly} (V)'); grid on;
subplot(3,1,3); plot((w.t-w.t(1))*1e6, w.Vo); ylabel('V_{out} (V)'); xlabel('t (\mus)'); grid on;

%% 스윕 1: fs/fr  (ZCS 최적점 탐색)
ratios = [0.95 0.97 0.975 0.98 0.985 0.99 1.0 1.03 1.05];
T1 = zeros(numel(ratios),5);
for k=1:numel(ratios)
    r = sim_phase(P, fr, 788, 46.875, ratios(k), 300, 680, []);
    T1(k,:) = [ratios(k), r.zcs*100, r.Ipk, r.swing, r.Ploss];
end
disp('fs/fr 스윕: [fs/fr, ZCS off %, Ipk A, swing V, Ploss W]'); disp(T1);
figure('Name','TB-A1 fs/fr sweep'); yyaxis left; plot(T1(:,1),T1(:,2),'o-'); ylabel('|i_{off}|/I_{pk} (%)'); hold on; yline(5,'r--','ZCS 5 %');
yyaxis right; plot(T1(:,1),T1(:,5),'s-'); ylabel('P_{loss}/phase (W)'); xlabel('f_s/f_r'); grid on;

%% 스윕 2: 부하
loads = [5 12.5 25 46.875 60];
T2 = zeros(numel(loads),5);
for k=1:numel(loads)
    r = sim_phase(P, fr, 788, loads(k), 0.98, 300, 680, []);
    T2(k,:) = [loads(k), r.zcs*100, r.Ploss, r.eta*100, r.Rout*1e3];
end
disp('부하 스윕 @0.98fr: [I_ph A, ZCS %, Ploss W, eta %, Rout mohm]'); disp(T2);

%% 스윕 3: Vin
vins = [648 788 920];
T3 = zeros(numel(vins),4);
for k=1:numel(vins)
    r = sim_phase(P, fr, vins(k), 46.875, 0.98, 300, 680, []);
    T3(k,:) = [vins(k), r.zcs*100, r.Ploss, r.eta*100];
end
disp('Vin 스윕: [Vin V, ZCS %, Ploss W, eta %]'); disp(T3);

%% 스윕 4: 데드타임
tds = [50 100 200 400]*1e-9;
T4 = zeros(numel(tds),4);
for k=1:numel(tds)
    r = sim_phase(P, fr, 788, 46.875, 1.0, 300, 680, tds(k));
    T4(k,:) = [tds(k)*1e9, r.zcs*100, r.Pdiode, r.Ploss];
end
disp('데드타임 스윕 @fs=fr: [tdead ns, ZCS %, Pdiode W, Ploss W]'); disp(T4);

%% 합격 판정 (설계검증서 5.1 TB-A1)
r = sim_phase(P, fr, 920, 46.875, 0.98, 300, 680, []);
pass_zcs   = r.zcs <= 0.05;
pass_swing = abs(r.swing-20) <= 3;
pass_loss  = r.Ploss <= 59*1.3;
fprintf('\n판정 @920 V, 46.9 A, fs=0.98fr: ZCS %s (%.1f %%), swing %s (%.1f V), loss %s (%.1f W)\n', ...
    tf(pass_zcs), r.zcs*100, tf(pass_swing), r.swing, tf(pass_loss), r.Ploss);

%% ---------------------------------------------------------------- 함수
function s = tf(b), if b, s='PASS'; else, s='FAIL'; end, end

function [r, w] = sim_phase(P, fr, Vin, Iload, fratio, ncyc, Nstep, tdead)
    C=P.Cfly; L=P.Lr; R=2*P.Rds+P.ESR+P.RL+P.Rmisc; Vf=P.Vf; Co=P.Cout;
    if isempty(tdead), td=P.tdead; else, td=tdead; end
    fs=fratio*fr; T=1/fs; Vo0=Vin/2; Rload=Vo0/Iload;
    dt=T/Nstep; n=ncyc*Nstep; ndead=round(td/dt); half=Nstep/2;
    x=[0; Vo0; Vo0];
    iC=zeros(n,1); vC=zeros(n,1); Vo=zeros(n,1); st=zeros(n,1,'int8'); io=zeros(n,1);
    for k=0:n-1
        m=mod(k,Nstep);
        if m<half, if m>=ndead, s=1; else, s=0; end
        else,      if (m-half)>=ndead, s=2; else, s=0; end, end
        iC(k+1)=x(1); vC(k+1)=x(2); Vo(k+1)=x(3); st(k+1)=s;
        [k1,o]=f(x,s); k2=f(x+0.5*dt*k1,s); k3=f(x+0.5*dt*k2,s); k4=f(x+dt*k3,s);
        io(k+1)=o;
        xn=x+dt/6*(k1+2*k2+2*k3+k4);
        if s==0 && xn(1)*x(1)<=0, xn(1)=0; end     % 다이오드 차단(영교차)
        x=xn;
    end
    t=(0:n-1)'*dt; msk = t >= (ncyc-20)*T;          % 마지막 20주기 분석
    i=iC(msk); v=vC(msk); vo=Vo(msk); s=st(msk); o=io(msk);
    tr=find(diff(s)~=0);
    off=tr(s(tr)~=0 & s(tr+1)==0); on=tr(s(tr)==0 & s(tr+1)~=0);
    r.Ipk=max(abs(i)); r.Irms=sqrt(mean(i.^2));
    r.zcs=max(abs(i(off)))/r.Ipk; r.i_on=max(abs(i(on)));
    r.swing=max(v)-min(v);
    r.Pcond=mean(i.^2)*R; r.Pdiode=mean((s==0).*2*Vf.*abs(i));
    r.Pcoss=4*P.Eoss*fs; r.Pgate=4*P.Qg_E*fs;
    r.Pout=mean(vo.^2/Rload); r.Ploss=r.Pcond+r.Pdiode+r.Pcoss+r.Pgate;
    r.eta=r.Pout/(r.Pout+r.Ploss); r.Rout=(Vin/2-mean(vo))/mean(o); r.fs=fs;
    w.t=t(msk); w.iC=i; w.vC=v; w.Vo=vo; w.state=s;
    function [dx,iout]=f(x,s)
        ic=x(1); vc=x(2); vout=x(3);
        switch s
            case 1, di=(Vin-vout-vc-ic*R)/L; iout=ic;
            case 2, di=(vout-vc-ic*R)/L;     iout=-ic;
            otherwise
                if ic>1e-3,      di=(-vc-ic*R-2*Vf)/L;     iout=0;
                elseif ic<-1e-3, di=(Vin-vc-ic*R+2*Vf)/L;  iout=0;
                else,            di=0;                      iout=0; end
        end
        dx=[di; ic/C; (iout-vout/Rload)/Co];
    end
end
