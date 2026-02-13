"""--no-verify flag：停用品質驗證步驟"""


def add_to(parser):
    parser.add_argument("--no-verify", action="store_true", help="停用品質驗證")
