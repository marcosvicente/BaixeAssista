from PySide import QtCore, QtGui

## --------------------------------------------------------------------------
class TableRow(object):
    ROW_INDEX = 0
    
    def __init__(self, table):
        self._index = TableRow.ROW_INDEX
        self.table = table
        self.items = []
        
        # criando uma 'row' na tabela
        table.setRowCount(self.index+1)
        
    def create(self):
        for index in range( self.table.columnCount() ):
            item = QtGui.QTableWidgetItem("Item Row: %d, Col: %d"%(TableRow.ROW_INDEX, index))
            self.table.setItem(TableRow.ROW_INDEX, index, item)
            self.items.append(item)
            
        # indice para uma nova TableRow.
        TableRow.ROW_INDEX += 1
        
    def update(self, col=None, value='', values=()):
        """ atualiza o texto de todas as colunas, ou apenas uma coluna individual """
        if col is None:
            for index, value in enumerate(values):
                self.items[index].setText(str(value))
        else:
            self.items[col].setText(str(value))
            
    @property
    def index(self):
        return self._index
    
    def clear(self):
        self.table.setRowCount(self.table.rowCount()-1)
        self.table.removeRow(self.index)
        TableRow.ROW_INDEX -= 1