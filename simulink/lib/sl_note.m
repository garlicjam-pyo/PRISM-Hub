function h = sl_note(sys, txt, pos, style)
%SL_NOTE  모델 캔버스에 설명 주석(annotation)을 넣는다.
%
%   sl_note(sys, '설명 문장', [x1 y1 x2 y2], 'title' | 'box' | 'plain')
%     title : 굵은 큰 글씨(테스트벤치 제목)
%     box   : 옅은 배경의 설명 상자(검증 목적, 판정 기준, 파라미터 표)
%     plain : 일반 글씨(소자 옆 짧은 메모)

if nargin < 4, style = 'plain'; end
h = Simulink.Annotation([sys '/note']);
h.Text = txt;
h.Interpreter = 'off';
h.HorizontalAlignment = 'left';
h.Position = pos;
switch style
    case 'title'
        h.FontSize = 16; h.FontWeight = 'bold';
    case 'box'
        h.FontSize = 10;
        try, h.BackgroundColor = '[0.93, 0.96, 1.0]'; catch, h.BackgroundColor = 'lightBlue'; end
        h.DropShadow = 'off';
    otherwise
        h.FontSize = 10;
end
end
