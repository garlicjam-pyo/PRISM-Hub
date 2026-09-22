function dx = prism_pprc_rhs(x,command,Vbat,power,L,Cs,Cb,R,tau)
% Ideal DAB port preserves instantaneous power; includes no switching losses.
if nargin<5, L=1.5e-6; Cs=100e-6; Cb=400e-6; R=.0132; tau=10e-6; end
ip=x(1); vs=x(2); vb=x(3); id=x(4);
dx=[(Vbat/2-R*ip+vs-vb)/L; (id-ip)/Cs; ...
    (ip-(power+vs*id)/vb)/Cb; (command-id)/tau];
end
