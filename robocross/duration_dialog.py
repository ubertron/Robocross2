"""Modal dialog for selecting duration with hours, minutes, and seconds."""

from PySide6.QtWidgets import QDialog, QFormLayout, QSpinBox, QDialogButtonBox


class DurationDialog(QDialog):
    """Modal dialog for selecting duration."""

    def __init__(self, initial_seconds: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Duration")
        self.setup_ui(initial_seconds)

    def setup_ui(self, initial_seconds: int):
        """Create form layout with hour/minute/second spinners."""
        # Create form layout
        layout = QFormLayout(self)

        # Hour spinner (0-23)
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setSuffix(" hr")
        layout.addRow("Hours:", self.hour_spin)

        # Minute spinner (0-59)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setSuffix(" min")
        layout.addRow("Minutes:", self.minute_spin)

        # Second spinner (0-59)
        self.second_spin = QSpinBox()
        self.second_spin.setRange(0, 59)
        self.second_spin.setSuffix(" sec")
        layout.addRow("Seconds:", self.second_spin)

        # Set initial values from seconds
        self.set_from_seconds(initial_seconds)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def set_from_seconds(self, seconds: int):
        """Convert total seconds to hours/minutes/seconds and set spinners."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.hour_spin.setValue(hours)
        self.minute_spin.setValue(minutes)
        self.second_spin.setValue(seconds)

    def get_total_seconds(self) -> int:
        """Get total seconds from spinner values."""
        return (self.hour_spin.value() * 3600 +
                self.minute_spin.value() * 60 +
                self.second_spin.value())

    @staticmethod
    def get_duration(parent, initial_seconds: int) -> tuple[int, bool]:
        """
        Convenience static method to get duration from user.

        Returns:
            tuple[int, bool]: (total_seconds, ok_pressed)
        """
        dialog = DurationDialog(initial_seconds, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_total_seconds(), True
        return initial_seconds, False


if __name__ == '__main__':
    # Test the dialog
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test with 90 seconds (1 minute 30 seconds)
    seconds, ok = DurationDialog.get_duration(None, 90)
    if ok:
        print(f"Duration selected: {seconds} seconds")
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        print(f"  = {hours} hours, {minutes} minutes, {secs} seconds")
    else:
        print("Dialog cancelled")

    sys.exit(0)
