"""--vmaf-feedback flag：提供上次轉碼的 vmaf.json 供 AI 參考"""


def add_to(parser):
    parser.add_argument(
        "--vmaf-feedback", metavar="VMAF_JSON", help="提供上次轉碼的 vmaf.json 路徑，讓 AI 依品質指標調整參數建議"
    )
