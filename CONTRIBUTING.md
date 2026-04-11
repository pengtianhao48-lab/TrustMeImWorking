# Contributing to TrustMeImWorking

Thank you for your interest in contributing! Here's how to get started.

## Ways to Contribute

- **Add a new platform** — add an entry to `trustmework/platforms.py`
- **Improve the prompt pool** — add more realistic prompts to `engine.py`
- **Bug fixes** — open an issue first to discuss the fix
- **Documentation** — improve README, add examples, fix typos

## Development Setup

```bash
git clone https://github.com/pengtianhao48-lab/TrustMeImWorking
cd TrustMeImWorking
pip install -r requirements.txt
pip install ruff black pytest
```

## Adding a New Platform

Edit `trustmework/platforms.py` and add entries to all three dicts:

```python
PLATFORM_URLS["newplatform"] = "https://api.newplatform.com/v1"
PLATFORM_DEFAULT_MODELS["newplatform"] = "their-cheapest-model"
PLATFORM_DISPLAY_NAMES["newplatform"] = "New Platform (Display Name)"
```

Then test it:

```bash
python tmw.py platforms  # should appear in the list
```

## Code Style

```bash
ruff check .
black .
```

## Pull Request Guidelines

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Make your changes with clear commit messages
3. Run `ruff check .` to ensure no lint errors
4. Open a PR with a clear description of what changed and why

## Reporting Issues

Please include:
- Your OS and Python version
- The platform you're using
- The full error message or unexpected behavior
- Your config file (with `api_key` redacted)
