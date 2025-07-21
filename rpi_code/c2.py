import serial
import struct
import cv2
import numpy as np
import time



class Deneyap:

    def __init__(self):


        self.ser = serial.Serial("/dev/ttyUSB0", 921600, timeout=10)

        output_filename = 'captured.avi'
        fps = 10
        self.frame_size = (640, 480)

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(output_filename, fourcc, fps, self.frame_size)

        print("Starting video capture...")

    def loop(self):

        time.sleep(2)
        self.ser.reset_input_buffer()

        try:
            while True:
                self.ser.write(b'C')

                img_len_data = self.ser.read(4)
                if len(img_len_data) != 4:
                    continue

                img_len = struct.unpack('<I', img_len_data)[0]
                print(f"Receiving {img_len} bytes...")

                self.ser.write(b'C')

                img_data = b''
                while len(img_data) < img_len:
                    packet = self.ser.read(img_len - len(img_data))
                    if not packet:
                        break
                    img_data += packet

                if len(img_data) != img_len:
                    continue

                np_arr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    frame_resized = cv2.resize(frame, self.frame_size)
                    self.out.write(frame_resized)

        except Exception as e:
            print(e)

        finally:
            self.out.release()
            self.ser.close()
