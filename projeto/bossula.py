import sys
from math import sin, cos, radians
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QPointF

class CompassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0  # Ângulo em graus para o ponteiro da bússola
    
    def setAngle(self, angle: float):
        """Atualiza o ângulo do ponteiro da bússola (0-360)."""
        # Normaliza o ângulo dentro de 0° e 360°
        self._angle = angle % 360
        self.update()  # Redesenha o widget
    
    def angle(self) -> float:
        """Retorna o ângulo atual."""
        return self._angle

    def paintEvent(self, event):
        """Responsável por desenhar a bússola."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dimensões do widget
        width = self.width()
        height = self.height()
        center = QPointF(width / 2, height / 2)
        
        # Define o raio da bússola com base no tamanho do widget
        radius = min(width, height) / 2 - 10  # Margem interna

        # Desenha o círculo externo da bússola
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(QColor("#ffffff")))  # Fundo branco
        painter.drawEllipse(center, radius, radius)

        # Desenha marcações principais (N, S, L, O)
        font_point_size = int(radius * 0.1)
        directions = [("N", 0), ("L", 90), ("S", 180), ("O", 270)]
        for text, dir_angle in directions:
            # Converte o ângulo para radianos e posiciona o texto
            rad = radians(dir_angle)
            x = center.x() + (radius * 0.7) * sin(rad)
            y = center.y() - (radius * 0.7) * cos(rad)
            painter.drawText(x - font_point_size, y + font_point_size, text)

        # Desenha o ponteiro (vermelho) no ângulo atual
        painter.setPen(QPen(Qt.red, 3))
        rad_angle = radians(self._angle)
        pointer_length = radius * 0.8
        px = center.x() + pointer_length * sin(rad_angle)
        py = center.y() - pointer_length * cos(rad_angle)
        painter.drawLine(center, QPointF(px, py))

        # Desenha a cauda do ponteiro (opcional, azul)
        painter.setPen(QPen(Qt.blue, 3))
        back_px = center.x() - pointer_length * sin(rad_angle)
        back_py = center.y() + pointer_length * cos(rad_angle)
        painter.drawLine(center, QPointF(back_px, back_py))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Exemplo de Bússola PySide6 com Slider")

        self.compass = CompassWidget()
        self.compass.setMinimumSize(200, 200)

        # Cria o slider para controlar o ângulo
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 359)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.updateCompassAngle)

        layout = QVBoxLayout()
        layout.addWidget(self.compass)
        layout.addWidget(self.slider)
        self.setLayout(layout)

    def updateCompassAngle(self, value):
        """Atualiza o ângulo da bússola com base no valor do slider."""
        self.compass.setAngle(value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
