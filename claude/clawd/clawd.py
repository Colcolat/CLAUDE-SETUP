#!/usr/bin/python3
"""Clawd: an animated pixel-art status line for Claude Code.

  clawd.py statusline         render the status line (statusline JSON on stdin)
  clawd.py team               render the agent panel rows (subagentStatusLine)
  clawd.py hook <state|auto>  record what Claude is doing (hook JSON on stdin)
  clawd.py demo               play every state in your terminal
  clawd.py office [session]   open the 3D office in the browser
  clawd.py gemini-hook <ev>   record what Gemini (Antigravity) is doing

Clawd's size follows context usage, its color follows the 5-hour plan usage
(context usage when that is not available), and its pose follows the state
the hooks record in ~/.claude/clawd/state/<session_id>.json. When a subagent
starts, Clawd puts on that role's outfit for a few seconds, and each running
subagent gets a mini Clawd in its row of the agent panel.

The hooks also append what every agent does to
~/.claude/clawd/events/<session_id>.jsonl. The office (office.html, served
on 127.0.0.1 only) replays that log and follows it live over SSE: one voxel
Clawd per agent at its own desk, and an envelope for every SendMessage.
Gemini's hooks in Antigravity (~/.gemini/config/hooks.json) append to
~/.claude/clawd/events/gemini.jsonl, which the office follows next to it.

Each terminal cell holds 2x2 pixels drawn with quadrant glyphs. Cells that
are all body are painted with background color only, because glyphs leave
gaps between lines in terminals with line spacing. A cell can only show two
colors, so outfits keep eyes away from cells that already have a third one.
"""
import json
import os
import sys
import time

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.expanduser("~/.claude/clawd/state")
EVENTS_DIR = os.path.expanduser("~/.claude/clawd/events")
TEAM_SAMPLE = os.path.expanduser("~/.claude/clawd/team-sample.json")
OFFICE_HTML = os.path.join(HERE, "office.html")
OFFICE_PORTS = range(8737, 8745)
OFFICE_IDLE_SECS = 5 * 60  # the server quits after this long with no tab open
OFFICE_START_SECS = 60  # but first gives the browser time to open the tab
GEMINI_SID = "gemini"  # every Gemini conversation shares events/gemini.jsonl
GEMINI_REPLAY_SECS = 2 * 3600  # how far back the office replays Gemini

ORANGE = (217, 119, 87)
YELLOW = (230, 180, 30)
RED = (220, 50, 47)
EYE = (20, 20, 24)
SWEAT = (110, 180, 255)
GRAY = (160, 160, 165)
GREEN = (120, 220, 140)
WHITE = (235, 235, 235)
KHAKI = (196, 168, 110)
HARDHAT = (245, 200, 40)
NAVY = (40, 60, 120)
GOLD = (240, 190, 60)
TEAL = (60, 170, 170)
GLASS = (175, 215, 250)
GLINT = (255, 255, 255)
BRIDGE = (120, 150, 180)

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

W, H = 24, 6  # canvas in quadrant pixels: 12 cells x 3 lines
LAPTOP_W = 8  # pixels left of Clawd taken by the laptop
ACC_W = 3     # text column next to Clawd for bubbles, sparkles, zZz...
ROLE_SECS = 5    # how long a role transformation lasts
REPORT_SECS = 3  # how long Clawd holds a finished subagent's report

LABELS = {
    "idle": "ready",
    "thinking": "thinking",
    "reading": "reading",
    "typing": "typing",
    "running": "running",
    "delegating": "delegating",
    "working": "working",
    "asking": "asking you",
    "compacting": "compacting",
    "done": "done!",
    "sleeping": "sleeping",
}
ACTIVE = {"thinking", "reading", "typing", "running", "delegating", "working", "compacting"}

TOOL_STATES = {
    "Edit": "typing", "Write": "typing", "MultiEdit": "typing", "NotebookEdit": "typing",
    "Read": "reading", "Grep": "reading", "Glob": "reading", "LS": "reading",
    "WebFetch": "reading", "WebSearch": "reading",
    "Bash": "running", "BashOutput": "running",
    "Task": "delegating", "Agent": "delegating",
    "AskUserQuestion": "asking", "ExitPlanMode": "asking",
}

# Antigravity's tool names, by prefix: what Gemini looks like doing them.
GEMINI_TOOL_STATES = (
    (("view_", "grep", "list_dir", "find_", "search_", "read_url", "browser_"), "reading"),
    (("write_to_file", "replace"), "typing"),
    (("run_command", "command_status"), "running"),
)

# Text drawn to the right of Clawd, one tuple of 3 lines per animation frame.
# Every part is ACC_W cells wide; emoji take two cells.
ACCESSORIES = {
    "thinking": [("   ", "·  ", "   "), (" o ", "·  ", "   "), (" oO", "·  ", "   ")],
    "asking": [(" ? ", "   ", "   "), ("?  ", "   ", "   ")],
    "sleeping": [("   ", "z  ", "   "), (" z ", "   ", "   "), ("  Z", "   ", "   ")],
    "done": [("*  ", "  +", "   "), ("  *", "+  ", "   ")],
    "running": [("   ", ">_ ", "   "), ("   ", ">  ", "   ")],
    "typing": [("   ", "   ", "▁▃▁"), ("   ", "   ", "▃▁▃")],
    "delegating": [("   ", "   ", "▪  "), ("   ", "   ", " ▪ "), ("   ", "   ", "  ▪")],
}

