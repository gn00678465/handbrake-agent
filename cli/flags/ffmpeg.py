"""--ffmpeg flag：使用 FFmpeg 而非 HandBrake"""


def add_to(parser):
    parser.add_argument("--ffmpeg", action="store_true", help="使用 FFmpeg 而非 HandBrake")
