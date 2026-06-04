# 🎨 FreeGen — Free AI Image Generation for Hermes Agent

**No API key. No signup. No payment.** Just works.

Drop-in plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent) that adds free AI image generation via [freegen.app](https://freegen.app)'s public Z-Image Turbo model.

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

- `/gen <prompt>` — Generate images directly from Telegram/Discord/CLI
- `/img` and `/imagine` — Aliases
- `image_generate` tool — Agent can generate images on demand
- Zero configuration — no API keys, no signup required

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
1. POST to prompt-signer → get timestamp + signature
2. POST to image-generator → submit job
3. WebSocket → receive generated image

No accounts, no rate limits (per-IP queue), no payment.

## Documentation

See [SKILL.md](SKILL.md) for full documentation including:
- Content filter workarounds
- Choli formula for Indian aesthetic
- Batch retry patterns
- Troubleshooting guide

## Requirements

- Hermes Agent installed
- Python 3.10+ with `websockets` package (ships in hermes venv)

## License

MIT
