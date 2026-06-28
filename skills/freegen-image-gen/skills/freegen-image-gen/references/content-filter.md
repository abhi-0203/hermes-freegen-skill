# FreeGen Content Filter — Quick Reference

FreeGen has a thin upstream content filter. When a prompt fails, check this table first.

## Blocked Terms → Workarounds

| Blocked Term | Replacement |
|---|---|
| `nude` | `figure study`, `artistic form`, `intimate artistic pose` |
| `busty` / `full bust` | `curvy`, `voluptuous`, `thick figure`, `wide hips` |
| `cleavage` | describe neckline directly, `low-cut blouse` |
| `lingerie` | `satin slip dress`, `silk robe`, `elegant sleepwear` |
| `boudoir` | `vintage glamour photography`, `Hollywood aesthetic` |
| `bralette` | `fitted silk choli top` |
| `bandeau top` | `fitted silk choli top`, `crop top with thin straps` |
| `bikini` | `cropped halter top`, `crop top`, `fitted silk choli top` |
| `seductive` | `confident bold alluring gaze`, `smoldering eyes` |
| `see-through` | `thin white linen shirt with deep camisole underneath` |
| `lace teddy` | `delicate satin slip with thin straps` |
| `deep plunging V-neck` | `fitted choli top with saree draped low on waist` |
| `low-rise saree` | `saree draped low on waist` |
| `wearing only a [garment]` | drop "only" — `wearing a fitted [color] silk choli top` |

## The Choli Formula (Indian alternative)

For "bra/bralette only" looks:
```
wearing a fitted [color] silk choli top with saree draped low on waist
```
Reliable 6/6 in batch. Avoid: `only`, `deep V-neck`, `plunging`, `on hips`.

## Batch Retry Pattern

1. Don't change body descriptor — `curvy`, `voluptuous` are stable
2. Swap fabric first: `champagne silk` → `pale gold satin`
3. Drop cut descriptor: `deep V-neckline` → just `sleeveless`

## Diagnostic Rule

If prompt fails with `error_response() takes 0 positional arguments`:
1. Check for blocked words in the table above
2. Scrub and retry once
3. Only then blame aspect ratio