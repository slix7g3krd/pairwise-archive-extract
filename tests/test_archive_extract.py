import pytest

from security.archive_extract import (
    safe_member_path,
    is_link,
    ratio_ok,
    extract_plan,
    unique_target
)


def test_safe_path():
    import os
    root = os.path.abspath('root')
    assert safe_member_path(root, 'a/b.txt') is not None

def test_traversal():
    import os
    root = os.path.abspath('root')
    assert safe_member_path(root, '../x') is None

def test_absolute():
    import os
    root = os.path.abspath('root')
    assert safe_member_path(root, '/etc/passwd') is None

def test_windows():
    import os
    root = os.path.abspath('root')
    assert safe_member_path(root, 'C:' + chr(92) + 'x') is None

def test_symlink():
    assert is_link({'type': 'symlink'}) is True

def test_hardlink():
    assert is_link({'type': 'hardlink'}) is True

def test_ratio_ok():
    assert ratio_ok(1000, 1) is True

def test_ratio_bad():
    assert ratio_ok(1001, 1) is False

def test_unique():
    assert unique_target('/root/a.txt', {'/root/a.txt'}) != '/root/a.txt'

def test_max_entries():
    import os
    root = os.path.abspath('root')
    entries = [{'name': 'a', 'type': 'file'}, {'name': 'b', 'type': 'file'}]
    assert extract_plan(entries, root, 1) is None

def test_depth():
    import os
    root = os.path.abspath('root')
    entries = [{'name': 'a/b/c/d', 'type': 'file'}]
    assert extract_plan(entries, root, 10, 1) is None

def test_device():
    assert is_link({'type': 'device'}) is False

def test_empty_name():
    import os
    root = os.path.abspath('root')
    assert safe_member_path(root, '') is None

def test_root_collision():
    import os
    root = os.path.abspath('root')
    assert safe_member_path(root, '../root2/x') is None

def test_plan_ok():
    import os
    root = os.path.abspath('root')
    entries = [{'name': 'a', 'type': 'file'}]
    assert extract_plan(entries, root, 10) == ['a']
