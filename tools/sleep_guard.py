"""防止系統進入睡眠（Windows SetThreadExecutionState）"""

import contextlib
import sys

if sys.platform == "win32":
    import ctypes

    _ES_CONTINUOUS = 0x80000000
    _ES_SYSTEM_REQUIRED = 0x00000001


@contextlib.contextmanager
def prevent_sleep():
    """
    Context manager：執行期間阻止 Windows 進入睡眠。

    非 Windows 平台為 no-op，可安全跨平台使用。

    用法：
        with prevent_sleep():
            long_running_task()
    """
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED)
    try:
        yield
    finally:
        if sys.platform == "win32":
            # 恢復預設，允許系統正常睡眠
            ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
