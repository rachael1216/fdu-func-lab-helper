import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def session(msgs):
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "mcp_server.py")], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, timeout=300, encoding="utf8")
    return [json.loads(x) for x in p.stdout.splitlines() if x.strip()]


class TestMCP(unittest.TestCase):
    def test_protocol(self):
        out = session([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "prompts/list"},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "lab_calc", "arguments": {"args": ["map", "--sbp", "120", "--dbp", "80"]}}},
            {"jsonrpc": "2.0", "id": 5, "method": "prompts/get", "params": {"name": "fdu-lab-rag"}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "fdu_lab_menu", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 7, "method": "resources/read", "params": {"uri": "fdu-lab://format"}},
        ])
        by = {m["id"]: m["result"] for m in out}
        self.assertEqual(by[1]["serverInfo"]["name"], "fdu-lab")
        self.assertEqual(len(out), 7)  # 通知不应有响应
        names = {t["name"] for t in by[2]["tools"]}
        self.assertTrue({"rag_search", "lab_calc", "lab_dose", "style_check", "ref_check", "build_report"} <= names)
        self.assertGreaterEqual(len(by[3]["prompts"]), 13)  # 菜单 + 12 skill
        self.assertIn("93", by[4]["content"][0]["text"])  # MAP = 93.3
        self.assertFalse(by[4]["isError"])
        self.assertIn("tools/rag.py", by[5]["messages"][0]["content"]["text"])
        self.assertIn("菜单", by[6]["content"][0]["text"])
        self.assertIn("字体", by[7]["contents"][0]["text"])

    def test_rag_through_mcp(self):
        out = session([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "rag_search", "arguments": {"query": "半数致死量", "k": 2, "corpus": "textbook"}}}])
        r = out[0]["result"]
        self.assertFalse(r["isError"], r)
        self.assertIn("textbook", r["content"][0]["text"])

    def test_bad_tool(self):
        out = session([{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nope"}}])
        self.assertIn("error", out[0])


if __name__ == "__main__":
    unittest.main()
