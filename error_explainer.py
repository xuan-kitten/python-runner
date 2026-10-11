"""把 Python 运行时的报错翻译成「中文原因 + 修改建议」。

供 streamlit_app.py 使用：
    from error_explainer import ERR_UI, build_raw_error, explain_error
"""

import re
import traceback

# ---------------------------------------------------------------------------
# 报错解读区用到的界面文字
# ---------------------------------------------------------------------------
ERR_UI = {
    "zh": {
        "raw_title": "📋 原始报错信息（Traceback）",
        "hint_title": "🤖 报错原因（中文解读）",
        "type_label": "错误类型",
        "where": "出错位置",
        "line_n": "第 {n} 行",
        "code_line": "出错的那一行：",
        "why": "为什么会报错",
        "how": "可以这样改",
        "generic": "代码运行时抛出了异常。",
        "unknown": "这个错误比较少见，请结合左侧原始报错信息一起看。",
    },
    "en": {
        "raw_title": "📋 Raw traceback",
        "hint_title": "🤖 Why it failed",
        "type_label": "Error type",
        "where": "Where",
        "line_n": "line {n}",
        "code_line": "The failing line:",
        "why": "Why it failed",
        "how": "How to fix",
        "generic": "Your code raised an exception while running.",
        "unknown": "This error is uncommon; please also read the raw traceback.",
    },
}

