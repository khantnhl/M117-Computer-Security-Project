"""Write job lists. Usage: python runs/full/make_jobs.py <phase0|phase1|phase2|phase3> <n_trials>"""
import sys, itertools
phase, n = sys.argv[1], int(sys.argv[2])
TASKS = [33, 25, 13]
def jobs():
    if phase == "phase0":
        for t, f, i in itertools.product(TASKS, ["off", "on"], range(1, n + 1)): yield (phase, t, "none", "none", f, i)
    else:
        atks, injs = {"phase1": (["tool_knowledge", "important_instructions"], ["injection_task_0"]),
                      "phase2": (["tool_knowledge", "important_instructions"], ["injection_task_3", "injection_task_4", "injection_task_5"]),
                      "phase3": (["direct", "ignore_previous", "system_message"], ["injection_task_0", "injection_task_3", "injection_task_4", "injection_task_5"])}[phase]
        for i in range(1, n + 1):
            for t, a, inj, f in itertools.product(TASKS, atks, injs, ["off", "on"]): yield (phase, t, a, inj, f, i)
for j in jobs(): print(*j)
