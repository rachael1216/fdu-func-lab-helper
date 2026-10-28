\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{fdureport}[2026/10/29 FDU functional-lab report class]
% 版式规范见 docs/FORMAT.md：A4，正文宋体小四（12pt），1.5 倍行距，黑体分级标题，三线表，页眉左课程右学号。
\LoadClass[a4paper,12pt]{ctexart}
\RequirePackage[top=2.54cm,bottom=2.54cm,left=3cm,right=3cm,headheight=15pt,footskip=1.1cm]{geometry}
\RequirePackage{graphicx,xcolor,booktabs,array,longtable,fancyhdr,titlesec,tcolorbox,hyperref,enumitem,setspace,caption,amsmath,fontspec}
\tcbuselibrary{skins}
\definecolor{sage}{HTML}{5F7568}\definecolor{greyx}{HTML}{59606A}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=black,citecolor=black}
\linespread{1.3}\selectfont
\setlength{\parindent}{2em}\setlength{\parskip}{0pt}
% 标题：黑体，三号/四号/小四；编号 1、1.1、1.1.1
\renewcommand{\thesection}{\arabic{section}}
\renewcommand{\thesubsection}{\arabic{section}.\arabic{subsection}}
\renewcommand{\thesubsubsection}{\arabic{section}.\arabic{subsection}.\arabic{subsubsection}}
\titleformat{\section}{\heiti\bfseries\fontsize{16}{22}\selectfont}{\thesection}{0.6em}{}
\titleformat{\subsection}{\heiti\bfseries\fontsize{14}{20}\selectfont}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\heiti\bfseries\fontsize{12}{18}\selectfont}{\thesubsubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{1.4ex plus .3ex}{1ex}
\titlespacing*{\subsection}{0pt}{1.1ex plus .3ex}{0.8ex}
\titlespacing*{\subsubsection}{0pt}{0.8ex plus .3ex}{0.6ex}
\renewcommand{\contentsname}{目\quad 录}
\captionsetup{font=small,labelsep=quad}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
% 提示/AI 使用说明
\newtcolorbox{hintbox}{colback=gray!6,colframe=gray!6,borderline west={2.5pt}{0pt}{sage},sharp corners,left=6pt,fontupper=\small\kaishu\color{greyx}}
% 页眉：左 图标+课程，右 学号；细线。页脚：居中页码
\newcommand{\fduheader}[3]{\pagestyle{fancy}\fancyhf{}%
  \fancyhead[L]{\small\color{greyx}\raisebox{-0.12em}{\includegraphics[height=0.42cm]{#1}}\ #2}%
  \fancyhead[R]{\small\color{greyx}#3}\fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0.4pt}\renewcommand{\headrule}{\hbox to\headwidth{\color{sage}\leaders\hrule height \headrulewidth\hfill}}}
% 封面：先 \def 各字段，再 \fducover
\newcommand{\fducover}{\thispagestyle{empty}\begin{center}\vspace*{\fill}
  {\heiti\fontsize{14}{20}\selectfont\color{greyx}复旦大学上海医学院}\par\vspace{0.3em}
  {\heiti\fontsize{16}{22}\selectfont\fducourse}\par\vspace{2.4em}
  {\heiti\bfseries\fontsize{26}{36}\selectfont\fdutitle}\par
  \ifx\fduexp\empty\else\vspace{0.3em}{\color{greyx}实验\ \fduexp}\par\fi
  \vspace{2.4em}\includegraphics[width=7cm]{\fduimage}\par\vspace{2.4em}
  \def\fduline##1##2{\ifx##2\empty\else{\heiti\color{greyx}##1}\quad ##2\par\vspace{0.5em}\fi}
  {\fontsize{14}{20}\selectfont
  \fduline{班\hspace{1em}级}{\fduclass}\fduline{姓\hspace{1em}名}{\fduname}\fduline{学\hspace{1em}号}{\fduid}
  \fduline{小\hspace{1em}组}{\fdugroup}\fduline{指导教师}{\fduteacher}\fduline{日\hspace{1em}期}{\fdudate}}
  \vspace*{\fill}\end{center}\newpage}
% 目录页（罗马页码），之后正文页码从 1 起
\newcommand{\fdufront}{\pagenumbering{Roman}\tableofcontents\clearpage\pagenumbering{arabic}}
