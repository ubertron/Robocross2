import enum
import platform

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QSpacerItem, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from typing import Callable, Optional
from shiboken6 import wrapInstance

DARWIN_STR = 'Darwin'


class GridWidget(QWidget):
    def __init__(self, title: str = '', margin: int = 4, spacing: int = 2):
        super(GridWidget, self).__init__()
        self.setWindowTitle(title)
        layout: QGridLayout = QGridLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)

    @property
    def row_count(self) -> int:
        return self.layout().rowCount()

    @property
    def first_row_empty(self) -> bool:
        """
        The initial grid has one empty row. Check this first so you can populate it.
        :return:
        """
        for i in range(self.column_count):
            item = self.layout().itemAtPosition(0, i)

            if item and item.widget is not None:
                return False

        return True

    @property
    def column_count(self) -> int:
        return self.layout().columnCount()

    def add_widget(self, widget: QWidget, row: int, column: int, row_span: int = 1, col_span: int = 1,
                   replace: bool = False) -> QWidget:
        """
        Adds a widget to the layout
        :param widget:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param replace:
        :return:
        """
        if replace:
            self.delete_widget(row=row, column=column)

        self.layout().addWidget(widget, row, column, row_span, col_span)

        return widget

    def add_label(self, text: str, row: int, column: int, row_span: int = 1, col_span: int = 1,
                  alignment: enum = Qt.AlignmentFlag.AlignCenter, replace: bool = False,
                  style: Optional[str] = None, nice: bool = False) -> QLabel:
        """
        Adds a label to the layout
        :param text:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param alignment:
        :param replace:
        :param style:
        :param nice:
        :return:
        """
        label = QLabel(text.replace('_', ' ') if nice else text)
        label.setAlignment(alignment)

        if style:
            label.setStyleSheet(style)

        result = self.add_widget(widget=label, row=row, column=column, row_span=row_span, col_span=col_span,
                                 replace=replace)

        return result

    def set_text(self, row: int, column: int, text: str, style: Optional[str] = None, nice: bool = False):
        """
        Set the text of an existing widget
        :param row:
        :param column:
        :param text:
        :param style:
        :param nice:
        """
        item = self.layout().itemAtPosition(row, column)

        if item:
            widget: QWidget = item.widget()

            if type(widget) in (QLabel, QPushButton):
                if nice:
                    text = text.replace('_', ' ')

                widget.setText(text)

                if style:
                    widget.setStyleSheet(style)

    def add_button(self, label: str, row: int, column: int, row_span: int = 1, col_span: int = 1,
                   tool_tip: Optional[str] = None, clicked: Optional[Callable] = None, replace: bool = False):
        """
        Add button to the layout
        :param label:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param tool_tip:
        :param clicked:
        :param replace: object
        :return:
        """
        button = QPushButton(label)
        button.setToolTip(tool_tip)
        if clicked:
            button.clicked.connect(clicked)

        return self.add_widget(widget=button, row=row, column=column, row_span=row_span, col_span=col_span,
                               replace=replace)

    def get_row_by_text(self, text: str, column: int = 0) -> int or None:
        """
        Gets the index of the row whose widget has the value 'text'
        Works for QLabels and QPushButtons
        :param text:
        :param column:
        :return:
        """
        values = self.get_column_values(column=column)

        if text in values:
            return values.index(text)
        else:
            return None

    def get_column_values(self, column: int) -> list:
        values = []
        for i in range(self.row_count):
            item = self.layout().itemAtPosition(i, column)
            values.append(item.widget().text() if item else None)

        return values

    def delete_widget(self, row: int, column: int):
        """
        Removes a widget from a location if it exists
        :param row:
        :param column:
        """
        assert row < self.row_count, 'Invalid row id'
        assert column < self.column_count, 'Invalid column id'
        item = self.layout().itemAtPosition(row, column)

        if item is not None:
            widget = item.widget()
            self.layout().removeWidget(widget)
            widget.deleteLater()

    def delete_row(self, row: int):
        """
        Delete an entire row
        :param row:
        """
        assert row < self.row_count, 'Invalid row id'

        for i in range(self.column_count):
            self.delete_widget(row=row, column=i)

    def clear_layout(self):
        """
        Remove all widgets and spacer items from the current layout
        """
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)

            if isinstance(item, QSpacerItem):
                self.layout().takeAt(i)
            else:
                item.widget().setParent(None)


class GridWidgetTest(GridWidget):
    def __init__(self):
        super(GridWidgetTest, self).__init__(title='Test Grid Widget')
        self.init_buttons()

    def init_buttons(self):
        self.label1 = self.add_label('1', row=0, column=0)
        self.label1.setStyleSheet('background-color: green')
        self.label2 = self.add_label('2', row=0, column=1, row_span=2)
        self.label2.setStyleSheet('background-color: red')
        button3: QPushButton = self.add_button('3', row=1, column=0)
        self.add_button('4', row=2, column=0, col_span=2, tool_tip='set the text!', clicked=self.button4_clicked)
        self.add_label('Remove me', row=3, column=0)
        self.add_label('Remove me', row=3, column=1)
        self.delete_widget(row=3, column=0)
        self.add_label('Replacement', row=3, column=1, replace=True)
        self.resize(320, 240)
        button3.clicked.connect(self.button3_clicked)

    def button3_clicked(self):
        self.label1.setText('Button 3 clicked')

    def button4_clicked(self):
        self.label2.setText('Button 4 clicked')


class StackedWidget(GridWidget):
    def __init__(self):
        super(StackedWidget, self).__init__("Stacked Widget")
        background = self.add_label('', row=0, column=0)
        background.setStyleSheet('background-color: rgb(128, 0, 128)')
        text = self.add_label('BLUE TURTLE', row=0, column=0)
        text.setStyleSheet('color: rgb(255, 255, 0)')


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    test_widget = StackedWidget()
    test_widget.show()
    app.exec()
