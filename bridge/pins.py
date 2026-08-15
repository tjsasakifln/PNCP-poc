"""Invariants of the hash-pinned web-cfg#62 execute set.

These constants describe SHA-256
``c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d``.
A different manifesto file must fail closed before any artifact is emitted.
"""

from __future__ import annotations

PINNED_SHA256 = "c2cee8362321099205b76b11f89485d4248a00b8abbbda354d15964f6b316e0d"
# SHA-256 of the canonical map payload (not the on-disk file, which also stores this digest).
PINNED_CONFIG_SHA256 = "c07c1a5dc99932ae0536380e904379418b6a16015c02ac3c80f36660ab79ea68"
PINNED_COMMIT = "3f112bfbd9e6b042691e1c09812af00f42735adb"
PINNED_VERSION = "v1"
PINNED_SCHEMA = "smartlic-confenge-manifesto-v1"
PINNED_REDIRECT_COUNT = 11
PINNED_RETIRE_COUNT = 1244
PINNED_CANONICAL_HOST = "https://confenge.com.br"
PINNED_LEGACY_HOST = "https://smartlic.tech"
PINNED_SOURCE = (
    "https://raw.githubusercontent.com/tjsasakifln/web-cfg/"
    f"{PINNED_COMMIT}/data/migration/smartlic-confenge/manifesto.v1.json"
)

LEGACY_HOSTNAMES = frozenset({"smartlic.tech", "www.smartlic.tech"})
TARGET_HOSTNAME = "confenge.com.br"
FORBIDDEN_TARGET_PATHS = frozenset({"/", "/consultoria-b2g", "/consultoria-b2g/"})
FORBIDDEN_GENERIC_TARGETS = frozenset(
    {
        "https://confenge.com.br/",
        "https://confenge.com.br",
        "https://confenge.com.br/consultoria-b2g/",
        "https://confenge.com.br/consultoria-b2g",
        "https://www.confenge.com.br/",
        "https://www.confenge.com.br",
    }
)

PII_QUERY_KEYS = frozenset(
    {
        "email",
        "phone",
        "name",
        "cnpj",
        "cpf",
        "telefone",
        "nome",
        "password",
        "token",
        "secret",
    }
)

DEFAULT_STATUS = 410
REDIRECT_STATUS = 301
OBSERVATION_WINDOW_DAYS = 28
BRIDGE_OWNER = "SmartLic#2115"
COST = "UNKNOWN"
