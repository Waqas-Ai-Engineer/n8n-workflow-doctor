"""CLI: n8n-doctor <file-or-dir> [--json] [--fail-on error|warning|info]"""
import argparse, json, sys
from pathlib import Path
from .rules import RULES

SEV = {"info": 1, "warning": 2, "error": 3}
PEN = {"error": 15, "warning": 6, "info": 2}

def lint(wf):
    findings = []
    for rule in RULES:
        findings.extend(rule(wf))
    score = max(0, 100 - sum(PEN[f["severity"]] for f in findings))
    return findings, score

def grade(s):
    return "A" if s >= 90 else "B" if s >= 75 else "C" if s >= 60 else "D" if s >= 40 else "F"

def collect(p):
    p = Path(p)
    return sorted(p.rglob("*.json")) if p.is_dir() else [p]

def main(argv=None):
    ap = argparse.ArgumentParser(prog="n8n-doctor", description="Lint n8n workflow JSON exports.")
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-on", choices=SEV, default="error")
    a = ap.parse_args(argv)
    results, worst = [], 0
    for f in collect(a.path):
        try:
            wf = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"{f}: cannot parse ({e})", file=sys.stderr); worst = 3; continue
        if not isinstance(wf, dict) or "nodes" not in wf:
            continue
        fs, score = lint(wf)
        results.append({"file": str(f), "score": score, "grade": grade(score), "findings": fs})
        for x in fs:
            worst = max(worst, SEV[x["severity"]])
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        icon = {"error": "ERR ", "warning": "WARN", "info": "INFO"}
        for r in results:
            print(f"\n{r['file']}  score {r['score']}/100  grade {r['grade']}")
            for x in r["findings"]:
                print(f"  [{icon[x['severity']]}] {x['node'] or '(workflow)'}: {x['message']}")
                print(f"         fix: {x['fix']}")
        print(f"\n{len(results)} workflow(s) checked.")
    return 1 if worst >= SEV[a.fail_on] else 0

if __name__ == "__main__":
    sys.exit(main())