# Subagent roles. "frames" are the accessory column during the transformation,
# one per second; "look" moves the eyes in step with them.
POOF = ("✨ ", " ✨", "✨ ")
ROLES = {
    "explorador": {
        "name": "Explorer", "icon": "🧭", "color": KHAKI, "mini": KHAKI,
        "outfit": "hat", "hat": KHAKI, "brim": True, "walk": True,
        "look": (0, 1, -1, 1, 1),
        "frames": [POOF, ("   ", " 🔍", "   "), ("   ", "🔍 ", "   "),
                   (" 🔍", "   ", "   "), ("   ", " 🔍", "   ")],
    },
    "planificador": {
        "name": "Planner", "icon": "📋", "color": HARDHAT, "mini": HARDHAT,
        "outfit": "hat", "hat": HARDHAT, "brim": True,
        "look": (0, -1, 0, 1, 0),
        "frames": [POOF, ("📋 ", "1  ", "   "), ("📋 ", "12 ", "   "),
                   ("📋 ", "123", "   "), ("📋 ", "✓  ", "   ")],
    },
    "revisor": {
        "name": "Reviewer", "icon": "🧐", "color": GRAY, "mini": GRAY,
        "outfit": "glasses",
        "look": (1, -1, 1, -1, 1),
        "frames": [POOF, ("   ", "📄 ", "   "), ("   ", "📄 ", "   "),
                   ("   ", "📄 ", "   "), ("   ", "✅ ", "   ")],
    },
    "seguridad": {
        "name": "Security", "icon": "🔐", "color": (110, 150, 230), "mini": NAVY,
        "outfit": "guard", "hat": NAVY, "walk": True,
        "look": (0, 0, 0, 0, 0),
        "frames": [POOF, ("   ", "🔦 ", "   "), ("   ", " 🔦", "   "),
                   ("   ", "🔦 ", "   "), ("   ", "🔒 ", "   ")],
    },
    "guia-tdd": {
        "name": "TDD Guide", "icon": "🧪", "color": GREEN, "mini": WHITE,
        "outfit": "coat", "cheer": (3, 4),
        "look": (0, 0, 0, 0, 0),
        "frames": [POOF, ("🧪 ", "🔴 ", "   "), ("🧪 ", "🔴 ", "   "),
                   ("🧪 ", "🟢 ", "   "), ("🧪 ", "✨ ", "   ")],
    },
    "ayudante": {
        "name": "Helper", "icon": "🔧", "color": TEAL, "mini": TEAL,
        "outfit": "band", "hat": TEAL, "hammer": True,
        "look": (0, 0, 0, 0, 0),
        "frames": [POOF, ("   ", "🔧 ", "   "), ("   ", " 🔧", "   "),
                   ("   ", "🔧 ", "   "), ("   ", " 🔧", "   ")],
    },
}
ROLE_ALIASES = {"Explore": "explorador", "Plan": "planificador"}

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def fg(c):
    return "\033[38;2;%d;%d;%dm" % c


def bg(c):
    return "\033[48;2;%d;%d;%dm" % c


def level_color(pct):
    if pct > 85:
        return RED
    if pct > 60:
        return YELLOW
    return ORANGE


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def role_for(agent_type):
    base = (agent_type or "").split(":")[-1]  # plugin agents are "plugin:name"
    if base in ROLES:
        return base
    return ROLE_ALIASES.get(base, "ayudante")


def safe_id(sid):
    return "".join(ch for ch in sid or "" if ch.isalnum() or ch in "-_")


def state_path(sid):
    return os.path.join(STATE_DIR, safe_id(sid) + ".json")


def events_path(sid):
    return os.path.join(EVENTS_DIR, safe_id(sid) + ".jsonl")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f)
        return s if isinstance(s, dict) else {}
    except (OSError, ValueError):
        return {}


def lock_file(f):
    """Block until this process holds the lock on the open file f."""
    if sys.platform == "win32":
        while True:  # LK_LOCK gives up after 10 tries, so keep trying
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:
                pass
    else:
        fcntl.flock(f, fcntl.LOCK_EX)


def replace(tmp, path):
    """os.replace, retried on Windows while a reader has path open."""
    for _ in range(20):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.01)
    os.replace(tmp, path)


# ---------------------------------------------------------------- hooks

def tool_state(tool):
    if tool.startswith("mcp__"):
        return "working"
    return TOOL_STATES.get(tool, "working")


def cleanup(max_age=3 * 86400):
    now = time.time()
    for folder in (STATE_DIR, EVENTS_DIR):
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            path = os.path.join(folder, name)
            try:
                if now - os.path.getmtime(path) > max_age:
                    os.remove(path)
            except OSError:
                pass


def short(text, n=80):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[:n - 1] + "…"


def tool_detail(tool, inp):
    """A few words on what a tool call touches, for the office labels."""
    path = (inp.get("file_path") or inp.get("notebook_path") or inp.get("path")
            or inp.get("TargetFile") or inp.get("AbsolutePath") or inp.get("DirectoryPath"))
    if path:
        return os.path.basename(str(path).rstrip("/"))
    if tool in ("Bash", "run_command"):
        return short(inp.get("description") or inp.get("command") or inp.get("CommandLine"), 40)
    for key in ("pattern", "query", "url", "description", "subject", "Query", "Url"):
        if inp.get(key):
            return short(inp[key], 40)
    return ""


