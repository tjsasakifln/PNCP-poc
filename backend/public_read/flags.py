"""Cutover flags for public_read_v1 — #2108.

Mode is an env string (not a boolean feature flag):
  PUBLIC_READ_V1_MODE=off|shadow|canary|on

Kill switch is a boolean flag that independently disables extra-cli reads.
"""

from __future__ import annotations

import os
from enum import StrEnum

VALID_MODES = frozenset({"off", "shadow", "canary", "on"})


class PublicReadMode(StrEnum):
    OFF = "off"
    SHADOW = "shadow"
    CANARY = "canary"
    ON = "on"


def get_public_read_mode() -> PublicReadMode:
    raw = os.getenv("PUBLIC_READ_V1_MODE", "off").strip().lower()
    if raw not in VALID_MODES:
        return PublicReadMode.OFF
    return PublicReadMode(raw)


def is_kill_switch_on() -> bool:
    from config.features import get_feature_flag

    return bool(get_feature_flag("PUBLIC_READ_KILL_SWITCH"))


def should_read_legacy() -> bool:
    mode = get_public_read_mode()
    return mode in {PublicReadMode.OFF, PublicReadMode.SHADOW, PublicReadMode.CANARY}


def should_read_public() -> bool:
    if is_kill_switch_on():
        return False
    return get_public_read_mode() in {
        PublicReadMode.SHADOW,
        PublicReadMode.CANARY,
        PublicReadMode.ON,
    }


def should_serve_public() -> bool:
    if is_kill_switch_on():
        return False
    return get_public_read_mode() in {PublicReadMode.CANARY, PublicReadMode.ON}
