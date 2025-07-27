
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
        self.rot = (360 * degree * self.rf + self.intr) % 360


    def resizeEvent(self, event):
        self.rescaleImage()
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


    def resizeEvent(self, event):
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

    def setVertical(self, ratio):
        self.ratio = ratio if abs(ratio) < 1.5 else -1.5 if ratio < -1.5 else 1.5  


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


    def setSlide(self, ratio):
        self.ratio = ratio

    def resizeEvent(self, event):
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


    def resizeEvent(self, event):
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



class StyledButton2(QPushButton):
    def __init__(self, parent_widget, text, parent = None):
        super().__init__(text, parent)

        self.parent_widget = parent_widget

        self.setStyleSheet("""
    QPushButton {
        background-color: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #1c1c1c, stop:1 #0a0a0a);
        color: #ffaa00;
        border: 1px solid #ffaa00;
        border-radius: 2px;
        padding: 6px 12px;
    }

    QPushButton:hover {
        border: 1px solid #ffcc00;
        background-color: #2a2a2a;
    }

    QPushButton:pressed {
        background-color: #000000;
        border: 1px inset #ffaa00;
        color: #ffaa00;
    }

    QPushButton:disabled {
        background-color: #444;
        border: 1px solid #555;
        color: #777;
    }
    """)

        

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy


    def resizeEvent(self, event):
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

        self.lat_range = 0.02
        self.lon_range = 0.02

        self.grid_lon_spacing = 0.007
        self.grid_lat_spacing = 0.007

        self.grid_lon_ref = 5
        self.grid_lat_ref = 5

        self._wf = 1
        self._hf = 1
        self._offx = 0.5
        self._offy = 0.5

        self.scale = 0

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf
        self._hf = hf
        self._offx = offx
        self._offy = offy
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

        self.scale = self.imgw / 350

        self.setGeometry(posx, posy, self.imgw, self.imgh)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def updatePosition(self, lat, lon, head):
        self.current_lat = lat
        self.current_lon = lon
        self.curret_head = head
        self.update()

    def setPos(self, lat, lon):
        self.center_lat = lat
        self.center_lon = lon
        self.update()


    def setRangeLA(self, rangev):
        self.lat_range = rangev
        self.grid_lat_spacing = rangev / self.grid_lat_ref

    def setRangeLO(self, rangev):
        self.lon_range = rangev
        self.grid_lon_spacing = rangev / self.grid_lon_ref

    def setGridRefLO(self, rangev):
        self.grid_lon_ref = rangev
        self.grid_lon_spacing = self.lon_range / self.grid_lon_ref

    def setGridRefLA(self, rangev):
        self.grid_lat_ref = rangev
        self.grid_lat_spacing = self.lat_range / self.grid_lat_ref


    def scaled(self, val):
        return round(self.scale*val)


    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        neon = QColor(0, 255, 100, 220)
        pen = QPen(neon)
        pen.setWidth(self.scaled(1))
        painter.setPen(pen)

        width = self.imgw
        height = self.imgh
        center_x = width // 2
        center_y = height // 2

        deg_per_px_x = self.lon_range / (width / 2)
        deg_per_px_y = self.lat_range / (height / 2)

        lon = self.center_lon
        i = 0
        while True:
            dx = int((lon - self.center_lon) / deg_per_px_x)
            x = center_x + dx
            if 0 <= x <= width:
                painter.drawLine(x, 0, x, height)
                label = f"{lon:.3f}°"
                painter.setFont(QFont("Consolas", self.scaled(6)))
                painter.drawText(x + self.scaled(2), self.scaled(12) + self.scaled(15)*i, label)
                lon += self.grid_lon_spacing

                i = (i + 1) % 2
            else:
                break

        lon = self.center_lon - self.grid_lon_spacing
        i = 1
        while True:
            dx = int((lon - self.center_lon) / deg_per_px_x)
            x = center_x + dx
            if 0 <= x <= width:
                painter.drawLine(x, 0, x, height)
                label = f"{lon:.3f}°"
                painter.setFont(QFont("Consolas", self.scaled(6)))
                painter.drawText(x + self.scaled(2), self.scaled(12) + self.scaled(15)*i, label)
                lon -= self.grid_lon_spacing

                i = (i + 1) % 2
            else:
                break

        lat = self.center_lat
        while True:
            dy = int((self.center_lat - lat) / deg_per_px_y)
            y = center_y + dy
            if 0 <= y <= height:
                painter.drawLine(0, y, width, y)
                label = f"{lat:.3f}°"
                painter.setFont(QFont("Consolas", self.scaled(6)))
                painter.drawText(self.scaled(2), y - self.scaled(2), label)
                lat -= self.grid_lat_spacing
            else:
                break

        lat = self.center_lat + self.grid_lat_spacing
        while True:
            dy = int((self.center_lat - lat) / deg_per_px_y)
            y = center_y + dy
            if 0 <= y <= height:
                painter.drawLine(0, y, width, y)
                label = f"{lat:.3f}°"
                painter.setFont(QFont("Consolas", self.scaled(6)))
                painter.drawText(self.scaled(2), y - self.scaled(2), label)
                lat += self.grid_lat_spacing
            else:
                break

        cur_x = int((self.current_lon - self.center_lon) / deg_per_px_x + center_x)
        cur_y = int((self.center_lat - self.current_lat) / deg_per_px_y + center_y)

        glow_color = QColor(0, 255, 100, 180)
        painter.setBrush(glow_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cur_x - self.scaled(10), cur_y - self.scaled(10), self.scaled(20), self.scaled(20))

        painter.setBrush(QColor(255, 0, 0, 220))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(cur_x - self.scaled(5), cur_y - self.scaled(5), self.scaled(10), self.scaled(10))

        painter.setBrush(neon)
        painter.setPen(QPen(glow_color, 1))
        painter.drawEllipse(round(cur_x + self.scaled(10)*np.sin(self.curret_head) - self.scaled(5)),
                            round(cur_y - self.scaled(10)*np.cos(self.curret_head) - self.scaled(5)),
                            self.scaled(10), self.scaled(10))

        painter.setFont(QFont("Consolas", self.scaled(6), QFont.Weight.Bold))
        painter.setPen(neon)
        coord_text = f"Lat: {self.current_lat:.4f}\nLon: {self.current_lon:.4f}"
        lines = coord_text.split('\n')
        line_height = painter.fontMetrics().height()
        for i, line in enumerate(lines):
            painter.drawText(cur_x + self.scaled(25), cur_y - self.scaled(20) + i * line_height, line)

        painter.end()