def event(arg, data, s, now):
    """The office log entry for one hook event, or None.

    Runs before update(), under the same lock, so it still sees the team
    entry of a subagent that is stopping and the pending Agent calls.
    """
    aid = data.get("agent_id") or "main"
    atype = data.get("agent_type") or ""
    cwd = data.get("cwd") or ""
    e = {"t": round(now, 3), "agent": aid, "proj": os.path.basename(cwd.rstrip("/"))}
    if aid != "main" and atype:
        e["type"], e["role"] = atype, role_for(atype)

    if arg == "subagent-start":
        if aid == "main" or not atype:
            return None
        # SubagentStart has no name: take it from the Agent call that asked
        # for this type, which PreToolUse recorded a moment ago.
        pending = [p for p in s.get("pending") or [] if now - p["t"] < 120]
        match = next((p for p in pending if p["type"] == atype), None)
        if match:
            pending.remove(match)
            e["name"], e["desc"] = match.get("name"), match.get("desc")
        s["pending"] = pending
        e["ev"] = "spawn"
        return e
    if arg == "subagent-stop":
        if aid == "main":
            return None
        if not atype:
            atype = ((s.get("team") or {}).get(aid) or {}).get("type")
            if atype:
                e["type"], e["role"] = atype, role_for(atype)
        e["ev"] = "stop"
        e["report"] = short(data.get("last_assistant_message"), 160)
        return e
    if arg in ("task-created", "task-completed"):
        e["ev"] = "task" if arg == "task-created" else "task-done"
        e["id"] = data.get("task_id")
        e["subject"] = short(data.get("task_subject"), 80)
        e["name"] = data.get("teammate_name")
        return e
    if arg == "teammate-idle":
        e["ev"], e["name"] = "idle", data.get("teammate_name")
        return e
    if arg == "auto" and data.get("hook_event_name", "PreToolUse") == "PreToolUse":
        tool = data.get("tool_name") or ""
        inp = data.get("tool_input") or {}
        if not isinstance(inp, dict):
            inp = {}
        if tool == "SendMessage":
            msg = inp.get("message")
            e["ev"] = "msg"
            e["to"] = inp.get("to") or inp.get("recipient") or ""
            e["summary"] = short(inp.get("summary") or (msg if isinstance(msg, str) else ""))
            return e
        if tool in ("Agent", "Task") and inp.get("subagent_type"):
            pending = [p for p in s.get("pending") or [] if now - p["t"] < 120]
            pending.append({"t": now, "type": inp["subagent_type"],
                            "name": inp.get("name"), "desc": short(inp.get("description"), 60)})
            s["pending"] = pending
        e["ev"], e["tool"] = "tool", tool
        e["activity"], e["detail"] = tool_state(tool), tool_detail(tool, inp)
        return e
    if arg == "auto":
        return None
    e["ev"] = "state"
    e["state"] = arg
    if arg == "start":
        e["source"] = data.get("source")
    elif arg == "postcompact":
        e["state"] = "thinking" if data.get("trigger") == "auto" else "idle"
    return e


