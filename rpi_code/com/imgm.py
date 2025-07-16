import os, time
#os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2, numpy as np
cv2.imshow = lambda *args, **kwargs: None

from ultralytics import YOLO
from scipy.spatial.transform import Rotation


class DetectClass:

	def __init__(self, model_path, fx, fy, cx, cy):
		self.model = YOLO(model_path)
		self.fx, self.fy, self.cx, self.cy = fx, fy, cx, cy
		print("Model is ready...")

	def get_boxes(self, img):
		return self.model.predict(img, show = False)[0].boxes

	def get_distance(self, x, y, roll, pitch, h):
		
		X = (x - self.cx) / self.fx
		Y = (y - self.cy) / self.fy
		
		r_cam = np.array([X, Y, 1.0])
		r = Rotation.from_euler('xyz', [roll, pitch, 0], degrees=True)
		r_world = r.inv().apply(r_cam)

		t = h / r_world[2]

		ground_point = t * r_world
		dx, dy = ground_point[0], ground_point[1]
	
		return dx, dy




class RecvClass:

	def __init__(self):

		self.gst_pipeline = (
    		"libcamerasrc ! "
    		"video/x-raw,width=640,height=480,format=NV12,framerate=30/1 ! "
    		"videoconvert ! appsink")

		self.is_open = False

	def recv(self):
		ret, frame = self.cap.read()
		return frame if ret else None

	def close(self):
		self.cap.release()
		self.is_open = False

	def start(self):
		self.cap = cv2.VideoCapture(self.gst_pipeline, cv2.CAP_GSTREAMER)

		if not self.cap.isOpened():
			self.is_open = False
			return 0
		self.is_open = True
		return 1




class SendClass:
	def __init__(self, ip, port, fps = 30, width = 640, height = 480):

		self.gst_pipeline = (
    f'appsrc ! '
    f'video/x-raw,format=BGR,width={width},height={height},framerate={fps}/1 ! '
    f'videoconvert ! '
    f'video/x-raw,format=I420 ! '
    f'x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! '
    f'rtph264pay config-interval=1 pt=96 ! '
    f'udpsink host={ip} port={port}'
)
		self.width = width
		self.height = height
		self.fps = fps

		self.is_open = False

	def send(self, img):
		self.out.write(img)

	def close(self):
		self.out.release()
		self.is_open = False

	def start(self):
		self.out = cv2.VideoWriter(self.gst_pipeline, cv2.CAP_GSTREAMER, 0, self.fps, (self.width, self.height), True)

		if not self.out.isOpened():
			self.is_open = False
			return 0
		self.is_open = True
		return 1