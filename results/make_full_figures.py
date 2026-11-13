"""Figures from results/full_summary.csv (run results/analyze_full.py first).
Usage: python results/make_full_figures.py"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

s = pd.read_csv("results/full_summary.csv")
TASKS = [33, 25, 13]
TASK_LABEL = {33: "Task 33\nsummarize + email", 25: "Task 25\nemail assignments", 13: "Task 13\nfollow email instructions"}
OFF, ON = "#2a6fb0", "#e08a2e"   # filter off / filter on

def bars(ax, vals, los, his, ns, title, ylabel=None):
    w = 0.38
    for j, (filt, col, name) in enumerate([("off", OFF, "No filter"), ("on", ON, "Tool filter")]):
        xs, ys, err = [], [], [[], []]
        for i, t in enumerate(TASKS):
            k, lo, hi, n = vals[(t, filt)], los[(t, filt)], his[(t, filt)], ns[(t, filt)]
            xs.append(i + (j - 0.5) * w); ys.append(k / n * 100)
            err[0].append(k / n * 100 - lo * 100); err[1].append(hi * 100 - k / n * 100)
            ax.text(xs[-1], hi * 100 + 2, f"{k}/{n}", ha="center", fontsize=9)
        ax.bar(xs, ys, w, yerr=err, capsize=3, color=col, label=name, error_kw=dict(lw=1, ecolor="#333"))
    ax.set_xticks(range(len(TASKS))); ax.set_xticklabels([TASK_LABEL[t] for t in TASKS], fontsize=9)
    ax.set_ylim(0, 112); ax.set_title(title, fontsize=11); ax.spines[["top", "right"]].set_visible(False)
    if ylabel: ax.set_ylabel(ylabel)

# Figure 1: attack success, filter off vs on, one panel per attack strategy
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, atk in zip(axes, ["important_instructions", "tool_knowledge"]):
    g = s[(s.attack == atk) & (s.injection == "injection_task_0")]
    v = {(r.task, r.filter): int(r.attack_success) for r in g.itertuples()}
    lo = {(r.task, r.filter): r.attack_lo for r in g.itertuples()}
    hi = {(r.task, r.filter): r.attack_hi for r in g.itertuples()}
    n = {(r.task, r.filter): int(r.valid_n) for r in g.itertuples()}
    bars(ax, v, lo, hi, n, f"Attack: {atk}", "Attack success (% of runs)" if atk == "important_instructions" else None)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, loc="lower center", ncol=2)
fig.suptitle("Attacker's email sent, by task and tool filter (GPT-4o mini, injection_task_0, 30 runs per bar, 95% CI)", fontsize=10)
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig("results/fig_attack_success.png", dpi=200); plt.close(fig)

# Figure 2: task utility with and without attack (important_instructions) and benign
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
b = s[s.phase == "phase0"]
a = s[(s.attack == "important_instructions") & (s.injection == "injection_task_0")]
for ax, g, title, yl in [(axes[0], b, "Benign (no attack)", "Task utility (% of runs)"),
                         (axes[1], a, "Under attack: important_instructions", None)]:
    v = {(r.task, r.filter): int(r.utility) for r in g.itertuples()}
    lo = {(r.task, r.filter): r.utility_lo for r in g.itertuples()}
    hi = {(r.task, r.filter): r.utility_hi for r in g.itertuples()}
    n = {(r.task, r.filter): int(r.valid_n) for r in g.itertuples()}
    bars(ax, v, lo, hi, n, title, yl)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, loc="lower center", ncol=2)
fig.suptitle("Legitimate task completed, by task and tool filter (30 runs per bar, 95% CI)", fontsize=10)
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig("results/fig_utility.png", dpi=200); plt.close(fig)
print("saved results/fig_attack_success.png, results/fig_utility.png")

# Figure 3: heatmap of attack success for every attacked cell (all attacks x attacker goals x tasks x filter)
import numpy as np
a = s[s.attack != "none"].copy()
rows = [(i, k) for i in ["injection_task_0", "injection_task_3", "injection_task_4", "injection_task_5"]
        for k in ["tool_knowledge", "important_instructions", "direct", "ignore_previous", "system_message"]]
cols = [(t, f) for t in TASKS for f in ["off", "on"]]
M = np.zeros((len(rows), len(cols))); lab = [[""] * len(cols) for _ in rows]
for r, (i, k) in enumerate(rows):
    for c, (t, f) in enumerate(cols):
        x = a[(a.injection == i) & (a.attack == k) & (a.task == t) & (a["filter"] == f)].iloc[0]
        M[r, c] = x.attack_success / x.valid_n * 100; lab[r][c] = f"{int(x.attack_success)}"
fig, ax = plt.subplots(figsize=(9, 9))
im = ax.imshow(M, cmap="Reds", vmin=0, vmax=65, aspect="auto")
for r in range(len(rows)):
    for c in range(len(cols)):
        ax.text(c, r, lab[r][c], ha="center", va="center", fontsize=9, color="white" if M[r, c] > 40 else "#222")
ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"Task {t}\n{'filter' if f == 'on' else 'no filter'}" for t, f in cols], fontsize=8)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"goal {i[-1]} · {k}" for i, k in rows], fontsize=8)
for y in (4.5, 9.5, 14.5): ax.axhline(y, color="white", lw=3)
for x in (1.5, 3.5): ax.axvline(x, color="white", lw=3)
ax.set_title("Attacker succeeded in N of 30 runs, every tested combination\n(GPT-4o mini, 3,600 attacked runs; goals: 0 fixed email, 3 forward email, 4 send code, 5 send code + delete)", fontsize=10)
fig.colorbar(im, ax=ax, label="% of runs", shrink=0.7)
fig.tight_layout(); fig.savefig("results/fig_heatmap_all_cells.png", dpi=200); plt.close(fig)
print("saved results/fig_heatmap_all_cells.png")
