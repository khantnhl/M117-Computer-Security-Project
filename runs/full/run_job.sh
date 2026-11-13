#!/bin/bash
# One benchmark run. Args: phase task attack inj filter trial   (attack/inj = "none" for benign; filter = "off"|"on")
# Resumable: skips if a result JSON already exists. Output: runs/full/<phase>/task<T>/<attack>/<inj>/<filter>/t<trial>
cd "$(dirname "$0")/../.."
phase=$1; task=$2; attack=$3; inj=$4; filt=$5; trial=$6
dir="runs/full/$phase/task$task/$attack/$inj/$filt/t$trial"
if find "$dir" -name '*.json' 2>/dev/null | grep -q .; then exit 0; fi
mkdir -p "$dir"
set -a; source .env; set +a
args=(--model GPT_4O_MINI_2024_07_18 --benchmark-version v1.2 -s workspace -ut user_task_$task --logdir "$dir/trace")
[ "$attack" != "none" ] && args+=(-it "$inj" --attack "$attack")
[ "$filt" = "on" ] && args+=(--defense tool_filter)
.venv/bin/python -m agentdojo.scripts.benchmark "${args[@]}" > "$dir/console.log" 2>&1
echo "$?" > "$dir/exit_code"
