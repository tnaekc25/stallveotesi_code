
import os
os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QRegion, QPalette, QColor, QFont, QImage
from PyQt6.QtCore import Qt, QSize, QPoint, QRect, QRectF, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import numpy as np
import folium

RATIO = 16/9


class ImageWidget(QWidget):
    def __init__(self, image_path, parent_widget, parent = None):
        super().__init__(parent)

        self.name = image_path

        self.img = QPixmap(image_path)
        self.parent_widget = parent_widget

        self.rot = 0
        self.imgw = self.imgh = 0
        self.scaled_img = None

    
    def cv2_to_qpixmap(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_image)

    def setImg(self, img):
        if (img is not None):
            self.img = self.cv2_to_qpixmap(img)
        self.rescaleImage()

    def setFactors(self, wf, hf, offx, offy, intr = 0, rf = 1):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy

        self.intr = intr
        self.rf = rf

        self.rescaleImage()
        self.updateGeometry()


    def rescaleImage(self):
        self.scaled_img = self.img.scaled(
            QSize(self.imgw, self.imgh), 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation)


    def updateGeometry(self):

        rrot = np.deg2rad(self.rot)

        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        self.imgw = round(max(pw, (ph*RATIO))*self._wf)
        self.imgh = round(max(ph, (pw/RATIO))*self._hf)

        rw = round(abs(np.sin(rrot)*self.imgh) + abs(np.cos(rrot)*self.imgw))
        rh = round(abs(np.cos(rrot)*self.imgh) + abs(np.sin(rrot)*self.imgw))

        posx = round(pw*self._offx-rw // 2)
        posy = round(ph*self._offy-rh // 2)

        self.setGeometry(posx, posy, rw, rh)


    def setRotation(self, degree):
        self.rot = 360 * degree * self.rf + self.intr
        self.updateGeometry()


    def resizeEvent(self, event):
        self.rescaleImage()
        self.updateGeometry()
        return super().resizeEvent(event)


    def paintEvent(self, event):

        painter = QPainter(self)
        
        if (self.scaled_img):
            painter.translate(QPoint(self.width()//2, self.height()//2))
            painter.rotate(self.rot)
        
            painter.drawPixmap(-self.imgw // 2, -self.imgh // 2, self.scaled_img)

        painter.end()



class SlideDigit(QWidget):
    def __init__(self, parent_widget, parent = None):
        super().__init__(parent)

        #self.setAutoFillBackground(True)
        #palette = self.palette()
        #palette.setColor(QPalette.ColorRole.Window, QColor("blue"))  # or QColor(0, 0, 255)
        #self.setPalette(palette)

        self.parent_widget = parent_widget
        self.ratio = 0

        self.num1 = "0"
        self.num2 = "1"

        self.font1 = 0

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy

        self.updateGeometry()


    def updateGeometry(self):

        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        self.hr = (max(ph, (pw/RATIO))*self._hf)
        self.w = round(max(pw, (ph*RATIO))*self._wf*30)
        self.h = round(self.hr*40)

        self.font1 = round(self.hr*16)
        h = round(self.ratio*50*self.hr)

        self.rect1 = QRect(
            QPoint(0, -h), QPoint(self.w, self.h-h)
        )

        self.rect2 = QRect(
            QPoint(0, round(self.hr*50)-h), QPoint(self.w, round(self.hr*50)+self.h-h)
        )

        posx = round(pw*self._offx-self.w // 2)
        posy = round(ph*self._offy-self.h // 2)

        self.setGeometry(posx, posy, self.w, self.h)


    def setSlide(self, num1, num2, ratio):

        self.num1 = str(num1)
        self.num2 = str(num2)

        self.ratio = ratio

        self.updateGeometry()


    def resizeEvent(self, event):
        self.updateGeometry()
        return super().resizeEvent(event)

    def paintEvent(self, event):

        painter = QPainter(self)

        font = QFont("Arial", self.font1)
        font.setBold(True)
        painter.setFont(font)

        painter.setPen(QColor(220, 135, 0))
        painter.drawText(self.rect1, Qt.AlignmentFlag.AlignCenter, self.num1)
        painter.setPen(QColor(120, 70, 0))
        painter.drawText(self.rect2, Qt.AlignmentFlag.AlignCenter, self.num2)

        painter.end()



class FullDigits:

    def __init__(self, parent_widget, chlst, offx, offy, intv, parent = None):

        self.digit1 = SlideDigit(parent_widget, parent)
        self.digit1.setFactors(0.00035, 0.0006, offx, offy)

        self.digit2 = SlideDigit(parent_widget, parent)
        self.digit2.setFactors(0.00035, 0.0006, offx+intv, offy)

        self.digit3 = SlideDigit(parent_widget, parent)
        self.digit3.setFactors(0.00035, 0.0006, offx+intv*2, offy)

        self.digit4 = SlideDigit(parent_widget, parent)
        self.digit4.setFactors(0.00035, 0.0006, offx+intv*3, offy)

        chlst.append(self.digit1)
        chlst.append(self.digit2)
        chlst.append(self.digit3)
        chlst.append(self.digit4)

    def setDigits(self, num):
        r4 = num % 1
        r3 = num%10 / 10
        r2 = num%100 / 100
        r1 = num%1000 / 1000

        d4 = int(num % 10)
        num //= 10
        d3 = int(num % 10)
        num //= 10
        d2 = int(num % 10)
        num //= 10
        d1 = int(num % 10)

        self.digit1.setSlide(d1, (d1+1) % 10, r1**4)
        self.digit2.setSlide(d2, (d2+1) % 10, r2**4)
        self.digit3.setSlide(d3, (d3+1) % 10, r3**4)
        self.digit4.setSlide(d4, (d4+1) % 10, r4**4)


class Needle(ImageWidget):
    
    def __init__(self, image_path, parent_widget, parent = None):
        super().__init__(image_path, parent_widget, parent)

    def setLimits(self, ll, ul):
        self.ll = ll
        self.ul = ul
        self.margin = self.ul - self.ll

    def num2Rot(self, num):
        self.setRotation((num % self.ul - self.ll) / self.margin)




class SlideBand(ImageWidget):

    def __init__(self, image_path, parent_widget, parent = None):
        super().__init__(image_path, parent_widget, parent)
        self.ratio = 0

    def setSlide(self, ratio):
        self.ratio = ratio




class Attitude(ImageWidget):

    def __init__(self, image_path, parent_widget, parent = None):
        super().__init__(image_path, parent_widget, parent)

        self.vshift = 0
        self.hshift = 0

        self.ratio = 0

    def setFactors(self, wf, hf, wf2, hf2, offx, offy, intr = 0, rf = 1):
        self._wf = wf 
        self._hf = hf
        self._wf2 = wf2 
        self._hf2 = hf2
        self._offx = offx
        self._offy = offy

        self.intr = intr
        self.rf = rf

        self.rescaleImage()
        self.updateGeometry()

    def setVertical(self, ratio):
        self.ratio = ratio if abs(ratio) < 1.5 else -1.5 if ratio < -1.5 else 1.5  
        self.updateGeometry()


    def updateGeometry(self):

        rrot = np.deg2rad(self.rot)

        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        self.ew = round(max(pw, (ph*RATIO))*self._wf2)
        self.eh = round(max(ph, (pw/RATIO))*self._hf2)

        self.hr = (max(ph, (pw/RATIO))*self._hf)

        self.imgw = round(max(pw, (ph*RATIO))*self._wf)
        self.imgh = round(self.hr)

        rw = round(abs(np.sin(rrot)*self.imgh) + abs(np.cos(rrot)*self.imgw))
        rh = round(abs(np.cos(rrot)*self.imgh) + abs(np.sin(rrot)*self.imgw))

        self.hshift = round(self.ratio*self.hr/11.7)

        posx = round(pw*self._offx-rw // 2)
        posy = round(ph*self._offy-rh // 2)

        self.setGeometry(posx, posy, rw, rh)


    def paintEvent(self, event):
        if not self.scaled_img:
            return
    
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
    
        painter.translate(self.width() // 2, self.height() // 2)
        painter.rotate(self.rot)
    
        ellipse_path = QPainterPath()
        ellipse_rect = QRectF(-self.ew // 2, -self.eh // 2, self.ew, self.eh)
        ellipse_path.addEllipse(ellipse_rect)
        painter.setClipPath(ellipse_path)
    
        painter.drawPixmap(-self.imgw // 2, -self.imgh // 2 + self.hshift, self.scaled_img)
    
        painter.end()



class BarWidget(QWidget):
    def __init__(self, parent_widget, parent = None):
        super().__init__(parent)

        self.parent_widget = parent_widget

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("orange"))  # or QColor(0, 0, 255)
        self.setPalette(palette)

        self.ratio = 1

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy

        self.updateGeometry()

    def setSlide(self, ratio):

        self.ratio = ratio
        self.updateGeometry()

    def resizeEvent(self, event):
        self.updateGeometry()
        return super().resizeEvent(event)

    def updateGeometry(self):

        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        h = max(ph, (pw/RATIO))*self._hf
        w = max(pw, (ph*RATIO))*self._wf

        posx = round(pw*self._offx - w / 2)
        posy = int(ph*self._offy - 2*(self.ratio-0.5)*(h / 2))

        self.imgh = round(h*self.ratio)
        self.imgw = round(w)

        self.setGeometry(posx, posy, self.imgw, self.imgh)



class StyledButton(QPushButton):
    def __init__(self, parent_widget, text, parent = None):
        super().__init__(text, parent)

        self.parent_widget = parent_widget

        self.setStyleSheet("""
        QPushButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1c1c1c, stop:1 #0a0a0a);
            color: #ffaa00;
            border: 2px solid #ffaa00;
            border-radius: 6px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            border: 2px solid #ffcc00;
            background-color: #2a2a2a;
        }

        QPushButton:pressed {
            background-color: #000000;
            border: 2px inset #ffaa00;
            color: #ffaa00;
        }

        QPushButton:disabled {
            background-color: #444;
            border: 2px solid #555;
            color: #777;
        }
""")

        

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy

        self.updateGeometry()

    def resizeEvent(self, event):
        self.updateGeometry()
        return super().resizeEvent(event)

    def updateGeometry(self):
    
        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        tw = (max(pw, (ph*RATIO))*self._wf)
        th = (max(ph, (pw/RATIO))*self._hf)

        posx = round(pw*self._offx-tw / 2)
        posy = round(ph*self._offy-th / 2)

        factor = ph/1664
        self.setFont(QFont("Arial", round(8*factor), QFont.Weight.Black))

        self.setGeometry(posx, posy, round(tw), round(th))



class TelemBox(QWidget):
    def __init__(self, parent_widget, text, parent = None):
        super().__init__(parent)

        self.parent_widget = parent_widget
        self.ratio = 0

        self.font1 = 0
        self.basef = 0

        self.text = text


    def setFactors(self, basef, wf, hf, offx, offy):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy
        self.basef = basef

        self.updateGeometry()


    def updateGeometry(self):

        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        h = (max(ph, (pw/RATIO)))

        raww = max(pw, (ph*RATIO))*self._wf
        rawh = h*self._hf

        self.imgw = round(raww)
        self.imgh = round(rawh)

        posx = round(pw*self._offx-self.imgw // 2)
        posy = round(ph*self._offy-self.imgh // 2)

        self.rect1 = QRect(
            QPoint(0, 0), QPoint(self.imgw, self.imgh)
        )

        self.font1 = round(self.basef*(h/1664))

        self.setGeometry(posx, posy, self.imgw, self.imgh)

    def setText(self, text):
        self.text = text

    def resizeEvent(self, event):
        self.updateGeometry()
        return super().resizeEvent(event)

    def paintEvent(self, event):

        painter = QPainter(self)

        font = QFont("Courier New", self.font1)
        font.setBold(True)
        painter.setFont(font)

        painter.setPen(QColor(220, 135, 0))
        painter.drawText(self.rect1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.text)

        painter.end()


from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtCore import Qt


class MapWidget(QWidget):
    def __init__(self, parent, lat, lon):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;")

        self.parent_widget = parent
        self.center_lat = lat
        self.center_lon = lon
        self.current_lat = lat
        self.current_lon = lon
        self.curret_head = 0

        self.lat_range = 1
        self.lon_range = 1
        self.grid_deg_spacing = 0.2

        self._wf = 1
        self._hf = 1
        self._offx = 0.5
        self._offy = 0.5

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf
        self._hf = hf
        self._offx = offx
        self._offy = offy
        self.updateGeometry()
        self.update()

    def updateGeometry(self):
        if not self.parent():
            return
        ph = self.parent_widget.height()
        pw = self.parent_widget.width()

        self.imgw = round(max(pw, (ph * 16 / 9)) * self._wf)
        self.imgh = round(max(ph, (pw / (16 / 9))) * self._hf)

        posx = round(pw * self._offx - self.imgw // 2)
        posy = round(ph * self._offy - self.imgh // 2)

        self.setGeometry(posx, posy, self.imgw, self.imgh)

    def resizeEvent(self, event):
        self.updateGeometry()
        super().resizeEvent(event)

    def updatePosition(self, lat, lon, head):
        self.current_lat = lat
        self.current_lon = lon
        self.curret_head = head
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        neon = QColor(0, 255, 100, 220)
        pen = QPen(neon)
        pen.setWidth(1)
        painter.setPen(pen)

        width = self.imgw
        height = self.imgh

        lat_min = self.center_lat - self.lat_range
        lat_max = self.center_lat + self.lat_range
        lon_min = self.center_lon - self.lon_range
        lon_max = self.center_lon + self.lon_range

        lon = lon_min
        while lon <= lon_max:
            x = int((lon - lon_min) / (lon_max - lon_min) * width)
            painter.drawLine(x, 0, x, height)
            label = f"{lon:.1f}°"
            painter.setFont(QFont("Consolas", 6))
            painter.drawText(x + 2, 12, label)
            lon += self.grid_deg_spacing

        lat = lat_max
        while lat >= lat_min:
            y = int((lat_max - lat) / (lat_max - lat_min) * height)
            painter.drawLine(0, y, width, y)
            label = f"{lat:.1f}°"
            painter.setFont(QFont("Consolas", 6))
            painter.drawText(2, y - 2, label)
            lat -= self.grid_deg_spacing

        cur_x = int((self.current_lon - lon_min) / (lon_max - lon_min) * width)
        cur_y = int((lat_max - self.current_lat) / (lat_max - lat_min) * height)

        glow_color = QColor(0, 255, 100, 180)
        painter.setBrush(glow_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cur_x - 14, cur_y - 14, 28, 28)

        painter.setBrush(QColor(255, 0, 0, 220))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(cur_x - 7, cur_y - 7, 14, 14)

        painter.setBrush(neon)
        painter.setPen(QPen(glow_color, 1))
        painter.drawEllipse(round(cur_x - 15*np.sin(self.curret_head) - 7),
         round(cur_y - 15*np.cos(self.curret_head) - 7), 14, 14)

        painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        painter.setPen(neon)
        coord_text = f"Lat: {self.current_lat:.4f}\nLon: {self.current_lon:.4f}"
        lines = coord_text.split('\n')
        line_height = painter.fontMetrics().height()
        for i, line in enumerate(lines):
            painter.drawText(cur_x + 25, cur_y - 20 + i * line_height, line)

        painter.end()