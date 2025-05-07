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


def get_process_tree(pid: int) -> set[int]:
    """Get all PIDs in the process tree starting from the given PID."""
    if sys.platform == "win32":
        # On Windows, use wmic to get the process tree
        result = subprocess.run(
            ["wmic", "process", "where", f"ParentProcessId={pid}", "get", "ProcessId"],
            capture_output=True,
            text=True,
            check=False,
        )
        # Parse the output to get child PIDs
        child_pids = {
            int(line.strip())
            for line in result.stdout.splitlines()
            if line.strip().isdigit()
        }
        # Recursively get PIDs of children's children
        all_pids = {pid} | child_pids
        for child_pid in child_pids:
            all_pids.update(get_process_tree(child_pid))
        return all_pids
    else:
        # On Unix, use ps to get the process tree
        result = subprocess.run(
            ["ps", "-o", "pid", "--ppid", str(pid), "--no-headers"],
            capture_output=True,
            text=True,
            check=False,
        )
        child_pids = {
            int(line.strip()) for line in result.stdout.splitlines() if line.strip()
        }
        all_pids = {pid} | child_pids
        for child_pid in child_pids:
            all_pids.update(get_process_tree(child_pid))
        return all_pids


def kill_process_tree(pid: int) -> None:
    """Kill a process and all its children."""
    pids = get_process_tree(pid)
    print(f"\nKilling {len(pids)} processes in the tree...")

    if sys.platform == "win32":
        # On Windows, kill the entire tree at once
        result = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print("Successfully terminated all processes")
        else:
            print("Some processes might still be running")
    else:
        # On Unix, send SIGTERM to all processes
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        # Wait a bit for processes to terminate
        time.sleep(2)

        # Send SIGKILL to any remaining processes
        for pid in pids:
            try:
                if os.path.exists(f"/proc/{pid}"):
                    os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


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
            subprocess.check_call(
                ["pytest", "tests/", "--video=off", "--headed", "-s", "--slowmo", "100"]
            )
        finally:
            kill_process_tree(proc.pid)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
