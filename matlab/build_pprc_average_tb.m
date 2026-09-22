function results=build_pprc_average_tb
% Build AND run an energy-conserving average Simulink model (not Simscape switches).
% Bipolar output port is virtual; actual polarity stage and losses remain open.
root=fileparts(fileparts(mfilename('fullpath'))); folder=fullfile(root,'validation','2026-09-22');
if ~isfolder(folder), mkdir(folder); end
mdl='prism_pprc_average_tb'; if bdIsLoaded(mdl), close_system(mdl,0); end
load_system('simulink'); new_system(mdl);
cleanup=onCleanup(@()close_system(mdl,0));
set_param(mdl,'SolverType','Fixed-step','Solver','ode4','FixedStep','1e-7', ...
    'StopTime','.0025','ReturnWorkspaceOutputs','on');
x0=prism_pprc_equilibrium(788,5000); reference=prism_pprc_step(788,60);
K=reference.K; q0=-(x0(1)+K(1:4)*x0)/K(5);
add_block('simulink/Continuous/Integrator',[mdl '/States'],'InitialCondition',mat2str(x0,17),'Position',[480 100 510 140]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Plant'],'Position',[330 80 430 165]);
rt=sfroot; chart=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Plant']);
chart.Script=sprintf(['function dx=plant(x,u,power,Vbat)\n' ...
 'ip=x(1); vs=x(2); vb=x(3); id=x(4);\n' ...
 'dx=[(Vbat/2-.0132*ip+vs-vb)/1.5e-6; (id-ip)/100e-6; ' ...
 '(ip-(power+vs*id)/vb)/400e-6; (u-id)/1e-5];\nend\n']);
add_block('simulink/Sources/Step',[mdl '/LoadPower'],'Time','.001','Before','5000','After','29000','Position',[140 240 175 265]);
add_block('simulink/Sources/Constant',[mdl '/Battery'],'Value','788','Position',[230 280 265 305]);
add_block('simulink/Signal Routing/Demux',[mdl '/Split'],'Outputs','4','Position',[560 110 565 200]);
add_block('simulink/Sources/Constant',[mdl '/Vref'],'Value','400','Position',[630 260 665 285]);
add_block('simulink/Math Operations/Sum',[mdl '/Error'],'Inputs','+-','Position',[700 250 730 280]);
add_block('simulink/Continuous/Integrator',[mdl '/Integral'],'InitialCondition',num2str(q0,17),'Position',[780 250 810 280]);
add_block('simulink/Signal Routing/Mux',[mdl '/Augment'],'Inputs','2','Position',[650 30 655 80]);
add_block('simulink/Math Operations/Gain',[mdl '/Feedback'],'Gain',mat2str(-K,17),'Multiplication','Matrix(K*u)','Position',[710 35 800 65]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/CurrentLimit'],'Position',[830 25 880 80]);
lim=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/CurrentLimit']);
lim.Script=sprintf(['function y=limit(u,x)\n' ...
    'cap=min([80.0800800800801,80.0800800800801*max(x(3),0)/400,8000/max(abs(x(2)),1e-9)]);\n' ...
    'y=min(cap,max(-cap,u));\nend\n']);
add_block('simulink/Discrete/Zero-Order Hold',[mdl '/Sample'],'SampleTime','5e-6','Position',[900 35 945 65]);
add_block('simulink/Continuous/Transport Delay',[mdl '/Delay'],'DelayTime','5e-6','InitialOutput',num2str(x0(1),17),'Position',[990 35 1040 65]);
add_block('simulink/Sinks/To Workspace',[mdl '/Record'],'VariableName','states','SaveFormat','Timeseries','Position',[630 125 720 155]);
net={'Plant/1','States/1';'States/1','Plant/1';'Delay/1','Plant/2';'LoadPower/1','Plant/3';'Battery/1','Plant/4'; ...
     'States/1','Split/1';'States/1','Augment/1';'Integral/1','Augment/2';'Augment/1','Feedback/1'; ...
     'Feedback/1','CurrentLimit/1';'States/1','CurrentLimit/2';'CurrentLimit/1','Sample/1';'Sample/1','Delay/1'; ...
     'Vref/1','Error/1';'Split/3','Error/2';'Error/1','Integral/1';'States/1','Record/1'};
for k=1:size(net,1), add_line(mdl,net{k,1},net{k,2},'autorouting','on'); end
note=Simulink.Annotation(mdl,'Ideal output-fed bipolar PPRC average model. No switch-level, loss, or isolation certification.');
note.Position=[200 350];
set_param(mdl,'SimulationCommand','update');
save_system(mdl,fullfile(folder,[mdl '.slx']));
simout=sim(mdl); trace=simout.get('states'); x=squeeze(trace.Data); t=trace.Time;
if size(x,2)~=4, x=x'; end
vb=x(:,3); m=t>=.001;
results=struct('matlab_version',version,'model',mdl,'model_type','lossless bipolar averaged Simulink model', ...
    'droop',400-min(vb(m)),'vbus_end',vb(end),'current_peak',max(abs(x(:,4))));
results.vser_peak=max(abs(x(:,2))); results.power_peak=max(abs(x(:,2).*x(:,4)));
comparison=interp1(t,vb,reference.t);
results.max_voltage_difference_vs_euler=max(abs(comparison-reference.x(:,3)));
assert(abs(vb(end)-400)<.1 && results.droop<8);
assert(results.vser_peak<=90 && results.power_peak<=8000 && results.current_peak<=80.080081);
assert(results.max_voltage_difference_vs_euler<1);
fid=fopen(fullfile(folder,'simulink_results.json'),'w','n','UTF-8');
fprintf(fid,'%s\n',jsonencode(results,PrettyPrint=true)); fclose(fid);
disp(results);
end
