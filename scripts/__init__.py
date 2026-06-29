"""FreeGen.app image generation backend.

Free, no-API-key text-to-image via https://freegen.app using their public
``prompt-signer → image-generator → websocket-bridge`` pipeline under the
hood. Powers the same "Z-Image Turbo" model that Pollinations exposes as
``zimage``.

Protocol reverse-engineered from the page's inline JS (June 2026):

    1. POST  https://prompt-signer.freegen.app        body: {prompt}
       ← returns {ts, sig}
    2. POST  https://image-generator.freegen.app      body: {prompt, ts, sig, ratio_id}
       ← returns {job_id, status}
    3. WS    wss://websocket-bridge.freegen.app/ws    send: {type:"subscribe", job_id, auth}
       ← auth = base64(SHA-256(jobId+ts2))[:20] + ":" + ts2
       ← receives {type:"result", image_data: "data:image/...;base64,..."}
"""

from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# websockets is a hard runtime dep — it ships in the hermes venv.
import websockets  # type: ignore

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "zimage"

SIGNER_URL = "https://prompt-signer.freegen.app"
GENERATOR_URL = "https://image-generator.freegen.app"
WEBSOCKET_URL = "wss://websocket-bridge.freegen.app/ws"

# Browser-like headers — freegen's edge will 403 non-browser user-agents.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin": "https://freegen.app",
    "Referer": "https://freegen.app/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Map our standard aspect ratios → freegen ratio_id values.
# Includes both friendly names AND normalized ratios (what resolve_aspect_ratio returns).
_ASPECT_TO_RATIO_ID = {
    # Friendly names
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
    "wide": "16:9",
    "tall": "9:16",
    "ultrawide": "21:9",
    "cinematic": "21:9",
    "photo": "3:2",
    "classic": "4:3",
    "phone": "9:16",
    "desktop": "16:9",
    "banner": "3:1",
    "social": "4:5",
    "story": "9:16",
    # Normalized ratios (resolve_aspect_ratio returns these)
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "4:3": "4:3",
    "3:4": "3:4",
    "3:2": "3:2",
    "2:3": "2:3",
    "4:5": "4:5",
    "5:4": "5:4",
    "21:9": "21:9",
    "9:21": "9:21",
}

_WS_TIMEOUT_SECONDS = 180.0
_MAX_PROMPT_LEN = 2000
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds, doubles each attempt
_HTTP_TIMEOUT = 30.0

# Shared thread pool for offloading async work when an event loop is already running.
_thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _get_thread_pool() -> concurrent.futures.ThreadPoolExecutor:
    """Return a lazily-initialised shared thread pool."""
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    return _thread_pool


