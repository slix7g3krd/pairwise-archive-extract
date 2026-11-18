"""安全解压规划：路径归一、根目录锁定、链接/特殊类型拒绝、压缩比与数量/深度限制。"""

import os
import re
import unicodedata

# 压缩比上限（解压后大小 / 压缩大小）
MAX_COMPRESSION_RATIO = 1000

# 允许解出的 entry 类型；device/fifo/socket 等特殊文件一律拒绝
_ALLOWED_TYPES = frozenset({'file', 'dir'})
# 链接类型：符号链接/硬链接都不得解出
_LINK_TYPES = frozenset({'symlink', 'hardlink'})

# Windows 盘符（C:、D:\ ...），含归一前后的形态
_DRIVE_RE = re.compile(r'^[A-Za-z]:')
# 控制字符（含 NUL），entry 名中不允许出现
_CONTROL_RE = re.compile(r'[\x00-\x1f\x7f]')


def _normalize_name(name):
    """编码归一（UTF-8/CP437）+ Unicode NFC 归一 + 统一路径分隔符。"""
    if isinstance(name, bytes):
        try:
            name = name.decode('utf-8')
        except UnicodeDecodeError:
            name = name.decode('cp437', errors='replace')
    if not isinstance(name, str):
        return None
    # Unicode 归一：同形字符（如全角、组合字符）归一到同一形态，防止绕过黑名单
    name = unicodedata.normalize('NFC', name)
    # 反斜杠统一为正斜杠，Windows 分隔符不能成为绕过手段
    name = name.replace('\\', '/')
    return name


def safe_member_path(root, name):
    """把 entry 名归一到 root 之内的绝对路径；越界/非法一律返回 None。

    拒绝：空名、绝对路径、Windows 盘符、.. 穿越、控制字符，
    并锁定结果必须位于 root 之内（根目录本身不可被 entry 改写）。
    """
    if not name:
        return None
    name = _normalize_name(name)
    if not name:
        return None
    if _CONTROL_RE.search(name):
        return None
    # 绝对路径（POSIX / UNC）与 Windows 盘符
    if name.startswith('/') or _DRIVE_RE.match(name):
        return None

    root_abs = os.path.abspath(root)
    parts = []
    for part in name.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            return None
        parts.append(part)
    if not parts:
        # 名归一后没有任何有效段（如 '.' 或 '..'），不允许指向根目录本身
        return None

    target = os.path.abspath(os.path.join(root_abs, *parts))
    # 根目录锁定：共同前缀必须就是 root（防止 ../root2 这类兄弟目录逃逸）
    if target != root_abs and os.path.commonpath([root_abs, target]) == root_abs:
        return target
    return None


def is_link(entry):
    """entry 是否为符号链接/硬链接（这两类一律拒绝解出）。"""
    if not isinstance(entry, dict):
        return False
    return entry.get('type') in _LINK_TYPES


def ratio_ok(uncompressed_size, compressed_size):
    """压缩比检查：解压后/压缩前不得超过 MAX_COMPRESSION_RATIO（防 zip 炸弹）。"""
    if uncompressed_size is None or compressed_size is None:
        return False
    if uncompressed_size < 0 or compressed_size < 0:
        return False
    if compressed_size == 0:
        return uncompressed_size == 0
    return uncompressed_size <= compressed_size * MAX_COMPRESSION_RATIO


def unique_target(path, existing):
    """同名 entry 不允许后写覆盖先写：冲突时生成不重复的目标路径。"""
    if path not in existing:
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = '{}_{}{}'.format(base, i, ext)
        if candidate not in existing:
            return candidate
        i += 1


def extract_plan(entries, root, max_entries, max_depth=None):
    """生成解压计划（归一后的相对路径列表）；任何一项不合法即整体失败返回 None。

    - entry 数量不得超过 max_entries
    - 拒绝符号/硬链接与 file/dir 之外的特殊类型（device/fifo 等）
    - 每个 entry 名必须通过 safe_member_path 的根目录锁定检查
    - max_depth 限制嵌套深度（防递归解压炸弹）
    - 重名 entry 经 unique_target 改名，不允许覆盖
    """
    if entries is None or max_entries is None or max_entries < 0:
        return None
    if len(entries) > max_entries:
        return None

    root_abs = os.path.abspath(root)
    planned = set()
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        entry_type = entry.get('type')
        if is_link(entry) or entry_type not in _ALLOWED_TYPES:
            return None
        target = safe_member_path(root_abs, entry.get('name'))
        if target is None:
            return None
        rel = os.path.relpath(target, root_abs)
        if max_depth is not None:
            # 深度 = 相对路径的目录层数（'a' 为 0，'a/b' 为 1）
            depth = len(rel.split(os.sep)) - 1
            if depth > max_depth:
                return None
        target = unique_target(target, planned)
        planned.add(target)
        result.append(os.path.relpath(target, root_abs))
    return result
