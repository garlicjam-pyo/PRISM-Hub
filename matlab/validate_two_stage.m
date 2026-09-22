function result = validate_two_stage()
% Independent finite-link plant integration using exported, identical gains.
% Run python/validate_two_stage.py first. This is not a switching model.
root=fileparts(fileparts(mfilename('fullpath')));
folder=fullfile(root,'validation','2026-09-22-integration');
cases=jsondecode(fileread(fullfile(folder,'two_stage_cases.json')));
for j=1:numel(cases)
    c=cases(j); p=c.parameters; K=reshape(c.K,1,[]);
    ip=fzero(@(i) p.vref*i-c.power0-primary((p.vref-c.vbat/2+(p.R+p.Rh)*i)*i,p),[-500 500]);
    vs=p.vref-c.vbat/2+p.R*ip; m=(vs+p.Rh*ip)/p.vlink;
    x=[ip;vs;p.vref;ip;p.vlink;m*ip]; u=[m;m*ip];
    q=-(ip+K(1:4)*x(1:4))/K(5); qlink=0;
    dt=c.dt; n=round(c.duration/dt); sample=round(p.Ts/dt); lag=round(p.delay/dt);
    assert(abs(sample*dt-p.Ts)<1e-12 && abs(lag*dt-p.delay)<1e-12);
    buffer=repmat(u',lag+1,1); tick=1; trace=zeros(n,6); controls=zeros(n,2);
    residual=0; completed=true; wlink=2*pi*p.link_bw;
    for k=1:n
        t=(k-1)*dt; power=c.power0;
        if t>=.001, power=c.power1; end
        if mod(k-1,sample)==0
            raw=-K(1:4)*x(1:4)-K(5)*q;
            iref=clip(raw,p.reference_max);
            q=q+p.Ts*(p.vref-x(3))+.1*(iref-raw)/(-K(5));
            mraw=(x(2)+p.Rh*x(4)+p.Lh/p.inner_tau*(iref-x(4)))/x(5);
            m=clip(mraw,p.modulation_max);
            rawlink=m*x(4)+p.Clink*(2*.7*wlink*(p.vlink-x(5))+wlink^2*qlink);
            ilink=clip(rawlink,limit(x(3),x(5),p));
            qlink=qlink+p.Ts*(p.vlink-x(5))+.1*(ilink-rawlink)/(p.Clink*wlink^2);
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
    rows(j)=r; %#ok<AGROW>
    assert(residual<1e-7,'Energy balance mismatch');
    fprintf('%s: droop %.6f V, path peak %.6f A, port limits %d, voltage quality %d\n',c.name,r.droop,r.path_peak,r.within_port_limits,r.voltage_quality_pass);
end
assert(all([rows(1:10).within_port_limits]) && all([rows(1:10).voltage_quality_pass]));
assert(~rows(11).within_port_limits && ~rows(11).voltage_quality_pass);
assert(~rows(12).within_port_limits && rows(12).voltage_quality_pass);
result.scope='Independent MATLAB midpoint integration; shared controller gains from Python';
result.matlab_version=version; result.cases=rows;
result.status='PASS: scoped regression including expected engineering failures';
f=fopen(fullfile(folder,'two_stage_matlab.json'),'w');
cleanup=onCleanup(@() fclose(f)); fwrite(f,jsonencode(result,PrettyPrint=true),'char');
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
