"""Best-effort, process-scoped Python socket egress guard.

This intentionally does not claim to replace a firewall or air-gapped network.
Native extensions or external child processes may not use Python sockets.
"""

import socket
from contextlib import contextmanager
from unittest.mock import patch


def _blocked(*args, **kwargs):
    raise PermissionError(
        "Network access blocked by --offline. Preinstall dependencies and OCR "
        "model weights, or use OS/container/network egress controls for stronger isolation."
    )


@contextmanager
def offline_network_guard(enabled: bool = False):
    """Reject Python socket connections while the caller processes documents."""
    if not enabled:
        yield
        return

    with (
        patch.object(socket.socket, "connect", _blocked),
        patch.object(socket.socket, "connect_ex", _blocked),
        patch.object(socket, "create_connection", _blocked),
        patch.object(socket, "getaddrinfo", _blocked),
    ):
        yield
