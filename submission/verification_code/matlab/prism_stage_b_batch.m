function R = prism_stage_b_batch(C, ctl, opt)
% PRISM_STAGE_B_BATCH  Stage B 6상태 평균모델 + 표본화 제어기(비교·채택 설계)의 독립 MATLAB 구현 (E11)
%
%  여러 시험 사례를 "사례 방향"으로 벡터화해 한 번에 적분한다(시간 방향은 순차). Python 구현
%  (model_stage_b.py, controller_adopted.py, stage_b_tests.py)과 코드를 공유하지 않으며, 같은 방정식과
%  판정 기준을 따로 코딩했다. 사례마다 플랜트 파라미터·전달지연·부하 프로파일이 다를 수 있다.
%
%  플랜트  x = [i_p; v_s; v_bus; i_h; v_link; i_dab]  (각 행 1 x N)
%    L di_p/dt = V_bat/2 - R i_p + v_s - v_bus,   Cs dv_s/dt = i_h - i_p
%    Cb dv_bus/dt = i_p - (P + P_DAB,in)/v_bus,    Lh di_h/dt = m v_link - v_s - Rh i_h
%    Cl dv_link/dt = i_dab - m i_h,                tau di_dab/dt = i_link_cmd - i_dab
%  적분   명시적 중점법, 간격 opt.dt. 제어 갱신 Ts = 5 us, 지령은 lag = delay/dt 스텝 뒤에 적용.
%  제어기 상태궤환 + 버스전압 적분 -> 전류지령(+-84 A, 역포화) -> 내부 전류 법칙 -> 변조율,
%         링크전압 PI + 소비전류 앞먹임 -> DAB 링크전류 지령(순시 한계).
%         ctl.predict = true 이면 채택 설계: 직전 지령 m(k-1)과 공칭 모델로 [i_p, v_s, i_h]를
%         한 주기 앞까지 중점법 n_sub 단계로 예측해 지령을 계산(v_bus, v_link는 측정값).
%  입력   C   : 1 x N 필드 vbat, power0, power1, profile(0 스텝, 1-4 계약 시퀀스), tier,
%               p(플랜트 파라미터 구조체, 각 필드 1 x N)
%         ctl : K(1x5), cp(제어기 공칭 파라미터 구조체), predict(논리), n_sub
%         opt : dt, duration, step, T1_A, T2_A, T2_band, tail_ih, tail_m
%  출력   R   : 사례별 지표와 판정(구조체 배열)

N=numel(C.vbat); p=C.p; cp=ctl.cp; K=ctl.K;
dt=opt.dt; n=round(opt.duration/dt); sample=round(cp.Ts/dt); stp=opt.step;
assert(abs(sample*dt-cp.Ts)<1e-12,'dt가 제어주기를 나누지 않음');
lag=round(p.delay/dt); assert(all(abs(lag*dt-p.delay)<1e-12),'dt가 전달지연을 나누지 않음');
Lmax=max(lag)+1;

%% 평형점(사례별): v_ref i_p = P0 + P_DAB,in,  v_s = v_ref - V_bat/2 + R i_p
x=zeros(6,N); u=zeros(2,N);
for c=1:N
    pr=@(pl) (pl>=0).*pl/p.eta(c)+(pl<0).*pl*p.eta(c);
    ip=fzero(@(i) p.vref(c)*i-C.power0(c)-pr((p.vref(c)-C.vbat(c)/2+(p.R(c)+p.Rh(c))*i)*i),[-500 500]);
    vs=p.vref(c)-C.vbat(c)/2+p.R(c)*ip; m=(vs+p.Rh(c)*ip)/p.vlink(c);
    x(:,c)=[ip;vs;p.vref(c);ip;p.vlink(c);m*ip]; u(:,c)=[m;m*ip];
end
% 제어기 초기화: 적분기를 평형점 지령(= i_p)에 맞춤
q=-(x(1,:)+K(1)*x(1,:)+K(2)*x(2,:)+K(3)*x(3,:)+K(4)*x(4,:))/K(5); qlink=zeros(1,N); uprev=u;
wl=2*pi*cp.link_bw;
bufm=repmat(u(1,:),Lmax,1); bufi=repmat(u(2,:),Lmax,1); colofs=(0:N-1)*Lmax;

