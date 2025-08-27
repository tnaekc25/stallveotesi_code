from imgw import (
    ImageWidget, FullDigits, Needle, Attitude, BarWidget,
    StyledButton, StyledButton2, TelemBox, MapWidget,
    PotentiometerWidget, TapeIndicator
)

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer

import sys
import os
import numpy as np
import time
from threading import Thread

from cscom import MavCom, ImageCom


os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0' 

upimg = None
IP = "192.168.0.101" 
PORT1 = 14550 
PORT2 = 14551

class BottomWidget(ImageWidget):
    def __init__(self, image_path, parent):
        super().__init__(image_path, parent)

        self.children = []
        self.prev_vals = {
            "altitude" : 0,
            "airspeed" : 0,
            "ground_speed" : 0,
            "vertical_speed" : 0,
            "direction": 0,
            "roll": 0,
            "pitch": 0,
            "cont_inputs_0" : 0,
            "cont_inputs_1" : 0,
            "cont_inputs_2" : 0,
            "cont_inputs_3" : 0,
            "img_id" : 0,
            "gps_pos": (0, 0)
        }

        # |||||||||||||||||||||| Images ||||||||||||||||||||||

        self.image_comp = ImageWidget("src/test.png", self, self)
        self.image_comp.setFactors(0.15, 0.261, 0.7944, 0.3461)
        self.children.append(self.image_comp)

        self.connected_img = ImageWidget("src/connected.png", self, self)
        self.connected_img.setFactors(0.03897, 0.0673, 0.7118, 0.072)
        self.children.append(self.connected_img)

        self.detection_on = ImageWidget("src/connected.png", self, self)
        self.detection_on.setFactors(0.03897, 0.0673, 0.7493, 0.072)
        self.children.append(self.detection_on)


        # |||||||||||||||||||||| GPS ||||||||||||||||||||||

        self.gps_comp = MapWidget(self, 0, 0)
        self.gps_comp.setFactors(0.15, 0.261, 0.2156, 0.3461)
        self.children.append(self.gps_comp)

        self.rot1 = PotentiometerWidget("src/dial.png", self, 0.01, 0.001, 0.0005, self)
        self.rot1.setFactors(0.03125, 0.054, 0.310764, 0.51)
        self.children.append(self.rot1)

        self.rot2 = PotentiometerWidget("src/dial.png", self, 0.01, 0.001, 0.0005, self)
        self.rot2.setFactors(0.03125, 0.054, 0.310764, 0.186)
        self.children.append(self.rot2)

        self.rot3 = PotentiometerWidget("src/dial.png", self, 2, 1, 0.003, self)
        self.rot3.setFactors(0.03125, 0.054, 0.1215, 0.186)
        self.children.append(self.rot3)

        self.rot4 = PotentiometerWidget("src/dial.png", self, 2, 1, 0.003, self)
        self.rot4.setFactors(0.03125, 0.054, 0.1215, 0.51)
        self.children.append(self.rot4)

        # |||||||||||||||||||||| Sliding Numbers ||||||||||||||||||||||
        self.speednum = FullDigits(self, self.children, 0.409, 0.481, 0.013, self)
        self.altnum = FullDigits(self, self.children, 0.538, 0.4285, 0.013, self)

        # |||||||||||||||||||||| Altitude and Airspeed Indicators ||||||||||||||||||||||
        self.needle1 = Needle("src/needle2.png", self, self)
        self.needle1.setFactors(0.1, 0.017, 0.4299, 0.4270, -30, 0.67)
        self.needle1.setLimits(0, 2001)
        self.children.append(self.needle1)

        self.needle2 = Needle("src/needle1.png", self, self)
        self.needle2.setFactors(0.1, 0.017, 0.5705, 0.4270, 90)
        self.needle2.setLimits(0, 1001)
        self.children.append(self.needle2)

        # |||||||||||||||||||||| Attitude Indicator ||||||||||||||||||||||
        self.attitude_frame = ImageWidget("src/gyro_frame.png", self, self)
        self.attitude_frame.setFactors(0.135, 0.24, 0.5, 0.649073)
        self.children.append(self.attitude_frame)

        self.attitude_inner = Attitude("src/gyro.png", self, self)
        self.attitude_inner.setFactors(0.26, 0.46, 0.1153, 0.20497, 0.5, 0.649073)
        self.children.append(self.attitude_inner)

        self.attitude_bezel = ImageWidget("src/gyro_bezel.png", self, self)
        self.attitude_bezel.setFactors(0.184, 0.33, 0.5, 0.649073)
        self.children.append(self.attitude_bezel)
        
        self.attitude_overlay = ImageWidget("src/gyro_inner.png", self, self)
        self.attitude_overlay.setFactors(0.157, 0.2791, 0.5, 0.649073)
        self.children.append(self.attitude_overlay)

        # |||||||||||||||||||||| Tapes ||||||||||||||||||||||
        self.vertical_tape = TapeIndicator(self, self)
        self.vertical_tape.setFactors(0.033, 0.175, 0.398, 0.65)
        self.children.append(self.vertical_tape)

        self.ground_tape = TapeIndicator(self, self)
        self.ground_tape.setFactors(0.033, 0.175, 0.6, 0.65)
        self.children.append(self.ground_tape)

        # |||||||||||||||||||||| Heading Indicator ||||||||||||||||||||||
        self.compass = ImageWidget("src/compass.png", self, self)
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

        # |||||||||||||||||||||| Left Buttons ||||||||||||||||||||||
        self.bt11 = StyledButton(self, "FIRE1", self)
        self.bt11.setFactors(0.0347, 0.0601, 0.400, 0.075)
        self.bt11.clicked.connect(lambda : com.send_button(0))
        self.children.append(self.bt11)

        self.bt12 = StyledButton(self, "ARM", self)
        self.bt12.setFactors(0.0347, 0.0601, 0.400, 0.152)
        self.bt12.clicked.connect(lambda : com.send_button(1))
        self.children.append(self.bt12)

        self.bt13 = StyledButton(self, "DET", self)
        self.bt13.setFactors(0.0347, 0.0601, 0.400, 0.229)
        self.bt13.clicked.connect(lambda : com.send_button(2))
        self.children.append(self.bt13)

        # |||||||||||||||||||||| Right Buttons ||||||||||||||||||||||
        self.bt21 = StyledButton(self, "FIRE2", self)
        self.bt21.setFactors(0.0347, 0.0601, 0.6111, 0.075)
        self.bt21.clicked.connect(lambda : com.send_button(3))
        self.children.append(self.bt21)

        self.bt22 = StyledButton(self, "CONT", self)
        self.bt22.setFactors(0.0347, 0.0601, 0.6111, 0.152)
        self.bt22.clicked.connect(lambda : com.send_button(4))
        self.children.append(self.bt22)

        self.bt23 = StyledButton(self, "NET", self)
        self.bt23.setFactors(0.0347, 0.0601, 0.6111, 0.229)
        self.bt23.clicked.connect(lambda : com.send_button(5))
        self.children.append(self.bt23)

        self.bt24 = StyledButton2(self, "MAV", self)
        self.bt24.setFactors(0.026, 0.045, 0.3, 0.075)
        self.bt24.clicked.connect(lambda : (com.close(), com.connect(IP, PORT1, PORT2)))
        self.children.append(self.bt24)

        self.bt25 = StyledButton2(self, "GST", self)
        self.bt25.setFactors(0.026, 0.045, 0.26, 0.075)
        self.bt25.clicked.connect(lambda : Thread(target = restart_gst).start())
        self.children.append(self.bt25)

        self.bt26 = StyledButton2(self, "GPS", self)
        self.bt26.setFactors(0.026, 0.045, 0.22, 0.075)
        self.bt26.clicked.connect(lambda : self.gps_comp.setPos(*com.gps_pos))
        self.children.append(self.bt26)

        # |||||||||||||||||||||| Telemetry ||||||||||||||||||||||

        self.telem_text = """\
 Airspeed  │ {:6} m/s
 Altitude  │ {:6} m  
 Direction │ {:6}° {:1}   
───────────────────────
 Attitude (RPY):
 {:6}° {:6}° {:6}°    
───────────────────────
 Armed / Control / Payld:
 {:4} / {:7} / {:6} 
 ───────────────────────
 Battery   │ {:3}% {:4}V  
 ───────────────────────
 Throttle  | {:6}%
"""

        self.telem = TelemBox(self, self.telem_text.format(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), self)
        self.telem.setFactors(8, 0.12, 0.19, 0.5055, 0.152)
        self.children.append(self.telem)

        self.startUpdater()


    # |||||||||||||||||||||| Update Children ||||||||||||||||||||||
    def resizeEvent(self, event):
        self.updateGeometry()
        self.updateLayer()

        for child in self.children:
            child.updateGeometry()
            child.updateLayer()

        return super().resizeEvent(event)

    # |||||||||||||||||||||| Update Values ||||||||||||||||||||||
    def startUpdater(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(10)
    
    def updateValues(self):
        self.changed_widgets = []
    
        if com.connected and self.connected_img.name != "src/connected.png":
            self.connected_img.setImgbyName("src/connected.png")
            self.connected_img.repaint()
        elif not com.connected and self.connected_img.name != "src/not_connected.png":
            self.connected_img.setImgbyName("src/not_connected.png")
            self.connected_img.repaint()

        if com.is_det and self.detection_on.name != "src/connected.png":
            self.detection_on.setImgbyName("src/connected.png")
            self.detection_on.repaint()
        elif not com.is_det and self.detection_on.name != "src/not_connected.png":
            self.detection_on.setImgbyName("src/not_connected.png")
            self.detection_on.repaint()

    
        if abs(com.airspeed - self.prev_vals["airspeed"]) > 0.1:
            self.needle1.num2Rot(com.airspeed*100)
            self.speednum.setDigits(com.airspeed)
            self.prev_vals["airspeed"] = com.airspeed
    
        if abs(com.altitude - self.prev_vals["altitude"]) > 0.1:
            self.needle2.num2Rot(com.altitude*100)
            self.altnum.setDigits(com.altitude)
            self.prev_vals["altitude"] = com.altitude
        
        roll = com.attitude[0] / (np.pi * 2)
        pitch = com.attitude[1] / (np.pi * 2)

        if (abs(com.attitude[0] - self.prev_vals["roll"]) > 0.05 or 
        abs(com.attitude[1] - self.prev_vals["pitch"]) > 0.05):
            self.attitude_inner.setRotation(-roll)
            self.attitude_bezel.setRotation(-roll)
            self.attitude_inner.setVertical(pitch * 18)

            self.prev_vals["roll"] = com.attitude[0]
            self.prev_vals["pitch"] = com.attitude[1]
            
            self.attitude_inner.repaint()

        


        repaintGps = False

        comprot = - (com.heading / 360)
        if abs(com.heading - self.prev_vals["direction"]) > 0.1:
            self.compass.setRotation(comprot)
            self.gps_comp.updateHeading(np.deg2rad(com.heading))
            self.prev_vals["direction"] = com.heading

            self.compass.repaint()
            repaintGps = True
    
        if (abs(com.gps_pos[0] - self.prev_vals["gps_pos"][0]) > 0.0001 or
            abs(com.gps_pos[1] - self.prev_vals["gps_pos"][1]) > 0.0001):
            self.gps_comp.updatePosition(*com.gps_pos)
            self.prev_vals["gps_pos"] = com.gps_pos
            
            repaintGps = True

        if self.rot1.changed:
            self.gps_comp.setRangeLA(self.rot1.counter)
            self.rot1.changed = False
            self.rot1.repaint()
            repaintGps = True
    
        if self.rot2.changed:
            self.gps_comp.setRangeLO(self.rot2.counter)
            self.rot2.changed = False
            self.rot2.repaint()
            repaintGps = True
    
        if self.rot3.changed:
            self.gps_comp.setGridRefLA(self.rot3.counter)
            self.rot3.changed = False
            self.rot3.repaint()
    
        if self.rot4.changed:
            self.gps_comp.setGridRefLO(self.rot4.counter)
            self.rot4.changed = False
            self.rot4.repaint()
            repaintGps = True

        if (repaintGps):
            self.gps_comp.repaint()
    

        if abs(com.vertical_speed - self.prev_vals["vertical_speed"]) > 0.1:
            self.vertical_tape.setNumber(com.vertical_speed)
            self.prev_vals["vertical_speed"] = com.vertical_speed
            self.vertical_tape.repaint()
    
        if abs(com.ground_speed - self.prev_vals["ground_speed"]) > 0.1:
            self.ground_tape.setNumber(com.ground_speed)
            self.prev_vals["ground_speed"] = com.ground_speed
            self.ground_tape.repaint()
    
        if abs(com.cont_inputs[0] - self.prev_vals["cont_inputs_0"]) > 0.01:
            self.bar1.setSlide(com.cont_inputs[0])
            self.prev_vals["cont_inputs_0"] = com.cont_inputs[0]
        
        if abs(com.cont_inputs[1] - self.prev_vals["cont_inputs_1"]) > 0.01:
            self.bar2.setSlide(com.cont_inputs[1])
            self.prev_vals["cont_inputs_1"] = com.cont_inputs[1]
    
        if abs(com.cont_inputs[2] - self.prev_vals["cont_inputs_2"]) > 0.01:
            self.bar3.setSlide(com.cont_inputs[2])
            self.prev_vals["cont_inputs_2"] = com.cont_inputs[2]
    
        if abs(com.cont_inputs[3] - self.prev_vals["cont_inputs_3"]) > 0.01:
            self.bar4.setSlide(com.cont_inputs[3])
            self.prev_vals["cont_inputs_3"] = com.cont_inputs[3]

        self.telem.setText(self.telem_text.format(*[format(x, ".4g") if type(x) != str else x for x in (
            com.airspeed, com.altitude, com.heading, 0,
            roll*360, pitch*360, com.attitude[2] * (360 / (np.pi * 2)),
            "YES" if com.is_armed else "NO", "MANUAL" if com.control_mode else "AUTO",
            f"{'Y' if com.left_stat else 'N'} - {'Y' if com.right_stat else 'N'}",
            com.battery_per, com.battery_volt, com.cont_inputs[0])]))

        self.telem.repaint()
        
        if (id(upimg) != self.prev_vals["img_id"]):
            self.image_comp.setImg(upimg)
            self.prev_vals["img_id"] = id(upimg)
            self.image_comp.repaint()



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ground Control Station")
        self.resize(1995, 1167)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QLabel("Stall ve Ötesi Control Station")
        top_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout()

        self.bottom_widget = BottomWidget("src/bg1.png", bottom_container)
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
            if (com.mav_in and com.mav_out):
                com.recv_message()
                #com.read_test()
            else:
                time.sleep(1)
        except Exception as e:
            print("ERROR AT MAVLINK", e)
            time.sleep(1)

def check_com():

    global com

    while True:
        try:
            if (com.mav_in and com.mav_out):
                com.check_connection()
            else:
                time.sleep(1)
        except Exception as e:
            print("ERROR AT MAVLINK CHECK", e)
            if (com.mav_in and com.mav_out):
                com.close()
            time.sleep(1)

def update_img():

    global upimg, imgcom

    while True:
        try:
            if (imgcom):
                #upimg = imgcom.cv2_to_qpixmap(imgcom.get_test())
                #time.sleep(0.033)
                
                raw_img = imgcom.get_img()
                if (raw_img is not None):
                    com.draw_rect(raw_img)
                    upimg = imgcom.cv2_to_qpixmap(raw_img)
            else:
                time.sleep(1)

        except Exception as e:
            print("ERROR AT GSTREAMER", e)
            imgcom.close()
            time.sleep(1)
            imgcom = ImageCom(5000)


def restart_gst():

    global imgcom

    try:
        print("Starting Gstreamer...")
        if (imgcom):
            imgcom.close()
            time.sleep(0.5)
        imgcom = ImageCom(5000)

        if imgcom.cap.isOpened():
            print("Success...")
        else:
            print("FAILED...")
    
    except Exception as e:
        print("FAILED... >>>", e)


com = MavCom()
imgcom = None
#Thread(target = restart_gst).start()

Thread(target = update_com).start()
Thread(target = check_com).start()

Thread(target = update_img).start()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
