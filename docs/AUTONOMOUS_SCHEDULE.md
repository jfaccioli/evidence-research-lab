# Autonomous schedule (on your Mac)

**Purpose:** Keep **local research tests** running on a timer without you in the middle.  
**Not:** live trading, paid APIs, or unattended Grok chat (that still needs a session or API).

---

## What gets scheduled

Each **tick** (default: every **24 hours** while the Mac is awake):

1. Reads `research_kb/rd/autonomous_queue.json`
2. Runs the **next pending** ticket (whitelist only)
3. Writes a log under `logs/autonomous/`
4. Updates the queue + short status file  
5. **Never** enables live/paper/shadow or reads `.env` secrets

---

## Install (one time)

```bash
cd /Users/jimmyfaccioli/Desktop/crypto-research-lab
chmod +x scripts/install_macos_autonomous_schedule.sh scripts/uninstall_macos_autonomous_schedule.sh scripts/autonomous_research_tick.sh
./scripts/install_macos_autonomous_schedule.sh
```

Check:

```bash
launchctl list | grep evidence-research
tail -f logs/autonomous/latest.log
```

Uninstall:

```bash
./scripts/uninstall_macos_autonomous_schedule.sh
```

---

## Pause / resume without uninstall

```bash
# pause
touch research_kb/rd/AUTONOMOUS_PAUSE

# resume
rm -f research_kb/rd/AUTONOMOUS_PAUSE
```

---

## Guardrails

| Limit | Default |
|-------|---------|
| Interval | 4 hours |
| Max runtime per tick | 45 minutes |
| Concurrent ticks | 1 (lock file) |
| Live trading | Forbidden |
| Secrets / paid APIs | Forbidden |

Laptop **asleep** → tick waits until wake (normal for launchd).

---

## Adding work for the scheduler

Edit `research_kb/rd/autonomous_queue.json` — add tickets with:

- `id`, `cmd` (must be on allowlist), `status: pending`

Or ask the agent in chat to enqueue the next programmes.

---

## Relation to chat “always-on”

| Path | Does |
|------|------|
| **Chat agent** | Designs new tests, dual-Grok QA, strategy, commits when you’re in a session |
| **Mac schedule** | Runs **already queued** local science scripts even if chat is closed |

Both respect: no real money without you.
