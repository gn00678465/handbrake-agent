"""--prompt / -p flag：使用者自訂的額外 AI 提示詞"""


def add_to(parser):
    parser.add_argument("--prompt", "-p", metavar="TEXT", help="使用者自訂的額外提示詞，會附加在 AI 分析 prompt 後面")
