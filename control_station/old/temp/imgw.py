
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QRegion, QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QPoint, QRect, QRectF
import numpy as np

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

    def setImg(self, image_path):
        self.img = QPixmap(image_path)

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

        print(self.name ,">>", self.geometry(), self.imgw, self.imgh)

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

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("blue"))  # or QColor(0, 0, 255)
        self.setPalette(palette)

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

    def __init__(self, parent_widget, layout, offx, offy, intv, parent = None):

        self.digit1 = SlideDigit(parent_widget)
        self.digit1.setFactors(0.00035, 0.0006, offx, offy)

        self.digit2 = SlideDigit(parent_widget)
        self.digit2.setFactors(0.00035, 0.0006, offx+intv, offy)

        self.digit3 = SlideDigit(parent_widget)
        self.digit3.setFactors(0.00035, 0.0006, offx+intv*2, offy)

        self.digit4 = SlideDigit(parent_widget)
        self.digit4.setFactors(0.00035, 0.0006, offx+intv*3, offy)

        layout.addWidget(self.digit1)
        layout.addWidget(self.digit2)
        layout.addWidget(self.digit3)
        layout.addWidget(self.digit4)

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
        self.ratio = ratio
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
    def __init__(self, parent_widget, text):
        super().__init__(text)

        self.parent_widget = parent_widget

        

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
        self.setFont(QFont("Arial", round(10*factor), QFont.Weight.Black))

        self.setGeometry(posx, posy, round(tw), round(th))