"""Batch image generation for FreeGen plugin.

Supports generating multiple images in a single request,
with configurable batch sizes and parallel/sequential processing.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)

from . import (
    _BROWSER_HEADERS,
    _ASPECT_TO_RATIO_ID,
    _WS_TIMEOUT_SECONDS,
    _MAX_PROMPT_LEN,
    FreegenImageGenProvider,
)

logger = logging.getLogger(__name__)

# Batch configuration
_MAX_BATCH_SIZE = 10  # Maximum images in a single batch
_DEFAULT_BATCH_SIZE = 3  # Default if not specified
_MAX_PARALLEL = 3  # Maximum parallel generations (avoid rate limiting)


class BatchGenerator:
    """Manages batch image generation with parallel processing."""
    
    def __init__(self, provider: FreegenImageGenProvider):
        self.provider = provider
    
    def generate_batch(
        self,
        prompts: List[str],
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        parallel: bool = True,
        max_parallel: int = _MAX_PARALLEL,
    ) -> Dict[str, Any]:
        """Generate multiple images in a batch.
        
        Args:
            prompts: List of prompts to generate
            aspect_ratio: Aspect ratio for all images
            parallel: Whether to process in parallel (default: True)
            max_parallel: Maximum parallel generations
            
        Returns:
            Batch result with individual results
        """
        if not prompts:
            return error_response(
                error="No prompts provided for batch generation.",
                provider=self.provider.name,
            )
        
        if len(prompts) > _MAX_BATCH_SIZE:
            return error_response(
                error=f"Batch size {len(prompts)} exceeds maximum {_MAX_BATCH_SIZE}.",
                provider=self.provider.name,
            )
        
        # Validate prompts
        for i, prompt in enumerate(prompts):
            if not prompt or not prompt.strip():
                return error_response(
                    error=f"Prompt {i + 1} is empty.",
                    provider=self.provider.name,
                )
            if len(prompt.strip()) > _MAX_PROMPT_LEN:
                return error_response(
                    error=f"Prompt {i + 1} too long ({len(prompt)} chars, max {_MAX_PROMPT_LEN}).",
                    provider=self.provider.name,
                )
        
        start_time = time.time()
        results = []
        
        if parallel and len(prompts) > 1:
            # Parallel processing with ThreadPoolExecutor
            actual_parallel = min(max_parallel, len(prompts))
            logger.info(f"Batch generating {len(prompts)} images with {actual_parallel} parallel workers")
            
            with ThreadPoolExecutor(max_workers=actual_parallel) as executor:
                # Submit all generation tasks
                future_to_index = {
                    executor.submit(
                        self.provider.generate,
                        prompt=prompt.strip(),
                        aspect_ratio=aspect_ratio,
                    ): i
                    for i, prompt in enumerate(prompts)
                }
                
                # Collect results in order
                results = [None] * len(prompts)
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result(timeout=_WS_TIMEOUT_SECONDS + 30)
                        results[index] = result
                    except Exception as exc:
                        logger.exception(f"Batch item {index} failed")
                        results[index] = error_response(
                            error=f"Generation failed: {exc}",
                            provider=self.provider.name,
                        )
        else:
            # Sequential processing
            logger.info(f"Batch generating {len(prompts)} images sequentially")
            for i, prompt in enumerate(prompts):
                try:
                    result = self.provider.generate(
                        prompt=prompt.strip(),
                        aspect_ratio=aspect_ratio,
                    )
                    results.append(result)
                except Exception as exc:
                    logger.exception(f"Batch item {i} failed")
                    results.append(error_response(
                        error=f"Generation failed: {exc}",
                        provider=self.provider.name,
                    ))
        
        duration = time.time() - start_time
        
        # Calculate summary
        successful = sum(1 for r in results if r and r.get("success"))
        failed = len(results) - successful
        
        return {
            "success": True,
            "batch_size": len(prompts),
            "successful": successful,
            "failed": failed,
            "duration_seconds": round(duration, 2),
            "results": results,
            "provider": self.provider.name,
            "model": "zimage",
            "aspect_ratio": aspect_ratio,
        }


def format_batch_result(result: Dict[str, Any]) -> str:
    """Format batch result for chat display.
    
    Args:
        result: The batch result dict
        
    Returns:
        Formatted string with MEDIA tags for each image
    """
    if not result.get("success"):
        return f"❌ Batch generation failed: {result.get('error', 'unknown error')}"
    
    batch_size = result.get("batch_size", 0)
    successful = result.get("successful", 0)
    failed = result.get("failed", 0)
    duration = result.get("duration_seconds", 0)
    
    lines = [
        f"🎨 **Batch Complete**: {successful}/{batch_size} images generated in {duration:.1f}s",
        "",
    ]
    
    for i, item_result in enumerate(result.get("results", [])):
        if item_result and item_result.get("success"):
            image = item_result.get("image") or item_result.get("url") or ""
            prompt = item_result.get("prompt", "unknown")
            model = item_result.get("model", "zimage")
            
            lines.append(f"**{i + 1}.** {prompt[:80]}{'…' if len(prompt) > 80 else ''}")
            if image.startswith("/") or image.startswith("~") or os.path.isabs(str(image)):
                lines.append(f"MEDIA:{image}")
            elif image.startswith("data:"):
                lines.append(f"[Inline data URI - saved separately]")
            else:
                lines.append(f"[{image}]")
            lines.append("")
        elif item_result:
            error = item_result.get("error", "generation failed")
            lines.append(f"**{i + 1}.** ❌ {error}")
            lines.append("")
    
    if failed > 0:
        lines.append(f"⚠️ {failed} image(s) failed to generate.")
    
    return "\n".join(lines)


def parse_batch_args(args: str) -> Tuple[List[str], Dict[str, Any]]:
    """Parse batch command arguments.
    
    Supported formats:
        /batch "prompt1" "prompt2" "prompt3"
        /batch --ratio landscape "prompt1" "prompt2"
        /batch --parallel 2 "prompt1" "prompt2"
        
    Returns:
        Tuple of (prompts list, options dict)
    """
    import shlex
    
    prompts = []
    options = {
        "aspect_ratio": DEFAULT_ASPECT_RATIO,
        "parallel": True,
        "max_parallel": _MAX_PARALLEL,
    }
    
    try:
        tokens = shlex.split(args)
    except ValueError:
        tokens = args.split()
    
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--ratio" and i + 1 < len(tokens):
            options["aspect_ratio"] = tokens[i + 1].lower()
            i += 2
        elif tok == "--ratio=":
            options["aspect_ratio"] = tok.split("=", 1)[1].lower()
            i += 1
        elif tok == "--parallel" and i + 1 < len(tokens):
            try:
                options["max_parallel"] = int(tokens[i + 1])
                options["parallel"] = True
            except ValueError:
                options["parallel"] = tokens[i + 1].lower() in ("true", "1", "yes")
            i += 2
        elif tok == "--sequential":
            options["parallel"] = False
            i += 1
        elif tok.startswith("-"):
            # Unknown option, skip
            i += 1
        else:
            # Treat as prompt
            prompts.append(tok)
            i += 1
    
    return prompts, options


def handle_batch_command(args: str) -> str:
    """Handle /batch slash command.
    
    Usage:
        /batch "prompt1" "prompt2" "prompt3"
        /batch --ratio landscape "prompt1" "prompt2"
        /batch --parallel 2 "prompt1" "prompt2"
        /batch --sequential "prompt1" "prompt2"
    """
    if not args or not args.strip():
        return (
            "✏️ Usage: `/batch \"prompt1\" \"prompt2\" [\"prompt3\"...]`\n\n"
            "Options:\n"
            "  `--ratio <ratio>` — Aspect ratio (square, landscape, portrait)\n"
            "  `--parallel N` — Number of parallel workers (default: 3)\n"
            "  `--sequential` — Generate one at a time\n\n"
            f"Maximum batch size: {_MAX_BATCH_SIZE}\n\n"
            "Examples:\n"
            "  `/batch \"corgi in space\" \"cat astronaut\" \"dog astronaut\"`\n"
            "  `/batch --ratio landscape \"mountain\" \"ocean\"`"
        )
    
    prompts, options = parse_batch_args(args)
    
    if not prompts:
        return "✏️ No prompts provided. Use: `/batch \"prompt1\" \"prompt2\"`"
    
    if len(prompts) > _MAX_BATCH_SIZE:
        return f"❌ Batch size {len(prompts)} exceeds maximum {_MAX_BATCH_SIZE}."
    
    provider = FreegenImageGenProvider()
    batch_gen = BatchGenerator(provider)
    
    result = batch_gen.generate_batch(
        prompts=prompts,
        aspect_ratio=options["aspect_ratio"],
        parallel=options["parallel"],
        max_parallel=options["max_parallel"],
    )
    
    return format_batch_result(result)