class FreegenImageGenProvider(ImageGenProvider):
    """FreeGen.app backend — anonymous, no API key required."""

    name = "freegen"
    display_name = "FreeGen (Free, No Key)"

    def is_available(self) -> bool:
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "zimage",
                "name": "Z-Image Turbo",
                "description": "FreeGen's default Z-Image Turbo model. Fast text-to-image, no signup, no API key.",
                "speed": "fast",
                "strengths": ["speed", "free", "no-signup"],
                "price_tier": "free",
            }
        ]

    def default_model(self) -> str:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "title": "FreeGen.app (no setup required)",
            "description": (
                "Uses https://freegen.app's public anonymous pipeline. "
                "No API key, no signup, no payment."
            ),
            "fields": [],
            "setup_steps": [
                "Open https://freegen.app/ in a browser to confirm it loads in your region.",
                "That's it — no account, no key, no payment.",
            ],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            return error_response(
                error="Prompt cannot be empty.",
                provider=self.name,
            )
        prompt = prompt.strip()
        if len(prompt) > _MAX_PROMPT_LEN:
            return error_response(
                error=f"Prompt too long ({len(prompt)} chars, max {_MAX_PROMPT_LEN}).",
                provider=self.name,
            )

        chosen_model = (model or DEFAULT_MODEL).lower()
        if chosen_model not in ("zimage", DEFAULT_MODEL, "freegen"):
            logger.info(
                "FreeGen only ships one model ('zimage'); ignoring requested '%s'.",
                chosen_model,
            )
        model_id = DEFAULT_MODEL

        aspect = resolve_aspect_ratio(aspect_ratio)
        ratio_id = _ASPECT_TO_RATIO_ID.get(aspect, "1:1")
        if aspect not in _ASPECT_TO_RATIO_ID:
            logger.warning(
                "Unknown aspect ratio '%s', falling back to 1:1. "
                "Supported: %s",
                aspect,
                ", ".join(sorted(set(_ASPECT_TO_RATIO_ID.values()))),
            )

        # 1. Sign the prompt.
        try:
            ts, sig = self._sign_prompt(prompt)
        except Exception as exc:
            logger.exception("freegen: sign step failed")
            return error_response(
                error=f"FreeGen sign step failed: {exc}",
                provider=self.name,
            )

        # 2. Submit the generation job.
        try:
            job_id = self._submit_job(prompt, ts, sig, ratio_id)
        except Exception as exc:
            logger.exception("freegen: submit step failed")
            return error_response(
                error=f"FreeGen submit step failed: {exc}",
                provider=self.name,
            )

        # 3. Subscribe to the WebSocket and wait for the result.
        try:
            image_data_uri = self._wait_for_result(job_id, timeout=_WS_TIMEOUT_SECONDS)
        except Exception as exc:
            logger.exception("freegen: websocket wait failed")
            return error_response(
                error=f"FreeGen WebSocket wait failed: {exc}",
                provider=self.name,
            )

        # 4. Decode the data URI and save the bytes locally.
        try:
            header, b64 = image_data_uri.split(",", 1)
            mime = header.split(";")[0].split(":", 1)[1]
            ext = "png" if "png" in mime else ("webp" if "webp" in mime else "jpg")
            raw = base64.b64decode(b64)
        except Exception as exc:
            return error_response(
                error=f"FreeGen result decode failed: {exc}",
                provider=self.name,
            )

        try:
            saved_path = save_b64_image(
                base64.b64encode(raw).decode("ascii"),
                prefix=f"freegen_{model_id}",
                extension=ext,
            )
        except Exception as exc:
            logger.warning("freegen: save_b64_image failed (%s); returning URL only", exc)
            saved_path = None

        return success_response(
            image=str(saved_path) if saved_path else image_data_uri,
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider=self.name,
        )

    # --- internals: HTTP with retry ---

    @staticmethod
    def _post_json(
        url: str,
        body: Dict[str, Any],
        timeout: float = _HTTP_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> Dict[str, Any]:
        """POST JSON with exponential-backoff retry on transient failures."""
        last_exc: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={**_BROWSER_HEADERS, "Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    payload = r.read()
                try:
                    return json.loads(payload)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        f"Non-JSON response from {url}: {payload[:200]!r}"
                    ) from exc
            except urllib.error.HTTPError as exc:
                # 4xx client errors (except 429) are not retryable.
                if 400 <= exc.code < 500 and exc.code != 429:
                    body_text = ""
                    try:
                        body_text = exc.read().decode("utf-8", errors="replace")[:300]
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"HTTP {exc.code} from {url}: {body_text or exc.reason}"
                    ) from exc
                last_exc = exc
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "freegen: HTTP %s from %s (attempt %d/%d), retrying in %.1fs",
                    exc.code, url, attempt, max_retries, delay,
                )
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                last_exc = exc
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "freegen: network error from %s (attempt %d/%d): %s — retrying in %.1fs",
                    url, attempt, max_retries, exc, delay,
                )
            except RuntimeError:
                raise  # don't retry JSON decode errors
            time.sleep(delay)
        raise RuntimeError(
            f"freegen: {url} failed after {max_retries} attempts"
        ) from last_exc

    def _sign_prompt(self, prompt: str) -> tuple[int, str]:
        resp = self._post_json(SIGNER_URL, {"prompt": prompt})
        if "ts" not in resp or "sig" not in resp:
            raise RuntimeError(f"Signer returned no ts/sig: {resp}")
        return int(resp["ts"]), str(resp["sig"])

    def _submit_job(self, prompt: str, ts: int, sig: str, ratio_id: str) -> str:
        resp = self._post_json(
            GENERATOR_URL,
            {"prompt": prompt, "ts": ts, "sig": sig, "ratio_id": ratio_id},
        )
        if "job_id" not in resp:
            raise RuntimeError(f"Generator returned no job_id: {resp}")
        return str(resp["job_id"])

    # --- internals: WebSocket ---

    @staticmethod
    def _compute_ws_auth(job_id: str, ts2: int) -> str:
        msg = f"{job_id}{ts2}"
        digest = hashlib.sha256(msg.encode("utf-8")).digest()
        return base64.b64encode(digest).decode("ascii")[:20] + ":" + str(ts2)

    def _wait_for_result(self, job_id: str, timeout: float) -> str:
        ts2 = int(time.time())
        auth = self._compute_ws_auth(job_id, ts2)
        # Can't use asyncio.run() inside the gateway's own event loop.
        # Detect running loop and offload to a thread if needed.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            pool = _get_thread_pool()
            future = pool.submit(asyncio.run, self._ws_recv(job_id, auth, timeout))
            return future.result(timeout=timeout + 30)
        else:
            return asyncio.run(self._ws_recv(job_id, auth, timeout))

    @staticmethod
    async def _ws_recv(job_id: str, auth: str, timeout: float) -> str:
        """Connect to the WebSocket bridge, subscribe, and wait for the image result."""
        last_exc: Optional[Exception] = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with websockets.connect(
                    WEBSOCKET_URL,
                    ping_interval=20,
                    close_timeout=10,
                    additional_headers={
                        "User-Agent": _BROWSER_HEADERS["User-Agent"],
                        "Origin": "https://freegen.app",
                    },
                ) as ws:
                    await ws.send(
                        json.dumps({"type": "subscribe", "job_id": job_id, "auth": auth})
                    )

                    deadline = time.monotonic() + timeout
                    while time.monotonic() < deadline:
                        remaining = max(0.05, deadline - time.monotonic())
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        except asyncio.TimeoutError:
                            raise RuntimeError(
                                f"WebSocket timed out after {timeout:.0f}s waiting for job {job_id}"
                            )
                        # Handle non-JSON messages gracefully (ping/pong, binary, etc.)
                        if not isinstance(raw, str):
                            logger.debug("freegen: ignoring non-text WS message: %r", type(raw))
                            continue
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            logger.debug("freegen: ignoring malformed WS message: %s", raw[:200])
                            continue
                        t = msg.get("type")
                        if t == "result":
                            image_data = msg.get("image_data") or msg.get("image_data_url")
                            if not image_data:
                                raise RuntimeError(
                                    f"WS result message had no image_data: {msg}"
                                )
                            return image_data
                        # Log unexpected message types at debug level
                        if t and t not in ("subscribe", "subscribed", "ack"):
                            logger.debug("freegen: unexpected WS message type '%s': %s", t, msg)
                    raise RuntimeError(
                        f"WebSocket loop exited after {timeout:.0f}s without a result"
                    )
            except (websockets.exceptions.ConnectionClosed, OSError, ConnectionError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "freegen: WS connection lost for job %s (attempt %d/%d): %s — reconnecting in %.1fs",
                        job_id, attempt, _MAX_RETRIES, exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.exception("freegen: WS connection failed after %d attempts", _MAX_RETRIES)
            except RuntimeError:
                raise  # don't retry timeout/results errors
            except Exception as exc:
                last_exc = exc
                logger.exception("freegen: unexpected WS error (attempt %d/%d)", attempt, _MAX_RETRIES)
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"freegen: WebSocket failed after {_MAX_RETRIES} attempts for job {job_id}"
        ) from last_exc


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

