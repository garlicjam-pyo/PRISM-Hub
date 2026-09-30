function [r,w] = prism_sim_array(B,fr0,N,Vbat,Iload,Cbus,mode,fratio,tol,R_in,ncyc,Nstep,vC0,Vb0,C_in,en)
% PRISM_SIM_ARRAY  Stage A(2:1 RSC) N위상 어레이 스위칭 ODE 모델 (E1에서 사용)
%
%  Python 구현 python/model_stage_a.py 와 같은 알고리즘이다.
%  위상 k 상태: 공진전류 iC(k), 플라잉 커패시터 전압 vC(k) / 공용 상태: 버스전압 Vb
%    구간 1(충전) : L diC/dt = Vin - Vb - vC - R iC      (입력 -> C_fly -> 버스)
%    구간 2(방전) : L diC/dt = Vb - vC - R iC            (C_fly -> 버스)
%    데드타임(0)  : 남은 전류는 바디 다이오드(2 Vf)로 환류, 영을 지나면 차단
%    C dvC/dt = iC,   Cbus dVb/dt = sum(i_out) - Iload
%
%  입력
%    B       부품 파라미터 구조체(Cfly, Lr, Rds, ESR, RL, Rmisc, Vf, Eoss, Qg_E, tdead, tdet, ithr)
%    fr0     공칭 공진주파수 [Hz]
%    N       위상 수,  Vbat 배터리 전압 [V],  Iload 버스 부하전류 [A](음수 = 역방향 전력)
%    mode    'fixed'(고정 타이밍) | 'zcp'(자기발진 영교차 추종)
%    fratio  스위칭 주파수 / f_r0 (zcp에서는 적분 간격 기준으로만 사용)
%    tol     부품 공차 구조체 struct('C',..,'L',..,'R',..) 또는 [] (rand로 균일분포 추출)
%    R_in    프리차지 저항(>0이면 입력 커패시터 0 V에서 시작),  C_in 입력 커패시터
%    ncyc, Nstep  적분 주기 수, 주기당 RK4 단계 수
%    vC0, Vb0     초기 플라잉 커패시터·버스 전압([]이면 Vbat/2)
%    en      위상별 동작 여부(모듈 셰딩 시험)
%  출력
%    r  마지막 10주기 요약: Vbus, ripple, zcs_ph(턴오프 전류/피크), Iavg, Ploss_ph, zcs, Ploss
%    w  파형 기록(t, i, v, vb, st, io)

    if nargin<16 || isempty(en), en=ones(1,N); end
    % 위상별 부품값(공차 적용: C 전체 -> L 전체 -> R 전체 순서로 난수 추출)
    C=B.Cfly*ones(1,N); L=B.Lr*ones(1,N); R=(2*B.Rds+B.ESR+B.RL+B.Rmisc)*ones(1,N);
    if ~isempty(tol)
        C=C.*(1+tol.C*(2*rand(1,N)-1)); L=L.*(1+tol.L*(2*rand(1,N)-1)); R=R.*(1+tol.R*(2*rand(1,N)-1));
    end
    Vf=B.Vf; td=B.tdead; fs=fratio*fr0; T=1/fs; dt=T/Nstep; n=ncyc*Nstep;
    ndead=round(td/dt); half=Nstep/2; ndet=round(B.tdet/dt);
    off=round((0:N-1)*(Nstep/2)/N);                   % 인터리빙 오프셋 T/(2N)
    Vo0=Vbat/2; iC=zeros(1,N);
    if isempty(vC0), vC=Vo0*ones(1,N); else, vC=vC0*ones(1,N); end
    if isempty(Vb0), Vb=Vo0; else, Vb=Vb0; end
    if R_in>0, Vin=0; else, Vin=Vbat; end
    if isempty(C_in), C_in=100e-6; end
    % 자기발진 상태기계: 공칭 도통시간의 0.80-1.12배를 블랭킹·보호 창으로 사용
    t_on=0.5/fr0*(1-2*td*fr0); min_on=round(0.8*t_on/dt); max_on=round(1.12*t_on/dt);
    st=zeros(1,N); nxt=ones(1,N); tmr=-off; oncnt=zeros(1,N); armed=false(1,N); det=zeros(1,N); pulse_sign=zeros(1,N);
    Li=zeros(n,N,'single'); Lv=zeros(n,N,'single'); Lb=zeros(n,1,'single'); Ls=zeros(n,N,'int8'); Lio=zeros(n,N,'single');
    for k=0:n-1
        if strcmp(mode,'zcp')
            % 데드타임이 끝난 위상은 다음 구간(1 <-> 2 교대) 시작
            start=(st==0)&(tmr>=ndead); st(start)=nxt(start); nxt(start)=3-nxt(start);
            armed(start)=false; det(start)=0; oncnt(start)=0; tmr(start)=0;
            % 전류가 충분히 커지면 펄스 부호를 기억(역방향 전력에서도 같은 논리)
            new_arm=(st~=0)&~armed&(abs(iC)>B.ithr*5);
            pulse_sign(new_arm)=sign(iC(new_arm)); armed=armed|new_arm;
            % 펄스 부호 기준으로 전류가 ithr 아래로 돌아오면 영교차, 검출 지연 ndet 단계 뒤 턴오프
            cross=(st~=0)&armed&(pulse_sign.*iC<B.ithr);
            det(~cross)=0;
            det(cross)=det(cross)+1; oncnt(st~=0)=oncnt(st~=0)+1;
            stop=(st~=0)&(((oncnt>=min_on)&cross&(det>ndet))|(oncnt>=max_on));
            st(stop)=0; tmr(stop)=0; tmr(st==0)=tmr(st==0)+1; s=st;
        else
            % 고정 타이밍: 반주기마다 구간 교대, 반주기 앞에 데드타임
            m=mod(k-off,Nstep); s=zeros(1,N);
            s(m<half & m>=ndead)=1; s(m>=half & (m-half)>=ndead)=2;
        end
        s(~en)=0;
        % RK4 (입력 커패시터 전압 Vin은 단계 안에서 고정)
        [k1,io,iin]=deriv(iC,vC,Vb,s,Vin,C,L,R,Vf,Cbus,Iload);
        k2=deriv(iC+0.5*dt*k1(1,:),vC+0.5*dt*k1(2,:),Vb+0.5*dt*k1(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        k3=deriv(iC+0.5*dt*k2(1,:),vC+0.5*dt*k2(2,:),Vb+0.5*dt*k2(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        k4=deriv(iC+dt*k3(1,:),vC+dt*k3(2,:),Vb+dt*k3(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        Li(k+1,:)=iC; Lv(k+1,:)=vC; Lb(k+1)=Vb; Ls(k+1,:)=s; Lio(k+1,:)=io;
        iCn=iC+dt/6*(k1(1,:)+2*k2(1,:)+2*k3(1,:)+k4(1,:));
        vC=vC+dt/6*(k1(2,:)+2*k2(2,:)+2*k3(2,:)+k4(2,:));
        Vb=Vb+dt/6*(k1(3,1)+2*k2(3,1)+2*k3(3,1)+k4(3,1));
        blk=(s==0)&(iCn.*iC<=0); iCn(blk)=0; iC=iCn;       % 데드타임 다이오드 전류 영교차 시 차단
        if R_in>0, Vin=Vin+dt*((Vbat-Vin)/R_in-sum(iin))/C_in; end   % 프리차지
    end
    t=(0:n-1)'*dt; w.t=t; w.i=Li; w.v=Lv; w.vb=Lb; w.st=Ls; w.io=Lio;
    % 마지막 10주기 요약
    msk=t>=t(end)-10*T; r.Vbus=mean(Lb(msk)); r.ripple=max(Lb(msk))-min(Lb(msk));
    for kk=1:N
        ik=double(Li(msk,kk)); sk=double(Ls(msk,kk)); tr=find(diff(sk)~=0);
        offk=tr(sk(tr)~=0 & sk(tr+1)==0); onk=tr(sk(tr)==0 & sk(tr+1)==1);     % 턴오프, 충전 시작 순간
        Ipk=max(abs(ik)); if isempty(offk), ioff=0; else, ioff=max(abs(ik(offk))); end
        if numel(onk)>2, fsk=1/(mean(diff(onk))*dt); else, fsk=fs; end
        r.zcs_ph(kk)=ioff/max(Ipk,1e-6); r.Iavg(kk)=mean(double(Lio(msk,kk)));
        % 손실 = 도통 i^2 R + 다이오드 2 Vf |i| + 출력용량 4 Eoss fs + 게이트 4 Qg_E fs
        r.Ploss_ph(kk)=mean(ik.^2)*R(kk)+mean((sk==0).*2*Vf.*abs(ik))+4*B.Eoss*fsk+4*B.Qg_E*fsk;
    end
    r.zcs=max(r.zcs_ph); r.Ploss=sum(r.Ploss_ph);
end

function [dx,io,iin] = deriv(iC,vC,Vb,s,Vin,C,L,R,Vf,Cbus,Iload)
% 구간 s(0 데드, 1 충전, 2 방전)별 상태 미분. dx 행: [diC; dvC; dVb]
    di=zeros(size(iC));
    p1=s==1; p2=s==2; d=s==0;
    di(p1)=(Vin-Vb-vC(p1)-iC(p1).*R(p1))./L(p1);
    di(p2)=(Vb-vC(p2)-iC(p2).*R(p2))./L(p2);
    dp=d&(iC>1e-3); dn=d&(iC<-1e-3);
    di(dp)=(-vC(dp)-iC(dp).*R(dp)-2*Vf)./L(dp);          % 다이오드 환류
    di(dn)=(Vin-vC(dn)-iC(dn).*R(dn)+2*Vf)./L(dn);       % 회생
    io=zeros(size(iC)); io(p1)=iC(p1); io(p2)=-iC(p2);    % 버스로 나가는 전류
    iin=zeros(size(iC)); iin(p1)=iC(p1); iin(dn)=iC(dn);  % 입력에서 들어오는 전류
    dx=[di; iC./C; (sum(io)-Iload)/Cbus*ones(1,numel(iC))];
end
