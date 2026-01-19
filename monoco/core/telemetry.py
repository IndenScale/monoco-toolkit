import os
import uuid
import json

import time
from pathlib import Path
from typing import Optional, Dict, Any
from monoco.core.config import get_config

POSTHOG_API_KEY = "phc_MndV8H8v0W3P7Yv1P7Z8X7X7X7X7X7X7X7X7"
POSTHOG_HOST = "https://app.posthog.com"


class Telemetry:
    def __init__(self):
        self.config = get_config()
        self._device_id = self._get_or_create_device_id()

    def _get_or_create_device_id(self) -> str:
        state_path = Path.home() / ".monoco" / "state.json"
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    state = json.load(f)
                    if "device_id" in state:
                        return state["device_id"]
            except Exception:
                pass

        device_id = str(uuid.uuid4())
        state_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            state = {}
            if state_path.exists():
                with open(state_path, "r") as f:
                    state = json.load(f)
            state["device_id"] = device_id
            with open(state_path, "w") as f:
                json.dump(state, f)
        except Exception:
            pass
        return device_id

    def capture(self, event_name: str, properties: Optional[Dict[str, Any]] = None):
        # Notify user on first use if not configured
        if self.config.telemetry.enabled is None:
            # We don't want to spam, but we must be transparent
            # This is a one-time notice in a session via a class-level flag?
            # Or just rely on the fact that 'init' will fix it.
            # To be safe and minimal, we'll just skip capture if not explicitly enabled
            return

        if self.config.telemetry.enabled is False:
            return

        # Namespace events
        namespaced_event = f"cli:{event_name}"
        props = {
            "distinct_id": self._device_id,
            "project_key": self.config.project.key,
            "project_name": self.config.project.name,
            "os": os.name,
            "cli_version": "0.1.0",
        }
        if properties:
            props.update(properties)

        data = {
            "api_key": POSTHOG_API_KEY,
            "event": namespaced_event,
            "properties": props,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }

        # Send asynchronously? For now, we'll do a simple non-blocking-ish call
        try:
            import httpx

            httpx.post(f"{POSTHOG_HOST}/capture/", json=data, timeout=1.0)
        except ImportError:
            pass  # Telemetry is optional
        except Exception:
            pass


_instance = None


def capture_event(event: str, properties: Optional[Dict[str, Any]] = None):
    global _instance
    if _instance is None:
        _instance = Telemetry()
    _instance.capture(event, properties)
