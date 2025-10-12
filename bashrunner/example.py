from bashrunner import run_bash_command

if __name__ == "__main__":
    result = run_bash_command("echo Hello from Bash!")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return Code:", result.returncode)
