"""--vmaf flag：啟用 VMAF 品質驗證，可選擇性指定取樣間隔"""


def add_to(parser, run_mode: bool = False):
    """
    Args:
        run_mode: True 時為 run 子命令模式（說明文字略有不同）
    """
    if run_mode:
        help_text = "VMAF 取樣間隔（不帶數字=1 逐幀精確；--vmaf 5 每 5 幀取樣，加速 ~5x，誤差 ±1-2 分）"
    else:
        help_text = "啟用 VMAF 品質驗證。不帶數字=N=1（逐幀精確）；--vmaf 5 表示每 5 幀取樣，加速 ~5x，誤差 ±1-2 分。"

    parser.add_argument("--vmaf", nargs="?", const=1, type=int, default=None, metavar="N", help=help_text)
