function [Aa,Ba] = prism_pprc_linearize(L,Cs,Cb,Vbat,power,R,tau)
% CPL Jacobian includes DAB primary power drawn from the regulated bus.
if nargin<4, Vbat=788; end
if nargin<5, power=5e3; end
if nargin<6, R=0.0132; end
if nargin<7, tau=10e-6; end
x=prism_pprc_equilibrium(Vbat,power,R); vs=x(2); vb=x(3); id=x(4);
A=[-R/L 1/L -1/L 0; -1/Cs 0 0 1/Cs; ...
   1/Cb -id/(vb*Cb) (power+vs*id)/(vb^2*Cb) -vs/(vb*Cb); 0 0 0 -1/tau];
Aa=blkdiag(A,0); Aa(5,3)=-1; Ba=[0;0;0;1/tau;0];
end
