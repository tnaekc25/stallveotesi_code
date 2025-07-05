import os, time
os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2
cv2.imshow = lambda *args, **kwargs: None

from ultralytics import YOLO



class RecvClass:

	def __init__(self, model_path):

		gst_pipeline = (
    		"libcamerasrc ! "
    		"video/x-raw,width=640,height=480,framerate=30/1 ! "
    		"videoconvert ! appsink"
		)

		self.model = YOLO(model_path)
		print("Model is ready...")

		self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

		if not self.cap.isOpened():
			print("Failed to open camera stream...")
			exit()

		print("Camera stream is ready...")

	def recv(self):
		ret, frame = self.cap.read()
		return frame if ret else None

	def get_boxes(self, img):
		return self.model.predict(img, show = False)[0].boxes

	def draw_boxes(self, ref, boxes):

		img = ref.copy()

		for box in boxes:
			x1, y1, x2, y2 = map(int, box.xyxy[0])
			cls = int(box.cls[0])
			cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255 if cls else 0, 0 if cls else 255), 2)

		return img


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



if __name__ == "__main__":
	test1 = SendClass("127.0.0.1", 5000)
	img = cv2.imread("test.png")
	img = cv2.resize(img, (640, 480))

	img2 = cv2.imread("test2.png")
	img2 = cv2.resize(img2, (640, 480))

	while True:
		test1.send(img2)
		time.sleep(0.1)
		test1.send(img)
		time.sleep(0.1)