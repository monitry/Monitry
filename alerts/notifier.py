import subprocess


def notify(title: str, message: str, sound: bool = True):
    safe_title = title.replace('"', '\\"')
    safe_msg   = message.replace('"', '\\"')
    sound_part = ' sound name "Basso"' if sound else ""
    script = f'display notification "{safe_msg}" with title "{safe_title}"{sound_part}'
    subprocess.run(["osascript", "-e", script], check=False)


def speak(text: str):
    subprocess.Popen(["say", "-r", "200", text])


def alert_off_task(task: str, reminder: str, interupt: bool = True):
    msg = reminder if reminder else f"Get back to: {task}"
    if interupt:
        speak(msg)           # popup handles the visual; just add audio
    else:
        notify("Monitry", msg, sound=False)   # silent banner only
