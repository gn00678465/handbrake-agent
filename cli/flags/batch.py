"""--batch flag：批次處理資料夾中所有影片"""


def add_to(parser):
    parser.add_argument("--batch", action="store_true", help="批次處理模式")
