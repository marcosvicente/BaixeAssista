# coding: utf-8
import threading


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

        self.send_info = {"nbytes": {}, "sending": 0}
        self.seekpos = params.get("seekpos", 0)
        self.pending = params.get("pending", [])

        self.maxsize = params["maxsize"]
        self.maxsplit = params.get("maxsplit", 2)

        self.default_block_size = self.calcBlockSize()

        self.blocks = {}
        self.locks = {}

        # caso a posição inicial leitura seja maior que zero, offset 
        # ajusta essa posição para zero. equivalente a start - offset
        self.offset = params.get("offset", self.seekpos)

    def __del__(self):
        del self.offset
        del self.seekpos
        del self.send_info
        del self.blocks
        del self.pending

    def canContinue(self, obj_id):
        """ Avalia se o objeto conexão pode continuar a leitura, 
        sem comprometer a montagem da stream de vídeo(ou seja, sem corromper o arquivo) """
        if self.has(obj_id):
            return (self.getEnd(obj_id) == self.seekpos)
        return False

    def getMinBlock(self):
        return self.min_block

    def getOffset(self):
        """ offset deve ser usado somente para leitura """
        return self.offset

    def getIndex(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[0])

    def getStart(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[1])

    def getEnd(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[2])

    def getBlockSize(self, obj_id):
        """ retorna o tamanho do bloco de bytes"""
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[3])

    def has(self, obj_id):
        """ avalia se o objeto tem um intervalo ligado a ele """
        return obj_id in self.blocks

    def getFirstStart(self):
        """ retorna o começo(start) do primeiro intervalo da lista de blocks """
        blocks = ([item[1] for item in list(self.blocks.values())] +
                  [item[2] for item in self.pending])
        blocks.sort()
        return (-1 if len(blocks) == 0 else blocks[0])

    def remove(self, obj_id):
        self.blocks.pop(obj_id, None)
        self.locks.pop(obj_id, None)

    def getPending(self):
        return self.pending

    def setPending(self, *args):
        """ index; nbytes; start; end; block_size """
        self.pending.append(args)

    def countPending(self):
        return len(self.pending)

    def calcBlockSize(self):
        """ calcula quantos bytes serão lidos por conexão criada """
        size = int(float(self.maxsize) / float(self.maxsplit))
        return (size if size > self.min_block else self.min_block)

    def updateIndex(self):
        """ reorganiza a tabela de indices """
        items = list(self.blocks.items())

        # organiza por start: (obj_id = 1, (0, start = 1, 2, 3))
        items.sort(key=lambda item: item[1][1])

        for index, data in enumerate(items, 1):
            # aplicando a reorganização dos indices
            self.blocks[data[0]][0] = index

    def setNewLock(self, obj_id):
        """ lock usando na sincronização da divisão do intervalo desse objeto """
        self.locks[obj_id] = threading.Lock()

    def getLock(self, obj_id):
        return self.locks[obj_id]

    def configurePending(self, obj_id):
        """ Configura uma conexão existente com um intervalo pendente(não baixado) """
        self.pending.sort()
        index, blocklen, start, end, block = self.pending.pop(0)

        self.send_info["nbytes"].pop(start, 0)
        start += blocklen

        self.blocks[obj_id] = [index, start, end, (end - start)]
        self.send_info["nbytes"][start] = 0
        self.setNewLock(obj_id)

    def configureDerivate(self, other_obj_id):
        """ cria um novo intervalo, apartir de um já existente """

        def get_average(data):
            """ retorna a média de bytes atual do intervalo """
            index, start, end, block = data
            nbytes = self.send_info["nbytes"][start]
            return int(float((block - nbytes)) * 0.5)

        def is_suitable(data):
            """ verifica se o intervalo é condidato a alteração """
            return (get_average(data) > self.min_block)

        items = list(self.blocks.items())
        items.sort(key=lambda item: item[1][1])

        for obj_id, data in items:
            if not is_suitable(data): continue

            with self.getLock(obj_id):
                # se o objeto alterou seus dados quando chamou o lock
                data = self.blocks[obj_id]  # dados atualizados
                index, start, end, block_size = data

                # segunda verificação, quarante que o intervalo ainda é candidato.
                if not is_suitable(data): continue
                # reduzindo o tamanho do intervalo antigo
                new_end = end - get_average(data)

                # recalculando o tamanho do bloco de bytes
                new_block_size = new_end - start
                self.blocks[obj_id][-2] = new_end
                self.blocks[obj_id][-1] = new_block_size

                # criando um novo intervalo, derivado do atual
                start = new_end
                block_size = end - start

                self.blocks[other_obj_id] = [0, start, end, block_size]
                self.setNewLock(other_obj_id)

                self.send_info["nbytes"][start] = 0
                self.updateIndex()
                break

    def createNew(self, obj_id):
        """ cria um novo intervalo de divisão da stream """
        start = self.seekpos

        if start < self.maxsize:  # A origem em relação ao final
            end = start + self.default_block_size

            # verificando se final da stream já foi alcançado.
            if end > self.maxsize: end = self.maxsize
            difer = self.maxsize - end

            # Quando o resto da stream for muito pequeno, adiciona ao final do interv.
            if difer > 0 and difer < self.min_block: end += difer
            block_size = end - start

            self.blocks[obj_id] = [0, start, end, block_size]
            self.setNewLock(obj_id)

            # associando o início do intervalo ao contador
            self.send_info["nbytes"][start] = 0

            self.seekpos = end
            self.updateIndex()