_provider_singleton: Optional[FreegenImageGenProvider] = None


def _get_provider() -> FreegenImageGenProvider:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = FreegenImageGenProvider()
    return _provider_singleton


def _format_success(result: Dict[str, Any], prompt: str) -> str:
    """Build the chat reply text with MEDIA: tag for gateway delivery."""
    image = result.get("image") or result.get("url") or ""
    if not isinstance(image, str):
        image = str(image)
    model = result.get("model", "zimage")
    duration = result.get("duration_seconds", "")
    duration_str = f" in {duration:.1f}s" if isinstance(duration, (int, float)) else ""
    header = f"✨ *{model}* · {prompt[:120]}{'…' if len(prompt) > 120 else ''}{duration_str}\n"
    if image.startswith("/") or image.startswith("~") or os.path.isabs(image):
        return header + f"MEDIA:{image}"
    if image.startswith("data:"):
        try:
            header_b64, b64 = image.split(",", 1)
            mime = header_b64.split(";")[0].split(":", 1)[1]
            ext = "png" if "png" in mime else ("webp" if "webp" in mime else "jpg")
            saved = save_b64_image(b64, prefix="freegen_inline", extension=ext)
            return header + f"MEDIA:{saved}"
        except Exception as exc:
            return f"⚠️ generated image (data URI) but couldn't save to disk: {exc}"
    return header + image


