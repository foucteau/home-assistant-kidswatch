"""Stable machine-derived KidsWatch client identifier."""
from __future__ import annotations

import hashlib
import os
import platform
import socket
from pathlib import Path

from homeassistant.core import HomeAssistant


def _read_first_existing(paths: tuple[str, ...]) -> str:
    for raw_path in paths:
        try:
            path = Path(raw_path)
            if path.is_file():
                value = path.read_text(encoding="utf-8", errors="ignore").strip()
                if value:
                    return value
        except OSError:
            continue
    return ""


def generate_machine_m2(hass: HomeAssistant) -> str:
    """Return a stable 32-character hexadecimal client identifier."""
    machine_id = _read_first_existing(("/etc/machine-id", "/var/lib/dbus/machine-id"))
    pieces = [
        "kidswatch-ha-m2-v1",
        machine_id,
        socket.gethostname(),
        platform.node(),
        platform.machine(),
        platform.system(),
        platform.release(),
        str(Path(hass.config.config_dir).resolve()),
        os.environ.get("HOSTNAME", ""),
    ]
    material = "|".join(piece.strip() for piece in pieces if piece and piece.strip())
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
