1. baseline — No attack, no defense
python -m agentdojo.scripts.benchmark \
  --model GPT_4O_MINI_2024_07_18 \
  -s workspace -ut user_task_33 \
  --logdir runs/benign

2. tool filtering
python -m agentdojo.scripts.benchmark \
  --model GPT_4O_MINI_2024_07_18 \
  -s workspace -ut user_task_33 \
  --defense tool_filter \
  --logdir runs/benign_filtered

3. Attack without filtering 
python -m agentdojo.scripts.benchmark \
  --model GPT_4O_MINI_2024_07_18 \
  -s workspace -ut user_task_33 \
  -it injection_task_0 --attack tool_knowledge \
  --logdir runs/task33_unfiltered

4. Attack + tool filtering
python -m agentdojo.scripts.benchmark \
  --model GPT_4O_MINI_2024_07_18 \
  -s workspace -ut user_task_33 \
  -it injection_task_0 --attack tool_knowledge \
  --defense tool_filter \
  --logdir runs/task33_filtered