# ---------------------------------------------------------------------------
# 错误类型 -> 解释（title 名称 / why 原因 / fix 修改建议）
# ---------------------------------------------------------------------------
ERRLIB = {
    "SyntaxError": {
        "zh": {
            "title": "语法错误（SyntaxError）",
            "why": "Python 还没开始运行就看不懂这段代码了——括号、引号或冒号没有配对。",
            "fix": "- 检查报错行以及它的上一行：`()`、`[]`、引号是否都成对闭合\n"
                   "- 中文标点（`（`、`“`、`：`）不是合法语法，要换成英文半角符号",
        },
        "en": {
            "title": "SyntaxError",
            "why": "Python could not even parse the code: brackets, quotes or colons are unbalanced.",
            "fix": "- Check the reported line and the line above for unclosed `()`, `[]` or quotes\n"
                   "- Full-width punctuation such as `（` `“` `：` is not valid Python",
        },
    },
    "IndentationError": {
        "zh": {
            "title": "缩进错误（IndentationError）",
            "why": "同一层级语句的缩进不一致，或者该缩进的地方没有缩进。",
            "fix": "- 统一用 4 个空格缩进，同一代码块里的缩进必须完全一样\n"
                   "- `if` / `for` / `while` / `def` 的下一行必须缩进",
        },
        "en": {
            "title": "IndentationError",
            "why": "Statements on the same level have inconsistent indentation.",
            "fix": "- Use 4 spaces consistently; blocks must line up exactly\n"
                   "- The line after `if` / `for` / `while` / `def` must be indented",
        },
    },
    "TabError": {
        "zh": {
            "title": "混用 Tab 与空格（TabError）",
            "why": "同一个代码块里既用了 Tab 又用了空格缩进。",
            "fix": "- 全部统一改成空格（推荐 4 个空格）\n- 编辑器里开启「将 Tab 转成空格」",
        },
        "en": {
            "title": "TabError",
            "why": "Tabs and spaces are mixed for indentation in the same block.",
            "fix": "- Convert all indentation to spaces (4 spaces recommended)\n"
                   "- Enable 'convert tabs to spaces' in your editor",
        },
    },
    "NameError": {
        "zh": {
            "title": "名字未定义（NameError）",
            "why": "你用了一个程序还不认识的名字——在使用它之前没有给它赋值。",
            "fix": "- 检查名字是否拼写错误（Python 区分大小写）\n"
                   "- 先赋值再使用，例如 `a = 10` 之后才能 `print(a)`",
        },
        "en": {
            "title": "NameError",
            "why": "You used a name that was never assigned before use.",
            "fix": "- Check the spelling (Python is case-sensitive)\n"
                   "- Assign it first, e.g. `a = 10` before `print(a)`",
        },
    },
    "UnboundLocalError": {
        "zh": {
            "title": "变量在赋值前被使用（UnboundLocalError）",
            "why": "函数里给某个变量赋值了，它就成了局部变量，但在赋值之前就被读取了。",
            "fix": "- 把赋值语句挪到使用之前\n- 或改用别的变量名，避免和函数外的同名变量混淆",
        },
        "en": {
            "title": "UnboundLocalError",
            "why": "A variable is local (assigned inside the function) but read before assignment.",
            "fix": "- Move the assignment before the usage\n- Or use a different variable name",
        },
    },
    "TypeError": {
        "zh": {
            "title": "类型错误（TypeError）",
            "why": "把不匹配的数据类型放在一起运算，或把不是函数的东西当函数调用。",
            "fix": "- 数字和字符串不能直接相加，先转换：`str(数字)` 或 `int(文字)`\n"
                   "- 检查函数调用的参数个数和括号是否写对",
        },
        "en": {
            "title": "TypeError",
            "why": "Incompatible types were used together, or something that is not a function was called.",
            "fix": "- Convert first: `str(number)` or `int(text)`\n"
                   "- Check the number of arguments and the parentheses",
        },
    },
    "ValueError": {
        "zh": {
            "title": "值错误（ValueError）",
            "why": "类型是对的，但值本身不合法（例如把一段文字转换成整数）。",
            "fix": "- 用 `int()` / `float()` 转换前，先确认内容真的是数字\n"
                   "- 可以先用 `.strip()` 去掉首尾空格，或用 `try / except` 兜住",
        },
        "en": {
            "title": "ValueError",
            "why": "The type is right but the value is invalid (e.g. converting text to int).",
            "fix": "- Make sure the text is numeric before `int()` / `float()`\n"
                   "- Use `.strip()` to remove spaces, or wrap it in `try / except`",
        },
    },
    "ZeroDivisionError": {
        "zh": {
            "title": "除以零（ZeroDivisionError）",
            "why": "除数是 0，数学上不允许这样做。",
            "fix": "- 运算前先判断除数，例如 `if b != 0:`\n- 顺便检查 `%`（取余）右边的数字",
        },
        "en": {
            "title": "ZeroDivisionError",
            "why": "The divisor is 0, which is not allowed.",
            "fix": "- Guard the divisor first, e.g. `if b != 0:`\n- Also check the right side of `%`",
        },
    },
    "IndexError": {
        "zh": {
            "title": "索引越界（IndexError）",
            "why": "用 `[...]` 取的序号超出了范围。",
            "fix": "- 索引从 0 开始；长度为 n 的序列最后一个索引是 n-1\n"
                   "- 取最后一个元素用 `-1`，不确定长度时先用 `len()` 判断",
        },
        "en": {
            "title": "IndexError",
            "why": "The index is outside the valid range.",
            "fix": "- Indexes start at 0; the last index is len-1\n"
                   "- Use `-1` for the last item, or check with `len()`",
        },
    },
    "KeyError": {
        "zh": {
            "title": "字典键不存在（KeyError）",
            "why": "字典里没有你取的那个键。",
            "fix": "- 用 `d.get('键', 默认值)` 代替 `d['键']` 会更安全\n"
                   "- 或者先用 `if '键' in d:` 判断一下",
        },
        "en": {
            "title": "KeyError",
            "why": "The dictionary has no such key.",
            "fix": "- Use `d.get(key, default)` instead of `d[key]`\n"
                   "- Or check first: `if key in d:`",
        },
    },
    "AttributeError": {
        "zh": {
            "title": "属性或方法不存在（AttributeError）",
            "why": "这个类型的对象没有你调用的属性 / 方法（多为拼写错误或类型不符合预期）。",
            "fix": "- 检查方法名拼写，例如该用 `.append()` 还是 `.add()`\n"
                   "- 用 `print(type(x))` 看看对象到底是什么类型",
        },
        "en": {
            "title": "AttributeError",
            "why": "The object has no such attribute or method (often a typo or unexpected type).",
            "fix": "- Check the method name, e.g. `.append()` vs `.add()`\n"
                   "- Use `print(type(x))` to see the real type",
        },
    },
    "ModuleNotFoundError": {
        "zh": {
            "title": "找不到模块（ModuleNotFoundError）",
            "why": "代码里 `import` 了一个还没安装（或名字写错）的模块。",
            "fix": "- 安装它：`pip install 模块名`\n- 检查模块名拼写，注意不要和文件名重名",
        },
        "en": {
            "title": "ModuleNotFoundError",
            "why": "The imported module is not installed (or the name is wrong).",
            "fix": "- Install it: `pip install <module>`\n- Check the spelling, avoid clashing with your file name",
        },
    },
    "ImportError": {
        "zh": {
            "title": "导入失败（ImportError）",
            "why": "模块存在，但里面要导入的名字不存在。",
            "fix": "- 检查 `from 模块 import 名字` 里的名字拼写\n"
                   "- 换成 `import 模块` 然后用 `模块.名字` 访问",
        },
        "en": {
            "title": "ImportError",
            "why": "The module exists but the imported name does not.",
            "fix": "- Check the name in `from module import name`\n"
                   "- Or `import module` and use `module.name`",
        },
    },
    "FileNotFoundError": {
        "zh": {
            "title": "找不到文件（FileNotFoundError）",
            "why": "要打开的文件路径不存在。",
            "fix": "- 检查路径拼写，Windows 下注意反斜杠要写成 `\\\\` 或用 `/`\n"
                   "- 用绝对路径更保险，也可以先用 `os.path.exists()` 判断",
        },
        "en": {
            "title": "FileNotFoundError",
            "why": "The file path does not exist.",
            "fix": "- Check the path; on Windows escape `\\` or use `/`\n"
                   "- Prefer absolute paths, or check with `os.path.exists()`",
        },
    },
    "PermissionError": {
        "zh": {
            "title": "权限不足（PermissionError）",
            "why": "没有权限读写这个文件 / 目录（或文件正被别的程序占用）。",
            "fix": "- 关闭正在占用该文件的程序再试\n- 换一个可写的目录，或以管理员身份运行",
        },
        "en": {
            "title": "PermissionError",
            "why": "No permission to access the file (or it is locked by another program).",
            "fix": "- Close the program locking the file\n- Use a writable folder, or run as administrator",
        },
    },
    "OSError": {
        "zh": {
            "title": "系统 / 输入输出错误（OSError）",
            "why": "操作系统层面的操作失败了，例如读写文件、网络等。",
            "fix": "- 看具体错误信息里的文件或地址\n- 检查路径、网络连接和磁盘空间",
        },
        "en": {
            "title": "OSError",
            "why": "An operating-system level operation failed (file I/O, network, ...).",
            "fix": "- Read the file/address in the message\n- Check the path, network and disk space",
        },
    },
    "RecursionError": {
        "zh": {
            "title": "递归太深（RecursionError）",
            "why": "函数自己调用自己，但没有正确的结束条件，就会一直调用下去。",
            "fix": "- 检查递归函数是否漏了 `return` 的终止条件\n"
                   "- 确认每次递归都在向终止条件靠近",
        },
        "en": {
            "title": "RecursionError",
            "why": "A function calls itself without a proper base case.",
            "fix": "- Make sure there is a terminating condition\n- Ensure each call moves toward it",
        },
    },
    "MemoryError": {
        "zh": {
            "title": "内存不足（MemoryError）",
            "why": "一次性创建的数据太大了，内存放不下。",
            "fix": "- 不要一次生成超大的列表 / 字符串，改成边算边用\n- 减小数据规模",
        },
        "en": {
            "title": "MemoryError",
            "why": "The data created at once is too large for memory.",
            "fix": "- Avoid building huge lists/strings at once\n- Reduce the data size",
        },
    },
    "OverflowError": {
        "zh": {
            "title": "数值溢出（OverflowError）",
            "why": "计算结果超出了该类型能表示的范围。",
            "fix": "- 减少运算量级，或改用支持更大范围的类型（如浮点 / 十进制）",
        },
        "en": {
            "title": "OverflowError",
            "why": "The result exceeds the range of the type.",
            "fix": "- Reduce the magnitude, or use a wider numeric type",
        },
    },
    "StopIteration": {
        "zh": {
            "title": "迭代已结束（StopIteration）",
            "why": "对已经没有元素的迭代器继续调用 `next()` 时会出现。",
            "fix": "- 用 `next(it, 默认值)` 提供默认值\n- 或改用 `for` 循环遍历",
        },
        "en": {
            "title": "StopIteration",
            "why": "Calling `next()` on an exhausted iterator.",
            "fix": "- Use `next(it, default)`\n- Or iterate with a `for` loop",
        },
    },
    "AssertionError": {
        "zh": {
            "title": "断言失败（AssertionError）",
            "why": "`assert 条件` 里的条件不成立。",
            "fix": "- 检查断言的条件是否符合预期\n- 断言常用于调试，确认后可以去掉或改成正常判断",
        },
        "en": {
            "title": "AssertionError",
            "why": "The condition in `assert` is not true.",
            "fix": "- Check whether the asserted condition is correct\n- Asserts are for debugging; replace them with real checks",
        },
    },
    "KeyboardInterrupt": {
        "zh": {
            "title": "被手动中断（KeyboardInterrupt）",
            "why": "程序在运行时被按下了 `Ctrl + C` 中断。",
            "fix": "- 重新运行即可\n- 如果代码里有循环，检查是否有合理的退出条件",
        },
        "en": {
            "title": "KeyboardInterrupt",
            "why": "The program was interrupted with `Ctrl + C`.",
            "fix": "- Just run it again\n- Make sure loops have a proper exit condition",
        },
    },
    "RuntimeError": {
        "zh": {
            "title": "运行时错误（RuntimeError）",
            "why": "代码语法没错，但运行过程中遇到了无法继续的情况。",
            "fix": "- 仔细读下面的报错信息，它通常说明了具体原因\n- 常见于字典在遍历时被修改等情况",
        },
        "en": {
            "title": "RuntimeError",
            "why": "The syntax is fine but something went wrong at run time.",
            "fix": "- Read the message below for the concrete cause\n- Often caused by mutating a dict while iterating",
        },
    },
    "BlockedModuleError": {
        "zh": {
            "title": "模块被禁用（安全限制）",
            "why": "你 import 的模块不在「允许名单」里。为了服务器安全，"
                   "本站禁止使用 `os`、`sys`、`subprocess`、`socket`、`shutil` 等能操作系统或网络的模块。",
            "fix": "- 换成允许使用的模块：`math`、`random`、`datetime`、`decimal`、`re`、`json`、"
                   "`string`、`collections`、`itertools`、`statistics` 等\n"
                   "- 如果只是想读写变量、做计算、打印结果，通常完全不需要 import 系统模块",
        },
        "en": {
            "title": "Module blocked (safety limit)",
            "why": "The imported module is not on the allow-list. For server safety, "
                   "`os`, `sys`, `subprocess`, `socket`, `shutil` and similar are not allowed.",
            "fix": "- Use an allowed module: `math`, `random`, `datetime`, `decimal`, `re`, `json`, "
                   "`string`, `collections`, `itertools`, `statistics`, ...\n"
                   "- Most beginner exercises need no system module at all",
        },
    },
    "CodeTimeoutError": {
        "zh": {
            "title": "运行超时（已强制停止）",
            "why": "代码运行超过了时间限制，被系统强制中断了。最常见的原因是写成了没有出口的死循环。",
            "fix": "- 检查 `while` 循环：循环条件最终能不能变成 False？\n"
                   "- 检查是否有漏掉的 `break`，或变量在循环里忘了更新\n"
                   "- 需要重复很多次计算时，先减小规模（比如把 1000000 改成 1000）再试",
        },
        "en": {
            "title": "Timeout (force-stopped)",
            "why": "The code ran longer than the time limit and was stopped. "
                   "The usual cause is an infinite loop.",
            "fix": "- Check every `while` loop: will its condition ever become False?\n"
                   "- Look for a missing `break`, or a variable never updated inside the loop\n"
                   "- For heavy computation, first reduce the size (e.g. 1000000 -> 1000)",
        },
    },
}

