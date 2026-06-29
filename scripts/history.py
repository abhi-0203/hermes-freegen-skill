"""Image generation history tracking for FreeGen plugin.

Stores metadata about each generated image: prompt, timestamp,
parameters, and file path. Allows users to browse and retrieve
past generations.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# History storage location
HISTORY_DIR = Path.home() / ".hermes" / "freegen" / "history"
HISTORY_FILE = HISTORY_DIR / "history.jsonl"


def _ensure_history_dir() -> None:
    """Create history directory if it doesn't exist."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _load_history() -> List[Dict[str, Any]]:
    """Load all history entries from the JSONL file."""
    if not HISTORY_FILE.exists():
        return []
    
    entries = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    return entries


def record_generation(
    prompt: str,
    model: str,
    aspect_ratio: str,
    image_path: str,
    provider: str = "freegen",
    duration_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """Record an image generation to history.
    
    Args:
        prompt: The generation prompt
        model: Model used (e.g., 'zimage')
        aspect_ratio: Aspect ratio used (e.g., 'square', 'landscape')
        image_path: Path to the saved image file
        provider: Provider name (default: 'freegen')
        duration_seconds: Time taken for generation
        
    Returns:
        The recorded history entry
    """
    _ensure_history_dir()
    
    entry = {
        "id": f"{int(time.time() * 1000)}_{os.path.basename(image_path)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "provider": provider,
        "image_path": str(image_path),
        "duration_seconds": duration_seconds,
    }
    
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    
    return entry


def get_history(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve generation history.
    
    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip (for pagination)
        search: Optional search term to filter by prompt
        
    Returns:
        List of history entries, newest first
    """
    entries = _load_history()
    
    # Reverse to get newest first
    entries = entries[::-1]
    
    # Filter by search term if provided
    if search:
        search_lower = search.lower()
        entries = [
            e for e in entries
            if search_lower in e.get("prompt", "").lower()
        ]
    
    # Apply pagination
    return entries[offset:offset + limit]


def get_history_count() -> int:
    """Get total number of history entries."""
    return len(_load_history())


def clear_history() -> int:
    """Clear all history entries.
    
    Returns:
        Number of entries cleared
    """
    count = get_history_count()
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    return count


def format_history_entry(entry: Dict[str, Any], index: int = 0) -> str:
    """Format a history entry for display.
    
    Args:
        entry: The history entry to format
        index: Display index (0-based)
        
    Returns:
        Formatted string
    """
    timestamp = entry.get("timestamp", "unknown")
    prompt = entry.get("prompt", "no prompt")
    model = entry.get("model", "unknown")
    aspect = entry.get("aspect_ratio", "unknown")
    path = entry.get("image_path", "")
    duration = entry.get("duration_seconds")
    
    # Truncate prompt for display
    if len(prompt) > 80:
        prompt_display = prompt[:77] + "..."
    else:
        prompt_display = prompt
    
    # Format duration
    duration_str = f" · {duration:.1f}s" if duration else ""
    
    # Check if image file exists
    exists = "✓" if os.path.exists(path) else "✗"
    
    return (
        f"[{index + 1}] {exists} {timestamp[:19]}\n"
        f"    Prompt: {prompt_display}\n"
        f"    Model: {model} · {aspect}{duration_str}\n"
        f"    Path: {path}"
    )


def format_history_list(
    entries: List[Dict[str, Any]],
    total: int,
    offset: int = 0,
) -> str:
    """Format a list of history entries for display.
    
    Args:
        entries: List of history entries
        total: Total number of entries (for pagination info)
        offset: Current offset
        
    Returns:
        Formatted string
    """
    if not entries:
        return "📭 No image generation history found."
    
    lines = [f"📚 Image History ({total} total, showing {offset + 1}-{offset + len(entries)})\n"]
    for i, entry in enumerate(entries):
        lines.append(format_history_entry(entry, offset + i))
        lines.append("")  # Empty line between entries
    
    # Pagination hint
    if offset + len(entries) < total:
        remaining = total - (offset + len(entries))
        lines.append(f"💡 {remaining} more entries. Use --offset {offset + len(entries)} to see next page.")
    
    return "\n".join(lines)


def handle_history_command(args: str) -> str:
    """Handle /history slash command.
    
    Usage:
        /history                    - Show recent history
        /history --limit N          - Show N entries
        /history --offset N         - Skip N entries
        /history --search "term"    - Search by prompt
        /history --clear            - Clear all history
    """
    import shlex
    
    # Parse arguments
    limit = 10
    offset = 0
    search = None
    clear = False
    
    try:
        tokens = shlex.split(args)
    except ValueError:
        tokens = args.split()
    
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--limit" and i + 1 < len(tokens):
            try:
                limit = int(tokens[i + 1])
            except ValueError:
                pass
            i += 2
        elif tok == "--offset" and i + 1 < len(tokens):
            try:
                offset = int(tokens[i + 1])
            except ValueError:
                pass
            i += 2
        elif tok == "--search" and i + 1 < len(tokens):
            search = tokens[i + 1]
            i += 2
        elif tok == "--clear":
            clear = True
            i += 1
        else:
            # Treat as search term
            search = tok
            i += 1
    
    if clear:
        count = clear_history()
        return f"🗑️ Cleared {count} history entries."
    
    entries = get_history(limit=limit, offset=offset, search=search)
    total = get_history_count()
    return format_history_list(entries, total, offset)
