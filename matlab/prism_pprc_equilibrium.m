function x = prism_pprc_equilibrium(Vbat, power, resistance, vref)
% Lossless output-fed bipolar average model. x=[i_path;v_ser;v_bus;i_dab].
if nargin<3, resistance=0.0132; end
if nargin<4, vref=400; end
vm=Vbat/2; disc=vm^2-4*resistance*power;
assert(disc>=0 && vm>0 && vref>0,'No high-voltage equilibrium');
ip=2*power/(vm+sqrt(disc));
x=[ip;vref-vm+resistance*ip;vref;ip];
end
