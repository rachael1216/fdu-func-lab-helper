% 仅供无 ctex 的沙箱做编译冒烟测试；真实环境用 TeX Live 自带的 ctex。
\NeedsTeXFormat{LaTeX2e}\ProvidesClass{ctexart}[shim]
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}\ProcessOptions\relax
\LoadClass{article}
\RequirePackage{fontspec}
\setmainfont{Noto Serif CJK TC}\setsansfont{Noto Sans CJK TC}
\newcommand{\heiti}{\sffamily}\newcommand{\kaishu}{\itshape}
