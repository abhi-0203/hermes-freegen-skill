---
name: freegen-image-gen
description: "Free AI image generation for Hermes Agent — no API key, no signup, no payment. Uses freegen.app's public Z-Image Turbo model via a sign→submit→subscribe WebSocket pipeline."
author: abhi-0203
version: 1.11.0
tags: [image-generation, free, keyless, plugin, freegen]
---

# 🎨 FreeGen — Free AI Image Generation for Hermes Agent

**No API key. No signup. No payment.** Just works.

Uses [freegen.app](https://freegen.app)'s public anonymous pipeline to generate images with the Z-Image Turbo model.

## Why This Exists

Every other "free, no key" image API in 2026 is either dead or behind a payment wall:
- **Pollinations** → crypto payments required
- **StableHorde** → requires API key
- **Puter.js** → requires auth flow
- **Civitai, DeepAI, Together, Segmind** → all 401/403

**FreeGen is the only working free option left.**

## Quick Install

```bash
git clone https://github.com/abhi-0203/hermes-freegen-skill.git
cd hermes-freegen-skill
bash scripts/install.sh
hermes gateway restart
```

## How It Works

```
1. POST  https://prompt-signer.freegen.app    {prompt}
   → {ts, sig}

2. POST  https://image-generator.freegen.app  {prompt, ts, sig, ratio_id}
   → {job_id, status: "queued"}

3. WSS   wss://websocket-bridge.freegen.app/ws
   send  {type: "subscribe", job_id, auth}
   auth  = base64(SHA-256(jobId + ts2))[:20] + ":" + ts2
   recv  {type: "result", image_data: "data:image/jpeg;base64,..."}
```

Total time: ~5–30s per image.

## Limits

| Field | Value |
|---|---|
| Model | `zimage` (Z-Image Turbo) |
| Aspect ratios | `1:1`, `4:3`, `16:9`, `9:16` |
| Prompt length | ≤ 2000 chars |
| Cost | Free |
| Rate limit | Per-IP queue (max 1 concurrent) |

## Prompt Tips

Use this formula for best results:

```
[Subject] + [Setting/Background] + [Lighting] + [Details] + [Mood/Style]
```

1. Use descriptive language — "elegant", "graceful", "cinematic"
2. Structure: subject → setting → lighting → clothing → mood/style
3. If 400 error: change 1-2 words, don't rewrite the whole prompt

## Troubleshooting

**asyncio error:** Update `__init__.py` from this repo's `scripts/__init__.py`

**HTTP 403:** Make sure you copied the full `__init__.py` with browser headers

**WebSocket timeout:** Queue can be long on busy days — try again in a few minutes

**Slash commands not in Telegram menu:** Core commands fill the limit. Just type `/gen a prompt` directly — it still works.

## License

MIT — use freely, modify freely. Built by the Hermes community.
