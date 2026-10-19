import subprocess


def _escape_applescript_string(s: str) -> str:
    """Escape for embedding in a double-quoted AppleScript string literal.

    Backslash must be escaped before quote — otherwise a message ending in
    `\\"` (backslash then quote) collapses to `\\\\"` (escaped backslash,
    then a now-unescaped quote), which closes the string early and lets
    whatever follows run as live AppleScript, e.g. `do shell script "..."`.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, sound: bool = True):
    safe_title = _escape_applescript_string(title)
    safe_msg   = _escape_applescript_string(message)
    sound_part = ' sound name "Basso"' if sound else ""
    script = f'display notification "{safe_msg}" with title "{safe_title}"{sound_part}'
    subprocess.run(["osascript", "-e", script], check=False)


def speak(text: str):
    subprocess.Popen(["say", "-r", "200", text])


def alert_off_task(task: str, reminder: str, interrupt: bool = True):
    msg = reminder if reminder else f"Get back to: {task}"
    if interrupt:
        speak(msg)           # popup handles the visual; just add audio
    else:
        notify("Full Focus", msg, sound=False)   # silent banner only
