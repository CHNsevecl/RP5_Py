#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import numpy as np
import cv2
import struct
import os

# ==================== 配置 ====================
PI_IP   = "127.0.0.1"   # 如果 Python 不在树莓派本机，改成树莓派实际 IP
PORT    = 5555
TOPIC   = b""           # 空 = 订阅全部；要和 C++ 端 setTopic() 一致
os.environ.setdefault("DISPLAY", ":0")

def main():
    # ---- 创建 ZMQ context 和 SUB socket ----
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    address = f"tcp://{PI_IP}:{PORT}"
    socket.connect(address)
    socket.setsockopt(zmq.SUBSCRIBE, TOPIC)

    print(f"[SUB] Connected to {address}, topic={TOPIC!r}")
    print("[SUB] Waiting for frames... (按 ESC 退出)")

    frame_count = 0

    while True:
        # ---- 收一整套多帧消息 ----
        try:
            frames = socket.recv_multipart()
        except KeyboardInterrupt:
            break
        except zmq.ZMQError as e:
            print(f"[SUB] ZMQ error: {e}")
            break

        # 根据帧数判断是哪种消息
        if len(frames) == 3:
            # ===== sendImage 发的消息 =====
            topic, header_raw, data = frames

            # ---- 解析 header ----
            if len(header_raw) != 20:
                print(f"[SUB] Bad header size: {len(header_raw)}")
                continue

            rows, cols, mat_type, channels, data_size = struct.unpack(
                "<iiiii", header_raw
            )
            #  '<' 小端，'i' int32，5个 → 和 C++ 的 5 个 int32_t 对齐

            # ---- 校验 data 长度 ----
            if data_size != len(data):
                print(f"[SUB] Size mismatch: header={data_size} "
                      f"actual={len(data)}")
                continue

            # ---- 字节流 → numpy → cv::Mat ----
            buf = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)

            if img is None:
                print("[SUB] imdecode failed")
                continue

            # ---- 显示 ----
            cv2.imshow("recv", img)
            frame_count += 1

            if frame_count % 30 == 0:
                print(f"[SUB] frame={frame_count} "
                      f"size={cols}x{rows} ch={channels} bytes={data_size}")

        elif len(frames) == 2:
            # ===== sendRawData / sendString 发的消息 =====
            topic, payload = frames
            # 尝试当字符串解析，不行就按字节处理
            try:
                text = payload.decode("utf-8")
                print(f"[SUB] text: {text}")
            except UnicodeDecodeError:
                print(f"[SUB] raw bytes, len={len(payload)}")
        else:
            print(f"[SUB] Unexpected frame count: {len(frames)}")
            continue

        # ---- 退出检测 ----
        if cv2.waitKey(1) & 0xFF == 27:   # ESC
            break

    socket.close()
    context.term()
    cv2.destroyAllWindows()
    print("[SUB] Closed")


if __name__ == "__main__":
    main()