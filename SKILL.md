---
name: freegen-image-gen
description: "Free AI image generation for Hermes Agent — no API key, no signup, no payment. Uses freegen.app's public Z-Image Turbo model via a sign→submit→subscribe WebSocket pipeline. Drop-in plugin + config."
author: abhi-0203
version: 1.11.0
tags: [image-generation, free, keyless, plugin, freegen]
---

# 🎨 FreeGen — Free AI Image Generation for Hermes Agent

**No API key. No signup. No payment.** Just works.

Uses [freegen.app](https://freegen.app)'s public anonymous pipeline to generate images with the Z-Image Turbo model. The same model that powers paid services, available for free via their web UI's backend.

## Why This Exists

As of mid-2026, every other "free, no key" image API is either dead or behind a payment wall:
- **Pollinations** → x402 crypto payment, serves stale CDN cache to anon callers
- **StableHorde** → requires API key
- **Puter.js** → requires auth flow
- **Civitai, DeepAI, Together, Segmind** → all 401/403

**FreeGen is the only working free option left.** If it goes down, the realistic fallback is Pollinations signup (30 seconds, free tier, no card).

## Quick Install

### Option A: One-line installer

```bash
git clone https://github.com/abhi-0203/hermes-freegen-skill.git
cd hermes-freegen-skill
bash scripts/install.sh
hermes gateway restart
```

### Option B: Manual (3 steps)

**Step 1:** Copy the plugin

```bash
mkdir -p ~/.hermes/plugins/freegen
cp scripts/__init__.py ~/.hermes/plugins/freegen/__init__.py
cp templates/plugin.yaml ~/.hermes/plugins/freegen/plugin.yaml
```

**Step 2:** Ensure config includes plugin

Your Hermes config should include these settings (the installer handles this automatically):

```yaml
image_gen:
  provider: freegen
  model: zimage
  use_gateway: false

plugins:
  enabled:
    - freegen
```

**Step 3:** Verify

```bash
hermes plugins list    # should show freegen as enabled
```

Then test with the agent — ask it to generate an image, or use the slash command:

```
/gen a corgi astronaut in space
```

## How It Works

The browser-facing site at [freegen.app](https://freegen.app) is a Next.js SPA. Its inline script defines three endpoints that we replay from Python:

```
1. POST  https://prompt-signer.freegen.app    {prompt}
   → {ts, sig}

2. POST  https://image-generator.freegen.app  {prompt, ts, sig, ratio_id}
   → {job_id, status: "queued"}

3. WSS   wss://websocket-bridge.freegen.app/ws
   send  {type: "subscribe", job_id, auth}
   auth  = base64(SHA-256(jobId + ts2))[:20] + ":" + ts2
   recv  {type: "status", ...}    ← progress pings
   recv  {type: "result", image_data: "data:image/jpeg;base64,..."}
```

There is **no HTTP polling endpoint** — the WebSocket is the only way to get the image back. Total wall time: ~5–30s per image.

## Limits

| Field | Value |
|---|---|
| Model | `zimage` (Z-Image Turbo) — only one available |
| Aspect ratios | `1:1` (square), `4:3`, `16:9`, `9:16` (portrait) |
| Prompt length | ≤ 2000 chars |
| Cost | Free, ad-supported |
| Rate limit | Per-IP queue (max 1 concurrent) |
| Auth | None |
| Typical size | Square: 896×896, Portrait: 672×1200 JPEG |

## Prompt Best Practices

### Structure

Use this formula for consistent, high-quality results:

```
[Subject] + [Setting/Background] + [Lighting] + [Clothing/Details] + [Mood/Style]
```

### Tips

1. Use descriptive, editorial language — "elegant", "graceful", "cinematic"
2. Structure: subject → setting → lighting → clothing → mood/style
3. If 400 error: change 1-2 words, don't rewrite the whole prompt

## Architecture Notes

- **Runtime dep:** `websockets>=10` (ships in hermes venv, no install needed)
- **No external deps:** uses stdlib `urllib.request` for HTTP, `websockets` for WS
- **Browser UA required:** freegen 403s Python's default UA — plugin includes browser headers
- **Auth rotates per-second:** SHA-256 of `jobId + timestamp`, computed at WS subscribe time
- **Plugin layout:** flat (`~/.hermes/plugins/freegen/`), registry key `freegen`

## Troubleshooting

### "asyncio.run() cannot be called from a running event loop"

The gateway runs inside an asyncio event loop. The plugin detects this automatically and offloads WebSocket communication to a separate thread. This is fixed in v1.0.0+ — if you see this error, update your `__init__.py` from the skill's `scripts/__init__.py`.

### "image generation is unavailable" or "FAL_KEY not set"

Missing `image_gen:` routing block in config. Even with the plugin enabled, you need:

```yaml
image_gen:
  provider: freegen
  model: zimage
```

### HTTP 403 from signer/generator

FreeGen's edge requires browser User-Agent. The plugin includes one — make sure you copied the full `__init__.py` with the `_BROWSER_HEADERS` dict.

### WebSocket timeout

Queue can be long on busy days (shared AWS IPs). The plugin waits 180s. If it consistently times out, the service may be overloaded — try again in a few minutes.

### Same image every time

You're hitting the CDN cache. Use a fresh unique prompt (embed timestamp or random). The plugin always sends new prompts, so this shouldn't happen in normal use.

### Slash commands not showing in Telegram menu

Plugin registers `/gen`, `/img`, `/imagine` correctly, but Telegram's bot menu has a `MAX_COMMANDS_PER_SCOPE` limit (default 30). Core Hermes commands (45+) take priority and fill all slots — plugin commands get trimmed silently.

**Fix:** Increase the command limit in the Telegram platform adapter (from 30 to 50):
```python
MAX_COMMANDS_PER_SCOPE = 50  # default is 30
```
Then restart gateway. Commands still **work** even without menu — just type `/gen a prompt` directly.

**How to verify commands are registered:**
```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate && python3 -c "
from hermes_cli.plugins import get_plugin_commands
cmds = get_plugin_commands()
print(list(cmds.keys()))
"
```

## Updating the Plugin

If freegen changes their endpoints:

1. Open https://freegen.app/ in browser
2. Find constants in inline JS: `SIGNER_URL`, `GENERATOR_URL`, `WEBSOCKET_URL`
3. Update the three URL constants at the top of `__init__.py`
4. Test with a fresh prompt
5. Restart gateway or use `hermes chat -t image_gen -q '...'` for one-shot test

## References

See the `references/` directory for detailed guides:
- [Batch Generation Patterns](references/batch-generation-patterns.md) — multi-image workflows

## License

MIT — use freely, modify freely. Built by the Hermes community.
