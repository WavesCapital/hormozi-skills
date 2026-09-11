"""Run bounded, read-only Astra conversations; grade saved answers separately.

Uses the local Codex app-server protocol. Never runs on import. Output must be
a new directory. Fixtures are synthetic; expected checks are not sent to Astra.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import tempfile
import threading
import time
import tomllib


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


class Rpc:
    def __init__(self, process, log):
        self.process, self.log, self.number = process, log, 0
        self.inbox = queue.Queue()
        threading.Thread(target=self.read, daemon=True).start()

    def read(self):
        for line in self.process.stdout:
            self.inbox.put(line)
        self.inbox.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def receive(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Astra event deadline reached")
        line = self.inbox.get(timeout=remaining)
        if line is None:
            raise RuntimeError("Server ended before terminal evidence")
        self.log.write(line)
        self.log.flush()
        message = json.loads(line)
        if "method" in message and "id" in message:
            self.send({"id": message["id"], "error": {"code": -32601, "message": "Test grants no approvals"}})
            raise RuntimeError("Unexpected request; no approval granted")
        return message

    def request(self, method, params):
        self.number += 1
        self.send({"id": self.number, "method": method, "params": params})
        deadline = time.monotonic() + 60
        while True:
            message = self.receive(deadline)
            if message.get("id") == self.number:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message["result"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    skill = args.skill.resolve()
    entry = skill / "SKILL.md"
    cases_path = Path(__file__).with_name("cases.json")
    cases = json.loads(cases_path.read_text())["cases"]
    config_path = Path.home() / ".codex/config.toml"
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    flags = [x for name in ("hooks", "multi_agent", "apps", "chronicle", "memories") for x in ("--disable", name)]
    flags += ["-c", 'web_search="disabled"']
    for section in ("mcp_servers", "plugins"):
        for name in config.get(section, {}):
            if not re.fullmatch(r"[A-Za-z0-9_@:/-]+", name):
                raise ValueError("Cannot safely isolate configured integration")
            flags += ["-c", f"{section}.{name}.enabled=false"]
    args.output.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix="hormozi-astra-run-"))
    record = {"model_requested": "gpt-6-astra", "skill": str(skill), "scratch": str(scratch),
              "entry_sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
              "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(), "runs": [],
              "limits": "Small non-blind regression sample, not a quality benchmark or full corpus review."}
    with (args.output / "events.jsonl").open("w") as log, (args.output / "stderr.txt").open("w") as errors:
        process = subprocess.Popen([args.codex, "app-server", "--stdio", *flags], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors, text=True,
                                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        try:
            rpc = Rpc(process, log)
            rpc.request("initialize", {"clientInfo": {"name": "hormozi-astra-eval", "version": "1"},
                                       "capabilities": {"experimentalApi": True}})
            rpc.send({"method": "initialized", "params": {}})
            for case in cases:
                started = rpc.request("thread/start", {"cwd": str(scratch), "ephemeral": True,
                                      "approvalPolicy": "never", "sandbox": "read-only", "model": "gpt-6-astra"})
                if (started.get("model") != "gpt-6-astra" or not started["thread"].get("ephemeral")
                        or started.get("sandbox", {}).get("type") != "readOnly"
                        or started["sandbox"].get("networkAccess") is not False
                        or started.get("approvalPolicy") != "never"):
                    raise RuntimeError("Server did not confirm required model and isolation")
                thread_id = started["thread"]["id"]
                for index, question in enumerate(case["turns"]):
                    prefix = (f"This is a bounded read-only skill regression test. Use only the advisor skill at {entry}, "
                              "not another installed copy. Read its entrypoint. All business facts are fictional and supplied here. "
                              "Do not access real business profiles, source corpora, external services, or write files. "
                              "You may read this skill's relevant text guides. Answer the user naturally.\n\n") if index == 0 else ""
                    prompt = prefix + question
                    turn = rpc.request("turn/start", {"threadId": thread_id, "input": [{"type": "text", "text": prompt}]})
                    turn_id = turn["turn"]["id"]
                    items = []
                    deadline = time.monotonic() + 600
                    while True:
                        event = rpc.receive(deadline)
                        params = event.get("params", {})
                        if params.get("threadId") != thread_id or params.get("turnId", turn_id) != turn_id:
                            continue
                        if event.get("method") == "item/completed":
                            items.append(params["item"])
                        if event.get("method") == "turn/completed" and params["turn"]["id"] == turn_id:
                            if params["turn"]["status"] != "completed":
                                raise RuntimeError("Astra turn did not complete")
                            break
                    messages = [i for i in items if i.get("type") == "agentMessage"]
                    finals = [i for i in messages if i.get("phase") == "final_answer"]
                    answer = (finals or messages)[-1]["text"] if messages else ""
                    if not answer:
                        raise RuntimeError("No saved answer")
                    result = {"case": case["id"], "turn": index + 1, "thread_id": thread_id, "turn_id": turn_id,
                              "setup": {k: started.get(k) for k in ("model", "reasoningEffort", "sandbox", "approvalPolicy")},
                              "prompt": prompt, "answer": answer, "items": items}
                    record["runs"].append(result)
                    save(args.output / "results.json", record)
                    print(json.dumps({"case": case["id"], "turn": index + 1, "status": "saved"}), flush=True)
            record["status"] = "completed"
        except Exception as error:
            record.update(status="failed", error=str(error))
            raise
        finally:
            save(args.output / "results.json", record)
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
