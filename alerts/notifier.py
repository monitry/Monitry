import subprocess
import shlex


def notify(title: str, message: str):
    """Show a macOS system notification."""
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "Basso"'
    subprocess.run(["osascript", "-e", script], check=False)


def speak(text: str):
    """Speak text aloud using macOS say."""
    subprocess.Popen(["say", "-r", "200", text])


def alert_off_task(task: str, activity: str, reminder: str):
    """Fire both a notification and spoken alert when user is off-task."""
    msg = reminder if reminder else f"Get back to: {task}"
    notify("Monitry — Back on task!", msg)
    speak(msg)
