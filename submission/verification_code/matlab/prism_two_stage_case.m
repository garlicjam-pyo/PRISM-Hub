function r = prism_two_stage_case(c)
% PRISM_TWO_STAGE_CASE  Stage B 유한 링크 6상태 평균모델 + 비교 설계 제어기의 독립 MATLAB 구현 (E2)
%
%  Python(model_stage_b.py, controller_reference.py)과 같은 방정식을 따로 코딩한 것이다.
%  공유하는 것은 사례 정의(전압, 부하, 이득 K, 파라미터)뿐이며, 평형점 계산·적분·지연 버퍼·
%  제어 법칙·판정 로직은 모두 이 파일에서 독립적으로 계산한다.
%
%  상태 x = [i_p; v_s; v_bus; i_h; v_link; i_dab],  입력 u = [m; i_link_cmd]
%    L  di_p/dt   = V_bat/2 - R i_p + v_s - v_bus
%    Cs dv_s/dt   = i_h - i_p
%    Cb dv_bus/dt = i_p - (P_load + P_DAB,in)/v_bus
%    Lh di_h/dt   = m v_link - v_s - Rh i_h
%    Cl dv_link/dt= i_dab - m i_h
%    tau di_dab/dt= i_link_cmd - i_dab
%  적분: 명시적 중점법(간격 c.dt), 제어 갱신 Ts = 5 us, 전달지연 p.delay(버퍼)
%  제어: 상태궤환 + 버스전압 적분 -> 브리지 전류지령(+-84 A 포화, 역포화) -> 내부 전류 법칙 -> 변조율,
%        링크전압 PI + 소비전류 앞먹임 -> DAB 링크전류 지령(순시 한계로 제한)
%  입력 c: name, vbat, power0, power1(1 ms에 스텝), dt, duration, K(1x5), parameters,
%          control_parameters(선택: 제어기가 아는 공칭값. 없으면 parameters와 같음)
%  출력 r: 지표(강하, 피크 전류 등), 포트 한계 위반(violations), 전압 품질 6항목(checks)

