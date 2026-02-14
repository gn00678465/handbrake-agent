"""--version flag：顯示版本資訊"""

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    try:
        return version("handbrake-agent")
    except PackageNotFoundError:
        return "unknown"


def add_to(parser):
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"handbrake-agent {get_version()}",
    )
