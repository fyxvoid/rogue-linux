import subprocess
from typing import Dict, Optional

from core.log.voice import info, err


class ExecutionError(SystemExit):
    """
    Raised when a command fails.
    """
    pass


def run(
    command: str,
    *,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
):
    """
    Execute a shell command with dignity and finality.

    Rules:
    - One command, one execution
    - No retries
    - Failure is fatal
    - Executor does not own presentation (no HUD here)
    """

    info("Proceeding with the requested operation")

    try:
        subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        err("The command did not complete as intended")
        raise ExecutionError(e.returncode)
