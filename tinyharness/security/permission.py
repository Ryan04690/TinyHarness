from enum import Enum


class PermissionAction(str, Enum):

    READ = "read"
    WRITE = "write"
    SHELL = "shell"



class PermissionDecision(str, Enum):

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"



class PermissionManager:
    def __init__(self, rules=None):
        self.rules = {    # The access control system can be customized
            PermissionAction.READ: PermissionDecision.ALLOW,
            PermissionAction.WRITE: PermissionDecision.ASK,
            PermissionAction.SHELL: PermissionDecision.ASK,
        }

        if rules is not None:
            self.rules.update(rules)

    def check(self, action: PermissionAction) -> PermissionDecision:
        # Unknown actions are denied by default.
        return self.rules.get(action, PermissionDecision.DENY)

    def require(
        self,
        action: PermissionAction,
        *,
        user_approved: bool = False,
    ) -> None:
        decision = self.check(action)

        if decision == PermissionDecision.ALLOW:
            return

        if (
            decision == PermissionDecision.ASK
            and user_approved
        ):
            return

        raise PermissionError(
            f"Permission denied: {action} ({decision})"
        )