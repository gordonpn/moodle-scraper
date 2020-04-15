import argparse

from converter.converter import PDFConverter
from downloader.downloader import Downloader


def arguments_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--automated",
        action="store_true",
        help="run the moodle scraper on a schedule",
    )
    parser.add_argument(
        "-d",
        "--directory",
        action="store",
        help="specify directory to save files",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "-u",
        "--username",
        action="store",
        help="your moodle username",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "-p",
        "--password",
        action="store",
        help="your moodle password",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "-c",
        "--convert",
        action="store_true",
        help="convert to PDF using LibreOffice after downloading. this option has only been tested on Ubuntu",
    )

    return parser.parse_args()


def job():
    pass


if __name__ == "__main__":
    args: argparse.Namespace = arguments_parser()
    downloader = Downloader(args.username, args.password, args.directory)

# downloader = Downloader()
# downloader.run()
# converter = PDFConverter(downloader.course_paths_list)
# converter.run()
