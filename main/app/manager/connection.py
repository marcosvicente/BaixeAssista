# coding: utf-8
from main.app.generators import Universal

class Connection(object):
    """ controla todas as conexões criadas """
    #----------------------------------------------------------------------
    def __init__(self, manage):
        self.manage = manage
        # controla a transferência do arquivo de vídeo.
        self.streamManager = Universal.getStreamManager(manage.getVideoUrl())
        # guarda as conexoes criadas
        self.connlist = []
        
    def __del__(self):
        del self.manage
        del self.streamManager
        del self.connlist
        
    def update(self, **params):
        """ atualiza os parametros de configuração das conexões ativas """
        for conn in self.connlist:
            if conn.wasStopped(): continue
            for key, value in params.items():
                conn[key] = value
            
    def start(self, noProxy=False, numOfConn=0, **params):
        return [self.startNew(noProxy, **params).ident for i in range(numOfConn)]
    
    def startWithProxy(self, numOfConn=0, **params):
        return self.start(False, numOfConn, **params)
    
    def startWithoutProxy(self, numOfConn=0, **params):
        return self.start(True, numOfConn, **params)
    
    def stop(self, numOfConn=0):
        """ pára groupos de conexões dado por 'numOfConn' """
        connlist = []
        for x in range(0, abs(numOfConn)):
            for y in range(len(self.connlist)-1, -1, -1):
                conn = self.connlist[y]
                # desconsidera conexões inativas
                if conn.wasStopped(): continue
                
                connlist.append(conn.ident)
                conn.stop(); break
        # remove todas as conexões paradas
        self.removeStopped()
        return connlist
        
    def startNew(self, noProxy=False, **params):
        """ inicia uma nova conexão """
        conn = self.streamManager(self.manage, noProxy, **params)
        conn.start(); self.add(conn)
        return conn

    def add(self, refer):
        """ adiciona a referência para uma nova conexão criada """
        self.connlist.append(refer)
        
    def countActive(self):
        """ retorna o número de conexões criadas e ativas """
        return len([conn for conn in self.connlist if not conn.wasStopped()])
        
    def count(self):
        """ retorna o número de conexões criadas"""
        return len(self.connlist)
    
    def removeStopped(self):
        """ remove as conexões que estiverem completamente paradas """
        self.connlist = [conn for conn in self.connlist if conn.isAlive()]
        
    def stopAll(self):
        """ pára todas as conexões atualmente ativas """
        for conn in self.connlist: conn.stop()
        
    def getByIDs(self, idlist=[]):
        """ retorna apenas as conexões que tenham o id na lista """
        return [conn for conn in self.connlist if conn.ident in idlist]
    
    def getById(self, ident):
        connlist = self.getByIDs([ident])
        return None if len(connlist) == 0 else connlist[0]
    
    def getConnList(self):
        """ retorna a lista com todas as conexões criadas """
        return self.connlist
    