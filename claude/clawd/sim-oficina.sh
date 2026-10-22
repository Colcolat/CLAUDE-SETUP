#!/bin/bash
# Simulates a session with the whole team to try the office without spending tokens:
# the 6 roles walk in, work, message each other, create tasks and leave.
# usage: sim-oficina.sh [SESSION] [PAUSE]   (default: demo-oficina 1.2)
#        sim-oficina.sh --gemini [PAUSE]    simulates Gemini working in Antigravity

if [ "$1" = --gemini ]; then
  D=${2:-1.2}
  # Like Antigravity: camelCase JSON on stdin, and the hook answers with JSON.
  g() {
    echo "  ✦ Gemini: $1"
    echo "$2" | /usr/bin/python3 "$HOME/.claude/clawd/clawd.py" gemini-hook $1 >/dev/null
    sleep $D
  }
  echo "Simulated Gemini (~15 s). Ctrl+C to stop."
  P='"conversationId":"'$(uuidgen | tr A-Z a-z)'","workspacePaths":["/x/login_rive_animation"],"modelName":"auto"'
  L='/x/login_rive_animation/lib'
  g session-start "{$P}"
  g pre-invocation "{$P,\"invocationNum\":1}"
  g post-tool "{$P,\"stepIdx\":1,\"toolCall\":{\"name\":\"list_dir\",\"args\":{\"DirectoryPath\":\"$L\"}}}"
  g post-tool "{$P,\"stepIdx\":2,\"toolCall\":{\"name\":\"view_file\",\"args\":{\"AbsolutePath\":\"$L/main.dart\"}}}"
  g post-tool "{$P,\"stepIdx\":3,\"toolCall\":{\"name\":\"grep_search\",\"args\":{\"Query\":\"StateMachine\",\"SearchPath\":\"$L\"}}}"
  g pre-invocation "{$P,\"invocationNum\":2}"
  g post-tool "{$P,\"stepIdx\":5,\"toolCall\":{\"name\":\"replace_file_content\",\"args\":{\"TargetFile\":\"$L/login_screen.dart\"}}}"
  g post-tool "{$P,\"stepIdx\":6,\"toolCall\":{\"name\":\"run_command\",\"args\":{\"CommandLine\":\"flutter analyze lib\"}},\"error\":\"exit status 1\"}"
  g post-tool "{$P,\"stepIdx\":7,\"toolCall\":{\"name\":\"write_to_file\",\"args\":{\"TargetFile\":\"$L/validators.dart\"}}}"
  g pre-invocation "{$P,\"invocationNum\":3}"
  g stop "{$P,\"executionNum\":1,\"terminationReason\":\"NO_TOOL_CALL\",\"fullyIdle\":true}"
  exit 0
fi

S=${1:-demo-oficina}; D=${2:-1.2}
R=$RANDOM  # fresh ids on every run, like Claude Code's
C=(/usr/bin/python3 "$HOME/.claude/clawd/clawd.py")
P='"cwd":"/x/login_rive_animation","session_id":"'$S'"'

h() { echo "$2" | "${C[@]}" hook $1; sleep $D; }
quick() { echo "$2" | "${C[@]}" hook $1; }  # same, without the pause

type_of() {
  case $1 in
    vale) echo explorador ;; pablo) echo planificador ;; sofia) echo revisor ;;
    bruno) echo seguridad ;; lucia) echo guia-tdd ;; *) echo general-purpose ;;
  esac
}
who() { echo "\"agent_id\":\"$1-$R\",\"agent_type\":\"$(type_of $1)\""; }

# spawn NAME DESCRIPTION: Claude calls Agent, then the subagent starts.
spawn() {
  echo "→ $1 ($(type_of $1)) walks in: $2"
  quick auto "{$P,\"hook_event_name\":\"PreToolUse\",\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$(type_of $1)\",\"name\":\"$1\",\"description\":\"$2\"}}"
  h subagent-start "{$P,$(who $1)}"
}
# tool NAME TOOL FILE_OR_PATTERN
tool() {
  local key=file_path; [ "$2" = Grep ] && key=pattern; [ "$2" = Bash ] && key=description
  echo "  $1: $2 $3"
  h auto "{$P,\"hook_event_name\":\"PreToolUse\",$(who $1),\"tool_name\":\"$2\",\"tool_input\":{\"$key\":\"$3\"}}"
}
# msg FROM TO SUMMARY (FROM "main" is Claude)
msg() {
  local from=""; [ "$1" != main ] && from=",$(who $1)"
  echo "  ✉ $1 → $2: $3"
  h auto "{$P,\"hook_event_name\":\"PreToolUse\"$from,\"tool_name\":\"SendMessage\",\"tool_input\":{\"to\":\"$2\",\"summary\":\"$3\"}}"
}
task() { echo "  📝 $1 creates: $3"; h task-created "{$P,$(who $1),\"task_id\":\"$2-$R\",\"task_subject\":\"$3\",\"teammate_name\":\"$1\"}"; }
done_task() { echo "  ✅ $1 completes: $3"; h task-completed "{$P,$(who $1),\"task_id\":\"$2-$R\",\"task_subject\":\"$3\",\"teammate_name\":\"$1\"}"; }
stop() { echo "← $1 leaves: $2"; h subagent-stop "{$P,$(who $1),\"last_assistant_message\":\"$2\"}"; }

echo "Team demo in session '$S' (~1 min with a $D s pause). Ctrl+C to stop."
echo "Watch it with /office, or: /usr/bin/python3 ~/.claude/clawd/clawd.py office $S"
echo
h start "{$P,\"source\":\"startup\"}"
h thinking "{$P,\"hook_event_name\":\"UserPromptSubmit\"}"

# Everyone arrives.
spawn vale "Trace the login flow"
spawn pablo "Plan email validation"
spawn sofia "Review login_screen.dart"
spawn bruno "Audit credentials"
spawn lucia "Validation tests"
spawn mateo "Update dependencies"

# Work and talk.
tool vale Read main.dart
tool bruno Grep api_key
task pablo t1 "Validate email format"
msg vale pablo "Login starts in main.dart and uses RiveAnimation"
tool sofia Read login_screen.dart
tool mateo Bash "flutter pub outdated"
msg pablo lucia "Write the empty-email test first"
task pablo t2 "Disable the button on invalid email"
tool lucia Write validators_test.dart
tool pablo Read pubspec.yaml
msg bruno sofia "Is the password printed in any print()?"
tool sofia Grep "print("
msg sofia bruno "Yes, line 88; flagging it"
tool lucia Bash "flutter test"
msg lucia pablo "2 tests fail, as expected"
done_task lucia t1 "Validate email format"
msg main sofia "Please check signup_screen.dart too"
tool sofia Read signup_screen.dart
tool mateo Edit pubspec.yaml
msg mateo main "Bumped rive to the latest version"
task bruno t3 "Remove the password print"
tool vale Grep isHandsUp
msg vale sofia "isHandsUp fires when the password gets focus"
done_task pablo t2 "Disable the button on invalid email"
tool bruno Edit login_screen.dart
done_task bruno t3 "Remove the password print"

# They leave one by one with their report.
stop mateo "Dependencies up to date, no conflicts"
stop vale "Traced the flow from main.dart to the bear"
msg pablo main "Plan ready in 4 steps"
stop pablo "Email validation plan in 4 steps"
stop lucia "3 new tests, all green"
stop bruno "1 critical finding, already fixed"
stop sofia "Approved with 2 warnings"
h done "{$P,\"hook_event_name\":\"Stop\"}"
echo
echo "Done: the team finished."
