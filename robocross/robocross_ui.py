import sys
from PySide6.QtWidgets import QLineEdit


from robocross import routine
from widgets import form_widget
from widgets.generic_widget import GenericWidget
from widgets.button_bar import ButtonBar

class RoboCrossUI(GenericWidget):
    name = 'RoboCross'
    version = '1.0'
    codename = 'dragonfly'
    title = f'{name} v{version} [{codename}]'
    default_interval_time = 120
    default_rest_time = 30

    def __init__(self, parent=None):
        super(RoboCrossUI, self).__init__(title=self.title, parent=parent)
        self.button_bar: ButtonBar = self.add_widget(ButtonBar())
        self.button_bar.add_button(text="Build", clicked=self.build_button_clicked)
        self.form: form_widget.FormWidget = self.add_widget(form_widget.FormWidget())
        self.interval_line_edit: QLineEdit = self.form.add_int_field(label="Interval (seconds)", default_value=self.default_interval_time)
        self.rest_time_line_edit: QLineEdit = self.form.add_int_field(label="Rest Time (seconds)", default_value=self.default_rest_time)
        self.workout_type: QComboBox = self.form.add_combo_box(label="Workout Type", items=self.workout_types, default_index=2)
        self.workout_panel: GenericWidget = self.add_widget(GenericWidget())

    @property
    def workout_types(self) -> list[str]:
        return [
            "cardio",
            "strength",
            "cardio/strength",
            "random"
        ]

    def build_button_clicked(self):
        pass


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = RoboCrossUI()
    widget.show()
    sys.exit(app.exec())
