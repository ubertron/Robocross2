from PySide6.QtWidgets import QFormLayout, QWidget, QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox


class FormWidget(QWidget):
    def __init__(self, title: str = ""):
        super().__init__()
        self.setWindowTitle(title)
        self.setLayout(QFormLayout())

    @property
    def data(self) -> dict[str, any]:
        data = {}
        for i in range(self.count):
            idx = i * 2
            label = self.layout().itemAt(idx).widget().text()
            widget = self.layout().itemAt(idx + 1).widget()
            if type(widget) is QLineEdit:
                _value = widget.text()
            elif type(widget) is QComboBox:
                _value = widget.currentText()
            elif type(widget) in (QSpinBox, QDoubleSpinBox):
                _value = widget.value()
            else:
                _value = None
            data[label] = _value
        return data

    @property
    def labels(self) -> list[str]:
        return list(self.data.keys())

    @property
    def count(self) -> int:
        """Number of rows."""
        return int(self.layout().count() / 2)

    def add_line_edit(self, label: str, default_value: str = "", placeholder_text: str = "") -> QLineEdit:
        """Add a line edit to the form."""
        line_edit = QLineEdit(text=default_value, placeholderText=placeholder_text)
        return self.add_row(label=label, widget=line_edit)

    def add_int_field(self, label: str, default_value: int = 0) -> QSpinBox:
        """Add an integer field."""
        spin_box = QSpinBox()
        spin_box.setMinimum(0)
        spin_box.setMaximum(999)
        spin_box.setValue(default_value)
        return self.add_row(label=label, widget=spin_box)

    def add_float_field(self, label: str, default_value: int = 0) -> QDoubleSpinBox:
        """Add an integer field."""
        spin_box = QDoubleSpinBox()
        spin_box.setValue(default_value)
        return self.add_row(label=label, widget=spin_box)

    def add_combo_box(self, label: str, items: list[str], default_index: int = 0) -> QComboBox:
        """Add a combo box to the form."""
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setCurrentIndex(default_index)
        return self.add_row(label=label, widget=combo_box)

    def add_row(self, label: str, widget: QWidget) -> any:
        """Add a widget to the form."""
        assert label not in self.labels, f"Label already used: {label}"
        self.layout().addRow(label, widget)
        return widget

    def get_value(self, label: str) -> str | int | float:
        """Get the value of a field."""
        return self.data.get(label)

    def get_widget_by_label(self, label: str) -> QWidget | None:
        if label in self.labels:
            idx = next(i for i in range(self.count) if self.layout().itemAt(i * 2).widget().text() == label)
            return self.layout().itemAt(idx * 2 + 1).widget()
        return None

    def set_value(self, label: str, value: any):
        """Set the value of a field."""
        widget = self.get_widget_by_label(label=label)
        assert widget is not None, f"Field not found: {label}"
        if type(widget) is QLineEdit:
            widget.setText(str(value))
        elif type(widget) is QComboBox:
            items = [widget.itemText(i) for i in range(widget.count())]
            if value in items:
                widget.setCurrentText(value)
        elif type(widget) is QSpinBox:
            widget.setValue(int(value))
        elif type(widget) is QDoubleSpinBox:
            widget.setValue(float(value))


class ExampleFormWidget(FormWidget):
    def __init__(self):
        super().__init__(title="Example Form Widget")
        self.animal = self.add_line_edit(label="Animal", default_value="cat", placeholder_text="Choose an animal")
        self.color = self.add_combo_box(label="Color", items=["black", "blue", "red"], default_index=1)
        self.count_field = self.add_int_field(label="Count", default_value=10)
        self.height = self.add_float_field(label="Height", default_value=0.8)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    example_form_widget = ExampleFormWidget()
    example_form_widget.show()
    for key, value in example_form_widget.data.items():
        print(f"{key}: {value}")
    print(example_form_widget.get_value("Color"))
    example_form_widget.set_value(label="Animal", value="fox")
    example_form_widget.set_value(label="Color", value="red")
    example_form_widget.set_value(label="Count", value=5)
    example_form_widget.set_value(label="Height", value=3.2)
    app.exec()
