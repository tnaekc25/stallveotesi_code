import os
os.add_dll_directory("C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64\\bin")
import cv2
cv2.imshow = lambda *args, **kwargs: None

from ultralytics import YOLO



class ImageClass:

	def __init__(self, model_path, ip, port):

		gst_pipeline = (
 		   f"libcamerasrc ! "
    		"video/x-raw,width=640,height=480,format=NV12,framerate=30/1 ! "
    		"tee name=t "
    		"t. ! queue ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
    		"rtph264pay config-interval=1 pt=96 ! udpsink host={ip} port={port} "
    		"t. ! queue ! videoconvert ! video/x-raw,format=BGR ! appsink"
		)



		self.model = YOLO(model_path)
		print("Model is ready...")

		cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

		if not cap.isOpened():
    		print("Failed to open camera stream...")
    		exit()

		print("Camera stream is ready...")

	def read_feed(self):
		ret, frame = cap.read()
		return frame if ret else None

	def get_boxes(self, img):
		return self.model.predict(img, show = False)[0].boxes

	def draw_boxes(self, img, boxes):
		for box in boxes:
			x1, y1, x2, y2 = map(int, box.xyxy[0])
			cls = int(box.cls[0])
			cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255 if cls else 0, 0 if cls else 255), 2)

			cv2.imwrite("output.jpg", img)

	def close():
		cap.release()


if __name__ == "__main__":
	det = ImageClass("model.pt")
	img = det.read_feed()
	box = det.get_boxes(img)
	det.draw_boxes(img, box)