def log_event(sid, e):
    try:  # the office is extra: never let it get in the way of the state
        os.makedirs(EVENTS_DIR, exist_ok=True)
        with open(events_path(sid), "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError):
        pass


def update(s, arg, data, now):
    """Apply one hook event to the session state dict."""
    aid = data.get("agent_id")
    team = s.setdefault("team", {})
    roles = s.setdefault("roles", [])

    if arg == "subagent-start":
        atype = data.get("agent_type") or ""
        if not aid or not atype:
            return  # internal agents (prompt suggestions, /btw) have no type
        team[aid] = {"type": atype, "since": now, "activity": "thinking"}
        # Transformations play one after another, ROLE_SECS each.
        roles[:] = [r for r in roles if r["start"] + ROLE_SECS > now]
        start = max([now] + [r["start"] + ROLE_SECS for r in roles])
        roles.append({"type": atype, "start": start})
        return
    if arg == "subagent-stop":
        entry = team.pop(aid, None) if aid else None
        atype = data.get("agent_type") or (entry or {}).get("type")
        if atype:
            s["report"] = {"type": atype, "since": now}
        return
    if arg in ("task-created", "task-completed", "teammate-idle"):
        return  # only the office shows these
    if aid and arg != "asking":
        # A subagent's own tool use only changes its row; permission prompts
        # still reach the main Clawd because you are the one who answers.
        if aid in team and arg == "auto":
            team[aid]["activity"] = tool_state(data.get("tool_name") or "")
        return

    if arg == "start":
        cleanup()
        state = "idle"
        if data.get("source") in ("startup", "clear"):
            team.clear()
            del roles[:]
    elif arg == "auto":
        state = tool_state(data.get("tool_name") or "")
    elif arg == "postcompact":
        state = "thinking" if data.get("trigger") == "auto" else "idle"
    else:
        state = arg
    s["state"], s["since"] = state, now
    for k in [k for k, v in team.items() if now - v.get("since", now) > 7200]:
        del team[k]  # missed SubagentStop


def hook(arg):
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    sid = data.get("session_id")
    if not sid:
        return
    path = state_path(sid)

    if arg == "end":
        for p in (path, path + ".lock"):
            try:
                os.remove(p)
            except OSError:
                pass
        log_event(sid, {"t": round(time.time(), 3), "agent": "main", "ev": "end"})
        return

    os.makedirs(STATE_DIR, exist_ok=True)
    # Parallel tool calls and subagents fire hooks at once: lock around the
    # read-modify-write, and replace the file atomically for the readers.
    # The event log is appended under the same lock, so it stays in order.
    with open(path + ".lock", "w") as lock:
        lock_file(lock)
        s = load(path)
        now = time.time()
        e = event(arg, data, s, now)
        if e:
            log_event(sid, e)
        update(s, arg, data, now)
        tmp = "%s.%d.tmp" % (path, os.getpid())
        with open(tmp, "w") as f:
            json.dump(s, f)
        replace(tmp, path)


def gemini_activity(tool):
    for prefixes, state in GEMINI_TOOL_STATES:
        if tool.startswith(prefixes):
            return state
    return "working"


def gemini_event(arg, data, now):
    """The office log entry for one Antigravity hook event, or None."""
    cid = safe_id(data.get("conversationId"))
    if not cid:
        return None
    paths = data.get("workspacePaths") or [""]
    proj = os.path.basename(str(paths[0] or "").rstrip("/"))
    e = {"t": round(now, 3), "src": "gemini", "agent": "gemini-" + cid[:8],
         "type": "gemini", "proj": proj}
    if arg == "session-start":
        e["ev"], e["model"] = "spawn", data.get("modelName")
    elif arg == "pre-invocation":
        e["ev"], e["state"] = "state", "thinking"
    elif arg == "post-tool":
        call = data.get("toolCall") or {}
        tool = str(call.get("name") or "")
        args = call.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        e["ev"], e["tool"] = "tool", tool
        e["activity"], e["detail"] = gemini_activity(tool), tool_detail(tool, args)
        if data.get("error"):
            e["error"] = True
    elif arg == "stop":
        e["ev"], e["state"] = "state", "done"
        e["reason"] = data.get("terminationReason")
    else:
        return None
    return e


def gemini_hook(arg):
    """Antigravity hooks block Gemini until they answer, and expect a JSON
    object back whatever happens: the answer goes out even if logging fails."""
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        if isinstance(data, dict):
            e = gemini_event(arg, data, time.time())
            if e:
                log_event(GEMINI_SID, e)
    except Exception:
        pass
    finally:
        # Stop blocks the stop only on "continue": anything else lets it end.
        print(json.dumps({"decision": "stop"} if arg == "stop" else {}))


def read_state(sid, now):
    """What the main Clawd shows: {state, role, rt, report, team}."""
    s = load(state_path(sid))
    state = s.get("state", "idle")
    age = now - (num(s.get("since")) or now)
    team = s.get("team") or {}

    if state == "done" and age > 6:
        state = "idle"
    if state == "idle" and age > 180:
        state = "sleeping"
    # Esc interrupts a turn without firing Stop, so active states expire.
    stale = 1800 if state == "running" else 600
    if (state in ACTIVE or state == "asking") and age > stale:
        state = "idle"
    if state not in LABELS:
        state = "working"
    if team and state in ("idle", "sleeping"):
        state = "delegating"  # background subagents still at work

    out = {"state": state, "role": None, "rt": 0, "report": None, "team": team}
    for r in s.get("roles") or []:
        start = num(r.get("start")) or 0
        if start <= now < start + ROLE_SECS:
            out["role"], out["rt"] = role_for(r.get("type")), now - start
            break
    report = s.get("report") or {}
    if not out["role"] and now - (num(report.get("since")) or 0) < REPORT_SECS:
        out["report"] = role_for(report.get("type"))
    return out


# ---------------------------------------------------------------- sprite

def sprite(state, t, ctx, color, role=None, frame=0):
    """Clawd as a W x H grid of colors (None is transparent), plus glyph
    overlays {(line, cell): (char, fg, bg)} for details finer than a pixel.

    Pixels are quadrants: half a cell wide and half a line tall, the same
    proportions as the Clawd on the welcome screen. With a role, Clawd wears
    that role's outfit and plays frame `frame` of its action.
    """
    grid = [[None] * W for _ in range(H)]
    overlays = {}

    def px(y, x, c=color, only_empty=False):
        if 0 <= y < H and 0 <= x < W and not (only_empty and grid[y][x]):
            grid[y][x] = c

    # Clawd gets fatter as the context fills up.
    bw = 12 if ctx < 50 else 14 if ctx < 80 else 16
    if state == "compacting" and t % 2 and not role:
        bw -= 2
    # At the laptop Clawd turns sideways, facing it on the left.
    at_laptop = not role and state in ("typing", "running")
    if at_laptop:
        x0 = LAPTOP_W
    else:
        x0 = (W - bw) // 2 & ~1  # even, so the body edges fall on cell edges
    right = x0 + bw

    # The body fills two whole lines, so it is drawn with background color
    # only and stays solid across the gap between lines.
    for y in range(4):
        for x in range(x0, right):
            px(y, x)

    def arm(y, side, raised=False, c=color):
        near, far = (x0 - 1, x0 - 2) if side < 0 else (right, right + 1)
        px(y, near, c)
        px(y - 1 if raised else y, far, c)

    if role:
        step = dress(ROLES[role], frame, px, arm, x0, right, bw)
    else:
        step = pose(state, t, px, arm, overlays, x0, right, color, at_laptop)

    for leg in (0, 2, bw - 3, bw - 1):
        px(4, x0 + leg + step)

    if at_laptop:
        # Open screen tilted back on the left, thin base under Clawd's hand.
        screen = GREEN if state == "running" and t % 2 else GRAY
        overlays[(1, 0)] = ("╲", screen, None)
        for cell in range(1, LAPTOP_W // 2):
            overlays[(2, cell)] = ("▔", GRAY, None)

    if ctx > 85 and state != "done" and not role:
        px(t % 2, right + 2, SWEAT, only_empty=True)  # nervous sweat
    return grid, overlays


def pose(state, t, px, arm, overlays, x0, right, color, at_laptop):
    """Eyes and arms for each state. Returns the legs' step offset."""
    eyes, dx, dy = True, 0, 0
    if state == "idle":
        if t % 6 == 0:
            eyes = False  # blink
        elif t % 10 in (3, 4):
            dx = 1
        elif t % 10 == 7:
            dx = -1
    elif state == "sleeping":
        eyes = False
    elif state == "thinking":
        dx, dy = t % 3 - 1, -1  # looking up, around
    elif state == "reading":
        dx = (-1, 0, 1, 0)[t % 4]  # scanning lines
    elif state == "compacting":
        eyes = t % 2 == 0  # squint while squished
    if at_laptop:
        px(1, x0 + 2, EYE)  # profile: one eye, on the screen
    else:
        for ex in (x0 + 2, right - 3):
            if eyes:
                px(1 + dy, ex + dx, EYE)
            else:  # closed: a thin lid line across the eye's cell
                overlays[(0, ex // 2)] = ("▂", EYE, color)

    if at_laptop:
        arm(3 - t % 2 if state == "typing" else 3, -1)  # hand on the keyboard
        px(2, right)  # back arm
    elif state == "done":
        arm(1, -1, raised=t % 2 == 0)  # cheering, one arm then the other
        arm(1, 1, raised=t % 2 == 1)
    elif state == "asking":
        arm(1, -1)
        arm(1, 1, raised=t % 2 == 0)  # waving
    elif state == "sleeping":
        arm(2, -1)
        arm(2, 1)
    else:
        arm(1, -1)
        arm(1, 1)
    return 1 if state == "done" and t % 2 else 0  # dancing


def dress(role, f, px, arm, x0, right, bw):
    """Outfit, eyes and arms for a role's action frame. Returns the legs' step.

    Hats take the top body row, so eyes and arms move down one row (into the
    second line) to keep every cell at two colors.
    """
    kind = role["outfit"]
    hat = role.get("hat")
    if kind in ("hat", "guard", "band"):
        for x in range(x0, right):
            px(0, x, hat)
        if role.get("brim"):
            px(0, x0 - 1, hat)
            px(0, right, hat)
        if kind == "band":
            px(0, right, hat)  # the knot
    if kind == "coat":
        for y in (2, 3):
            for x in range(x0, right):
                px(y, x, WHITE)
    eye_row = 1 if kind == "coat" else 2
    dx = role["look"][f % len(role["look"])]
    if kind == "glasses":
        # Big nerd glasses: two light blue 4x3 lenses, a diagonal glint in
        # the top left cell and the pupil in the top right one, so no cell
        # needs more than two colors (the bottom cells are glass over body).
        off = (bw - 12) // 2 & ~1
        lenses = (x0 + off, right - off - 4)
        for lx in lenses:
            for y in range(3):
                for x in range(lx, lx + 4):
                    px(y, x, GLASS)
            px(1, lx, GLINT)
            px(0, lx + 1, GLINT)
            px(1, lx + (2 if dx < 0 else 3), EYE)  # pupil, reading the page
        for x in range(lenses[0] + 4, lenses[1]):
            px(1, x, BRIDGE)
    elif kind == "guard":
        for ex in (x0 + 2, right - 4):  # sunglasses, two pixels wide
            px(2, ex, EYE)
            px(2, ex + 1, EYE)
        px(3, x0 + bw // 2, GOLD)  # badge
    else:
        for ex in (x0 + 2, right - 3):
            px(eye_row, ex + dx, EYE)

    sleeve = WHITE if kind == "coat" else None
    c = sleeve or ORANGE
    if role.get("hammer"):
        arm(2 + f % 2, -1, c=c)
        arm(3 - f % 2, 1, c=c)
    elif f in role.get("cheer", ()):
        arm(2, -1, raised=True, c=c)
        arm(2, 1, raised=True, c=c)
    else:
        arm(2, -1, c=c)
        arm(2, 1, c=c)
    return f % 2 if role.get("walk") and f else 0


# Quadrant glyphs indexed by mask: 1 upper left, 2 upper right,
# 4 lower left, 8 lower right.
QUADS = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"


def cells(grid, overlays):
    lines = []
    for r in range(0, H, 2):
        s = RESET  # never start a line with plain spaces
        for x in range(0, W, 2):
            over = overlays.get((r // 2, x // 2))
            if over:
                char, f, b = over
                s += fg(f) + (bg(b) if b else "") + char + RESET
                continue
            quad = (grid[r][x], grid[r][x + 1], grid[r + 1][x], grid[r + 1][x + 1])
            colors = [c for c in quad if c is not None]
            kinds = list(dict.fromkeys(colors))
            if not colors:
                s += " "
            elif len(colors) == 4 and len(kinds) == 1:
                s += bg(kinds[0]) + " " + RESET  # solid: no glyph edges
            elif len(kinds) == 1:
                mask = sum(1 << i for i, c in enumerate(quad) if c is not None)
                s += fg(kinds[0]) + QUADS[mask] + RESET
            else:
                # Detail (an eye) drawn over the most common color (the body).
                base = max(kinds, key=colors.count)
                top = next(c for c in kinds if c != base)
                mask = sum(1 << i for i, c in enumerate(quad) if c == top)
                s += fg(top) + bg(base) + QUADS[mask] + RESET
        lines.append(s)
    return lines


def accessory(state, t, color):
    frames = ACCESSORIES.get(state)
    if not frames:
        return [" " * ACC_W] * 3
    style = {
        "thinking": DIM,
        "asking": BOLD + fg(YELLOW),
        "sleeping": fg(SWEAT),
        "done": fg(YELLOW),
        "running": DIM,
        "typing": DIM,
        "delegating": fg(color),
    }[state]
    return [style + part + RESET for part in frames[t % len(frames)]]


# ---------------------------------------------------------------- text

def bar(pct, n=10):
    filled = int(round(min(max(pct, 0), 100) / 100.0 * n))
    return fg(level_color(pct)) + "━" * filled + RESET + DIM + "━" * (n - filled) + RESET


def duration(secs):
    h, m = divmod(int(secs) // 60, 60)
    return "%dh%02dm" % (h, m) if h else "%dm" % m


def info(d, state, t, ctx, usage, color, now, label=None):
    model = (d.get("model") or {}).get("display_name") or "Claude"
    if label is None:
        text = LABELS[state] + ("." * (t % 3 + 1) if state in ACTIVE else "")
        style = BOLD + fg(YELLOW) if state == "asking" else fg(color)
        label = style + text + RESET
    line0 = BOLD + model + RESET + DIM + "  ·  " + RESET + label
    line1 = bar(ctx) + " %d%% context" % round(ctx)
    if usage is not None:
        line2 = bar(usage) + " %d%% 5h usage" % round(usage)
        five = (d.get("rate_limits") or {}).get("five_hour") or {}
        resets = num(five.get("resets_at"))
        suffix = " · resets in " + duration(resets - now) if resets and resets > now else ""
        cols = int(os.environ.get("COLUMNS") or 0)
        if suffix and (not cols or W // 2 + ACC_W + 2 + 20 + len(suffix) < cols - 2):
            line2 += DIM + suffix + RESET  # only when it fits the terminal
    else:
        cwd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or ""
        line2 = DIM + os.path.basename(cwd) + RESET
    return [line0, line1, line2]


def render(d, st, now):
    t = int(now)
    state, role, report = st["state"], st.get("role"), st.get("report")
    ctx = num((d.get("context_window") or {}).get("used_percentage")) or 0.0
    five = (d.get("rate_limits") or {}).get("five_hour") or {}
    usage = num(five.get("used_percentage"))
    color = level_color(usage if usage is not None else ctx)

    label = None
    if role:
        o = ROLES[role]
        f = min(int(st.get("rt", 0)), len(o["frames"]) - 1)
        art = cells(*sprite(state, t, ctx, color, role, f))
        acc = [fg(o["color"]) + part + RESET for part in o["frames"][f]]
        label = BOLD + fg(o["color"]) + "%s on duty!" % o["name"] + RESET
    else:
        art = cells(*sprite(state, t, ctx, color))
        acc = accessory(state, t, color)
        if report:
            o = ROLES[report]
            acc = ["   ", "📨 " if t % 2 else " 📨", "   "]
            label = fg(o["color"]) + "%s's report" % o["name"] + RESET
    text = info(d, state, t, ctx, usage, color, now, label)
    return [art[i] + acc[i] + "  " + text[i] for i in range(3)]


def statusline():
    d = json.load(sys.stdin)
    now = time.time()
    st = read_state(d.get("session_id") or "", now)
    print("\n".join(render(d, st, now)))


# ---------------------------------------------------------------- team panel

def mini(role, t, running):
    """One-line Clawd: hat color on top, body with eyes below."""
    eyes = ((1, 3), (2, 4), (1, 3), (0, 2))[t % 4] if running else (1, 3)
    top = ROLES[role]["mini"]
    return "".join(fg(top) + bg(EYE if i in eyes else ORANGE) + "▀" + RESET for i in range(5))


def width(text):
    """Visible cells: emoji take two."""
    return sum(2 if ord(ch) >= 0x1F000 or ch in "✨✅" else 1 for ch in text)


def clip(text, cells):
    out, used = "", 0
    for ch in text:
        w = width(ch)
        if used + w > cells - 1:
            return out + "…"
        out, used = out + ch, used + w
    return out


def tokens(n):
    n = num(n) or 0
    return "%.1fk" % (n / 1000) if n >= 1000 else "%d" % n


def team_row(task, team, t, now, cols):
    role = role_for(task.get("agentType"))
    o = ROLES[role]
    status = task.get("status") or "running"
    running = status == "running"

    if running:
        mark = fg(o["color"]) + SPINNER[t % len(SPINNER)] + RESET
    elif status == "completed":
        mark = fg(GREEN) + "✓" + RESET
    else:
        mark = fg(RED) + "✗" + RESET

    # Hooks know what the subagent is doing; Claude Code knows its summary.
    tid = task.get("id") or ""
    entry = team.get(tid) or next(
        (v for k, v in team.items() if tid and (k.endswith(tid) or tid.endswith(k))), None)
    doing = LABELS.get((entry or {}).get("activity"), "") if running else ""
    summary = task.get("label") or task.get("description") or ""

    secs = max(0, now - (num(task.get("startTime")) or now * 1000) / 1000)
    tail = "%s · %d:%02d" % (tokens(task.get("tokenCount")), secs // 60, secs % 60)

    name = o["name"].ljust(12)
    head_w = width(o["icon"]) + 1 + 5 + 1 + len(name) + 1 + 1 + 1  # icon mini name mark
    room = (cols or 80) - head_w - width(tail) - 2
    body = clip((doing + " · " if doing else "") + summary, max(room, 8))
    pad = " " * max(1, room - width(body) + 1)
    return ("%s %s %s %s %s%s%s" % (
        o["icon"], mini(role, t, running), BOLD + fg(o["color"]) + name + RESET, mark,
        body if running else DIM + body + RESET, pad, DIM + tail + RESET))


def team_rows(d, now):
    t = int(now)
    team = read_state(d.get("session_id") or "", now)["team"]
    cols = int(num(d.get("columns")) or 0)
    return [(task["id"], team_row(task, team, t, now, cols))
            for task in d.get("tasks") or [] if task.get("id")]


def team_panel():
    d = json.load(sys.stdin)
    if not os.path.exists(TEAM_SAMPLE):
        # Keep one real input to check how task ids match hook agent ids.
        with open(TEAM_SAMPLE, "w") as f:
            json.dump(d, f, indent=2)
    for tid, content in team_rows(d, time.time()):
        print(json.dumps({"id": tid, "content": content}, ensure_ascii=False))


# ---------------------------------------------------------------- office

def hexcolor(c):
    return "#%02x%02x%02x" % c


def office_page():
    """office.html with the roles and labels filled in from this file."""
    roles = {}
    for key, o in ROLES.items():
        roles[key] = {
            "name": o["name"], "icon": o["icon"], "color": hexcolor(o["color"]),
            "hat": hexcolor(o.get("hat") or o["mini"]), "outfit": o["outfit"],
            "brim": bool(o.get("brim")),
        }
    with open(OFFICE_HTML, encoding="utf-8") as f:
        page = f.read()
    page = page.replace("/*ROLES*/null", json.dumps(roles, ensure_ascii=False))
    page = page.replace("/*ALIASES*/null", json.dumps(ROLE_ALIASES))
    page = page.replace("/*LABELS*/null", json.dumps(LABELS, ensure_ascii=False))
    return page.encode("utf-8")


def newest_session():
    try:
        names = [n for n in os.listdir(EVENTS_DIR)
                 if n.endswith(".jsonl") and n != GEMINI_SID + ".jsonl"]
    except OSError:
        return None
    if not names:
        return None
    name = max(names, key=lambda n: os.path.getmtime(os.path.join(EVENTS_DIR, n)))
    return name[:-len(".jsonl")]


def read_log(path, tails):
    """The parsed lines of an event log, remembering in tails where to go on."""
    pos, lines = 0, [b""]
    try:
        with open(path, "rb") as f:
            data = f.read()
        pos, lines = len(data), data.split(b"\n")
    except OSError:
        pass
    tails[path] = [pos, lines.pop()]
    good = []
    for line in lines:
        try:
            e = json.loads(line.decode("utf-8"))
        except ValueError:
            continue
        if isinstance(e, dict):
            good.append(e)
    return good


def office_serve():
    """The office server: the page, and each session's log as SSE."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    clients = [0]
    last_seen = [time.time() + OFFICE_START_SECS - OFFICE_IDLE_SECS]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, body, ctype="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            # Only pages opened as 127.0.0.1/localhost may talk to us, so a
            # web site cannot read the log through DNS rebinding.
            port = self.server.server_address[1]
            if self.headers.get("Host") not in ("127.0.0.1:%d" % port, "localhost:%d" % port):
                return self.send(403, b"forbidden")
            url = urlparse(self.path)
            last_seen[0] = time.time()
            if url.path == "/ping":
                return self.send(200, b"clawd-office")
            if url.path == "/":
                return self.send(200, office_page(), "text/html; charset=utf-8")
            if url.path == "/events":
                sid = safe_id((parse_qs(url.query).get("s") or [""])[0])
                return self.stream(sid)
            return self.send(404, b"not found")

        def stream(self, pinned):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            clients[0] += 1
            try:
                self.follow(pinned)
            except (OSError, ValueError):
                pass  # the tab closed
            finally:
                clients[0] -= 1
                last_seen[0] = time.time()

        def sse(self, data, kind=None):
            msg = ("event: %s\n" % kind if kind else "") + "data: %s\n\n" % data
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

        def follow(self, pinned):
            """Replay a session's log and Gemini's recent one, then send each
            new line of both as it comes. Without a pinned session, follow
            whichever Claude log moved last."""
            gemini = events_path(GEMINI_SID)
            sid, tails, beat, check = None, {}, 0, 0  # tails: path -> [pos, rest]
            while True:
                now = time.time()
                if now > check:
                    check = now + 2
                    want = pinned or newest_session()
                    if want != sid:
                        sid, tails = want, {}
                        self.sse(json.dumps({"sid": sid, "pinned": bool(pinned)}), "session")
                        good = []
                        if sid and sid != GEMINI_SID:
                            good = read_log(events_path(sid), tails)[-4000:]
                        cut = now - GEMINI_REPLAY_SECS
                        good += [e for e in read_log(gemini, tails)
                                 if (num(e.get("t")) or 0) > cut][-4000:]
                        good.sort(key=lambda e: num(e.get("t")) or 0)  # stable
                        self.sse(json.dumps(good, ensure_ascii=False), "replay")
                for path, tail in tails.items():
                    try:
                        with open(path, "rb") as f:
                            f.seek(0, 2)
                            size = f.tell()
                            if size < tail[0]:
                                if path != gemini:  # the log was replaced: start over
                                    check, sid = 0, None
                                    break
                                tail[:] = [0, b""]  # Gemini's expired: a new one
                            f.seek(tail[0])
                            data = f.read()
                    except OSError:
                        data = b""
                    tail[0] += len(data)
                    lines = (tail[1] + data).split(b"\n")
                    tail[1] = lines.pop()
                    for line in lines:
                        if line.strip():
                            self.sse(line.decode("utf-8", "replace"))
                if now > beat:
                    beat = now + 2  # also how soon a closed tab is noticed
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                time.sleep(0.25)

    server = None
    for port in OFFICE_PORTS:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if not server:
        return
    server.daemon_threads = True

    def watchdog():
        while True:
            time.sleep(2)
            if not clients[0] and time.time() - last_seen[0] > OFFICE_IDLE_SECS:
                server.shutdown()
                return

    threading.Thread(target=watchdog, daemon=True).start()
    server.serve_forever()


def office_port():
    """The port of an office server that is already running, or None."""
    from urllib.request import urlopen
    for port in OFFICE_PORTS:
        try:
            with urlopen("http://127.0.0.1:%d/ping" % port, timeout=0.3) as r:
                if r.read() == b"clawd-office":
                    return port
        except Exception:
            continue
    return None


def office(sid):
    import subprocess
    port = office_port()
    if not port:
        # Detached, so it outlives the command that started it.
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "office-serve"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
            creationflags=flags)
        for _ in range(30):
            time.sleep(0.1)
            port = office_port()
            if port:
                break
    if not port:
        print("Couldn't open the office: ports %d-%d are taken."
              % (OFFICE_PORTS[0], OFFICE_PORTS[-1]))
        return
    sid = safe_id(sid)
    if sid and not os.path.exists(events_path(sid)):
        sid = ""  # no log yet: follow whichever session moves
    url = "http://127.0.0.1:%d/" % port + ("?s=" + sid if sid else "")
    if sys.platform == "darwin":
        subprocess.call(["open", url])
    else:
        import webbrowser
        webbrowser.open(url)
    print("Office open at " + url)


# ---------------------------------------------------------------- demo

def demo():
    scenes = [
        ("idle", 10, 20), ("thinking", 30, 35), ("reading", 35, 40),
        ("typing", 55, 65), ("running", 60, 70), ("delegating", 65, 72),
        ("asking", 70, 75), ("compacting", 88, 80), ("typing", 92, 92),
        ("done", 45, 50), ("sleeping", 20, 30),
    ]
    scenes = [(s, ctx, use, None) for s, ctx, use in scenes]
    scenes[5:5] = [("delegating", 40, 50, role) for role in ROLES]
    resets = time.time() + 2 * 3600 + 13 * 60

    def show(lines, n):
        sys.stdout.write("\033[%dA" % n)
        for line in lines:
            sys.stdout.write("\033[2K" + line + "\n")
        sys.stdout.flush()

    print("\n\n")
    try:
        for state, ctx, usage, role in scenes:
            d = {
                "model": {"display_name": "Opus 5.5"},
                "context_window": {"used_percentage": ctx},
                "rate_limits": {"five_hour": {"used_percentage": usage, "resets_at": resets}},
            }
            frames = ROLE_SECS if role else 6
            base = int(time.time()) // 60 * 60  # t % n cycles start at frame 0
            for frame in range(frames):
                st = {"state": state, "role": role, "rt": frame}
                show(render(d, st, base + frame), 3)
                time.sleep(0.8 if role else 0.5)

        print("\nTeam in the agent panel:\n\n\n\n")
        now = time.time()
        tasks = [
            {"id": "a1", "agentType": "revisor", "status": "running",
             "label": "Reviewing login_screen.dart", "tokenCount": 12400, "startTime": (now - 42) * 1000},
            {"id": "a2", "agentType": "seguridad", "status": "running",
             "label": "Looking for exposed secrets", "tokenCount": 8100, "startTime": (now - 15) * 1000},
            {"id": "a3", "agentType": "Explore", "status": "completed",
             "label": "Traced the login flow", "tokenCount": 20300, "startTime": (now - 95) * 1000},
            {"id": "a4", "agentType": "guia-tdd", "status": "failed",
             "label": "Email validation test", "tokenCount": 5000, "startTime": (now - 60) * 1000},
        ]
        team = {"a1": {"activity": "reading"}, "a2": {"activity": "running"}}
        cols = int(os.environ.get("COLUMNS") or 90)
        for frame in range(12):
            show([team_row(task, team, frame, now + frame * 0.5, cols) for task in tasks], 4)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "statusline"
    # Windows defaults to the ANSI code page, which can't print Clawd's glyphs,
    # and to \r\n line ends.
    for stream in (sys.stdin, sys.stdout):
        if stream is not None:
            stream.reconfigure(encoding="utf-8", newline="\n")
    try:
        if mode == "hook":
            hook(sys.argv[2] if len(sys.argv) > 2 else "auto")
        elif mode == "gemini-hook":
            gemini_hook(sys.argv[2] if len(sys.argv) > 2 else "")
        elif mode == "team":
            team_panel()
        elif mode == "demo":
            demo()
        elif mode == "office":
            office(sys.argv[2] if len(sys.argv) > 2 else "")
        elif mode == "office-serve":
            office_serve()
        else:
            statusline()
    except Exception:
        # A broken hook must never block Claude, and the status line
        # should still say something. Broken team rows keep the default.
        if mode == "statusline":
            print("Clawd tripped :(")
        elif mode == "office":
            raise


if __name__ == "__main__":
    main()
