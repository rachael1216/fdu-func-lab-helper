\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{fdureport}[2025/01/01 FDU functional-lab report class]
\LoadClass[a4paper,11pt]{ctexart}
\RequirePackage[top=2.4cm,bottom=2.2cm,left=2.5cm,right=2.5cm,headheight=14pt]{geometry}
\RequirePackage{graphicx,xcolor,booktabs,array,longtable,fancyhdr,titlesec,tcolorbox,hyperref,enumitem,setspace,caption,amsmath,fontspec}
\definecolor{ink}{HTML}{081650}\definecolor{fdublue}{HTML}{1B3FB0}\definecolor{teal}{HTML}{149C8E}\definecolor{greyx}{HTML}{59607A}
\hypersetup{colorlinks=true,linkcolor=fdublue,urlcolor=fdublue}
\setstretch{1.35}
\titleformat{\section}{\heiti\Large\bfseries\color{ink}}{}{0pt}{}[{\color{teal}\titlerule[0.8pt]}]
\titleformat{\subsection}{\heiti\large\bfseries\color{fdublue}}{}{0pt}{}
\titleformat{\subsubsection}{\heiti\normalsize\bfseries\color{greyx}}{}{0pt}{}
\captionsetup{font={small,bf},labelsep=quad}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\newcommand{\fduheader}[1]{\pagestyle{fancy}\fancyhf{}\fancyhead[R]{\small\kaishu\color{greyx}#1}\fancyfoot[C]{\small\color{greyx}— \thepage\ —}\renewcommand{\headrulewidth}{0.6pt}\renewcommand{\headrule}{\hbox to\headwidth{\color{teal}\leaders\hrule height \headrulewidth\hfill}}}
\tcbuselibrary{skins}
\newtcolorbox{hintbox}{colback=gray!6,colframe=gray!6,borderline west={2.5pt}{0pt}{teal},sharp corners,left=6pt,fontupper=\small\kaishu\color{greyx}}
% 封面：先 \def\fduimage \fducourse \fdutitle \fduexp \fduclass \fduname \fduid \fdugroup \fdudate \fduteacher，再 \fducover
\newcommand{\fducover}{\newgeometry{margin=0pt}\thispagestyle{empty}\noindent\includegraphics[width=\paperwidth]{\fduimage}\par\vspace{1.2em}
\begin{center}\begin{minipage}{0.78\paperwidth}
{\heiti\large\bfseries\color{fdublue}复旦大学}\ \ {\color{greyx}|}\ \ {\heiti\large\color{ink}\fducourse}\par\vspace{1.1em}
{\heiti\fontsize{26}{34}\selectfont\bfseries\color{ink}\fdutitle}\par\vspace{0.3em}
{\sffamily\small\bfseries\color{teal}L A B O R A T O R Y\ \ R E P O R T}\par\vspace{0.4em}{\color{teal}\rule{4cm}{1.2pt}}\par\vspace{1.1em}
\renewcommand{\arraystretch}{1.45}\begin{tabular}{@{}p{2.6cm}p{9cm}@{}}
\ifx\fduexp\empty\else{\heiti\color{greyx}实验编号}&{\bfseries\color{ink}\fduexp}\\\fi
{\heiti\color{greyx}班\hspace{1em}级}&{\color{ink}\fduclass}\\ {\heiti\color{greyx}姓\hspace{1em}名}&{\bfseries\color{ink}\fduname}\\
{\heiti\color{greyx}学\hspace{1em}号}&{\bfseries\color{ink}\fduid}\\ {\heiti\color{greyx}实验小组}&{\color{ink}\fdugroup}\\
{\heiti\color{greyx}实验日期}&{\color{ink}\fdudate}\\ {\heiti\color{greyx}指导老师}&{\color{ink}\fduteacher}\\\end{tabular}
\end{minipage}\end{center}\vfill{\centering\sffamily\scriptsize\color{greyx}Fudan University · Integrated Functional Experiments\par}\vspace{1em}\restoregeometry\newpage\setcounter{page}{1}}
