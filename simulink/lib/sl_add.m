function h = sl_add(sys, src, name, pos, varargin)
%SL_ADD  라이브러리 블록을 sys 안에 추가하고 위치와 파라미터를 설정한다.
%
%   h = sl_add(sys, 'fl_lib/Electrical/Electrical Elements/Inductor', 'Lr', [x1 y1 x2 y2], 'l', 'TB.A.Lr')
%
%   pos      : [왼쪽 위쪽 오른쪽 아래쪽] (픽셀)
%   varargin : set_param 이름/값 쌍. 'Orientation'(right/left/up/down)도 여기서 준다.

h = add_block(src, [sys '/' name], 'Position', pos);
if ~isempty(varargin)
    set_param(h, varargin{:});
end
end
