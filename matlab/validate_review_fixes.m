function results = validate_review_fixes
% Actual MATLAB regression suite. Writes versioned results outside historical reviews.
root=fileparts(fileparts(mfilename('fullpath')));
outdir=fullfile(root,'validation','2026-09-22'); if ~isfolder(outdir), mkdir(outdir); end
results.matlab_version=version;
p=get_parameters();
assert(p.A.Cin_Vrated>p.bat.Vabs);
assert(p.B.Isps<81 && p.B.Isps>80);
assert(~p.C.combined_rating_ok); % known open design issue must remain visible
results.parameters=struct('Isps',p.B.Isps,'PPRC_power',p.B.P_need,'CLLC_required',p.C.Po_combined_required,'CLLC_rating_ok',p.C.combined_rating_ok);

% Physical identity and finite-difference Jacobian independently of the controller.
L=1.5e-6; Cs=100e-6; Cb=400e-6; R=.0132;
for k=1:3
    vs=[648 788 907]; Vbat=vs(k); x=prism_pprc_equilibrium(Vbat,25000,R);
    dx=prism_pprc_rhs(x,x(4),Vbat,25000);
    assert(norm(dx,inf)<1e-5);
    y=x+[3;-2;4;-1]; dy=prism_pprc_rhs(y,10,Vbat,27000);
    err=abs(L*y(1)*dy(1)+Cs*y(2)*dy(2)+Cb*y(3)*dy(3)-(Vbat/2*y(1)-R*y(1)^2-27000));
    assert(err<1e-7); results.equilibrium(k)=struct('Vbat',Vbat,'x',x','energy_residual',err);
end
x=prism_pprc_equilibrium(788,5000); [A,~]=prism_pprc_linearize(L,Cs,Cb);
J=zeros(4); h=1e-4;
for j=1:4
    e=zeros(4,1); e(j)=h;
    J(:,j)=(prism_pprc_rhs(x+e,x(4),788,5000)-prism_pprc_rhs(x-e,x(4),788,5000))/(2*h);
end
assert(max(abs(J-A(1:4,1:4)),[],'all')<.01);
for k=1:3
    vs=[648 788 907]; rr=prism_pprc_step(vs(k),60);
    assert(rr.energy_residual_max<1e-7);
    results.step(k)=rmfield(rr,{'t','x'});
end
rr=prism_pprc_step(788,0); assert(max(abs(rr.x(:,3)-400))<1e-6);
rr=prism_pprc_step(648,50,1e-7,.008); % include slow recovery near current limit
assert(rr.within_port_limits && rr.voltage_quality_pass);
results.rated_low_battery=rmfield(rr,{'t','x'});
assert(~results.step(1).voltage_quality_pass); % 29 kW must not silently pass the 80 A hardware limit
assert(all([results.step(2:3).voltage_quality_pass]) && all([results.step.within_port_limits]));

B.Cfly=7.8125e-6; B.Lr=1.441e-7; B.Rds=6e-3; B.ESR=1.5e-3; B.RL=1e-3; B.Rmisc=1.5e-3;
B.Vf=.9; B.Eoss=24e-6; B.Qg_E=2e-6; B.tdead=100e-9; B.tdet=20e-9; B.ithr=.5;
fr=1/(2*pi*sqrt(B.Lr*B.Cfly));
for k=1:4
    directions=[1 -1 1 -1]; direction=directions(k);
    tol=[]; if k>2, tol=struct('C',.1,'L',.1,'R',.1); end
    rng(3);
    [r,~]=prism_sim_array(B,fr,8,788,375*direction,400e-6,'zcp',1,tol,0,60,340,[],[],[]);
    assert(max(r.zcs_ph)<.05,'Stage A ZCS regression');
    results.stage_a(k)=struct('direction',direction,'tolerance',k>2,'zcs_max',max(r.zcs_ph),'Vbus',r.Vbus,'Iout',sum(r.Iavg));
end
results.status='PASS: scoped regression assertions; open architecture issues are not certified';
fid=fopen(fullfile(outdir,'matlab_results.json'),'w','n','UTF-8');
assert(fid>=0); cleaner=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(results,PrettyPrint=true));
disp(results.status);
end

function p=get_parameters
% Keep prism_design_params' clear inside this function workspace.
prism_design_params;
p=P;
end
