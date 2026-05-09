"""--config flag：載入 YAML 設定檔（含批次 inputs 與共用設定）"""


def add_to(parser):
    parser.add_argument(
        "--config",
        metavar="CONFIG_YAML",
        help="載入 YAML 設定檔，可指定共用 flag 設定與 inputs 批次清單；CLI flag 仍會覆寫檔案值",
    )
