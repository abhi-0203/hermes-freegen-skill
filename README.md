<p align="center">
  <img src="social-preview.jpg" alt="FreeGen Banner" width="100%">
</p>

<h1 align="center">🎨 FreeGen</h1>

<p align="center">
  <strong>Free AI Image Generation for Hermes Agent</strong><br>
  No API key. No signup. No payment. Just works.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/abhi-0203/hermes-freegen-skill"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python"></a>
  <a href="https://github.com/NousResearch/hermes-agent"><img src="https://img.shields.io/badge/hermes-agent-compatible-purple.svg" alt="Hermes"></a>
</p>

---

Drop-in plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent) that adds free AI image generation via [freegen.app](https://freegen.app)'s public Z-Image Turbo model.

## Why FreeGen?

Every other "free" image API in 2026 is either dead or behind a paywall:

| Provider | Status |
|----------|--------|
| Pollinations | 💀 Crypto payments |
| StableHorde | 🔑 API key required |
| Civitai, DeepAI, Together | 🚫 401/403 |
| **FreeGen** | ✅ **Works** |

**FreeGen is the only working free option left.** It reverse-engineers freegen.app's browser-based image generator so you can generate images from your terminal, Telegram, or Discord — no account needed.

## Quick Install

```bash
# Clone this repo
git clone https://github.com/abhi-0203/hermes-freegen-skill.git
cd hermes-freegen-skill

# Run the installer
bash scripts/install.sh
```

Then restart your gateway:

```bash
hermes gateway restart
```

## What You Get

| Feature | Description |
|---------|-------------|
| `/gen <prompt>` | Generate images directly from Telegram/Discord/CLI |
| `/img` / `/imagine` | Aliases for `/gen` |
| `image_generate` tool | Agent can generate images on demand |
| Zero config | No API keys, no signup required |
| Multiple ratios | Square, landscape, portrait, 4:3 |

## Examples

```
/gen golden retriever puppy playing in a sunlit garden
/gen woman in elegant red saree at golden hour, cinematic portrait
/gen sunset over Hyderabad Charminar, warm tones, dreamy atmosphere
/gen cozy coffee shop scene with fairy lights, rainy evening
/gen astronaut floating above Earth, dramatic lighting
```

## How It Works

Uses freegen.app's public anonymous pipeline:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Prompt Signer  │────▶│ Image Generator  │────▶│    WebSocket    │
│  POST /sign     │     │ POST /generate   │     │  Receive image  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

No accounts, no rate limits (per-IP queue), no payment.

## Requirements

- Hermes Agent installed
- Python 3.10+ with `websockets` package (ships in hermes venv)

## Documentation

See [SKILL.md](SKILL.md) for full documentation including:
- Architecture details
- Troubleshooting guide
- Content filter bypass tips
- Batch generation patterns

## Contributing

Found a bug? Have an improvement? Open an issue or submit a PR!

## License

MIT
