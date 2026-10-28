# FAQ

**Q：必须用 DeepSeek 吗？** 不必。skill 是通用 Markdown，Claude Code、Codex 等支持 `.agents/skills` 的 agent 也能读；DeepSeek 只是最容易注册的选择。

**Q：我的 API Key 安全吗？** Key 只填在你本机的 dsh 设置里。不要把它写进仓库文件、截图或聊天。

**Q：AI 会替我写数据吗？** 规则里禁止。数据必须你提供；它发现缺数据会追问或标“未记录”。

**Q：教材在哪？** 不在仓库（版权）。有自己 PDF 的同学可 `python tools/kb.py build 教材.pdf` 在本机建索引。

**Q：知识卡可信吗？** 是 AI 依据教材起草、**未经教师审校**（`review_status: draft-ai`）。请以教材与老师为准，发现错误欢迎 PR。

**Q：LaTeX 编译报 ctex 找不到？** 安装完整 TeX Live / MiKTeX，或上传 Overleaf（XeLaTeX）。

**Q：Word 封面图太大/想换？** 替换 `assets/covers/cover_<theme>.jpg`，或 `--theme` 选别的主题，或 `--no-cover`。

**Q：能处理照片/示波图吗？** DeepSeek 视作文本模型。请用文字描述峰值、拐点与读数。

**Q：dsh 命令跑不起来？** 先用方案 A；同时开 Issue 附上 `node -v` 与报错。
