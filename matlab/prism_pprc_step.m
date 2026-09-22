function r = prism_pprc_step(Vbat,dI,dt,tend)
% Reproducible sampled/transport-delayed, lossless bipolar average model.
% Voltage-port violations are reported, not hidden by clamping stored energy.
if nargin<1, Vbat=788; end
if nargin<2, dI=60; end
if nargin<3, dt=1e-7; end
if nargin<4, tend=.0025; end
L=1.5e-6; Cs=100e-6; Cb=400e-6; R=.0132; tau=1e-5;
Ts=5e-6; delay=5e-6; P0=5000; vref=400;
imax=400*4*(pi/3)*(1-1/3)/(2*pi*200e3*11.1e-6);
[A,B]=prism_pprc_linearize(L,Cs,Cb,Vbat,P0,R,tau);
w=2*pi*8000; z=.7;
K=place(A,B,[-z*w+1i*w*sqrt(1-z*z),-z*w-1i*w*sqrt(1-z*z),-w,-w/3,-2.5*w]);
x=prism_pprc_equilibrium(Vbat,P0,R); q=-(x(1)+K(1:4)*x)/K(5);
n=round(tend/dt); t=(0:n-1)'*dt; log=zeros(n,4);
buffer=x(1)*ones(round(delay/dt)+1,1); command=x(1); kc=round(Ts/dt); residual=0;
for k=1:n
    power=P0+400*dI*(t(k)>=.001);
    if mod(k-1,kc)==0
        limit=min([imax,imax*max(x(3),0)/400,8000/max(abs(x(2)),1e-9)]);
        command=min(limit,max(-limit,-K(1:4)*x-K(5)*q));
        q=q+Ts*(vref-x(3));
    end
    buffer=[command;buffer(1:end-1)];
    dx=prism_pprc_rhs(x,buffer(end),Vbat,power,L,Cs,Cb,R,tau);
    de=L*x(1)*dx(1)+Cs*x(2)*dx(2)+Cb*x(3)*dx(3);
    residual=max(residual,abs(de-(Vbat/2*x(1)-R*x(1)^2-power)));
    x=x+dt*dx; log(k,:)=x';
    assert(all(isfinite(x)) && x(3)>50,'Average model collapsed');
end
m=t>=.001; r.Vbat=Vbat; r.dI=dI; r.droop=400-min(log(m,3));
r.vbus_end=log(end,3); r.current_peak=max(abs(log(:,4)));
r.vser_peak=max(abs(log(:,2))); r.power_peak=max(abs(log(:,2).*log(:,4)));
r.energy_residual_max=residual; r.within_port_limits=r.vser_peak<=90 && r.power_peak<=8000 && r.current_peak<=imax+1e-6;
r.voltage_quality_pass=r.droop<=8 && abs(r.vbus_end-400)<=4;
r.K=K; r.t=t; r.x=log;
end
