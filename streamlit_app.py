"""一个带可爱样式的 Streamlit 网页应用。

功能：
1. 浅绿色背景 + 可爱卡通形象
2. 左侧菜单：Python 小课堂（讲解 print 和变量）
3. 中英文切换单选按钮
4. 输入 Python 代码的文本框
5. “运行代码”按钮，运行后展示结果
6. 代码报错时，右侧自动显示「中文报错原因 + 修改建议」
7. 安全护栏：超时限制 + 模块白名单 + 输出上限（适合公开部署）

运行方式：
    .\\.venv\\Scripts\\python -m streamlit run streamlit_app.py
"""

import base64
import os
import sys

import streamlit as st

# 让「报错解读」和「安全沙箱」模块总能被找到
# （Streamlit 会把脚本目录加入 sys.path，这里再兜底一次）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_sandbox import DEFAULT_TIMEOUT, run_user_code  # noqa: E402
from error_explainer import ERR_UI, build_raw_error, explain_error  # noqa: E402

# ---------------------------------------------------------------------------
# 可爱卡通形象：黄瞳小黑猫（内联 SVG，base64 内嵌，不依赖网络，离线也能显示）
# 如果你更喜欢用开源图片 URL，可以把 CUTE_IMG 换成，例如：
#   CUTE_IMG = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f408.svg"
# （Twemoji 采用 CC-BY 4.0 开源协议）
# ---------------------------------------------------------------------------
CUTE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 184">
  <ellipse cx="100" cy="172" rx="52" ry="9" fill="#00000012"/>
  <!-- 耳朵（外黑 + 内粉） -->
  <path d="M48 64 L36 16 L84 44 Z" fill="#25252e" stroke="#4d4d61" stroke-width="4" stroke-linejoin="round"/>
  <path d="M152 64 L164 16 L116 44 Z" fill="#25252e" stroke="#4d4d61" stroke-width="4" stroke-linejoin="round"/>
  <path d="M53 55 L45 28 L73 45 Z" fill="#f5a3b7"/>
  <path d="M147 55 L155 28 L127 45 Z" fill="#f5a3b7"/>
  <!-- 头（黑色） -->
  <circle cx="100" cy="102" r="62" fill="#25252e" stroke="#4d4d61" stroke-width="4"/>
  <!-- 黄色猫眼 -->
  <ellipse cx="77" cy="96" rx="14" ry="13" fill="#ffd21e"/>
  <ellipse cx="123" cy="96" rx="14" ry="13" fill="#ffd21e"/>
  <!-- 竖瞳 -->
  <ellipse cx="77" cy="96" rx="4.2" ry="10" fill="#141420"/>
  <ellipse cx="123" cy="96" rx="4.2" ry="10" fill="#141420"/>
  <!-- 眼神高光 -->
  <circle cx="71.5" cy="89" r="3.4" fill="#ffffff" opacity="0.95"/>
  <circle cx="117.5" cy="89" r="3.4" fill="#ffffff" opacity="0.95"/>
  <!-- 鼻子 + 嘴巴 -->
  <path d="M94 115 L106 115 L100 122 Z" fill="#f5a3b7"/>
  <path d="M100 122 v5 M100 127 q-8 7 -14 0 M100 127 q8 7 14 0" fill="none"
        stroke="#f5a3b7" stroke-width="3" stroke-linecap="round"/>
  <!-- 腮红 -->
  <ellipse cx="58" cy="120" rx="9" ry="5.5" fill="#ff8fa8" opacity="0.4"/>
  <ellipse cx="142" cy="120" rx="9" ry="5.5" fill="#ff8fa8" opacity="0.4"/>
  <!-- 胡须（浅灰，黑脸上看得见） -->
  <path d="M38 106 h-16 M38 118 h-16 M162 106 h16 M162 118 h16" stroke="#cbcdda" stroke-width="3" stroke-linecap="round"/>
