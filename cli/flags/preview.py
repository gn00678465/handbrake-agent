"""--preview / --preview-duration flags：預覽模式設定"""


def add_to(parser, include_toggle: bool = True):
    """
    Args:
        include_toggle: True 時加入 --preview 開關（run 子命令不需要，固定使用 preview）
    """
    if include_toggle:
        parser.add_argument(
            "--preview",
            action="store_true",
            help="預覽模式：只轉換影片開頭部分（vmaf json 與 params 僅在此模式下保留）",
        )

    parser.add_argument(
        "--preview-duration", type=int, default=30, metavar="SECONDS", help="預覽模式的時長（秒，預設 30 秒）"
    )
