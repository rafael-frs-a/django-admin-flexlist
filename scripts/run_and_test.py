import os
import signal
import subprocess
import sys
import time
import typing as t

import requests  # type: ignore[import-untyped]


def run_manage(cmd: list[str]) -> None:
    subprocess.check_call([sys.executable, "demo_project/manage.py"] + cmd)


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for the server to become responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    return False


def runserver_and_wait() -> subprocess.Popen[str]:
    kwargs: dict[str, t.Any] = {
        "stdout": None,  # Show stdout in real-time
        "stderr": None,  # Show stderr in real-time
        "text": True,  # Enable text mode for string output
    }

    if sys.platform == "win32":
        # On Windows, we use CREATE_NEW_PROCESS_GROUP to allow sending CTRL+C
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        # On Unix, we use setsid to create a new process group
        kwargs["preexec_fn"] = os.setsid

    p = subprocess.Popen(
        [sys.executable, "demo_project/manage.py", "runserver", "0.0.0.0:8000"],
        **kwargs,
    )

    # Wait for server to become responsive
    if not wait_for_server("http://localhost:8000/admin/"):
        p.terminate()
        raise RuntimeError("Server failed to start within timeout period")

    return p


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "test"

    # Delete DB file if it exists
    if os.path.exists("demo_project/db.sqlite3"):
        os.remove("demo_project/db.sqlite3")

    # Reset DB and add mock data
    run_manage(["migrate", "--noinput"])
    run_manage(["loaddata", "demo_project/fixtures/initial_data.json"])

    if action == "runserver":
        subprocess.call([sys.executable, "demo_project/manage.py", "runserver"])
    elif action == "test":
        proc = runserver_and_wait()

        try:
            subprocess.check_call(["pytest", "tests/", "--video=off", "--headed", "-s"])
        finally:
            if sys.platform == "win32":
                # First try to terminate gracefully
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # If graceful termination fails, force kill
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(proc.pid)], check=False
                        )
                    else:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                # On Unix, kill the process group
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # If graceful termination fails, force kill
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