class PotentiometerWidget(ImageWidget):
    def __init__(self, image_path, parent_widget, defval = 0, minval = 0, trnf = 1, parent=None):
        super().__init__(image_path, parent_widget, parent)
        self.dragging = False
        self.last = None
        self.counter = defval
        self.minval = minval
        self.trnf = trnf
        self.changed = True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging == False:
                initial_pos = event.position()

                dx = initial_pos.x() - self.width() / 2
                dy = self.height() / 2 - initial_pos.y()

                self.last = np.degrees(np.arctan2(dy, dx)) + 180

                self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.update_rotation_from_pos(event.position())
            self.changed = True

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def update_rotation_from_pos(self, pos):
        dx = pos.x() - self.width() / 2
        dy = self.height() / 2 - pos.y()
        angle = np.degrees(np.arctan2(dy, dx)) + 180

        diff = self.last - angle
        if (diff > 100):
            diff = diff - 360

        elif (diff < -100):
            diff = diff + 360

        self.setRotation((self.rot + diff) / 360)
        self.last = angle
        self.counter = max(self.minval, self.counter + self.trnf*diff)

        self.update()



class TapeIndicator(QWidget):
    def __init__(self, parent_widget, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget
        self.ratio = 0
        self.draw_count = 5
        self.font1 = 10
        self.rect_lst = []
        self._wf = 0.1
        self._hf = 0.1
        self._offx = 0.5
        self._offy = 0.5
        self.ref = 0

    def setFactors(self, wf, hf, offx, offy):
        self._wf = wf 
        self._hf = hf
        self._offx = offx
        self._offy = offy

    def setNumber(self, num):
        self.ratio = num - int(num)
        self.ref = int(num)

    def updateGeometry(self):
        pw = self.parent_widget.width()
        ph = self.parent_widget.height()

        hr = max(ph, pw / RATIO) * self._hf

        self.imgw = round(max(pw, ph * RATIO) * self._wf)
        self.imgh = round(hr)

        csize = self.imgh / self.draw_count

        posx = round(pw * self._offx - self.imgw // 2)
        posy = round(ph * self._offy - self.imgh // 2)

        self.rect_lst.clear()

        for i in range(self.draw_count + 1, -1, -1):
            top = round(csize * (i - self.draw_count / 2) + csize*self.ratio)
            bottom = round(csize * i - self.draw_count / 2 + 1 + csize*self.ratio)
            self.rect_lst.append(QRect(QPoint(0, top + round(3*csize/4)),
             QPoint(self.imgw, bottom + round(3*csize/4))))

        self.scale = self.imgw / 100

        self.setGeometry(posx, posy, self.imgw, self.imgh)
        self.update()

    def resizeEvent(self, event):
        return super().resizeEvent(event)

    def scaled(self, val):
        return round(self.scale*val)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
        font = QFont("Arial", self.scaled(self.font1))
        font.setBold(True)
        painter.setFont(font)
    
        painter.fillRect(self.rect(), QColor(8, 8, 8))
    
        center_index = (self.draw_count + 2) // 2
        full_tick_length = int(self.imgw * 0.4)
        half_tick_length = int(self.imgw * 0.2)
        text_padding = 5
    
        for i, rect in enumerate(self.rect_lst):
            is_center = (i == center_index)
            y = (rect.top() + rect.bottom()) // 2
    
            tick_len = full_tick_length
            painter.setPen(QColor(200, 200, 200))
            painter.drawLine(self.imgw - tick_len, y, self.imgw, y)
    
            value = str(i - center_index + self.ref)
    
            text_rect = QRect(0, rect.top(), self.imgw - tick_len - text_padding, rect.height())
    
            if is_center:
                painter.setPen(QColor(255, 165, 0))
            else:
                painter.setPen(QColor(160, 90, 0))
    
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, value)
    
        painter.setPen(QColor(0, 150, 150))
        for i in range(len(self.rect_lst) - 1):
            top = self.rect_lst[i].bottom()
            bottom = self.rect_lst[i + 1].top()
            y = (top + bottom) // 2
    
            painter.drawLine(self.imgw - half_tick_length, y, self.imgw, y)
    
        painter.end()
            
                                