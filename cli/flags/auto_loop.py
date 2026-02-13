"""--auto-loop flag：自動迭代模式設定"""


def add_to(parser, run_mode: bool = False):
    """
    Args:
        run_mode: True 時為 run 子命令（固定整數，預設 2）；
                  False 時為一般模式（可選值，不帶數字預設 3）
    """
    if run_mode:
        parser.add_argument("--auto-loop", type=int, default=2, metavar="N", help="Preview 迭代次數（預設 2）")
    else:
        parser.add_argument(
            "--auto-loop",
            nargs="?",
            const=3,
            type=int,
            metavar="N",
            help=("自動連續執行 preview + vmaf 迭代。不帶數字時預設執行 3 次；--auto-loop 2 最多執行 2 次。"),
        )
