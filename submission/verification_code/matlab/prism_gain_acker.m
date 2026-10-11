function K = prism_gain_acker(vbat, power, cp, z, a)
% PRISM_GAIN_ACKER  Stage B 제어기 이득을 아커만 공식으로 독립 계산한다 (E11, 툴박스 불필요).
%
%  설계 모델(Python design_poles와 같은 정의, 코드는 독립):
%    축약 4상태 [i_p, v_s, v_bus, i_h] + 버스전압 오차 적분 q (dq/dt = -v_bus 편차)
%      L di_p/dt = V_bat/2 - R i_p + v_s - v_bus,  Cs dv_s/dt = i_h - i_p,
%      Cb dv_bus/dt = i_p - (P + P_DAB,in(v_s, i_h))/v_bus,  di_h/dt = (i_ref - i_h)/tau_inner
%    설계점의 수치 야코비안(중심차분, h = 1e-4)으로 A(5x5), B = [0 0 0 1/tau_inner 0]' 를 만든다.
%  극   -z w +- j w sqrt(1-z^2),  -a1 w,  -a2 w,  -a3 w,   w = 2 pi bus_bw
%  계산 아커만 공식 K = [0 0 0 0 1] Co^-1 phi(A).  조건수를 줄이려고 시간축을 w로, 상태를
%       balance()의 변환 D로 척도화한 뒤 계산하고 원래 좌표로 되돌린다(K = Kb D^-1).
%  입력 cp: 제어기 공칭 파라미터 구조체,  z: 감쇠비,  a: [a1 a2 a3]

% 설계점 평형
pr=@(pl) (pl>=0).*pl/cp.eta+(pl<0).*pl*cp.eta;
ip=fzero(@(i) cp.vref*i-power-pr((cp.vref-vbat/2+(cp.R+cp.Rh)*i)*i),[-500 500]);
vs=cp.vref-vbat/2+cp.R*ip; xe=[ip;vs;cp.vref;ip];
f=@(x) [(vbat/2-cp.R*x(1)+x(2)-x(3))/cp.L; (x(4)-x(1))/cp.Cs; ...
        (x(1)-(power+pr((x(2)+cp.Rh*x(4))*x(4)))/x(3))/cp.Cb; -x(4)/cp.inner_tau];
h=1e-4; J=zeros(4);
for j=1:4, e=zeros(4,1); e(j)=h; J(:,j)=(f(xe+e)-f(xe-e))/(2*h); end
A=zeros(5); A(1:4,1:4)=J; A(5,3)=-1; B=zeros(5,1); B(4)=1/cp.inner_tau;
w=2*pi*cp.bus_bw;
poles=[-z*w+1i*w*sqrt(1-z^2); -z*w-1i*w*sqrt(1-z^2); -a(:)*w];
% 척도화: 시간 s -> s/w, 상태 x = D xb
[D,~]=balance(A);                          % D: 순열·척도 변환(가역)
Ab=(D\A*D)/w; Bb=(D\B)/w; pb=poles/w;
Co=zeros(5); v=Bb; for j=1:5, Co(:,j)=v; v=Ab*v; end
phi=eye(5); for j=1:5, phi=phi*(Ab-pb(j)*eye(5)); end
Kb=real([0 0 0 0 1]*(Co\phi));
K=Kb/D;                                     % u = -Kb xb = -Kb D^-1 x
end