%% 통계 누적값
alive=true(1,N); endk=(n-1)*ones(1,N);
S.path=zeros(1,N); S.bridge=S.path; S.link=S.path; S.series=S.path; S.dabp=S.path; S.modu=S.path;
S.vbmax=-inf(1,N); S.vlmin=inf(1,N); S.vlmax=-inf(1,N); S.env=-inf(1,N); S.res=zeros(1,N);
S.postmin=inf(1,N); S.postmax=-inf(1,N); S.lastout=-ones(1,N); S.vbend=zeros(1,N);
W=ceil(0.001/dt)+3; ringk=-ones(W,1); rvb=zeros(W,N); rih=rvb; rm=rvb;   % 마지막 1 ms 기록(링 버퍼)
T.vb=zeros(1,N); T.ih=T.vb; T.m=T.vb;                                     % 끝 1 ms 변동폭

for k=0:n-1
    t=k*dt;
    P=power_at(t,C,stp);
    if mod(k,sample)==0
        [u,q,qlink,uprev]=controller(x,q,qlink,uprev,C.vbat,K,cp,ctl,wl);
    end
    w=mod(k,Lmax)+1; bufm(w,:)=u(1,:); bufi(w,:)=u(2,:);
    r=mod(k-lag,Lmax)+1+colofs; ua=[bufm(r);bufi(r)];                 % lag 스텝 전의 지령 적용
    d1=plant(x,ua,C.vbat,P,p);
    % 에너지 보존 검산
    pin=prim(x(5,:).*x(6,:),p.eta);
    stored=p.L.*x(1,:).*d1(1,:)+p.Cs.*x(2,:).*d1(2,:)+p.Cb.*x(3,:).*d1(3,:)+p.Lh.*x(4,:).*d1(4,:)+p.Clink.*x(5,:).*d1(5,:);
    expct=C.vbat/2.*x(1,:)-p.R.*x(1,:).^2-p.Rh.*x(4,:).^2-P-(pin-x(5,:).*x(6,:));
    res=abs(stored-expct); S.res(alive)=max(S.res(alive),res(alive));
    xn=x+dt*plant(x+0.5*dt*d1,ua,C.vbat,P,p);                          % 중점법
    x(:,alive)=xn(:,alive);
    % 기록(살아 있는 사례만)
    a=alive; tk=(k+1)*dt;
    S.path(a)=max(S.path(a),abs(x(1,a))); S.bridge(a)=max(S.bridge(a),abs(x(4,a)));
    S.series(a)=max(S.series(a),abs(x(2,a))); S.link(a)=max(S.link(a),abs(x(6,a)));
    S.dabp(a)=max(S.dabp(a),abs(x(5,a).*x(6,a))); S.modu(a)=max(S.modu(a),abs(ua(1,a)));
    S.vbmax(a)=max(S.vbmax(a),x(3,a)); S.vlmin(a)=min(S.vlmin(a),x(5,a)); S.vlmax(a)=max(S.vlmax(a),x(5,a));
    lim=dablimit(x(3,:),x(5,:),p); S.env(a)=max(S.env(a),abs(x(6,a))-lim(a));
    if tk>=stp
        S.postmin(a)=min(S.postmin(a),x(3,a)); S.postmax(a)=max(S.postmax(a),x(3,a));
        o=a & abs(x(3,:)-p.vref)>4; S.lastout(o)=k;
    end
    S.vbend(a)=x(3,a);
    j=mod(k,W)+1; ringk(j)=k; rvb(j,a)=x(3,a); rih(j,a)=x(4,a); rm(j,a)=ua(1,a);
    % 붕괴 판정(Python과 같은 조건): 비유한값, v_bus < 50 V, v_link < 10 V
    dead=a & (any(~isfinite(x),1) | x(3,:)<50 | x(5,:)<10);
    if any(dead)
        endk(dead)=k; T=tailstats(T,find(dead),k,dt,stp,ringk,rvb,rih,rm);
        alive(dead)=false;
    end
