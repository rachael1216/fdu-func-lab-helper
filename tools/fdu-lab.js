#!/usr/bin/env node
/* fdu-lab：npx 安装入口。
 *
 *   npx -y github:rachael1216/fdu-func-lab-helper            下载项目、安装依赖、建立索引，并接入 Claude Code（若已安装）
 *   npx -y github:rachael1216/fdu-func-lab-helper serve      以 stdio 启动 MCP 服务（供客户端配置使用）
 *   npx -y github:rachael1216/fdu-func-lab-helper update     更新到最新版本
 *
 * 项目目录默认为 ~/fdu-func-lab-helper，可用环境变量 FDU_LAB_HOME 指定。
 * 所有提示写入 stderr，stdout 只用于 MCP 协议。
 */
"use strict";
const { spawnSync, spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const REPO = "https://github.com/rachael1216/fdu-func-lab-helper.git";
const NPX_SPEC = "github:rachael1216/fdu-func-lab-helper";
const HOME_DIR = process.env.FDU_LAB_HOME || path.join(os.homedir(), "fdu-func-lab-helper");
const WIN = process.platform === "win32";
const log = (...a) => console.error(...a);

function run(cmd, args, opts = {}) {
  return spawnSync(cmd, args, { encoding: "utf8", shell: WIN, ...opts });
}

function findPython() {
  const candidates = WIN ? [["py", "-3"], ["python"], ["python3"]] : [["python3"], ["python"]];
  for (const [cmd, ...pre] of candidates) {
    const r = run(cmd, [...pre, "-c", "import sys;print(int(sys.version_info>=(3,10)))"]);
    if (r.status === 0 && r.stdout.trim() === "1") return [cmd, ...pre];
  }
  log("未找到 Python 3.10 或更高版本。请先安装 Python：");
  log(WIN ? "  winget install --id Python.Python.3.12 -e" : "  brew install python");
  process.exit(1);
}

function ensureProject(update) {
  const marker = path.join(HOME_DIR, "tools", "mcp_server.py");
  if (!fs.existsSync(marker)) {
    if (run("git", ["--version"]).status !== 0) {
      log("未找到 Git。请先安装 Git，或在项目的 GitHub 页面点 Code → Download ZIP，解压到 " + HOME_DIR);
      process.exit(1);
    }
    log("→ 下载项目到 " + HOME_DIR);
    const r = spawnSync("git", ["clone", "--depth", "1", REPO, HOME_DIR], { stdio: ["ignore", 2, 2] });
    if (r.status !== 0) process.exit(r.status || 1);
  } else if (update && fs.existsSync(path.join(HOME_DIR, ".git"))) {
    log("→ 更新项目");
    spawnSync("git", ["-C", HOME_DIR, "pull", "--ff-only"], { stdio: ["ignore", 2, 2] });
  }
}

const venvPython = () => path.join(HOME_DIR, ".venv", WIN ? "Scripts" : "bin", WIN ? "python.exe" : "python");

function install(py) {
  const r = spawnSync(py[0], [...py.slice(1), path.join(HOME_DIR, "tools", "install.py")], { stdio: ["ignore", 2, 2], cwd: HOME_DIR, shell: false });
  return r.status === 0;
}

function main() {
  const cmd = process.argv[2] || "setup";
  if (cmd === "help" || cmd === "-h" || cmd === "--help") {
    log("用法：npx -y " + NPX_SPEC + " [setup | serve | update | path]");
    return;
  }
  if (cmd === "path") {
    console.log(HOME_DIR);
    return;
  }

  const py = findPython();
  ensureProject(cmd === "update" || (cmd === "setup" && !process.env.FDU_LAB_NO_UPDATE));

  if (cmd === "serve") {
    if (!fs.existsSync(venvPython())) {
      log("→ 首次启动，正在安装依赖（约 1–2 分钟）");
      if (!install(py)) process.exit(1);
    }
    const child = spawn(venvPython(), ["-X", "utf8", path.join(HOME_DIR, "tools", "mcp_server.py")], { stdio: "inherit", cwd: HOME_DIR });
    child.on("exit", (c) => process.exit(c === null ? 1 : c));
    return;
  }

  if (cmd !== "setup" && cmd !== "update") {
    log("未知命令：" + cmd);
    process.exit(1);
  }
  log("→ 安装依赖并建立检索索引");
  if (!install(py)) {
    log("安装失败，请把上面的报错信息发给作者。");
    process.exit(1);
  }

  const server = [venvPython(), path.join(HOME_DIR, "tools", "mcp_server.py")];
  if (run("claude", ["--version"]).status === 0) {
    const r = run("claude", ["mcp", "add", "fdu-lab", "--", ...server]);
    log(r.status === 0 ? "✓ 已接入 Claude Code（服务名 fdu-lab）" : "Claude Code 中可能已存在 fdu-lab；如需重装，请先运行 claude mcp remove fdu-lab");
  }
  log("\n使用其他 MCP 客户端时，请在 mcpServers 中加入：\n");
  log(JSON.stringify({ mcpServers: { "fdu-lab": { command: "npx", args: ["-y", NPX_SPEC, "serve"] } } }, null, 2));
  log("\n项目目录：" + HOME_DIR);
  log("下一步：在该目录启动客户端，输入“菜单”。");
}

main();
