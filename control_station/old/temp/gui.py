from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt, QSize, QTimer
import sys, os, numpy as np

from imgw import ImageWidget, FullDigits, Needle, Attitude, BarWidget, StyledButton


os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0' 
os.environ['QT_SCALE_FACTOR'] = '1' 
os.environ['QT_FONT_DPI'] = '0'




class BottomWidget(ImageWidget):
    def __init__(self, image_path, parent):
        super().__init__(image_path, parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image1 = ImageWidget("test2.jpg", self)
        self.image1.setFactors(0.15, 0.261, 0.2156, 0.3461)

        self.image2 = ImageWidget("test.png", self)
        self.image2.setFactors(0.15, 0.261, 0.7944, 0.3461)

        self.needle1 = Needle("needle2.png", self)
        self.needle1.setFactors(0.1, 0.017, 0.4299, 0.4270, -30, 0.67)
        self.needle1.setLimits(0, 2001)

        self.needle2 = Needle("needle1.png", self)
        self.needle2.setFactors(0.1, 0.017, 0.5705, 0.4270, 90)
        self.needle2.setLimits(0, 1001)

        self.attitude_frame = ImageWidget("gyro_frame.png", self)
        self.attitude_frame.setFactors(0.135, 0.24, 0.5, 0.649073)

        self.attitude_inner = Attitude("gyro.png", self)
        self.attitude_inner.setFactors(0.26, 0.46, 0.1153, 0.20497, 0.5, 0.649073)

        self.attitude_bezel = ImageWidget("gyro_bezel.png", self)
        self.attitude_bezel.setFactors(0.184, 0.33, 0.5, 0.649073)
        
        self.attitude_overlay = ImageWidget("gyro_inner.png", self)
        self.attitude_overlay.setFactors(0.157, 0.2791, 0.5, 0.649073)

        self.compass = ImageWidget("compass.png", self)
        self.compass.setFactors(0.145, 0.25778, 0.5, 0.8774)

        self.speednum = FullDigits(self, layout, 0.409, 0.481, 0.013)
        self.altnum = FullDigits(self, layout, 0.538, 0.4285, 0.013)

        self.bar1 = BarWidget(self)
        self.bar1.setFactors(0.00903, 0.150, 0.3854, 0.879)

        self.bar2 = BarWidget(self)
        self.bar2.setFactors(0.00903, 0.150, 0.4125, 0.879)

        self.bar3 = BarWidget(self)
        self.bar3.setFactors(0.00903, 0.150, 0.5864, 0.879)

        self.bar4 = BarWidget(self)
        self.bar4.setFactors(0.00903, 0.150, 0.6135, 0.879)

        self.test = StyledButton(self, "test")
        self.test.setFactors(0.0347, 0.0601, 0.6135, 0.879)

        #self.compass.setRotation(65)

        layout.addWidget(self.needle1)
        layout.addWidget(self.needle2)
        layout.addWidget(self.compass)

        layout.addWidget(self.image1)
        layout.addWidget(self.image2)

        layout.addWidget(self.attitude_frame)
        layout.addWidget(self.attitude_inner)
        layout.addWidget(self.attitude_bezel)
        layout.addWidget(self.attitude_overlay)
        
        layout.addWidget(self.bar1)
        layout.addWidget(self.bar2)
        layout.addWidget(self.bar3)
        layout.addWidget(self.bar4)

        layout.addWidget(self.test)

        self.setLayout(layout)
        self.startUpdater()

    def startUpdater(self):
        self.i = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateValues)
        #self.timer.start(30)
    
    def updateValues(self):
        self.i = (self.i + 0.03) % 1000
        self.needle1.num2Rot(self.i * 2)
        self.speednum.setDigits(self.i * 2)
        self.needle2.num2Rot(self.i)
        self.altnum.setDigits(self.i)
        self.attitude_inner.setRotation(np.sin(self.i + np.sin(self.i * 3))/20)
        self.attitude_bezel.setRotation(np.sin(self.i + np.sin(self.i * 3))/20)
        #print(np.sin(self.i)/7*360)
        self.attitude_inner.setVertical((np.sin(self.i * 1.5) + np.sin(self.i * 0.9)) / 2)
        #self.attitude_inner.setRotation(self.i/10)
        self.compass.setRotation(np.sin(self.i)/5)

        self.bar1.setSlide(abs(np.sin(self.i)))
        self.bar2.setSlide(abs(np.cos(self.i)))
        self.bar3.setSlide(abs(np.sin(self.i)))
        self.bar4.setSlide(abs(np.cos(self.i)))
        
        self.update()

    #def mouseMoveEvent(self, event: QMouseEvent):

    #    self.attitude_inner.setRotation(event.position().x()*2 / 2880)
    #    self.attitude_bezel.setRotation(event.position().x()*2 / 2880)

    #    self.attitude_inner.setVertical((event.position().y()*2 / 1664)-1)

    #    self.needle1.num2Rot(event.position().y())
    #    self.speednum.setDigits(event.position().y())

    #    self.needle2.num2Rot(event.position().x()*4)
    #    self.altnum.setDigits(event.position().x()*4)

    #    self.compass.setRotation(event.position().x()*2 / 2880)
    #    self.update()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ground Control Station")
        self.resize(1995, 1167)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QLabel("test")
        top_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout()

        self.bottom_widget = BottomWidget("bg1.png", bottom_container)
        self.bottom_widget.setFactors(1, 1, 0.5, 0.5)

        bottom_layout.addWidget(self.bottom_widget)
        bottom_container.setLayout(bottom_layout)


        main_layout.addWidget(top_bar)
        main_layout.addWidget(bottom_container, stretch=1)

        self.setLayout(main_layout)
        self.showMaximized()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