</svg>"""

CUTE_IMG = "data:image/svg+xml;base64," + base64.b64encode(
    CUTE_SVG.encode("utf-8")
).decode("ascii")

# ---------------------------------------------------------------------------
# 多语言界面文案
# ---------------------------------------------------------------------------
UI = {
    "zh": {
        "lang_label": "🌏 请选择语言 / Language",
        "sidebar_title": "🐍 Python 小课堂",
        "lesson_label": "想学点什么？",
        "lesson_print": "print 是什么？",
        "lesson_var": "变量是什么？",
        "try_it": "👉 动手试一试：把上面的代码复制到右边的输入框里运行吧！",
        "title": "Python 代码在线运行器",
        "subtitle": "在这里写代码，点一下就能看到结果～",
        "code_label": "在这里输入 Python 代码：",
        "run_button": "▶️ 运行代码",
        "result_title": "🎉 运行结果",
        "stdout_title": "标准输出 (stdout)：",
        "error_title": "😵 发生错误：",
        "empty_code": "请先输入要运行的代码哦～",
        "no_output": "（代码执行完成，但没有产生任何输出）",
        "output_truncated": "（输出内容过长，已截断显示）",
        "warning": "⚠️ 代码会在本机进程中执行，请只运行你自己信任的代码。",
        "default_code": (
            "# 在这里写你的 Python 代码，点击“运行代码”查看结果\n"
            "print('你好，Streamlit！🐍')\n"
            "a = 10\n"
            "b = 20\n"
            "print('a + b =', a + b)\n"
        ),
    },
    "en": {
        "lang_label": "🌏 请选择语言 / Language",
        "sidebar_title": "🐍 Python Class",
        "lesson_label": "What do you want to learn?",
        "lesson_print": "What is print?",
        "lesson_var": "What is a variable?",
        "try_it": "👉 Try it: copy the code above into the editor on the right and run it!",
        "title": "Python Code Online Runner",
        "subtitle": "Write code here and see the result in one click~",
        "code_label": "Enter your Python code here:",
        "run_button": "▶️ Run Code",
        "result_title": "🎉 Result",
        "stdout_title": "Standard output (stdout):",
        "error_title": "😵 Error occurred:",
        "empty_code": "Please enter some code first~",
        "no_output": "(Execution finished with no output)",
        "output_truncated": "(Output was too long and has been truncated)",
        "warning": "⚠️ The code runs in a local process. Only run code you trust.",
        "default_code": (
            "# Write your Python code here, then click Run Code\n"
            "print('Hello, Streamlit! 🐍')\n"
            "a = 10\n"
            "b = 20\n"
            "print('a + b =', a + b)\n"
        ),
    },
}

# ---------------------------------------------------------------------------
# 左侧菜单「Python 小课堂」的讲解内容
# ---------------------------------------------------------------------------
DOC = {
    "print": {
        "zh": """**`print()` 是 Python 的「打印」函数。**

它的作用很简单：**把括号里的内容显示到屏幕上**。

```python
print("你好，世界！")     # 输出一段文字
print(1 + 1)             # 也可以直接算数
print("答案是", 42)       # 用逗号可以一次打印多个内容
```

**小提示：**
- 文字要用引号包起来，例如 `"你好"` 或 `'你好'`。
- 逗号隔开的内容，打印时会自动加一个空格。
- 数字不用加引号。
- 每次 `print()` 都会换到新的一行。
""",
        "en": """**`print()` is Python's "print" function.**

It simply **shows what is inside the parentheses on the screen**.

```python
print("Hello, world!")   # print some text
print(1 + 1)             # it can calculate too
print("answer is", 42)   # commas let you print several things
```

**Tips:**
- Text must be wrapped in quotes, e.g. `"hello"` or `'hello'`.
- Items separated by commas are printed with a space in between.
- Numbers need no quotes.
- Every `print()` starts a new line.
""",
    },
    "var": {
        "zh": """**变量就像一个「贴了标签的盒子」**，用来存放数据。

```python
name = "小明"    # 把 "小明" 放进名为 name 的盒子
age = 12         # 把 12 放进名为 age 的盒子

print(name)
print(age)
print(name, "今年", age, "岁")
```

**小提示：**
- `=` 不是「等于」，而是**赋值**：把右边的值交给左边的名字。
- 变量名建议用英文字母开头，不要用中文、空格或以数字开头。
- 可以给同一个变量重新赋值，旧的值会被覆盖。
- 变量的值可以参与计算，例如 `age + 1`。
""",
        "en": """**A variable is like a labelled box** that stores data.