p=c.parameters; K=reshape(c.K,1,[]);
cp=p; if isfield(c,'control_parameters'), cp=c.control_parameters; end
% 평형점: 전력수지 v_ref i_p = P_load + P_DAB,in 을 i_p에 대해 푼다
ip=fzero(@(i) p.vref*i-c.power0-primary((p.vref-c.vbat/2+(p.R+p.Rh)*i)*i,p),[-500 500]);
vs=p.vref-c.vbat/2+p.R*ip; m=(vs+p.Rh*ip)/p.vlink;
x=[ip;vs;p.vref;ip;p.vlink;m*ip]; u=[m;m*ip];
q=-(ip+K(1:4)*x(1:4))/K(5); qlink=0;                    % 적분기 초기값(평형점에서 지령 = i_p)
dt=c.dt; n=round(c.duration/dt); sample=round(cp.Ts/dt); lag=round(p.delay/dt);
assert(abs(sample*dt-cp.Ts)<1e-12 && abs(lag*dt-p.delay)<1e-12,'dt가 제어주기·지연을 나누지 않음');
buffer=repmat(u',lag+1,1); tick=1; trace=zeros(n,6); controls=zeros(n,2);
residual=0; completed=true; wlink=2*pi*cp.link_bw;
for k=1:n
    t=(k-1)*dt; power=c.power0;
    if t>=.001, power=c.power1; end
    if mod(k-1,sample)==0
        raw=-K(1:4)*x(1:4)-K(5)*q;                                   % 상태궤환 + 적분
        iref=clip(raw,cp.reference_max);                             % 전류지령 포화 +-84 A
        q=q+cp.Ts*(cp.vref-x(3))+.1*(iref-raw)/(-K(5));              % 적분 + 역포화 보정
        mraw=(x(2)+cp.Rh*x(4)+cp.Lh/cp.inner_tau*(iref-x(4)))/x(5);  % 내부 전류 법칙
        m=clip(mraw,cp.modulation_max);
        rawlink=m*x(4)+cp.Clink*(2*.7*wlink*(cp.vlink-x(5))+wlink^2*qlink);   % 링크전압 PI + 앞먹임
        ilink=clip(rawlink,limit(x(3),x(5),cp));
        qlink=qlink+cp.Ts*(cp.vlink-x(5))+.1*(ilink-rawlink)/(cp.Clink*wlink^2);
        u=[m;ilink];
    end
    buffer(tick,:)=u'; applied=buffer(mod(tick,size(buffer,1))+1,:)';   % lag 스텝 전의 지령을 적용
    tick=mod(tick,size(buffer,1))+1;
    d1=plant(x,applied,c.vbat,power,p);
    % 에너지 보존 검산: 저장에너지 변화율 = 입력 - 저항손실 - 부하 - DAB 손실
    stored=sum(x(1:5).*[p.L;p.Cs;p.Cb;p.Lh;p.Clink].*d1(1:5));
    loss=primary(x(5)*x(6),p)-x(5)*x(6);
    residual=max(residual,abs(stored-(c.vbat/2*x(1)-p.R*x(1)^2-p.Rh*x(4)^2-power-loss)));
    x=x+dt*plant(x+dt*.5*d1,applied,c.vbat,power,p);                 % 중점법
    trace(k,:)=x'; controls(k,:)=applied';
    if ~all(isfinite(x)) || x(3)<50 || x(5)<10                          % 붕괴 시 조기 종료
        trace=trace(1:k,:); controls=controls(1:k,:); completed=false; break
    end
end
t=(1:size(trace,1))'*dt; post=trace(t>=.001,3);
% 포트 물리 한계 위반
limits=arrayfun(@(vb,vl) limit(vb,vl,p),trace(:,3),trace(:,5));
violations.path_current=max(abs(trace(:,1)))>p.path_max+1e-6;
violations.bridge_current=max(abs(trace(:,4)))>p.path_max+1e-6;
violations.series_voltage=max(abs(trace(:,2)))>p.series_max+1e-6;
violations.link_current_rating=max(abs(trace(:,6)))>p.link_max+1e-6;
violations.instantaneous_dab_envelope=max(abs(trace(:,6))-limits)>1e-3;
violations.dab_power=max(abs(trace(:,5).*trace(:,6)))>p.power_max+1e-3;
violations.link_voltage_band=min(trace(:,5))<90 || max(trace(:,5))>110;
violations.modulation=max(abs(controls(:,1)))>p.modulation_max+1e-9;
r.name=c.name; r.vbat=c.vbat; r.power0=c.power0; r.power1=c.power1;
r.droop=p.vref-min(post); r.vbus_end=trace(end,3); r.vbus_max=max(trace(:,3));
r.vlink_min=min(trace(:,5)); r.vlink_max=max(trace(:,5));
r.path_peak=max(abs(trace(:,1))); r.bridge_peak=max(abs(trace(:,4)));
r.link_peak=max(abs(trace(:,6))); r.series_peak=max(abs(trace(:,2)));
r.dab_power_peak=max(abs(trace(:,5).*trace(:,6))); r.modulation_peak=max(abs(controls(:,1)));
r.energy_residual_max=residual; r.end_time=t(end); r.completed=completed;
r.violations=violations; r.within_port_limits=~any(structfun(@(v)v,violations));
r.voltage_quality_pass=completed && min(post)>=392 && max(post)<=408 && abs(trace(end,3)-400)<=4;
% 회복시간: 마지막으로 +-4 V를 벗어난 다음 표본까지(끝까지 밖이면 NaN)
outside=find(t>=.001 & abs(trace(:,3)-400)>4);
r.recovery_s=0;
if ~isempty(outside)
    if outside(end)==numel(t), r.recovery_s=NaN;
    else, r.recovery_s=t(outside(end)+1)-.001; end
end
if ~completed, r.recovery_s=NaN; end
tail=trace(t>=max(.001,t(end)-.001),3); r.tail_ripple_V=max(tail)-min(tail);
% 전압 품질 6항목
r.checks.completed=completed; r.checks.ports=r.within_port_limits;
r.checks.voltage_excursion=all(abs(post-400)<=8);
r.checks.final_voltage=abs(trace(end,3)-400)<=4;
r.checks.recovery_1ms=isfinite(r.recovery_s) && r.recovery_s<=.001;
r.checks.final_1ms_ripple=r.tail_ripple_V<=.1;
r.requirements_pass=all(structfun(@(v)v,r.checks));
assert(residual<1e-7,'에너지 보존 검산 실패');
end

function y=clip(x,maximum)
y=min(maximum,max(-maximum,x));
end

function pin=primary(power,p)
% 링크 전력 -> 버스 측 DAB 전력(방향별 효율 eta)
if power>=0, pin=power/p.eta; else, pin=power*p.eta; end
end

function maximum=limit(vbus,vlink,p)
% DAB 링크전류 순시 한계 = min(정격, SPS 전달 한계, 전력 한계/v_link)
sps=max(vbus,0)*p.turns*p.phase_max*(1-p.phase_max/pi)/(2*pi*p.fs*p.Ldab);
maximum=min([p.link_max,sps,p.power_max/max(vlink,1e-9)]);
end

function dx=plant(x,u,vbat,power,p)
% 6상태 평균모델 미분방정식
ip=x(1); vs=x(2); vb=x(3); ih=x(4); vl=x(5); id=x(6); m=u(1);
pin=primary(vl*id,p);
dx=[(vbat/2-p.R*ip+vs-vb)/p.L; (ih-ip)/p.Cs; (ip-(power+pin)/vb)/p.Cb; ...
    (m*vl-vs-p.Rh*ih)/p.Lh; (id-m*ih)/p.Clink; (u(2)-id)/p.tau];
end
