
from imgw import ImageWidget, FullDigits, Needle, Attitude, BarWidget, StyledButton, TelemBox, MapWidget

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt, QSize, QTimer

import sys, os, numpy as np, time
from threading import Thread

from cscom import MavCom, ImageCom


os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0' 
os.environ['QT_SCALE_FACTOR'] = '1' 
os.environ['QT_FONT_DPI'] = '0'

upimg = None
IP = "192.168.0.108" 
PORT1 = 14550 
PORT2 = 14551

class BottomWidget(ImageWidget):
    def __init__(self, image_path, parent):
        super().__init__(image_path, parent)

        self.children = []

        # |||||||||||||||||||||| Images ||||||||||||||||||||||
        self.image1 = MapWidget(self, 0, 0)
        self.image1.setFactors(0.15, 0.261, 0.2156, 0.3461)
        self.children.append(self.image1)

        self.image2 = ImageWidget("test.png", self, self)
        self.image2.setFactors(0.15, 0.261, 0.7944, 0.3461)
        #self.image2.setFactors(0.3, 0.524, 0.7944, 0.3461)
        self.children.append(self.image2)

        # |||||||||||||||||||||| Sliding Numbers ||||||||||||||||||||||
        self.speednum = FullDigits(self, self.children, 0.409, 0.481, 0.013, self)
        self.altnum = FullDigits(self, self.children, 0.538, 0.4285, 0.013, self)

        # |||||||||||||||||||||| Altitude and Airspeed Indicators ||||||||||||||||||||||
        self.needle1 = Needle("needle2.png", self, self)
        self.needle1.setFactors(0.1, 0.017, 0.4299, 0.4270, -30, 0.67)
        self.needle1.setLimits(0, 2001)
        self.children.append(self.needle1)

        self.needle2 = Needle("needle1.png", self, self)
        self.needle2.setFactors(0.1, 0.017, 0.5705, 0.4270, 90)
        self.needle2.setLimits(0, 1001)
        self.children.append(self.needle2)

        # |||||||||||||||||||||| Attitude Indicator ||||||||||||||||||||||
        self.attitude_frame = ImageWidget("gyro_frame.png", self, self)
        self.attitude_frame.setFactors(0.135, 0.24, 0.5, 0.649073)
        self.children.append(self.attitude_frame)

        self.attitude_inner = Attitude("gyro.png", self, self)
        self.attitude_inner.setFactors(0.26, 0.46, 0.1153, 0.20497, 0.5, 0.649073)
        self.children.append(self.attitude_inner)

        self.attitude_bezel = ImageWidget("gyro_bezel.png", self, self)
        self.attitude_bezel.setFactors(0.184, 0.33, 0.5, 0.649073)
        self.children.append(self.attitude_bezel)
        
        self.attitude_overlay = ImageWidget("gyro_inner.png", self, self)
        self.attitude_overlay.setFactors(0.157, 0.2791, 0.5, 0.649073)
        self.children.append(self.attitude_overlay)

        # |||||||||||||||||||||| Heading Indicator ||||||||||||||||||||||
        self.compass = ImageWidget("compass.png", self, self)
        self.compass.setFactors(0.145, 0.25778, 0.5, 0.8774)
        self.children.append(self.compass)

        # |||||||||||||||||||||| Input Bars ||||||||||||||||||||||
        self.bar1 = BarWidget(self, self)
        self.bar1.setFactors(0.00903, 0.150, 0.3854, 0.879)
        self.children.append(self.bar1)

        self.bar2 = BarWidget(self, self)
        self.bar2.setFactors(0.00903, 0.150, 0.4125, 0.879)
        self.children.append(self.bar2)

        self.bar3 = BarWidget(self, self)
        self.bar3.setFactors(0.00903, 0.150, 0.5864, 0.879)
        self.children.append(self.bar3)

        self.bar4 = BarWidget(self, self)
        self.bar4.setFactors(0.00903, 0.150, 0.6135, 0.879)
        self.children.append(self.bar4)

        #self.bar1.setSlide(0.3)
        #self.bar2.setSlide(0.4)
        #self.bar3.setSlide(0.6)
        #self.bar4.setSlide(0.2)

        # |||||||||||||||||||||| Left Buttons ||||||||||||||||||||||
        self.bt11 = StyledButton(self, "FIRE", self)
        self.bt11.setFactors(0.0347, 0.0601, 0.400, 0.075)
        self.bt11.clicked.connect(lambda : com.send_button(0))
        self.children.append(self.bt11)

        self.bt12 = StyledButton(self, "DET", self)
        self.bt12.setFactors(0.0347, 0.0601, 0.400, 0.152)
        self.bt12.clicked.connect(lambda : com.send_button(4))
        self.children.append(self.bt12)

        self.bt13 = StyledButton(self, "RET", self)
        self.bt13.setFactors(0.0347, 0.0601, 0.400, 0.229)
        self.bt13.clicked.connect(lambda : com.send_button(1))
        self.children.append(self.bt13)

        # |||||||||||||||||||||| Right Buttons ||||||||||||||||||||||
        self.bt21 = StyledButton(self, "AUTO", self)
        self.bt21.setFactors(0.0347, 0.0601, 0.6111, 0.075)
        self.bt21.clicked.connect(lambda : com.send_button(2))
        self.children.append(self.bt21)

        self.bt22 = StyledButton(self, "TEST", self)
        self.bt22.setFactors(0.0347, 0.0601, 0.6111, 0.152)
        self.bt22.clicked.connect(lambda : com.send_button(3))
        self.children.append(self.bt22)

        self.bt23 = StyledButton(self, "REC", self)
        self.bt23.setFactors(0.0347, 0.0601, 0.6111, 0.229)
        self.bt23.clicked.connect(lambda : com.connect(IP, PORT1, PORT2))
        self.children.append(self.bt23)

        self.is_updating = False

        # |||||||||||||||||||||| Telemetry ||||||||||||||||||||||

        self.telem_text = """\
 Airspeed  │ {:6} m/s
 Altitude  │ {:6} m  
 Direction │ {:6}° {:1}   
───────────────────────
 Roll      │ {:6}°   
 Pitch     │ {:6}°   
 Yaw       │ {:6}°   
───────────────────────
 Battery   │ {:6}%   
 Voltage   │ {:6} V  
 Bomb Stat │ {:6}
 ───────────────────────
 Throttle  | {:6}%
"""


        self.telem = TelemBox(self, self.telem_text.format(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), self)
        self.telem.setFactors(8, 0.1156, 0.1845, 0.5055, 0.152)
        self.children.append(self.telem)

        self.startUpdater()


    # |||||||||||||||||||||| Update Children ||||||||||||||||||||||
    def resizeEvent(self, event):
        for child in self.children:
            child.updateGeometry()
        return super().resizeEvent(event)


    # |||||||||||||||||||||| Update Values ||||||||||||||||||||||
    def startUpdater(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(10)
        self.i = 0
    
    def updateValues(self):
        if self.is_updating:
            return
        self.is_updating = True

        self.needle1.num2Rot(com.airspeed)
        self.speednum.setDigits(com.airspeed)

        self.needle2.num2Rot(com.altitude)
        self.altnum.setDigits(com.altitude)

        roll = com.attitude[0] / (np.pi * 2)
        pitch = com.attitude[1] / (np.pi * 2)
        
        self.attitude_inner.setRotation(-roll)
        self.attitude_bezel.setRotation(-roll)
        self.attitude_inner.setVertical(pitch * 18)

        comprot = - (com.heading / 360)

        self.compass.setRotation(comprot)

        self.i = (self.i + 0.05)
        #self.image1.updatePosition(np.sin(self.i)/3, np.sqrt(1-np.sin(self.i))/3)

        self.image1.updatePosition(*com.gps_pos, np.deg2rad(com.heading))

        self.bar1.setSlide(com.cont_inputs[0] / 1000 - 1)
        self.bar2.setSlide(com.cont_inputs[1] / 1000 - 1)
        self.bar3.setSlide(com.cont_inputs[2] / 1000 - 1)
        self.bar4.setSlide(com.cont_inputs[3] / 1000 - 1)

        self.telem.setText(self.telem_text.format(*[format(x, ".5g") for x in (
            com.airspeed, com.altitude, com.heading, 0,
             roll*360, pitch*360, com.attitude[2] * (360 / (np.pi * 2)), com.battery_per,
              com.battery_volt,
               1, com.cont_inputs[3]/1000)]))

        self.image2.setImg(upimg)

        self.update()
        self.is_updating = False



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




def update_com():

    global com

    while True:
        try:
            com.recv_message()
        except Exception as e:
            print("ERROR AT RECV", e)
            if (com.mav_in and com.mav_out):
                com.close()
            time.sleep(1)


def update_img():

    global upimg

    while True:
        imgcom = ImageCom(5000)

        try:
            while True:
                upimg = imgcom.get_img()
                com.draw_rect(upimg)

        except:
            print("ERROR AT GSTREAMER")
            imgcom.close()
            imgcom = ImageCom(5000)




com = MavCom()

Thread(target = update_com).start()
Thread(target = update_img).start()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
