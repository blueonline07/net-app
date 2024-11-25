from client import Downloader
from threading import Thread

if __name__ == '__main__':
    downloader1 = Downloader('downloads.torrent')
    thread1 = Thread(target=downloader1.start)
    downloader2 = Downloader('downloads.torrent')
    thread2 = Thread(target=downloader2.start)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
    print("Finished")
