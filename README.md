# 🎨 FreeGen — Free AI Image Generation for Hermes Agent

**No API key. No signup. No payment.** Just works.

Drop-in plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent) that adds free AI image generation via [freegen.app](https://freegen.app)'s public Z-Image Turbo model.

## Why FreeGen?

Every other "free" image API in 2026 is either dead or behind a paywall:
- Pollinations → crypto payments
- StableHorde → API key required
- Civitai, DeepAI, Together → 401/403

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

- `/gen <prompt>` — Generate images directly from Telegram/Discord/CLI
- `/img` and `/imagine` — Aliases
- `image_generate` tool — Agent can generate images on demand
- Zero configuration — no API keys, no signup required
- Supports square, landscape, and 4:3 aspect ratios

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

## Requirements

- Hermes Agent installed
- Python 3.10+ with `websockets` package (ships in hermes venv)

## Documentation

See [SKILL.md](SKILL.md) for full documentation including architecture details and troubleshooting guide.

## Contributing

Found a bug? Have an improvement? Open an issue or submit a PR!

## License

MIT
