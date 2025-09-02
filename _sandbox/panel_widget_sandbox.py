import sys

from widgets.generic_widget import GenericWidget
from widgets.panel_widget import PanelWidget


class PanelWidgetTest(GenericWidget):
    def __init__(self):
        super(PanelWidgetTest, self).__init__(title="Panel Widget Test")
        widget = GenericWidget(title="My Test Widget")
        widget.add_label("My test widget")
        self.panel = self.add_widget(PanelWidget(widget=widget, active=True))


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = PanelWidgetTest()
    widget.show()
    app.exec()
