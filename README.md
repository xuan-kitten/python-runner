# 🐍 Python 代码在线运行器

一个用 [Streamlit](https://streamlit.io) 搭建的、面向初学者的 **Python 在线练习网站**。

## ✨ 功能

- 🐈‍⬛ 黄瞳小黑猫 + 浅绿色清新主题
- 🌏 中文 / English 一键切换（界面 + 课程内容一起切）
- 📚 左侧「Python 小课堂」：图文讲解 `print` 与「变量」
- ▶️ 右侧在线写代码，点一下即可运行，结果显示在下方
- 🤖 **报错自动中文解读**：错误类型、出错位置、为什么会错、可以怎么改
- 🛡️ **安全护栏**：超时限制 + 模块白名单 + 输出上限

## 🚀 本地运行

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

浏览器会自动打开 <http://localhost:8501>。

## 📁 文件说明

| 文件 | 说明 |
| --- | --- |
| `streamlit_app.py` | 主程序（界面 + 逻辑） |
| `error_explainer.py` | 把 Python 报错翻译成「中文原因 + 修改建议」 |
| `code_sandbox.py` | 安全护栏：超时 / 模块白名单 / 输出上限 |
| `requirements.txt` | 依赖清单 |
| `.streamlit/config.toml` | 主题配色（浅绿色） |

## 🛡️ 安全说明

用户提交的代码运行在受限环境中：

| 护栏 | 效果 |
| --- | --- |
| 超时 5 秒 | 死循环会被强制停止 |
| 模块白名单 | 仅允许 `math`、`random`、`datetime`、`re`、`json` 等；`os`、`sys`、`subprocess` 等被拒绝 |
| 危险内置函数已移除 | `open`、`eval`、`exec`、`compile`、`input` 不可用 |
| 输出上限 | 最多保留 2 万字符 |

> ⚠️ 这是**防呆护栏**，不是完整的安全沙箱。
> 请部署在**云端隔离容器**中运行（例如 Streamlit Community Cloud），
> 不要把本应用直接暴露在自有机器的公网上。
