"""--params-file flag：載入先前儲存的 params.json，略過 AI 分析"""


def add_to(parser):
    parser.add_argument(
        "--params-file", metavar="PARAMS_JSON", help="載入先前儲存的 params.json，略過 AI 分析直接使用指定參數"
    )
