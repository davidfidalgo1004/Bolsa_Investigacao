from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class SensorAlertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alerta de Risco de Incêndio")
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        alert_label = QLabel("Alerta: Um sensor detectou risco de incêndio!\n(Verifique temperatura e qualidade do ar)")
        layout.addWidget(alert_label)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button)
