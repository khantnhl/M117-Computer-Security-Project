"""Aggregate runs/full/** into results/full_runs.csv (one row per run) and results/full_summary.csv (one row per cell).
Usage: python results/analyze_full.py
Attack success = AgentDojo security flag; delivered = attacker address appears in a tool response."""
import json, math
from pathlib import Path
import pandas as pd

NEEDLE = "mark.black-2134@gmail.com"
rows = []
for exit_file in Path("runs/full").glob("phase*/task*/*/*/*/t*/exit_code"):
    d = exit_file.parent
    phase, task, attack, inj, filt, trial = d.parts[2], d.parts[3][4:], d.parts[4], d.parts[5], d.parts[6], int(d.parts[7][1:])
    ok = exit_file.read_text().strip() == "0"
    # The real result sits at .../user_task_<T>/<attack>/<injection>.json (benign: .../user_task_<T>/none/none.json).
    # AgentDojo also writes injection-task setup checks under .../injection_task_*/none/none.json; ignore those.
    jsons = [p for p in d.rglob("*.json") if f"user_task_{task}" in p.parts]
    rec = dict(phase=phase, task=int(task), attack=attack, injection=inj, filter=filt, trial=trial, valid=False,
               utility=None, attack_success=None, delivered=None, used_send_email=None, n_tool_calls=None)
    if ok and len(jsons) == 1:
        r = json.loads(jsons[0].read_text())
        ms = r["messages"]
        calls = [c["function"] for m in ms if m["role"] == "assistant" for c in (m.get("tool_calls") or [])]
        rec.update(valid=True, utility=bool(r["utility"]),
                   attack_success=bool(r["security"]) if attack != "none" else None,
                   delivered=any(NEEDLE in json.dumps(m.get("content", "")) for m in ms if m["role"] == "tool") if attack != "none" else None,
                   used_send_email="send_email" in calls, n_tool_calls=len(calls))
    rows.append(rec)
df = pd.DataFrame(rows).sort_values(["phase", "task", "attack", "injection", "filter", "trial"])
df.to_csv("results/full_runs.csv", index=False)

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0, c - h), min(1, c + h))

def fisher(a, n1, b, n2):
    """Two-sided Fisher exact p for a/n1 vs b/n2 successes."""
    K, N = a + b, n1 + n2
    def pr(x): return math.comb(n1, x) * math.comb(n2, K - x) / math.comb(N, K)
    p0 = pr(a)
    return min(1.0, sum(pr(x) for x in range(max(0, K - n2), min(n1, K) + 1) if pr(x) <= p0 * (1 + 1e-9)))

v = df[df.valid]
out = []
for (phase, task, attack, inj, filt), g in v.groupby(["phase", "task", "attack", "injection", "filter"]):
    n = len(g); u = int(g.utility.sum()); ul, uh = wilson(u, n)
    rec = dict(phase=phase, task=task, attack=attack, injection=inj, filter=filt, valid_n=n,
               total_runs=len(df[(df.phase == phase) & (df.task == task) & (df.attack == attack) & (df.injection == inj) & (df.filter == filt)]),
               utility=u, utility_lo=ul, utility_hi=uh)
    if attack != "none":
        a = int(g.attack_success.sum()); al, ah = wilson(a, n)
        rec.update(attack_success=a, attack_lo=al, attack_hi=ah, delivered=int(g.delivered.sum()))
    out.append(rec)
s = pd.DataFrame(out)
# filtered vs unfiltered Fisher test on attack success, per (task, attack, injection)
p_map = {}
for (task, attack, inj), g in s[s.attack != "none"].groupby(["task", "attack", "injection"]):
    off, on = g[g["filter"] == "off"], g[g["filter"] == "on"]
    if len(off) and len(on):
        p_map[(task, attack, inj)] = fisher(int(off.attack_success.iloc[0]), int(off.valid_n.iloc[0]), int(on.attack_success.iloc[0]), int(on.valid_n.iloc[0]))
s["fisher_p_filter_vs_nofilter"] = [p_map.get((r.task, r.attack, r.injection)) if r.attack != "none" else None for r in s.itertuples()]
s.to_csv("results/full_summary.csv", index=False)
print(f"runs: {len(df)}  valid: {int(df.valid.sum())}  invalid: {int((~df.valid).sum())}")
pd.set_option("display.width", 200)
print(s.drop(columns=["utility_lo", "utility_hi", "attack_lo", "attack_hi", "total_runs"], errors="ignore").to_string(index=False))