def _handle_gen_command(raw_args: str) -> Optional[str]:
    """Slash command handler for /gen, /img, /imagine."""
    if not raw_args or not raw_args.strip():
        supported = ", ".join(sorted(set(_ASPECT_TO_RATIO_ID.values())))
        return (
            "✏️ Usage: `/gen <prompt>`\n"
            f"Optional: `--ratio <{supported}>` or named presets: "
            "square, landscape, portrait, wide, tall, ultrawide, cinematic, photo, classic, banner, social, story\n"
            "Example: `/gen a corgi astronaut in space --ratio wide`"
        )

    text = raw_args.strip()
    ratio: Optional[str] = None
    tokens = text.split()
    kept: List[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("--ratio", "-r") and i + 1 < len(tokens):
            ratio = tokens[i + 1].lower()
            i += 2
            continue
        if tok.startswith("--ratio="):
            ratio = tok.split("=", 1)[1].lower()
            i += 1
            continue
        kept.append(tok)
        i += 1
    prompt = " ".join(kept).strip()
    if not prompt:
        return "✏️ Prompt is empty. Try `/gen a corgi astronaut in space`."

    provider = _get_provider()
    kwargs: Dict[str, Any] = {}
    if ratio:
        kwargs["aspect_ratio"] = ratio

    result = provider.generate(prompt=prompt, **kwargs)
    if not result.get("success"):
        return f"❌ {result.get('error', 'generation failed')}"
    return _format_success(result, prompt)


def register(ctx) -> None:
    """Standard Hermes user-plugin entry point."""
    ctx.register_image_gen_provider(FreegenImageGenProvider())

    ctx.register_command(
        name="gen",
        handler=_handle_gen_command,
        description="Generate an AI image with the free freegen.app backend (Z-Image Turbo, no API key).",
        args_hint="<prompt> [--ratio <square|landscape|portrait|wide|tall|ultrawide|cinematic|photo|classic|banner|social|story>]",
    )
    ctx.register_command(
        name="img",
        handler=_handle_gen_command,
        description="Alias of /gen — generate an image with freegen.app.",
        args_hint="<prompt> [--ratio ...]",
    )
    ctx.register_command(
        name="imagine",
        handler=_handle_gen_command,
        description="Alias of /gen — generate an image with freegen.app.",
        args_hint="<prompt> [--ratio ...]",
    )
    logger.info("freegen plugin registered: /gen, /img, /imagine slash commands + image gen provider")
