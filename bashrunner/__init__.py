"""
bashrunner: Python library to run bash command line scripts from Python.
"""
import subprocess
import sys

def run_bash_command(command: str, capture_output: bool = True) -> subprocess.CompletedProcess:
    """
    Runs a bash command using subprocess.
    Args:
        command (str): The bash command to run.
        capture_output (bool): Whether to capture stdout/stderr.
    Returns:
        subprocess.CompletedProcess: The result of the command execution.
    """
    shell = True if sys.platform.startswith('win') else False
    return subprocess.run(command, shell=shell, capture_output=capture_output, text=True)
