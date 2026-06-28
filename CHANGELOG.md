# Changelog

## v1.11.0 (latest)

- Added retry logic with exponential backoff
- Added more aspect ratios (cinematic, photo, classic, banner, social, story)
- Better error messages with status codes
- Fixed duplicate dead code in WebSocket handler
- Fixed thread pool leak
- WebSocket now handles malformed data gracefully

## v1.0.0

- Initial release
- FreeGen.app image generation provider
- `/gen`, `/img`, `/imagine` slash commands
- WebSocket-based image delivery
- Browser User-Agent spoofing
- Square (1:1), landscape (16:9), portrait (9:16) aspect ratios

## v0.1.0

- Initial prototype
- FreeGen.app reverse engineering (sign → submit → subscribe pipeline)
