import os, time
#os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2, numpy as np
cv2.imshow = lambda *args, **kwargs: None

from ultralytics import YOLO
from scipy.spatial.transform import Rotation


class DetectClass:

	def __init__(self, model_path, fx, fy, cx, cy, default_pitch):
		self.model = YOLO(model_path)
		self.fx, self.fy, self.cx, self.cy = fx, fy, cx, cy
		self.default_pitch = default_pitch

	def preprocess(self, img):
	    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	    lower_blue = np.array([50, 120, 150])
	    upper_blue = np.array([170, 255, 255])
	    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
	    mask_blue_b = cv2.boxFilter(mask_blue, -1, (55, 55))
	    mask_blue_f = (mask_blue_b.astype(np.float32) / 255.0)[..., None]
	    target_blue = np.array([155, 76, 41], dtype=np.float32) 
	    mask_soft = cv2.normalize(mask_blue_f, None, 0, 255, cv2.NORM_MINMAX)
	    mask_soft = (mask_soft.astype(np.float32) / 255.0)[..., None]
	    
	    mask_binary = (mask_blue.astype(np.float32) / 255.0)[..., None]
	    mask_final = mask_soft * mask_binary    
	    boosted = img.astype(np.float32)
	    alpha = 0.9
	    boosted = boosted * (1 - alpha * mask_final) + target_blue * (alpha * mask_final)
	    kernel = np.array([[0, -1,  0],
	                       [-1,  5, -1],
	                       [0, -1,  0]])
	    sharpened = cv2.filter2D(np.clip(boosted, 0, 255).astype(np.uint8), -1, kernel)
	    return sharpened


	def get_boxes(self, img, conf):
		raw_box_data = self.model.predict(self.preprocess(img), conf=conf, show = False)[0].boxes
		return [[int(box.cls[0].item())] + list(map(int, box.xyxy[0])) for box in raw_box_data] 

	def get_distance(self, x, y, roll, pitch, h):
		
		X = (x - self.cx) / self.fx
		Y = (y - self.cy) / self.fy
		
		r_cam = np.array([X, Y, 1.0])
		r = Rotation.from_euler('xyz', [pitch + self.default_pitch, roll, 0], degrees=False)
		r_world = r.apply(r_cam)

		if r_world[2] <= 0:
			raise ValueError("horizon error")

		t = h / r_world[2]

		ground_point = t * r_world
		dx, dy = ground_point[0], ground_point[1]
	
		return dx, dy

	def pos_to_gps(self, gps, hud, x, y):
		a = 6378137.0
		b = 6356752.314245 
		e2 = 1 - (b*b)/(a*a)

		head = hud.heading
		lat0 = gps.lat / 1e7
		lon0 = gps.lon / 1e7

		lat_rad = np.radians(lat0)

		theta = np.radians(head)
		dNorth = y * np.cos(theta) - x * np.sin(theta)
		dEast  = y * np.sin(theta) + x * np.cos(theta)

		M = a * (1 - e2) / ((1 - e2 * (np.sin(lat_rad)**2))**1.5)
		N = a / np.sqrt(1 - e2 * (np.sin(lat_rad)**2))
		
		dphi = dNorth / M
		dlambda = dEast / (N * np.cos(lat_rad))
		
		new_lat = lat_rad + dphi
		new_lon = np.radians(lon0) + dlambda

		return np.degrees(new_lat), np.degrees(new_lon)



class RecvClass:

	def __init__(self, fps, width, height):

		self.gst_pipeline = (
    		"libcamerasrc ! "
    		f"video/x-raw,width={width},height={height},format=NV12,framerate={fps}/1 ! "
    		"videoconvert ! appsink")

		self.is_open = False
		self.cap = None

	def recv(self):
		ret, frame = self.cap.read()
		return cv2.flip(frame, 0) if ret else None

	def close(self):
		if (self.cap):
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
	def __init__(self, ip, port, fps, width, height):

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
		self.out = None

	def send(self, img):
		self.out.write(img)

	def close(self):
		if (self.out):
			self.out.release()
		self.is_open = False

	def start(self):
		self.out = cv2.VideoWriter(self.gst_pipeline, cv2.CAP_GSTREAMER, 0, self.fps, (self.width, self.height), True)

		if not self.out.isOpened():
			self.is_open = False
			return 0
		self.is_open = True
		return 1

class VideoSave:
	def __init__(self, fps, width, height):
		fourcc = cv2.VideoWriter_fourcc(*"XVID")
		self.out = cv2.VideoWriter("output.avi", fourcc, fps, (width, height))

		

