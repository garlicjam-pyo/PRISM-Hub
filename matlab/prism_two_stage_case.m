function r = prism_two_stage_case(c)
% Independent averaged plant; optional nominal control_parameters remain frozen.
p=c.parameters; K=reshape(c.K,1,[]);
cp=p; if isfield(c,'control_parameters'), cp=c.control_parameters; end
ip=fzero(@(i) p.vref*i-c.power0-primary((p.vref-c.vbat/2+(p.R+p.Rh)*i)*i,p),[-500 500]);
vs=p.vref-c.vbat/2+p.R*ip; m=(vs+p.Rh*ip)/p.vlink;
x=[ip;vs;p.vref;ip;p.vlink;m*ip]; u=[m;m*ip];
q=-(ip+K(1:4)*x(1:4))/K(5); qlink=0;
dt=c.dt; n=round(c.duration/dt); sample=round(cp.Ts/dt); lag=round(p.delay/dt);
assert(abs(sample*dt-cp.Ts)<1e-12 && abs(lag*dt-p.delay)<1e-12);
buffer=repmat(u',lag+1,1); tick=1; trace=zeros(n,6); controls=zeros(n,2);
residual=0; completed=true; wlink=2*pi*cp.link_bw;
for k=1:n
    t=(k-1)*dt; power=c.power0;
    if t>=.001, power=c.power1; end
    if mod(k-1,sample)==0
        raw=-K(1:4)*x(1:4)-K(5)*q;
        iref=clip(raw,cp.reference_max);
        q=q+cp.Ts*(cp.vref-x(3))+.1*(iref-raw)/(-K(5));
        mraw=(x(2)+cp.Rh*x(4)+cp.Lh/cp.inner_tau*(iref-x(4)))/x(5);
        m=clip(mraw,cp.modulation_max);
        rawlink=m*x(4)+cp.Clink*(2*.7*wlink*(cp.vlink-x(5))+wlink^2*qlink);
        ilink=clip(rawlink,limit(x(3),x(5),cp));
        qlink=qlink+cp.Ts*(cp.vlink-x(5))+.1*(ilink-rawlink)/(cp.Clink*wlink^2);
        u=[m;ilink];
    end
    buffer(tick,:)=u'; applied=buffer(mod(tick,size(buffer,1))+1,:)';
    tick=mod(tick,size(buffer,1))+1;
    d1=plant(x,applied,c.vbat,power,p);
    stored=sum(x(1:5).*[p.L;p.Cs;p.Cb;p.Lh;p.Clink].*d1(1:5));
    loss=primary(x(5)*x(6),p)-x(5)*x(6);
    residual=max(residual,abs(stored-(c.vbat/2*x(1)-p.R*x(1)^2-p.Rh*x(4)^2-power-loss)));
    x=x+dt*plant(x+dt*.5*d1,applied,c.vbat,power,p);
    trace(k,:)=x'; controls(k,:)=applied';
    if ~all(isfinite(x)) || x(3)<50 || x(5)<10
        trace=trace(1:k,:); controls=controls(1:k,:); completed=false; break
    end
end
t=(1:size(trace,1))'*dt; post=trace(t>=.001,3);
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
r.violations=violations; r.within_port_limits=~any(structfun(@(x)x,violations));
r.voltage_quality_pass=completed && min(post)>=392 && max(post)<=408 && abs(trace(end,3)-400)<=4;
outside=find(t>=.001 & abs(trace(:,3)-400)>4);
r.recovery_s=0;
if ~isempty(outside)
    if outside(end)==numel(t), r.recovery_s=NaN;
    else, r.recovery_s=t(outside(end)+1)-.001; end
end
if ~completed, r.recovery_s=NaN; end
r.tail_ripple_V=range(trace(t>=max(.001,t(end)-.001),3));
r.checks.completed=completed; r.checks.ports=r.within_port_limits;
r.checks.voltage_excursion=all(abs(post-400)<=8);
r.checks.final_voltage=abs(trace(end,3)-400)<=4;
r.checks.recovery_1ms=isfinite(r.recovery_s) && r.recovery_s<=.001;
r.checks.final_1ms_ripple=r.tail_ripple_V<=.1;
r.requirements_pass=all(structfun(@(v)v,r.checks));
assert(residual<1e-7,'Energy balance mismatch');
end

function y=clip(x,maximum)
y=min(maximum,max(-maximum,x));
end

function pin=primary(power,p)
if power>=0, pin=power/p.eta; else, pin=power*p.eta; end
end

function maximum=limit(vbus,vlink,p)
sps=max(vbus,0)*p.turns*p.phase_max*(1-p.phase_max/pi)/(2*pi*p.fs*p.Ldab);
maximum=min([p.link_max,sps,p.power_max/max(vlink,1e-9)]);
end

function dx=plant(x,u,vbat,power,p)
ip=x(1); vs=x(2); vb=x(3); ih=x(4); vl=x(5); id=x(6); m=u(1);
pin=primary(vl*id,p);
dx=[(vbat/2-p.R*ip+vs-vb)/p.L; (ih-ip)/p.Cs; (ip-(power+pin)/vb)/p.Cb; ...
    (m*vl-vs-p.Rh*ih)/p.Lh; (id-m*ih)/p.Clink; (u(2)-id)/p.tau];
end
