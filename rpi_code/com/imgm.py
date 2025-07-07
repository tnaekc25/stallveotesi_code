import os, time
#os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2, numpy as np
cv2.imshow = lambda *args, **kwargs: None

from ultralytics import YOLO


class DetectClass:

	def __init__(self, model_path, fx, fy, cx, cy):
		self.model = YOLO(model_path)
		self.fx, self.fy, self.cx, self.cy = fx, fy, cx, cy
		print("Model is ready...")

	def get_boxes(self, img):
		return self.model.predict(img, show = False)[0].boxes

	def get_distance(self, x, y, h, camera_tilt_deg):

		print(x, y)

		theta_rad = np.radians(camera_tilt_deg)
		alpha_vertical_rad = np.arctan2(y - self.cy, self.fy)
		total_angle_rad = theta_rad + alpha_vertical_rad

		if total_angle_rad <= 0:
			return np.inf, 0.0

		distance = h / np.tan(total_angle_rad)
		angle_rad = np.arctan2(x - self.cx, self.fx)
		hor_angle = np.degrees(angle_rad)

		return distance, hor_angle




class RecvClass:

	def __init__(self):

		gst_pipeline = (
    		"libcamerasrc ! "
    		"video/x-raw,width=640,height=480,format=NV12,framerate=30/1 ! "
    		"videoconvert ! appsink"
		)

		self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

		if not self.cap.isOpened():
			print("Failed to open camera stream...")
			exit()

		print("Camera stream is ready...")

	def recv(self):
		ret, frame = self.cap.read()
		return frame if ret else None


	def close(self):
		self.cap.release()

	def restart(self):
		self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

		if not self.cap.isOpened():
			print("Failed to open camera stream...")
			exit()

		print("Camera stream is ready...")




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


		self.out = cv2.VideoWriter(self.gst_pipeline, cv2.CAP_GSTREAMER, 0, fps, (width, height), True)

		if not self.out.isOpened():
			print("Failed to open video writer...")
			exit()

		print("Gstreamer is ready...")

	def send(self, img):
		self.out.write(img)

	def close(self):
		self.out.release()

	def restart(self):
		self.out = cv2.VideoWriter(self.gst_pipeline, cv2.CAP_GSTREAMER, 0, fps, (width, height), True)

		if not self.out.isOpened():
			print("Failed to open video writer...")
			exit()

		print("Gstreamer is ready...")