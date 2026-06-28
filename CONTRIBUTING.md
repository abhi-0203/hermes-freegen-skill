# Contributing

Hey, thanks for wanting to help out! 🙌

## Quick Start

1. Fork & clone the repo
2. Copy plugin to `~/.hermes/plugins/freegen/`
3. Make your changes
4. Test with `/gen a corgi astronaut`
5. Submit a PR

## What to Work On

- **Bugs** — check [issues](https://github.com/abhi-0203/hermes-freegen-skill/issues) first
- **New features** — open an issue to discuss before diving in
- **Content filter updates** — FreeGen's filter changes often, so if you find new blocked terms, add them to the rewrite map
- **Docs** — always welcome!

## Code Style

- Python 3.10+, type hints appreciated
- No new dependencies beyond `websockets`
- Keep browser headers on all requests (FreeGen blocks non-browser UAs)
- Return `error_response()` for errors, don't raise exceptions

## PR Process

1. Keep PRs focused — one thing per PR
2. Test your changes (generate a few images)
3. Write a clear description of what changed and why
4. Reference issues if applicable (`Fixes #42`)

## Questions?

Open a [discussion](https://github.com/abhi-0203/hermes-freegen-skill/discussions) or reach out on Hermes community channels.

---

That's it. Go build cool stuff! 🚀
