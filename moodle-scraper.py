from converter.converter import PDFConverter
from downloader.downloader import Downloader

if __name__ == '__main__':
    downloader = Downloader()
    downloader.run()
    converter = PDFConverter(downloader.course_paths_list)
    converter.run()
