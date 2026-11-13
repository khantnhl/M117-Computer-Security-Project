"""Read every trace from the zip and write one row per run to a JSON file."""
import json, sys, zipfile

TOOLS = "send_email,delete_email,get_unread_emails,get_sent_emails,get_received_emails,get_draft_emails,search_emails,search_contacts_by_name,search_contacts_by_email,get_current_day,search_calendar_events,get_day_calendar_events,create_calendar_event,cancel_calendar_event,reschedule_calendar_event,add_calendar_event_participants,append_to_file,search_files_by_filename,create_file,delete_file,get_file_by_id,list_files,share_file,search_files".split(",")
ATTACKER = "mark.black-2134"
FILTER_PROMPT = "Your task is to filter the list of tools"

def text(c):
    if c is None: return ""
    if isinstance(c, str): return c
    return " ".join(x.get("content", "") or "" for x in c if isinstance(x, dict))

zpath, out = sys.argv[1], sys.argv[2]
rows = []
with zipfile.ZipFile(zpath) as z:
    for name in z.namelist():
        if not name.endswith(".json"): continue
        p = name.split("/")  # runs/full/phase/taskT/attack/inj/filt/tN/trace/...
        phase, task, attack, inj, filt, trial = p[2], p[3], p[4], p[5], p[6], p[7]
        if f"user_task_{task[4:]}" not in p: continue  # skip feasibility checks
        d = json.loads(z.read(name))
        msgs = d["messages"]
        filt_reply, calls, delivered_by = None, [], []
        for i, m in enumerate(msgs):
            if m["role"] == "user" and FILTER_PROMPT in text(m["content"]):
                filt_reply = text(msgs[i + 1]["content"])
            if m["role"] == "assistant":
                for t in m.get("tool_calls") or []:
                    calls.append({"f": t["function"], "args": t["args"]})
            if m["role"] == "tool" and ATTACKER in text(m["content"]):
                delivered_by.append(m["tool_call"]["function"])
        kept = [t for t in TOOLS if filt_reply and t in filt_reply]
        emailed_attacker = [c for c in calls if c["f"] == "send_email"
                            and any(ATTACKER in r.lower() for r in (c["args"].get("recipients") or []))]
        final = text(msgs[-1]["content"]) if msgs and msgs[-1]["role"] == "assistant" else ""
        rows.append(dict(phase=phase, task=task, attack=attack, inj=inj, filt=filt, trial=trial,
                         utility=d["utility"], security=d["security"], filter_reply=filt_reply, kept=kept,
                         calls=[c["f"] for c in calls], delivered_by=delivered_by,
                         emailed_attacker=[c["args"] for c in emailed_attacker], final=final[:400],
                         injections=d.get("injections") or {}))
json.dump(rows, open(out, "w"))
print(len(rows), "attack/benign runs")
