import sys
import sqlite3

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMessageBox


class DialogAddOrChangeCoffee(QDialog):
    """Диалоговое окно для добавления или изменения кофе"""

    def __init__(self, mode: str, degrees: list, values=()):
        super().__init__()

        self.res = None

        uic.loadUi("addEditCoffeeForm.ui", self)

        self.setWindowTitle(f'{mode} кофе')
        self.input_degree.addItems(degrees)

        self.btn.clicked.connect(self.func)
        if mode == 'Изменение':
            self.btn.setText('Изменить')

        if values:
            for value, widget in zip(values,
                                     [self.input_name, self.input_degree,
                                      self.rb1, self.input_description,
                                      self.input_price, self.input_v
                                      ]):
                if widget is self.input_degree:
                    widget.setCurrentText(value)
                elif widget is self.input_description:
                    widget.setPlainText(str(value))
                elif widget is self.rb1:
                    if value:
                        self.rb1.toggle()
                    else:
                        self.rb2.toggle()
                else:
                    widget.setText(str(value))

    def func(self):
        """Слот, срабатывает по нажатию кнопки,
        обрабатывает различные случаи ввода"""
        self.error_lbl.setText('')
        name, price = self.input_name.text(), self.input_price.text()
        is_ground_coffee = self.rb1.isChecked()
        v = self.input_v.text()
        degree = self.input_degree.currentText()
        description = self.input_description.toPlainText()
        try:
            assert name and price and v and degree and description \
                   and (self.rb1.isChecked() or self.rb2.isChecked()), \
                'Не должно быть пустых полей'
            assert float(price) > 0, 'Цена дожна быть положительной'
            assert float(v) > 0, 'Объём должен быть положительным'
            self.res = name, degree, is_ground_coffee, description, price, v
            self.close()
        except ValueError:
            self.error_lbl.setText('Некорректный формат')
        except AssertionError as ae:
            self.error_lbl.setText(str(ae))

    def get_values(self) -> tuple or None:
        """Возращает значения, введённые пользователем"""
        self.exec_()
        return self.res


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

        self.add_btn.clicked.connect(self.add_coffee)
        self.change_btn.clicked.connect(self.change_coffee)

        mode = QHeaderView.Stretch
        header = self.table.horizontalHeader()
        for i in range(1, self.table.columnCount()):
            header.setSectionResizeMode(i, mode)  # по ширине экрана

    def add_coffee(self):
        """Добавляет кофе"""
        res = DialogAddOrChangeCoffee('Добавление',
                                      [el[0] for el in self.cursor.execute(
                                          "SELECT title FROM degrees_of_roast"
                                      ).fetchall()]).get_values()
        if res is not None:
            self.cursor.execute(
                """INSERT INTO coffees 
                        VALUES(?, ?, (
                        SELECT id from degrees_of_roast
                            WHERE title = ?
                        ), ?, ?, ?, ?)""",
                (self.cursor.execute("SELECT MAX(id) FROM coffees").fetchone()[
                     0] + 1,) + res)
            self.connection.commit()
            self.load_table()

    def change_coffee(self):
        """Изменяет кофе"""
        if self.table.currentItem() is None:
            QMessageBox.critical(self, "Ошибка",
                                 "Выберите кофе, которое вы хотите изменить")
            return
        now_id = int(self.table.item(self.table.currentItem().row(), 0).text())
        values = self.cursor.execute(
            """SELECT coffees.title, degrees_of_roast.title, is_ground_coffee,
            description, price, volume
                FROM coffees, degrees_of_roast
                    ON coffees.degree_of_roast = degrees_of_roast.id
                        WHERE coffees.id = ?""",
            (now_id,)).fetchone()
        res = DialogAddOrChangeCoffee('Изменение', [el[0] for el in self.cursor.execute(
            "SELECT title FROM degrees_of_roast").fetchall()], values).get_values()
        if res is not None:
            self.cursor.execute(
                """UPDATE coffees
                        SET title = ?, degree_of_roast = (
                            SELECT id from degrees_of_roast
                                WHERE title = ?
                        ), is_ground_coffee =  ?, description =  ?, 
                        price =  ?, volume =  ?
                    WHERE id = ?""", res + (now_id,))
            self.connection.commit()
            self.load_table()

    def load_table(self):
        """Загружает таблицу из БД"""
        res = self.cursor.execute(
            """SELECT coffees.id, coffees.title, degrees_of_roast.title, is_ground_coffee,
            description, price, volume
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
