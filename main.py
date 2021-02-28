import sys
import sqlite3

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.connection = sqlite3.connect("coffee.sqlite")
        self.cursor = self.connection.cursor()

        self.headers = ['ID', 'название сорта', 'степень обжарки',
                        'молотый/в зернах',
                        'описание вкуса', 'цена', 'объем упаковки']

        uic.loadUi("main.ui", self)

        self.setGeometry(200, 200, 1200, 600)
        self.setMinimumSize(600, 400)

        self.load_table()

        mode = QHeaderView.Stretch
        header = self.table.horizontalHeader()
        for i in range(1, self.table.columnCount()):
            header.setSectionResizeMode(i, mode)  # по ширине экрана

    def load_table(self):
        """Загружает таблицу из БД"""
        res = self.cursor.execute(
            """SELECT coffees.id, coffees.title, degrees_of_roast.title, is_ground_coffee,
            coffees.description, coffees.price, coffees.volume
                FROM coffees, degrees_of_roast
                    ON coffees.degree_of_roast = degrees_of_roast.id""").fetchall()
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        if res:
            self.table.setRowCount(len(res))
            for i, row in enumerate(res):
                for j, elem in enumerate(row):
                    if j == 3:
                        elem = 'молотый' if elem else 'в зёрнах'
                    item = QTableWidgetItem(str(elem))
                    # нельзя редактировать, только для чтения
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.table.setItem(i, j, item)
        self.table.resizeRowsToContents()

    def resizeEvent(self, event):
        self.table.resizeRowsToContents()

    def closeEvent(self, event):
        self.connection.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec())