end
T=tailstats(T,find(alive),n-1,dt,stp,ringk,rvb,rih,rm);

%% 판정
R=struct([]);
for c=1:N
    pc=structfun(@(v) v(c),p,'UniformOutput',false);
    completed=alive(c); e=endk(c); tend=(e+1)*dt;
    viol=[S.path(c)>pc.path_max+1e-6, S.bridge(c)>pc.path_max+1e-6, S.series(c)>pc.series_max+1e-6, ...
          S.link(c)>pc.link_max+1e-6, S.env(c)>1e-3, S.dabp(c)>pc.power_max+1e-3, ...
          S.vlmin(c)<90 || S.vlmax(c)>110, S.modu(c)>pc.modulation_max+1e-9];
    ports=~any(viol);
    % 회복시간: 마지막으로 +-4 V를 벗어난 다음 표본까지(끝까지 밖이거나 미완료면 없음)
    if S.lastout(c)<0, rec=0; elseif S.lastout(c)==e, rec=NaN; else, rec=(S.lastout(c)+2)*dt-stp; end
    if ~completed, rec=NaN; end
    chk=[completed, ports, max(abs(S.postmin(c)-400),abs(S.postmax(c)-400))<=8, abs(S.vbend(c)-400)<=4, ...
         isfinite(rec) && rec<=0.001, T.vb(c)<=0.1];
    internal=T.ih(c)<=opt.tail_ih && T.m(c)<=opt.tail_m;
    if C.tier(c)==1
        ok=all(chk) && internal && S.path(c)<=opt.T1_A && S.bridge(c)<=opt.T1_A;
    else
        ok=completed && ports && S.postmin(c)>=opt.T2_band(1) && S.postmax(c)<=opt.T2_band(2) && ...
           abs(S.vbend(c)-400)<=4 && S.path(c)<=opt.T2_A && S.bridge(c)<=opt.T2_A && internal;
    end
    R(c).pass_=logical(ok); R(c).completed=completed; R(c).end_time=tend;
    R(c).path_peak=S.path(c); R(c).bridge_peak=S.bridge(c); R(c).link_peak=S.link(c);
    R(c).dab_power_peak=S.dabp(c); R(c).droop=pc.vref-S.postmin(c); R(c).vbus_min_post=S.postmin(c);
    R(c).vbus_max_post=S.postmax(c); R(c).recovery_s=rec; R(c).tail_ripple_V=T.vb(c);
    R(c).modulation_peak=S.modu(c); R(c).series_peak=S.series(c); R(c).vlink_min=S.vlmin(c);
    R(c).tail_ih_pp_A=T.ih(c); R(c).tail_m_pp=T.m(c); R(c).energy_residual_max=S.res(c);
    R(c).ports_ok=ports; R(c).checks=chk;
end
end

% ------------------------------------------------------------------ 부하 프로파일
function P=power_at(t,C,stp)
if t>=stp, P=C.power1; else, P=C.power0; end
if any(C.profile>0)
    s=(t-stp)*1e3;                                              % 시퀀스 시작 후 경과 [ms]
    for kind=1:4
        sel=C.profile==kind; if ~any(sel), continue; end
        if t<stp, P(sel)=ifelse(kind<=2,12700,25000); continue; end
        if kind==1 || kind==3, sc=min(8500,s*4000); else, sc=min(8500,(floor(s)+1)*4000); end
        if kind<=2
            P(sel)=min(25000,12700+3800+sc+60*s*3);            % V2L +3.8 kW, Stage C 4 kW/ms, 느린 부하 0.06 kW/ms x 3
        else
            P(sel)=max(-3200,25000-3800-sc-min(6000,500*s)-min(7000,500*s)-min(2900,500*s));
        end
    end
end
end

function y=ifelse(c,a,b)
if c, y=a; else, y=b; end
end

% ------------------------------------------------------------------ 플랜트
function y=prim(pl,eta)
y=pl./eta; neg=pl<0; y(neg)=pl(neg).*eta(neg);                   % 링크 전력 -> 버스 측 DAB 전력
end

