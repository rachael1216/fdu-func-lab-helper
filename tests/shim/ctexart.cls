% 兼容层：仅在没有安装 ctex 的环境中用于编译预览与冒烟测试；真实环境使用 TeX Live 自带的 ctex。
% 提供：中文字体、汉字间换行（含标点避头尾的简化规则）、首行缩进、1.5 倍行距、章节与图表中文名称。
\NeedsTeXFormat{LaTeX2e}\ProvidesClass{ctexart}[2026/10/29 compatibility layer]
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}\ProcessOptions\relax
\LoadClass{article}
\RequirePackage{fontspec}
\setmainfont{Noto Serif CJK SC}\setsansfont{Noto Sans CJK SC}
\newcommand{\heiti}{\sffamily}\newcommand{\kaishu}{\itshape}
\setlength{\parindent}{2em}\linespread{1.3}
\renewcommand{\contentsname}{目录}\renewcommand{\figurename}{图}\renewcommand{\tablename}{表}
\renewcommand{\refname}{参考文献}\renewcommand{\appendixname}{附录}\renewcommand{\abstractname}{摘要}
% ---- 汉字之间允许断行
\newXeTeXintercharclass\fduhan\newXeTeXintercharclass\fduclose\newXeTeXintercharclass\fduopen
\count@="3400 \loop\XeTeXcharclass\count@=\fduhan \ifnum\count@<"9FFF \advance\count@\@ne\repeat
\XeTeXcharclass"3001=\fduclose \XeTeXcharclass"3002=\fduclose \XeTeXcharclass"FF0C=\fduclose \XeTeXcharclass"FF0E=\fduclose
\XeTeXcharclass"FF1A=\fduclose \XeTeXcharclass"FF1B=\fduclose \XeTeXcharclass"FF01=\fduclose \XeTeXcharclass"FF1F=\fduclose
\XeTeXcharclass"FF09=\fduclose \XeTeXcharclass"300D=\fduclose \XeTeXcharclass"300B=\fduclose \XeTeXcharclass"201D=\fduclose
\XeTeXcharclass"FF08=\fduopen \XeTeXcharclass"300C=\fduopen \XeTeXcharclass"300A=\fduopen \XeTeXcharclass"201C=\fduopen
\XeTeXinterchartoks\fduhan\fduhan={\penalty\z@}
\XeTeXinterchartoks\fduhan\fduopen={\penalty\z@}
\XeTeXinterchartoks\fduclose\fduhan={\penalty\z@}
\XeTeXinterchartoks\fduclose\fduopen={\penalty\z@}
\XeTeXinterchartoks\z@\fduhan={\penalty\z@}
\XeTeXinterchartoks\fduhan\z@={\penalty\z@}
\XeTeXinterchartoks\fduclose\z@={\penalty\z@}
\XeTeXinterchartokenstate=1
