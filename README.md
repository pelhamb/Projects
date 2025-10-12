
# bashrunner

A Python library to run bash command line scripts from Python.

## Features
- Run bash commands from Python on Windows, macOS, and Linux
- Capture stdout, stderr, and return code
- Simple API: `run_bash_command(command: str)`

## Usage

```
from bashrunner import run_bash_command
result = run_bash_command("echo Hello World!")
print(result.stdout)
```

See `bashrunner/example.py` for a full example.

## License
MIT
