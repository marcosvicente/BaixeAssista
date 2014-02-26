# coding: utf-8
import threading


class Segment(object):

    def __init__(self, index=0, start=0, end=0, size=0):
        self.index = index
        self.start = start
        self.end = end
        self._size = size

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value


class Interval(object):
    def __init__(self, **params):
        """params = {}; 
        seekpos: posição inicial de leitura da stream;
        index: indice do bloco de bytes; 
        pending: lista de 'blocks' pendetes(não baixados); 
        offset: deslocamento do ponteiro de escrita à esquerda.
        maxsize: tamanho do block que será segmentado.
        min_block: tamanho mínimo(em bytes) para um bloco de bytes
        """
        assert params.get("maxsize", None), "maxsize is null"
        self.min_block = params.get("min_block", 1024 ** 2)

        self.meta = {"nbytes": {}, "sending": 0}
        self.seekpos = params.get("seekpos", 0)
        self.pending = params.get("pending", [])

        self.maxsize = params["maxsize"]
        self.maxsplit = params.get("maxsplit", 2)

        self.default_block_size = self.calc_block_size()

        self.blocks = {}
        self.locks = {}

        # caso a posição inicial leitura seja maior que zero, offset 
        # ajusta essa posição para zero. equivalente a start - offset
        self.offset = params.get("offset", self.seekpos)

    def __del__(self):
        del self.offset
        del self.seekpos
        del self.meta
        del self.blocks
        del self.pending

    def __getattr__(self, name):
        return self.meta[name]

    def can_continue(self, obj_id):
        """
        Avalia se o objeto conexão pode continuar a leitura,
        sem comprometer a montagem da stream de vídeo(ou seja, sem corromper o arquivo)
        """
        return self.has(obj_id) and self.get_end(obj_id) == self.seekpos

    def get_min_block(self):
        return self.min_block

    def get_offset(self):
        """ offset deve ser usado somente para leitura """
        return self.offset

    def get_index(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return -1 if len(items) == 0 else items[0]

    def get_start(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return -1 if len(items) == 0 else items[1]

    def get_end(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return -1 if len(items) == 0 else items[2]

    def get_block_size(self, obj_id):
        """ retorna o tamanho do bloco de bytes"""
        items = self.blocks.get(obj_id, [])
        return -1 if len(items) == 0 else items[3]

    def has(self, obj_id):
        """ avalia se o objeto tem um intervalo ligado a ele """
        return obj_id in self.blocks

    def get_first_start(self):
        """ retorna o começo(start) do primeiro intervalo da lista de blocks """
        blocks = ([item[1] for item in list(self.blocks.values())] +
                  [item[2] for item in self.pending])
        blocks.sort()
        return -1 if len(blocks) == 0 else blocks[0]

    def remove(self, obj_id):
        self.blocks.pop(obj_id, None)
        self.locks.pop(obj_id, None)

    def get_pending(self):
        return self.pending

    def set_pending(self, *args):
        """ index; nbytes; start; end; block_size """
        self.pending.append(args)

    def size_pending(self):
        return len(self.pending)

    def calc_block_size(self):
        """ calcula quantos bytes serão lidos por conexão criada """
        size = int(float(self.maxsize) / float(self.maxsplit))
        return size if size > self.min_block else self.min_block

    def update_index(self):
        """ reorganiza a tabela de indices """
        items = list(self.blocks.items())

        # organiza por start: (obj_id = 1, (0, start = 1, 2, 3))
        items.sort(key=lambda item: item[1][1])

        for index, data in enumerate(items, 1):
            # aplicando a reorganização dos indices
            self.blocks[data[0]][0] = index

    def create_lock(self, obj_id):
        """ lock usando na sincronização da divisão do intervalo desse objeto """
        self.locks[obj_id] = threading.Lock()

    def get_lock(self, obj_id):
        return self.locks[obj_id]

    def config_pending(self, obj_id):
        """ Configura uma conexão existente com um intervalo pendente(não baixado) """
        self.pending.sort()
        index, block_size, start, end, block = self.pending.pop(0)

        self.meta["nbytes"].pop(start, 0)
        start += block_size

        self.blocks[obj_id] = [index, start, end, (end - start)]
        self.meta["nbytes"][start] = 0
        self.create_lock(obj_id)

    def config_derivative(self, main_obj_id):
        """ cria um novo intervalo, apartir de um já existente """

        def get_average(index, start, end, block):
            """ retorna a média de bytes atual do intervalo """
            block_size = self.meta["nbytes"][start]
            return int(float((block - block_size)) * 0.5)

        def is_suitable(*args):
            """ verifica se o intervalo é condidato a alteração """
            return get_average(*args) > self.min_block

        items = list(self.blocks.items())
        items.sort(key=lambda item: item[1][1])

        for obj_id, data in items:
            if not is_suitable(*data):
                continue
            with self.get_lock(obj_id):
                index, start, end, block_size = self.blocks[obj_id]  # dados atualizados

                # segunda verificação, quarante que o intervalo ainda é candidato.
                if not is_suitable(index, start, end, block_size):
                    continue
                # reduzindo o tamanho do intervalo antigo
                new_end = end - get_average(index, start, end, block_size)

                # recalculando o tamanho do bloco de bytes
                new_block_size = new_end - start
                self.blocks[obj_id][-2] = new_end
                self.blocks[obj_id][-1] = new_block_size

                # criando um novo intervalo, derivado do atual
                start = new_end
                block_size = end - start

                self.blocks[main_obj_id] = [0, start, end, block_size]
                self.create_lock(main_obj_id)

                self.meta["nbytes"][start] = 0
                self.update_index()
                break

    def create_new(self, obj_id):
        """ cria um novo intervalo de divisão da stream """
        start = self.seekpos

        if start < self.maxsize:  # A origem em relação ao final
            end = start + self.default_block_size

            # verificando se final da stream já foi alcançado.
            if end > self.maxsize:
                end = self.maxsize
            differ = self.maxsize - end

            # Quando o resto da stream for muito pequeno, adiciona ao final do interv.
            if 0 < differ < self.min_block:
                end += differ
            block_size = end - start

            self.blocks[obj_id] = [0, start, end, block_size]
            self.create_lock(obj_id)

            # associando o início do intervalo ao contador
            self.meta["nbytes"][start] = 0

            self.seekpos = end
            self.update_index()