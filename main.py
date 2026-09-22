import os
import cv2
import multiprocessing as mp
from src.zmq_receive import ZmqReceiver
from src.ui import UI
import threading

os.environ.setdefault("DISPLAY", ":0")
ui = UI()
zmq_receive = ZmqReceiver()

def zmq_loop():
    while True:
        frame = None
        try:
            frame = zmq_receive.recv()
            if(frame is not None):
                print("[ZmqReceiver] Received a frame of shape:", frame.shape)
                ui.push_frame(frame)
                 
            else:
                print("[ZmqReceiver] Received a None frame")
        except Exception as e:
            print("[ZmqReceiver] Error:", e)

if __name__ == "__main__":
    
    thread1 = threading.Thread(target=zmq_loop, daemon=True)
    thread1.start()
    ui.run()
    print("[MAIN] UI closed, exiting")