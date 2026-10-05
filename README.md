# n8n-workflow-doctor

**Run a health check on any n8n workflow in one command: catches leaked API keys, open webhooks, missing retries and dead nodes before a client does.**

![python](https://img.shields.io/badge/python-3.8%2B-blue) ![deps](https://img.shields.io/badge/dependencies-zero-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![n8n](https://img.shields.io/badge/n8n-workflow%20linter-orange)

## Quickstart (under 2 minutes, offline)

```bash
git clone https://github.com/Waqas-Ai-Engineer/n8n-workflow-doctor
cd n8n-workflow-doctor
python -m n8n_workflow_doctor examples/messy-lead-workflow.json
```

Point it at any workflow exported from n8n (Download JSON), or a whole folder:

```bash
python -m n8n_workflow_doctor ./my-workflows --fail-on warning
python -m n8n_workflow_doctor flow.json --json     # for CI / dashboards
```

No pip install, no API keys, no network. Python 3.8+ only. (`pip install .` also gives you an `n8n-doctor` command.)

## Sample output (real run on the bundled messy demo)

```
examples/messy-lead-workflow.json  score 49/100  grade D
  [ERR ] HTTP Request: Possible hardcoded secret at parameters.headerParameters.parameters[0].value
         fix: Move it into an n8n Credential and reference that instead.
  [WARN] (workflow): No error workflow configured: failures will go unnoticed.
  [WARN] HTTP Request: HTTP Request has no retry or error output; one flaky API call kills the run.
  [WARN] Webhook: Webhook has no authentication; anyone with the URL can fire it.
  [WARN] Floating note step: Node is not connected to anything.
  [INFO] Set: Node still has a default name; hard to debug in execution logs.
  [INFO] Old Slack: Node is disabled but left in the workflow.
```

The clean demo scores 100/100 (grade A).

## What it checks

| Rule | Severity | Why it matters |
|---|---|---|
| hardcoded-secret | error | Keys/tokens pasted into node parameters leak when you share or commit the JSON |
| no-error-workflow | warning | Failures go unnoticed by the client |
| http-no-retry | warning | One flaky API call breaks the whole run |
| open-webhook | warning | Anyone with the URL can trigger it |
| orphan-node | warning | Unconnected nodes = dead or forgotten logic |
| no-trigger | warning | Workflow can never start by itself |
| default-node-name | info | Unreadable execution logs |
| disabled-node | info | Dead weight left in production flows |
| big-code-node | info | Hard-to-maintain Code nodes |

Score = 100 minus penalties (error 15, warning 6, info 2). Exit code is 1 if anything at or above `--fail-on` (default `error`) is found, so it drops straight into CI.

## Use it in CI

```yaml
- run: python -m n8n_workflow_doctor workflows/ --fail-on warning
```

## Why this exists

Agencies hand over n8n automations (lead capture, WhatsApp/email follow-up, AI receptionists) for roofing, HVAC, clinics and salons. A pre-delivery audit that is fast, repeatable and shareable with the client is a cheap way to avoid 2 a.m. "the automation stopped" calls.

## Limits (honest)

Static checks on exported JSON only: it does not run your workflow or call any API. Secret detection is heuristic and can miss or over-flag; review findings. Rules are small functions in `n8n_workflow_doctor/rules.py`, PRs welcome.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Hire me / Need this built?

I'm **Muhammad Waqas, AI Agents & Business Automation**. I build n8n workflows, AI lead-capture and follow-up systems, and Python data tooling for service businesses. Reach me via my GitHub profile: [@Waqas-Ai-Engineer](https://github.com/Waqas-Ai-Engineer).

## License

MIT
