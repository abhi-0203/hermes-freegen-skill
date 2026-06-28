# Contributing to FreeGen

Thank you for your interest in contributing to FreeGen! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Code Style](#code-style)
- [Testing](#testing)
- [Project Structure](#project-structure)

## Code of Conduct

Be respectful, constructive, and inclusive. We're here to build cool stuff together.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/hermes-freegen-skill.git
   cd hermes-freegen-skill
   ```
3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/abhi-0203/hermes-freegen-skill.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.10+
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed
- `websockets` package (ships in hermes venv)

### Local Development

1. Install the plugin in development mode:
   ```bash
   # Copy plugin to Hermes plugins directory
   mkdir -p ~/.hermes/plugins/freegen
   cp scripts/__init__.py ~/.hermes/plugins/freegen/__init__.py
   cp templates/plugin.yaml ~/.hermes/plugins/freegen/plugin.yaml
   ```

2. Make your changes to `scripts/__init__.py`

3. Test against the live API:
   ```bash
   cd ~/.hermes/hermes-agent && source venv/bin/activate
   python3 -c "
   import sys; sys.path.insert(0, '/path/to/hermes-freegen-skill/scripts')
   from importlib import import_module
   mod = import_module('__init__')
   provider = mod.FreegenImageGenProvider()
   result = provider.generate(prompt='a corgi astronaut in space')
   print(result)
   "
   ```

4. Restart gateway to pick up changes:
   ```bash
   hermes gateway restart
   ```

## How to Contribute

### Bug Fixes

- Check [existing issues](https://github.com/abhi-0203/hermes-freegen-skill/issues) first
- Create a new issue if one doesn't exist
- Reference the issue number in your PR: `Fixes #42`

### New Features

- Open an issue first to discuss the feature
- Wait for approval before starting work
- Keep PRs focused — one feature per PR

### Documentation

- Fix typos, improve clarity, add examples
- Update SKILL.md if adding new features
- Add entries to CHANGELOG.md

### Content Filter Updates

FreeGen's filter evolves over time. If you discover:
- New blocked terms → add to the rewrite map in `__init__.py`
- New safe alternatives → update `references/content-filter.md`
- New prompt patterns → update `references/prompt-writing-bold-tasteful.md`

## Pull Request Process

1. **Update documentation** if your change affects user-facing behavior
2. **Add a CHANGELOG entry** under the `[Unreleased]` section
3. **Test thoroughly** — generate at least 3 images with different prompts
4. **Write a clear PR description:**
   - What changed and why
   - How to test the changes
   - Any breaking changes or migration steps

5. **PR title format:**
   ```
   feat: add support for XYZ
   fix: resolve WebSocket timeout on busy servers
   docs: update prompt writing guide
   refactor: simplify auth token generation
   ```

6. **Request review** from maintainers

### PR Checklist

- [ ] Code runs without errors
- [ ] No hardcoded API keys or secrets
- [ ] Browser headers are included for all HTTP requests
- [ ] Error messages are clear and actionable
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated

## Reporting Bugs

Use GitHub Issues with this template:

```markdown
## Bug Description
A clear description of what went wrong.

## Steps to Reproduce
1. Run `/gen ...`
2. Observe error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- Hermes version:
- Plugin version:
- Python version:
- OS:

## Logs
```
Paste relevant logs here (remove any API keys)
```
```

## Suggesting Features

Open an issue with the `enhancement` label. Include:
- What the feature does
- Why it's useful
- How it should work (user perspective)
- Any implementation ideas (optional)

## Code Style

- **Python:** Follow PEP 8. Use type hints.
- **No external dependencies** beyond `websockets` and Python stdlib
- **Browser headers required** — all HTTP requests to FreeGen need browser User-Agent
- **Error handling** — return `error_response()` with clear messages, never raise raw exceptions to callers
- **Logging** — use `logging.getLogger(__name__)` for debug/error messages

### Naming Conventions

| Element | Convention |
|---------|-----------|
| Constants | `UPPER_SNAKE_CASE` (e.g., `SIGNER_URL`) |
| Private helpers | `_leading_underscore` (e.g., `_post_json`) |
| Classes | `PascalCase` (e.g., `FreegenImageGenProvider`) |
| Functions | `snake_case` (e.g., `generate`, `list_models`) |

## Testing

### Manual Testing

```bash
# Test basic generation
cd ~/.hermes/hermes-agent && source venv/bin/activate
hermes chat -t image_gen -q 'a corgi astronaut in space'

# Test slash command
/gen a sunset over mountains

# Test with aspect ratio
/gen a wide panoramic landscape --ratio landscape
```

### Edge Cases to Test

- Empty prompt
- Prompt over 2,000 characters
- Prompt with blocked terms (should auto-sanitize)
- All aspect ratios (square, landscape, portrait)
- Concurrent requests (queue behavior)
- WebSocket timeout handling

## Project Structure

```
hermes-freegen-skill/
├── README.md                              # Main documentation
├── SKILL.md                               # Skill documentation for Hermes
├── CONTRIBUTING.md                        # This file
├── CHANGELOG.md                           # Version history
├── LICENSE                                # MIT license
├── social-preview.jpg                     # GitHub social preview image
├── scripts/
│   ├── __init__.py                        # Plugin implementation (the core code)
│   └── install.sh                         # One-line installer
├── templates/
│   └── plugin.yaml                        # Plugin metadata template
└── skills/
    └── freegen-image-gen/
        ├── SKILL.md                       # Skill definition for Hermes Skills Hub
        ├── scripts/
        │   ├── __init__.py                # Same plugin code
        │   └── install.sh                 # Same installer
        ├── templates/
        │   └── plugin.yaml                # Same template
        └── references/
            ├── content-filter.md          # Content filter bypass guide
            ├── batch-generation-patterns.md   # Batch generation formulas
            └── prompt-writing-bold-tasteful.md # Bold prompt writing guide
```

## Key Files

| File | Purpose | When to edit |
|------|---------|-------------|
| `scripts/__init__.py` | Core plugin — provider, commands, filter bypass | Bug fixes, new features, filter updates |
| `templates/plugin.yaml` | Plugin metadata | Version bumps, description changes |
| `scripts/install.sh` | Installer script | Install process changes |
| `SKILL.md` | Full documentation | Any user-facing change |
| `references/*.md` | Prompt guides | Filter updates, new patterns |

## Questions?

Open a [GitHub Discussion](https://github.com/abhi-0203/hermes-freegen-skill/discussions) or reach out on the Hermes community channels.
