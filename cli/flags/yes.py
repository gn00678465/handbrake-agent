"""--yes / -y flag：自動確認執行轉碼，略過互動式確認"""


def add_to(parser):
    parser.add_argument("--yes", "-y", action="store_true", help="自動確認執行轉碼，不需要手動輸入 y/n")