```python
name = "Tom"     # put "Tom" into a box named name
age = 12         # put 12 into a box named age

print(name)
print(age)
print(name, "is", age, "years old")
```

**Tips:**
- `=` is not "equals" but **assignment**: give the right value to the name on the left.
- Variable names should start with a letter; no spaces, no leading digits.
- You can assign a new value to the same variable; the old value is replaced.
- A variable's value can be used in calculations, e.g. `age + 1`.
""",
    },
}

# ---------------------------------------------------------------------------
# 页面配置 + 自定义样式（浅绿色背景、卡通卡片、浮动动画）
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Python Runner", page_icon="🐍", layout="centered")

st.markdown(
    """
    <style>
    /* 浅绿色渐变背景 */
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(160deg, #eafbf0 0%, #d5f4e1 55%, #c7efd8 100%);
    }
    [data-testid="stHeader"] { background: transparent; }

    /* 侧边栏浅绿色 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #dcf7e8 0%, #c6efd9 100%);
        border-right: 2px dashed #8fdcae;
    }

    /* 顶部可爱卡片 */
    .hero {
        display: flex; align-items: center; gap: 20px;
        background: rgba(255, 255, 255, 0.75);
        border: 2px dashed #8fdcae;
        border-radius: 24px;
        padding: 18px 24px;
        margin-bottom: 14px;
        box-shadow: 0 6px 20px rgba(34, 164, 99, 0.14);
    }
    .hero img { width: 132px; height: auto; }
    .hero .bounce { display: inline-block; animation: floaty 2.4s ease-in-out infinite; }
    .hero h1 { margin: 0; font-size: 30px; color: #157a46; }
    .hero p { margin: 6px 0 0; color: #2f6b4c; font-size: 15px; }

    @keyframes floaty {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-9px); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 左侧菜单：语言切换 + Python 小课堂
# ---------------------------------------------------------------------------
with st.sidebar:
    lang_choice = st.radio(
        UI["zh"]["lang_label"],
        options=["中文", "English"],
        horizontal=True,
        label_visibility="collapsed",
    )
    lang = "zh" if lang_choice == "中文" else "en"
    t = UI[lang]

    st.markdown("### " + t["sidebar_title"])
    st.image(CUTE_IMG, width=110)
    st.markdown("---")

    lesson = st.radio(
        t["lesson_label"],
        options=[t["lesson_print"], t["lesson_var"]],
    )
    lesson_key = "print" if lesson == t["lesson_print"] else "var"
    st.markdown(DOC[lesson_key][lang])
    st.info(t["try_it"])

    st.markdown("---")
    st.caption("Made with Streamlit 🐍🌿")

# ---------------------------------------------------------------------------
# 主区域：大标题（含卡通形象）+ 代码输入 + 运行
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <span class="bounce"><img src="{CUTE_IMG}" alt="cute cat"></span>
        <div>
            <h1>{t["title"]}</h1>
            <p>{t["subtitle"]}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(t["warning"])

code = st.text_area(
    t["code_label"],
    value=t["default_code"],
    height=260,
    key=f"code_{lang}",
)

if st.button(t["run_button"], type="primary"):
    if not code.strip():
        st.warning(t["empty_code"])
    else:
        st.subheader(t["result_title"])
        # 在受限环境（超时 + 模块白名单 + 输出上限）中运行用户代码
        output, error, _, truncated = run_user_code(code, timeout=DEFAULT_TIMEOUT)

        # 即使中途报错，也把「报错之前已经 print 出来」的内容展示出来
        if output:
            st.text(t["stdout_title"])
            st.code(output, language="text")
        if truncated:
            st.caption(t["output_truncated"])

        if error is None:
            if not output:
                st.info(t["no_output"])
        else:
            st.error("%s %s" % (t["error_title"], type(error).__name__))
            # 左：原始报错信息    右：报错原因解读（中文 / 英文随语言切换）
            col_raw, col_hint = st.columns([1, 1], gap="medium")
            with col_raw:
                st.markdown("#### " + ERR_UI[lang]["raw_title"])
                st.code(build_raw_error(error, code), language="text")
            with col_hint:
                st.markdown("#### " + ERR_UI[lang]["hint_title"])
                with st.container(border=True):
                    st.markdown(explain_error(error, code, lang))

