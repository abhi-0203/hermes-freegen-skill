# Batch Image Generation Patterns

## Quick Batch Template

Generate 3-5 images with varied prompts in a single session:

```
# Image 1: Landscape
prompt: "mountain landscape at sunrise, golden hour lighting, dramatic clouds"

# Image 2: Portrait
prompt: "close-up portrait of a cat with heterochromia eyes, soft bokeh"

# Image 3: Square
prompt: "cozy coffee shop interior with fairy lights, rainy evening"
```

## Subject-Setting-Lighting-Clothing-Mood Formula

Structure prompts consistently for best results:

```
[Subject] + [Setting/Background] + [Lighting] + [Details] + [Mood/Style]
```

Example:
```
A golden retriever puppy (subject)
playing in a sunlit garden (setting)
with warm afternoon light (lighting)
wearing a small red bandana (details)
happy joyful mood, photography style (mood/style)
```

## Clean Background Keywords

For studio/clean look:
- `clean white minimalist background`
- `clean soft beige background`
- `pure white background`
- `studio lighting`
- `against a solid color backdrop`

## Batch Generation Tips

1. **Vary subjects**: Don't just change colors — change the entire subject/scene
2. **Keep style consistent**: Same photography style across the batch
3. **Use random pose words**: Instead of specifying exact poses, use vague phrases like `"natural relaxed pose"`, `"casual standing pose"`
4. **Vary backgrounds**: white, beige, soft gradient, outdoor scenes
5. **3-5 images per batch**: enough variety without overwhelming

## Parallel Subagent Execution

For fastest batch generation, use `delegate_task` with 3 parallel subagents (the max concurrent limit). Each subagent loads FreeGen via `importlib` from `~/.hermes/plugins/freegen/__init__.py`, calls `generate()`, and copies the result to a named file. ~3 images in ~3 minutes wall time.

**Batches of 4-5:** Split into groups of 3 + remainder.

**Key details:**
- Subagents load FreeGen fresh via `importlib` — no gateway dependency
- Each subagent runs in isolated terminal session — no event loop conflicts
- Copy generated file to a named target for easy MEDIA: delivery
- Max 3 concurrent subagents per `delegate_task` call

## Upscaling for Batch

After generation, upscale all to 1024x1024:
```python
from PIL import Image
for img_path in batch_paths:
    img = Image.open(img_path)
    img_upscaled = img.resize((1024, 1024), Image.LANCZOS)
    img_upscaled.save(img_path.replace('.jpg', '_1024.jpg'), quality=95)
```
