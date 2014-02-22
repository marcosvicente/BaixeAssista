# coding: utf-8
import time


class Streamer(object):
    """ lê e retorna a stream de dados """

    def __init__(self, manage, blocksize=524288):
        self.seek_pos = self.sent = 0
        self.block_size = blocksize
        self.manage = manage
        self._stop = False

    def stop(self):
        self._stop = True

    def __iter__(self):
        self.manage.add_streamer(self)

        if self.manage.get_init_pos() > 0:
            yield self.manage.video_manager.get_header()

        while not self._stop and self.sent < self.manage.get_video_size():
            if self.seek_pos < self.manage.cache_bytes_counter:
                block_len = self.block_size

                if (self.seek_pos + block_len) > self.manage.cache_bytes_counter:
                    block_len = self.manage.cache_bytes_counter - self.seek_pos

                stream, self.seek_pos = self.manage.file_manager.read(self.seek_pos, block_len)
                self.sent += block_len
                yield stream
            time.sleep(0.001)
        print(("Exiting: ", self))
        raise StopIteration

    def __del__(self):
        self.stop()
        del self.manage