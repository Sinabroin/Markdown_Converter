"""Offline guard blocks Python socket egress and restores normal behavior."""

import socket

import pytest

from f2md.network_guard import offline_network_guard


def test_offline_blocks_socket_connect():
    sock = socket.socket()
    try:
        with offline_network_guard(enabled=True):
            with pytest.raises(PermissionError, match="--offline"):
                sock.connect(("127.0.0.1", 12345))
    finally:
        sock.close()


def test_offline_blocks_name_lookup():
    with offline_network_guard(enabled=True):
        with pytest.raises(PermissionError, match="--offline"):
            socket.getaddrinfo("example.com", 443)


def test_offline_is_scoped_and_restored():
    original_connect = socket.socket.connect
    original_getaddrinfo = socket.getaddrinfo
    with offline_network_guard(enabled=True):
        assert socket.socket.connect is not original_connect
        assert socket.getaddrinfo is not original_getaddrinfo
    assert socket.socket.connect is original_connect
    assert socket.getaddrinfo is original_getaddrinfo


def test_disabled_guard_does_not_patch_socket():
    original_connect = socket.socket.connect
    with offline_network_guard():
        assert socket.socket.connect is original_connect
