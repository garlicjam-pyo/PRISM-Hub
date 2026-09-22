function [r,w] = prism_sim_array(B,fr0,N,Vbat,Iload,Cbus,mode,fratio,tol,R_in,ncyc,Nstep,vC0,Vb0,C_in,en)
    if nargin<16 || isempty(en), en=ones(1,N); end
    C=B.Cfly*ones(1,N); L=B.Lr*ones(1,N); R=(2*B.Rds+B.ESR+B.RL+B.Rmisc)*ones(1,N);
    if ~isempty(tol)
        C=C.*(1+tol.C*(2*rand(1,N)-1)); L=L.*(1+tol.L*(2*rand(1,N)-1)); R=R.*(1+tol.R*(2*rand(1,N)-1));
    end
    Vf=B.Vf; td=B.tdead; fs=fratio*fr0; T=1/fs; dt=T/Nstep; n=ncyc*Nstep; ndead=round(td/dt); half=Nstep/2; ndet=round(B.tdet/dt);
    off=round((0:N-1)*(Nstep/2)/N);
    Vo0=Vbat/2; iC=zeros(1,N); if isempty(vC0), vC=Vo0*ones(1,N); else, vC=vC0*ones(1,N); end
    if isempty(Vb0), Vb=Vo0; else, Vb=Vb0; end
    if R_in>0, Vin=0; else, Vin=Vbat; end
    if isempty(C_in), C_in=100e-6; end
    t_on=0.5/fr0*(1-2*td*fr0); min_on=round(0.8*t_on/dt); max_on=round(1.12*t_on/dt);
    st=zeros(1,N); nxt=ones(1,N); tmr=-off; oncnt=zeros(1,N); armed=false(1,N); det=zeros(1,N); pulse_sign=zeros(1,N);
    Li=zeros(n,N,'single'); Lv=zeros(n,N,'single'); Lb=zeros(n,1,'single'); Ls=zeros(n,N,'int8'); Lio=zeros(n,N,'single');
    for k=0:n-1
        if strcmp(mode,'zcp')
            start=(st==0)&(tmr>=ndead); st(start)=nxt(start); nxt(start)=3-nxt(start);
            armed(start)=false; det(start)=0; oncnt(start)=0; tmr(start)=0;
            new_arm=(st~=0)&~armed&(abs(iC)>B.ithr*5);
            pulse_sign(new_arm)=sign(iC(new_arm)); armed=armed|new_arm;
            cross=(st~=0)&armed&(pulse_sign.*iC<B.ithr);
            det(~cross)=0;
            det(cross)=det(cross)+1; oncnt(st~=0)=oncnt(st~=0)+1;
            stop=(st~=0)&(((oncnt>=min_on)&cross&(det>ndet))|(oncnt>=max_on));
            st(stop)=0; tmr(stop)=0; tmr(st==0)=tmr(st==0)+1; s=st;
        else
            m=mod(k-off,Nstep); s=zeros(1,N);
            s(m<half & m>=ndead)=1; s(m>=half & (m-half)>=ndead)=2;
        end
        s(~en)=0;
        [k1,io,iin]=deriv(iC,vC,Vb,s,Vin,C,L,R,Vf,Cbus,Iload);
        k2=deriv(iC+0.5*dt*k1(1,:),vC+0.5*dt*k1(2,:),Vb+0.5*dt*k1(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        k3=deriv(iC+0.5*dt*k2(1,:),vC+0.5*dt*k2(2,:),Vb+0.5*dt*k2(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        k4=deriv(iC+dt*k3(1,:),vC+dt*k3(2,:),Vb+dt*k3(3,1),s,Vin,C,L,R,Vf,Cbus,Iload);
        Li(k+1,:)=iC; Lv(k+1,:)=vC; Lb(k+1)=Vb; Ls(k+1,:)=s; Lio(k+1,:)=io;
        iCn=iC+dt/6*(k1(1,:)+2*k2(1,:)+2*k3(1,:)+k4(1,:));
        vC=vC+dt/6*(k1(2,:)+2*k2(2,:)+2*k3(2,:)+k4(2,:));
        Vb=Vb+dt/6*(k1(3,1)+2*k2(3,1)+2*k3(3,1)+k4(3,1));
        blk=(s==0)&(iCn.*iC<=0); iCn(blk)=0; iC=iCn;
        if R_in>0, Vin=Vin+dt*((Vbat-Vin)/R_in-sum(iin))/C_in; end
    end
    t=(0:n-1)'*dt; w.t=t; w.i=Li; w.v=Lv; w.vb=Lb; w.st=Ls; w.io=Lio;
    msk=t>=t(end)-10*T; r.Vbus=mean(Lb(msk)); r.ripple=max(Lb(msk))-min(Lb(msk));
    for kk=1:N
        ik=double(Li(msk,kk)); sk=double(Ls(msk,kk)); tr=find(diff(sk)~=0);
        offk=tr(sk(tr)~=0 & sk(tr+1)==0); onk=tr(sk(tr)==0 & sk(tr+1)==1);
        Ipk=max(abs(ik)); if isempty(offk), ioff=0; else, ioff=max(abs(ik(offk))); end
        if numel(onk)>2, fsk=1/(mean(diff(onk))*dt); else, fsk=fs; end
        r.zcs_ph(kk)=ioff/max(Ipk,1e-6); r.Iavg(kk)=mean(double(Lio(msk,kk)));
        r.Ploss_ph(kk)=mean(ik.^2)*R(kk)+mean((sk==0).*2*Vf.*abs(ik))+4*B.Eoss*fsk+4*B.Qg_E*fsk;
    end
    r.zcs=max(r.zcs_ph); r.Ploss=sum(r.Ploss_ph);
end

function [dx,io,iin] = deriv(iC,vC,Vb,s,Vin,C,L,R,Vf,Cbus,Iload)
    di=zeros(size(iC));
    p1=s==1; p2=s==2; d=s==0;
    di(p1)=(Vin-Vb-vC(p1)-iC(p1).*R(p1))./L(p1);
    di(p2)=(Vb-vC(p2)-iC(p2).*R(p2))./L(p2);
    dp=d&(iC>1e-3); dn=d&(iC<-1e-3);
    di(dp)=(-vC(dp)-iC(dp).*R(dp)-2*Vf)./L(dp);
    di(dn)=(Vin-vC(dn)-iC(dn).*R(dn)+2*Vf)./L(dn);
    io=zeros(size(iC)); io(p1)=iC(p1); io(p2)=-iC(p2);
    iin=zeros(size(iC)); iin(p1)=iC(p1); iin(dn)=iC(dn);
    dx=[di; iC./C; (sum(io)-Iload)/Cbus*ones(1,numel(iC))];
end
