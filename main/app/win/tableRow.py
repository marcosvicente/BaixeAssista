# coding: utf-8
from PySide import QtCore, QtGui

## --------------------------------------------------------------------------
class BarWidget(QtGui.QWidget):
    """ Cria uma representação o de barra de progresso """
    offset = 2.0
    
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.pen = QtGui.QPen()
        
        linearGradient = QtGui.QLinearGradient(0, 0, 100, 100)
        linearGradient.setColorAt(0.01, QtCore.Qt.white)
        linearGradient.setColorAt(1.0, QtCore.Qt.green)
        
        self.brush = QtGui.QBrush( linearGradient )
        self.setBackgroundRole(QtGui.QPalette.Base)
        
        self.percent = 0.0
        
    @property
    def mWidth(self):
        return float(self.width() - self.offset)
    
    @property
    def now(self):
        return (self.mWidth/100.0) * self.percent
    
    @property
    def mHeight(self):
        return float(self.height() - (self.offset*2.0))
    
    @property
    def endpos(self):
        """ calcula a posicão final da barra de progresso """
        if self.now < self.mWidth:
            width = self.mWidth - self.now
        else:
            width = self.now - self.mWidth
        return width
    
    def setPercent(self, value):
        """ move a barra de progresso proprorcional a porcentagem dada """
        self.percent = value
        self.update()
        
    def setText(self, text):
        """ configura a procentagem no formato de texto """
        self.setPercent(float(text))
        
    def paintEvent(self, event):
        """ constrói a represtação da barra de progresso """
        painter = QtGui.QPainter()
        
        painter.begin(self)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.save()
        
        painter.drawRect(QtCore.QRectF(self.offset, self.offset, self.now, self.mHeight))
        
        painter.setBrush(QtGui.QColor(0, 0, 0, 25))
        painter.drawRect(QtCore.QRectF(self.now, self.offset, self.endpos, self.mHeight))
        
        painter.drawText(QtCore.QRectF(self.offset, self.offset, self.endpos, self.mHeight), 
                         QtCore.Qt.AlignCenter, "%.2f%%" % self.percent)
        
        painter.restore()
        painter.end()
        
## --------------------------------------------------------------------------
class TableRow(object):
    ROW_INDEX = 0
    
    def __init__(self, table):
        self._index = TableRow.ROW_INDEX
        self.table = table
        self.items = []
        
        # criando uma 'row' na tabela
        table.setRowCount(self.index+1)
        
    def create(self, wCol=-1):
        """ Cria os items da tabela.
            wCol: informa a coluna da barra de progresso.
        """
        for index in range( self.table.columnCount() ):
            if wCol != index:
                item = QtGui.QTableWidgetItem()
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(TableRow.ROW_INDEX, index, item)
            else:
                # cria uma barra de progresso na coordena.
                item = self.setupBarWidgetAt(TableRow.ROW_INDEX, index)
            self.items.append(item)
        # indice para uma nova TableRow.
        TableRow.ROW_INDEX += 1
        
    def update(self, col=None, value='', values=()):
        """ atualiza o texto de todas as colunas, ou apenas uma coluna individual """
        if col is None:
            for index, value in enumerate(values):
                self.items[index].setText(unicode(value))
        else:
            self.items[col].setText(unicode(value))
    
    def setupBarWidgetAt(self, col, row):
        """ configura a barra de progresso nas coordenada """
        barWidget = BarWidget( self.table )
        self.table.setCellWidget(col, row, barWidget)
        return barWidget
    
    @property
    def index(self):
        return self._index
    
    def clear(self):
        self.table.setRowCount(self.table.rowCount()-1)
        self.table.removeRow(self.index)
        TableRow.ROW_INDEX -= 1
        
        
## --------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    app = QtGui.QApplication(sys.argv)
    
    win = QtGui.QWidget()
    boxLayout = QtGui.QVBoxLayout()
    win.setLayout( boxLayout )
    
    table = QtGui.QTableWidget()
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(["progress", "widget"])
    
    row = TableRow( table)
    row.create(wCol=1)
    
    row.update(col=0, value="text")
    row.update(col=1, value="4.2")
    
    boxLayout.addWidget( table )
    
    win.show()

    sys.exit(app.exec_())
    
    
    
    
    
    