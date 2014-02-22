# coding: utf-8
import time


class Streamer(object):
    """ lê e retorna a stream de dados """

    def __init__(self, manage, blocksize=524288):
        self.seekpos = self.sended = 0
        self.blocksize = blocksize
        self.manage = manage
        self._stop = False

    def stop(self):
        self._stop = True

    def __iter__(self):
        self.manage.add_streamer(self)

        if self.manage.getInitPos() > 0:
            yield self.manage.videoManager.get_header()

        while not self._stop and self.sended < self.manage.getVideoSize():
            if self.seekpos < self.manage.cacheBytesCount:
                blocklen = self.blocksize

                if (self.seekpos + blocklen) > self.manage.cacheBytesCount:
                    blocklen = self.manage.cacheBytesCount - self.seekpos

                stream, self.seekpos = self.manage.fileManager.read(self.seekpos, blocklen)
                self.sended += blocklen
                yield stream
            time.sleep(0.001)
        print(("Exiting: ", self))
        raise StopIteration

    def __del__(self):
        self.stop()
        del self.manage