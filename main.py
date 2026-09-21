import os
import multiprocessing as mp

os.environ.setdefault("DISPLAY", ":0")


def zmq_process():
    """子进程：收 ZMQ 图像 + OpenCV 显示"""
    import cv2
    import zmq
    from src.zmq_receive import ZmqReceiver

    print("[ZMQ-PROC] started, pid =", os.getpid())

    # 子进程里建自己的 receiver（每个进程 socket 不能共享）
    rx = ZmqReceiver(
        address="tcp://127.0.0.1:5555",
        topic=b"",
        timeout_ms=500,      # 500ms 超时，不无限阻塞
        verbose=False,
    )

    try:
        while True:
            try:
                img = rx.recv()          # 用 recv()，不是 zmq_receive()
            except zmq.Again:
                # 500ms 内没收到，继续循环（可以顺便检查退出条件）
                continue
            except Exception as e:
                print("[ZMQ-PROC] recv error:", e)
                continue

            if img is None:
                continue

            cv2.imshow("img", img)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        rx.close()
        cv2.destroyAllWindows()
        print("[ZMQ-PROC] exited")


if __name__ == "__main__":
    from src.ui import UI

    # 1. 先起 ZMQ 子进程
    ctx = mp.get_context("fork")
    p = ctx.Process(target=zmq_process, daemon=True)
    p.start()

    # 2. 主进程跑 tkinter UI
    ui = UI()
    ui.run()

    print("[MAIN] UI closed, exiting")