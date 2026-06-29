# 🎨 FreeGen — Free AI Image Generation for Hermes Agent

**No API key. No signup. No payment.** Just works.

Uses [freegen.app](https://freegen.app)'s public anonymous pipeline to generate images with the Z-Image Turbo model. The same model that powers paid services, available for free via their web UI's backend.

## ✨ Features

- **Free forever** — No API key, no signup, no payment
- **Fast generation** — ~5-30 seconds per image
- **Batch generation** — Generate multiple images in parallel
- **Image history** — Track and search your generation history
- **Multiple aspect ratios** — Square, landscape, wide
- **Hermes integration** — Drop-in plugin with slash commands

## 🚀 Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/abhi-0203/hermes-freegen-skill.git

# 2. Run the installer
cd hermes-freegen-skill
./scripts/install.sh

# 3. Restart Hermes
hermes restart
```

## 📝 Slash Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/gen` | Generate a single image | `/gen a corgi in space` |
| `/img` | Alias for /gen | `/img a cat astronaut` |
| `/imagine` | Alias for /gen | `/imagine a dog astronaut` |
| `/batch` | Generate multiple images | `/batch "cat" "dog" "bird"` |
| `/history` | View generation history | `/history --search "cat"` |

## 🎯 Batch Generation

Generate multiple images in a single request:

```bash
# Basic batch
/batch "corgi in space" "cat astronaut" "dog astronaut"

# With options
/batch --ratio landscape "mountain" "ocean" "forest"
/batch --sequential "prompt1" "prompt2" "prompt3"
```

## 📚 Image History

Track all your generated images:

```bash
# View recent history
/history

# Search by prompt
/history --search "cat"

# Pagination
/history --limit 5 --offset 10

# Clear history
/history --clear
```

## 🏗️ Architecture

FreeGen uses a 3-step pipeline:
1. **Sign** — POST prompt to get timestamp + signature
2. **Submit** — POST to get job ID
3. **Subscribe** — WebSocket to receive the image

This avoids authentication while preventing abuse via rate limiting.

## ⚠️ Limitations

- **Portrait (9:16) is broken** — Always returns error
- **Rate limited** — Max 1 concurrent generation per IP
- **Single model** — Only Z-Image Turbo available

## 📁 Project Structure

```
hermes-freegen-skill/
├── scripts/
│   ├── __init__.py      # Main plugin code
│   ├── batch.py         # Batch generation module
│   ├── history.py       # Image history tracking
│   └── install.sh       # Installer script
├── skills/
│   └── freegen-image-gen/
│       └── SKILL.md     # Full documentation
├── templates/
│   └── plugin.yaml      # Plugin manifest template
├── SKILL.md             # Skill documentation
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT — use freely, modify freely.

---

Built by the [Hermes](https://github.com/NousResearch/hermes-agent) community.
