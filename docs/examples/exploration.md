# Exploration

Try Alloy interactively with `ask()` and your first `@command` (3 minutes).

---

## Freeform Q&A
```python
from alloy import ask
print(ask("Say hello!"))
```

## First command
```python
from alloy import command

@command
def summarize(text: str) -> str:
    return f"Summarize in one sentence: {text}"

print(summarize("Alloy lets you write typed AI functions in Python."))
```

## See on GitHub
- [00_hello.py](https://github.com/lydakis/alloy/blob/main/examples/00-explore/00_hello.py)
- [01_first_command.py](https://github.com/lydakis/alloy/blob/main/examples/10-commands/01_first_command.py)
- [00-explore folder](https://github.com/lydakis/alloy/tree/main/examples/00-explore)
