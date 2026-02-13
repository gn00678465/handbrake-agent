"""--model flag：指定 Copilot SDK 使用的 AI 模型"""

DEFAULT_MODEL = "gpt5-mini"


def add_to(parser, default: str = DEFAULT_MODEL):
    parser.add_argument(
        "--model", default=default, metavar="MODEL", help=f"指定 Copilot SDK 使用的 AI 模型（預設：{default}）"
    )
