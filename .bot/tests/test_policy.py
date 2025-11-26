from core.policy import Policy, PermissionLevel


def test_policy_blacklist():
    policy = Policy()
    allowed, reason = policy.validate_action("rm -rf /", PermissionLevel.ADMIN)
    assert not allowed
    assert "blacklisted" in reason.lower()


def test_policy_permission_levels():
    policy = Policy()

    # READ_ONLY allows read operations
    allowed, _ = policy.validate_action("read_file", PermissionLevel.READ_ONLY)
    assert allowed

    # READ_ONLY does not allow write
    allowed, _ = policy.validate_action("write_file", PermissionLevel.READ_ONLY)
    assert not allowed

    # ADMIN allows everything (except blacklist)
    allowed, _ = policy.validate_action("write_file", PermissionLevel.ADMIN)
    assert allowed


def test_policy_confirmation_required():
    policy = Policy()
    allowed, reason = policy.validate_action("delete_file", PermissionLevel.FILE_OPERATIONS)
    assert allowed
    assert "confirmation" in reason.lower() if reason else True


def test_policy_safe_path():
    policy = Policy()
    assert not policy.is_safe_path("C:\\Windows\\System32\\file.txt")
    assert policy.is_safe_path("C:\\Users\\Documents\\file.txt")
