"""在安全限制下运行用户提交的 Python 代码（给公开的教学网站用）。

四层护栏：
1. 超时保护 —— 防止 `while True: pass` 之类的死循环拖垮整个应用
2. 模块白名单 —— 禁止 os / sys / subprocess / socket 等系统与网络模块
3. 砍掉危险内置函数 —— open / eval / exec / compile / input 等
4. 输出上限 —— 防止疯狂 print 把内存刷爆

⚠️ 说明：这是「防呆护栏」，不是滴水不漏的安全沙箱。
   真正保证服务器安全的是：网页部署在**云端隔离容器**里运行
   （例如 Streamlit Community Cloud），而不是跑在你自己的电脑上。

对外接口只有一个：
    output, error, timed_out, truncated = run_user_code(code, timeout=5.0)
"""

import builtins as _builtins
import contextlib
import ctypes
import io
import threading

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
# 允许 import 的模块（学习常用 + 纯计算/文本处理，不涉及系统与网络）
ALLOWED_MODULES = {
    "math", "random", "datetime", "decimal", "fractions", "statistics",
    "string", "collections", "itertools", "functools", "operator",
    "re", "json", "time", "textwrap", "unicodedata", "heapq", "bisect",
    "copy", "enum", "typing", "numbers", "calendar", "io", "abc",
    "dataclasses", "zoneinfo", "uuid", "hashlib",
}

# 要从内置函数里移除的危险项
_REMOVED_BUILTINS = (
    "open", "eval", "exec", "compile", "input", "exit", "quit",
    "breakpoint", "help", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "memoryview",
)

MAX_OUTPUT_CHARS = 20000     # 输出最长保留的字符数
DEFAULT_TIMEOUT = 5.0        # 默认超时（秒）


class BlockedModuleError(Exception):
    """尝试导入白名单之外的模块。"""


class CodeTimeoutError(Exception):
    """代码运行超时，已被强制停止。"""


class _AsyncTimeout(BaseException):
    """注入到子线程里、用于中断死循环的内部异常（继承 BaseException 以免被用户代码捕获）。"""


# ---------------------------------------------------------------------------
# 受限运行环境
# ---------------------------------------------------------------------------
def _make_safe_globals():
    """构造一个受限的执行命名空间。"""
    real_import = _builtins.__import__

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        root = name.split(".")[0]
        if root not in ALLOWED_MODULES:
            raise BlockedModuleError(
                "模块 '%s' 已被禁用（为保护服务器安全，本网站只允许 "
                "math、random、datetime、re、json 等学习用模块）" % root
            )
        return real_import(name, globals, locals, fromlist, level)

    safe = {n: getattr(_builtins, n) for n in dir(_builtins) if not n.startswith("_")}
    for name in _REMOVED_BUILTINS:
        safe.pop(name, None)

    # 定义 class 时解释器需要它
    if hasattr(_builtins, "__build_class__"):
        safe["__build_class__"] = _builtins.__build_class__

    safe["__import__"] = safe_import

    return {"__name__": "__main__", "__builtins__": safe}


def _raise_in_thread(thread_id, exc_type):
    """尽力让某个子线程抛出指定异常（用于中断死循环）。"""
    if thread_id is None or not hasattr(ctypes, "pythonapi"):
        return
    try:
        func = ctypes.pythonapi.PyThreadState_SetAsyncExc
        func.argtypes = [ctypes.c_ulong, ctypes.py_object]
        func.restype = ctypes.c_int
        if func(ctypes.c_ulong(thread_id), ctypes.py_object(exc_type)) > 1:
            func(ctypes.c_ulong(thread_id), None)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def run_user_code(code, timeout=DEFAULT_TIMEOUT):
    """在受限环境 + 独立线程中执行用户代码。

    返回 (output, error, timed_out, truncated)：
        output    —— 捕获到的 stdout 文本（超长会截断）
        error     —— 异常对象；没有异常则为 None
        timed_out —— 是否因为超时被强制停止
        truncated —— 输出是否被截断过
    """
    buffer = io.StringIO()
    namespace = _make_safe_globals()
    box = {}

    def worker():
        try:
            with contextlib.redirect_stdout(buffer):
                exec(compile(code, "<user_code>", "exec"), namespace)
        except BaseException as exc:  # noqa: BLE001
            box["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)

    timed_out = thread.is_alive()
    if timed_out:
        _raise_in_thread(thread.ident, _AsyncTimeout)
        thread.join(0.5)

    output = buffer.getvalue()
    truncated = len(output) > MAX_OUTPUT_CHARS
    if truncated:
        output = output[:MAX_OUTPUT_CHARS] + "\n\n...（输出内容过长，已截断显示）"

    if timed_out:
        return output, CodeTimeoutError(
            "代码运行超过 %g 秒仍未结束，已被自动停止" % timeout
        ), True, truncated

    return output, box.get("error"), False, truncated
