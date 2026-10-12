function h = sl_line(sys, src, dst)
%SL_LINE  Simulink 신호선을 잇는다.   sl_line(sys, 'Clock/1', 'Gate/1')
h = add_line(sys, src, dst, 'autorouting', 'smart');
end
