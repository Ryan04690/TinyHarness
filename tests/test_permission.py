from tinyharness.security import (
    PermissionManager,
    PermissionAction,
    PermissionDecision,
)


def test_read_is_allowed():

    manager = PermissionManager()

    result = manager.check(
        PermissionAction.READ
    )

    assert result == PermissionDecision.ALLOW



def test_write_requires_confirmation():

    manager = PermissionManager()

    result = manager.check(
        PermissionAction.WRITE
    )

    assert result == PermissionDecision.ASK



def test_shell_requires_confirmation():

    manager = PermissionManager()

    result = manager.check(
        PermissionAction.SHELL
    )

    assert result == PermissionDecision.ASK

import pytest


def test_custom_deny_rule():
    manager = PermissionManager(
        rules={
            PermissionAction.SHELL: PermissionDecision.DENY,
        }
    )

    assert manager.check(
        PermissionAction.SHELL
    ) == PermissionDecision.DENY


def test_ask_requires_approval():
    manager = PermissionManager()

    with pytest.raises(PermissionError):
        manager.require(PermissionAction.WRITE)

    # Simulate approval from a trusted caller.
    manager.require(
        PermissionAction.WRITE,
        user_approved=True,
    )


def test_deny_cannot_be_approved():
    manager = PermissionManager(
        rules={
            PermissionAction.SHELL: PermissionDecision.DENY,
        }
    )

    with pytest.raises(PermissionError):
        manager.require(
            PermissionAction.SHELL,
            user_approved=True,
        )