function dx=plant(x,u,vbat,P,p)
pin=prim(x(5,:).*x(6,:),p.eta);
dx=[(vbat/2-p.R.*x(1,:)+x(2,:)-x(3,:))./p.L;
    (x(4,:)-x(1,:))./p.Cs;
    (x(1,:)-(P+pin)./x(3,:))./p.Cb;
    (u(1,:).*x(5,:)-x(2,:)-p.Rh.*x(4,:))./p.Lh;
    (x(6,:)-u(1,:).*x(4,:))./p.Clink;
    (u(2,:)-x(6,:))./p.tau];
end

function lim=dablimit(vb,vl,p)
% DAB 링크전류 순시 한계 = min(정격, SPS 전달 한계, 전력 한계 / v_link)
sps=max(vb,0).*p.turns.*p.phase_max.*(1-p.phase_max/pi)./(2*pi*p.fs.*p.Ldab);
lim=min(min(p.link_max,sps),p.power_max./max(vl,1e-9));
end

% ------------------------------------------------------------------ 제어기
function [u,q,qlink,uprev]=controller(x,q,qlink,uprev,vbat,K,cp,ctl,wl)
xs=x;
if ctl.predict                                                   % 연산 지연 보상: 1주기 예측
    h=cp.Ts/ctl.n_sub; m=uprev(1,:); vb=x(3,:); vl=x(5,:);
    s=[x(1,:);x(2,:);x(4,:)];
    for j=1:ctl.n_sub
        f1=fs(s,m,vb,vl,vbat,cp); f2=fs(s+0.5*h*f1,m,vb,vl,vbat,cp); s=s+h*f2;
    end
    xs(1,:)=s(1,:); xs(2,:)=s(2,:); xs(4,:)=s(3,:);
end
raw=-(K(1)*xs(1,:)+K(2)*xs(2,:)+K(3)*xs(3,:)+K(4)*xs(4,:))-K(5)*q;
iref=min(cp.reference_max,max(-cp.reference_max,raw));
q=q+cp.Ts*(cp.vref-x(3,:))+0.1*(iref-raw)/(-K(5));                % 적분(측정 v_bus) + 역포화
mraw=(xs(2,:)+cp.Rh*xs(4,:)+cp.Lh/cp.inner_tau*(iref-xs(4,:)))./xs(5,:);
m=min(cp.modulation_max,max(-cp.modulation_max,mraw));
rawlink=m.*xs(4,:)+cp.Clink*(2*0.7*wl*(cp.vlink-x(5,:))+wl*wl*qlink);
sps=max(x(3,:),0)*cp.turns*cp.phase_max*(1-cp.phase_max/pi)/(2*pi*cp.fs*cp.Ldab);
lim=min(min(cp.link_max,sps),cp.power_max./max(x(5,:),1e-9));
il=min(lim,max(-lim,rawlink));
qlink=qlink+cp.Ts*(cp.vlink-x(5,:))+0.1*(il-rawlink)/(cp.Clink*wl*wl);
u=[m;il]; uprev=u;
end

function d=fs(s,m,vb,vl,vbat,cp)
% 예측용 공칭 모델(고속 상태 [i_p, v_s, i_h])
d=[(vbat/2-cp.R*s(1,:)+s(2,:)-vb)/cp.L; (s(3,:)-s(1,:))/cp.Cs; (m.*vl-s(2,:)-cp.Rh*s(3,:))/cp.Lh];
end

% ------------------------------------------------------------------ 끝 1 ms 변동폭
function T=tailstats(T,idx,e,dt,stp,ringk,rvb,rih,rm)
if isempty(idx), return; end
% 버스 리플은 스텝 이후 마지막 1 ms(max(step, t_end-1 ms) 이후), 내부 진동은 마지막 1 ms
tt=(ringk+1)*dt; ok=ringk>=0 & ringk<=e;
sel1=ok & tt>=max(stp,(e+1)*dt-0.001); sel2=ok & tt>=(e+1)*dt-0.001;
for c=idx
    v=rvb(sel1,c); T.vb(c)=max(v)-min(v);
    v=rih(sel2,c); T.ih(c)=max(v)-min(v);
    v=rm(sel2,c);  T.m(c)=max(v)-min(v);
end
end
