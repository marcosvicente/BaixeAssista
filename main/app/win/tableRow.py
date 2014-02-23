# coding: utf-8
from PySide import QtCore, QtGui


class BarWidget(QtGui.QWidget):
    """ Cria uma representação o de barra de progresso """
    start_coord = 2.0

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.pen = QtGui.QPen()
        self.pen.setColor(QtCore.Qt.darkGreen)

        linearGradient = QtGui.QLinearGradient(0, 0, 100, 100)
        linearGradient.setColorAt(0.01, QtCore.Qt.white)
        linearGradient.setColorAt(1.0, QtCore.Qt.green)

        self.brush = QtGui.QBrush(linearGradient)
        self.setBackgroundRole(QtGui.QPalette.Base)

        self.percent = 0.0

    @property
    def max_width(self):
        return float(self.width() - self.start_coord)

    @property
    def max_height(self):
        return float(self.height() - (self.start_coord * 2.0))

    @property
    def now(self):
        return (self.max_width / 100.0) * self.percent

    @property
    def endpos(self):
        """ calcula a posicão final da barra de progresso """
        if self.now < self.max_width:
            width = self.max_width - self.now
        else:
            width = self.now - self.max_width
        return width

    def setPercent(self, value):
        """ move a barra de progresso proprorcional a porcentagem dada """
        self.percent = value
        self.update()

    def setText(self, text):
        """ configura a procentagem no formato de texto """
        self.setPercent(float(text if text else 0.0))

    def paintEvent(self, event):
        """ constrói a represtação da barra de progresso """
        painter = QtGui.QPainter()

        painter.begin(self)
        painter.setPen(self.pen)
        painter.setBrush(self.brush)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.save()

        painter.drawRect(QtCore.QRectF(self.start_coord, self.start_coord, self.now, self.max_height))

        painter.setBrush(QtGui.QColor(0, 0, 0, 25))
        painter.drawRect(QtCore.QRectF(self.now, self.start_coord, self.endpos, self.max_height))

        painter.drawText(QtCore.QRectF(self.start_coord, self.start_coord, self.max_width, self.max_height),
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
        table.setRowCount(self.index + 1)

    def create(self, wCol=-1):
        """ Cria os items da tabela.
            wCol: informa a coluna da barra de progresso.
        """
        for index in range(self.table.columnCount()):
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
                self.items[index].setText(str(value))
        else:
            self.items[col].setText(str(value))

    def setupBarWidgetAt(self, col, row):
        """ configura a barra de progresso nas coordenada """
        barWidget = BarWidget(self.table)
        self.table.setCellWidget(col, row, barWidget)
        return barWidget

    @property
    def index(self):
        return self._index

    def clear(self):
        self.table.setRowCount(self.table.rowCount() - 1)
        self.table.removeRow(self.index)
        TableRow.ROW_INDEX -= 1


## --------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)

    win = QtGui.QWidget()
    boxLayout = QtGui.QVBoxLayout()
    win.setLayout(boxLayout)

    table = QtGui.QTableWidget()
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(["progress", "widget"])

    row = TableRow(table)
    row.create(wCol=1)

    row.update(col=0, value="text")
    row.update(col=1, value="80.2")

    boxLayout.addWidget(table)

    win.show()

    sys.exit(app.exec_())
    
    
    
    
    
    