"""SmartLic consumer of extra-cli ``public_read_v1``.

Browser never talks to extra-cli. FastAPI is the only adapter.
"""

from public_read.flags import PublicReadMode, get_public_read_mode, is_kill_switch_on
from public_read.serve import serve_family

__all__ = [
    "PublicReadMode",
    "get_public_read_mode",
    "is_kill_switch_on",
    "serve_family",
]
