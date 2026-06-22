
# Find your project sessions
ls ~/.claude/projects/-Users-$(whoami)-fontforge/

# Peek at the latest session
ls -t ~/.claude/projects/-Users-$(whoami)-fontforge/*.jsonl | head -1 | xargs tail -n 20 | python3 -m json.tool

# Or, if you want to see all sessions in a more compact form
jq -s ~/.claude/projects/-Users-$(whoami)-fontforge/*.jsonl