# ---------------------------------------------------------------------------
# 内部工具函数
# ---------------------------------------------------------------------------
def _fmt(template, **kwargs):
    """安全格式化：模板里缺少的占位符原样保留，不会抛异常。"""
    class _Safe(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    return template.format_map(_Safe(**kwargs))


def _extract_name(message):
    """从 NameError 的信息里取出那个未定义的名字。"""
    found = re.search(r"name '([^']+)' is not defined", message)
    return found.group(1) if found else "?"


def _user_line(exc, code):
    """定位用户代码里出错的行号与该行内容（忽略框架自身的堆栈）。"""
    line_no = getattr(exc, "lineno", None)  # SyntaxError 用 lineno
    if line_no is None:
        tb = exc.__traceback__
        while tb is not None:
            if tb.tb_frame.f_code.co_filename == "<user_code>":
                line_no = tb.tb_lineno
            tb = tb.tb_next

    snippet = None
    if line_no:
        rows = code.splitlines()
        if 0 < line_no <= len(rows):
            snippet = rows[line_no - 1].strip()
    return line_no, snippet


def _lookup(exc):
    """按异常类型的继承链查找解释；找不到返回 None。"""
    for cls in type(exc).__mro__:
        if cls.__name__ in ERRLIB:
            return ERRLIB[cls.__name__]
    return None


def _message_detail(name, message, lang):
    """根据报错信息里的具体内容，给出更精确的一句解释。"""
    zh = lang == "zh"

    def pick(cn, en):
        return cn if zh else en

    if name == "NameError":
        m = re.search(r"name '([^']+)' is not defined", message)
        if m:
            return pick("这次用到的名字是 `%s`。" % m.group(1),
                        "The undefined name is `%s`." % m.group(1))

    if name == "ZeroDivisionError":
        return pick("除数是 0，请检查 `/`（除）或 `%`（取余）右边的数字。",
                    "The divisor is 0; check the right side of `/` or `%`.")

    if name == "TypeError":
        m = re.search(r"unsupported operand type\(s\) for (.+?): '(.+?)' and '(.+?)'", message)
        if m:
            return pick("具体是 `%s` 和 `%s` 之间不能做 `%s` 运算。" % (m.group(2), m.group(3), m.group(1)),
                        "`%s` and `%s` cannot be used with `%s`." % (m.group(2), m.group(3), m.group(1)))
        if "can only concatenate str" in message:
            return pick("字符串只能和字符串相加，数字要先 `str(...)` 转成字符串。",
                        "Strings can only be concatenated with strings; use `str(...)` first.")
        m = re.search(r"'(\w+)' object is not callable", message)
        if m:
            return pick("你把一个 `%s` 类型的东西当成函数调用了（是不是多写了一对括号 `()`？）" % m.group(1),
                        "A `%s` was called as if it were a function (extra `()`?)." % m.group(1))
        m = re.search(r"'(\w+)' object is not subscriptable", message)
        if m:
            return pick("`%s` 类型不能用 `[...]` 取值。" % m.group(1),
                        "A `%s` cannot be indexed with `[...]`." % m.group(1))
        m = re.search(r"missing (\d+) required positional argument", message)
        if m:
            return pick("函数少传了 %s 个必需参数。" % m.group(1),
                        "%s required argument(s) are missing." % m.group(1))

    if name == "ValueError":
        m = re.search(r"invalid literal for int\(\) with base 10: '([^']*)'", message)
        if m:
            return pick("`int()` 只认纯数字，`%s` 不是合法的整数。" % m.group(1),
                        "`int()` failed on `%s`." % m.group(1))
        m = re.search(r"could not convert string to float: '([^']*)'", message)
        if m:
            return pick("`float()` 无法把 `%s` 转成小数。" % m.group(1),
                        "`float()` failed on `%s`." % m.group(1))
        if "too many values to unpack" in message:
            return pick("左边变量比右边要拆开的元素少，可以用 `*多余` 接住。",
                        "More values than targets; use `*rest`.")
        if "not enough values to unpack" in message:
            return pick("左边变量比右边要拆开的元素多，两边数量要一致。",
                        "Fewer values than targets; make the counts match.")

    if name == "IndexError" and "list index out of range" in message:
        return pick("列表索引超出范围了（索引从 0 开始，最大是 长度-1）。",
                    "List index out of range (indexes start at 0).")

    if name == "KeyError":
        return pick("字典里没有 `%s` 这个键。" % message.strip("'\""),
                    "No such key `%s` in the dict." % message.strip("'\""))

    if name == "AttributeError":
        m = re.search(r"'(\w+)' object has no attribute '(\w+)'", message)
        if m:
            return pick("`%s` 类型没有 `%s` 这个属性或方法。" % (m.group(1), m.group(2)),
                        "A `%s` has no attribute `%s`." % (m.group(1), m.group(2)))

    if name in ("ModuleNotFoundError", "ImportError"):
        m = re.search(r"No module named '([^']+)'", message)
        if m:
            return pick("缺少模块 `%s`，可以执行 `pip install %s` 安装。" % (m.group(1), m.group(1)),
                        "Module `%s` is missing; try `pip install %s`." % (m.group(1), m.group(1)))

    if name == "FileNotFoundError":
        m = re.search(r"No such file or directory: '([^']*)'", message)
        if m:
            return pick("找不到文件：`%s`。" % m.group(1), "File not found: `%s`." % m.group(1))

    if name == "IndentationError":
        return pick("检查报错行的缩进：同一层级的语句，前面的空格数必须完全一致。",
                    "Check the indentation of the reported line.")

    return None


_MAX_FRAMES = 12          # 原始报错里最多展示多少层调用栈


def _frame_lines(line_no, rows):
    """生成一层调用栈的展示文本。"""
    out = ['  File "<user_code>", line %d' % line_no]
    if 0 < line_no <= len(rows):
        out.append("    " + rows[line_no - 1].strip())
    return out


def build_raw_error(exc, code):
    """生成只包含用户代码部分的报错信息（去掉框架自身的堆栈噪声）。"""
    if isinstance(exc, SyntaxError):
        return "".join(traceback.format_exception_only(exc)).rstrip()

    rows = code.splitlines()
    frames = []
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == "<user_code>":
            frames.append(tb.tb_lineno)
        tb = tb.tb_next

    parts = []
    if frames:
        parts.append("Traceback (most recent call last):")
        # 递归出错时调用栈会有上千层，这里折叠，避免报错信息刷屏
        if len(frames) <= _MAX_FRAMES:
            for line_no in frames:
                parts.extend(_frame_lines(line_no, rows))
        else:
            for line_no in frames[:6]:
                parts.extend(_frame_lines(line_no, rows))
            parts.append("  ... （中间 %d 层重复调用已省略 / %d frames omitted）" % (
                len(frames) - 12, len(frames) - 12))
            for line_no in frames[-6:]:
                parts.extend(_frame_lines(line_no, rows))
    message = str(exc).strip()
    exc_line = "%s: %s" % (type(exc).__name__, message) if message else type(exc).__name__
    parts.append(exc_line)
    return "\n".join(parts)


def explain_error(exc, code, lang="zh"):
    """把异常翻译成「出错位置 + 原因 + 修改建议」的 Markdown 文本。"""
    ui = ERR_UI[lang]
    name = type(exc).__name__
    message = str(exc).strip()
    line_no, snippet = _user_line(exc, code)
    entry = _lookup(exc)

    blocks = []

    # 1) 出错位置
    if line_no:
        blocks.append("🎯 **%s：%s**" % (ui["where"], _fmt(ui["line_n"], n=line_no)))
        if snippet:
            blocks.append("%s\n\n```python\n%s\n```" % (ui["code_line"], snippet))

    # 2) 错误类型（带中文名称）
    if entry:
        heading = entry[lang]["title"]
        if name in heading:
            blocks.append("**%s：** %s" % (ui["type_label"], heading))
        else:
            blocks.append("**%s：** %s（`%s`）" % (ui["type_label"], heading, name))
    else:
        blocks.append("**%s：** `%s`" % (ui["type_label"], name))

    # 3) 为什么报错
    if entry:
        why = _fmt(entry[lang]["why"], name=_extract_name(message))
        fixes = entry[lang]["fix"]
    else:
        why = ui["generic"]
        fixes = "- " + ui["unknown"]

    detail = _message_detail(name, message, lang)
    if detail:
        why = why + "\n\n> " + detail
    blocks.append("**%s**\n\n%s" % (ui["why"], why))

    # 4) 修改建议
    blocks.append("**%s**\n\n%s" % (ui["how"], fixes))

    return "\n\n".join(blocks)


