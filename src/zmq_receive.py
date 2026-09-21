#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zmq
import numpy as np
import cv2
import struct


class ZmqReceiver:
    """
    ZMQ SUB 接收端（类版本）。

    - context / socket 只在 __init__ 里建一次
    - recv() 可反复调用，不重连
    - close() 手动释放资源
    - 支持 with 语句自动 close
    """

    def __init__(self, address="tcp://127.0.0.1:5555",
                 topic=b"",
                 timeout_ms=None,
                 verbose=False):
        self.address = address
        self.topic = topic
        self.timeout_ms = timeout_ms
        self.verbose = verbose

        # ---- 只建一次 ----
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(address)
        self.socket.setsockopt(zmq.SUBSCRIBE, topic)

        if timeout_ms is not None and timeout_ms > 0:
            self.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

        if self.verbose:
            print(f"[ZmqReceiver] connected to {address}, topic={topic!r}")

    # ---------------------------------------------------------
    def recv(self, timeout_ms=None):
        """
        收一帧并解码为 BGR numpy 图像。

        参数
        ----
        timeout_ms : int | None
            本次调用的超时（毫秒）。None 表示用构造时的默认值。
            设 0 表示非阻塞（没数据立刻抛 zmq.Again）。

        返回
        ----
        img : np.ndarray | None
            解码成功返回图像；非图像消息或解码失败返回 None。

        异常
        ----
        zmq.Again
            超时/非阻塞模式下无数据。
        zmq.ZMQError
            ZMQ 底层错误。
        """
        # 临时覆盖超时
        if timeout_ms is not None:
            self.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

        frames = self.socket.recv_multipart()

        if self.verbose:
            print(f"[ZmqReceiver] got {len(frames)} frames")

        return self._decode(frames)

    # ---------------------------------------------------------
    def recv_frames(self):
        """
        只收原始帧，不做解码。
        适合需要自己处理帧的场景。

        返回
        ----
        frames : list[bytes]
            收到的帧列表。
        """
        return self.socket.recv_multipart()

    # ---------------------------------------------------------
    def _decode(self, frames):
        """把多帧消息解码为 BGR numpy 图像"""
        # ---- 情况 1：3 帧 → [topic][header][data] ----
        if len(frames) == 3:
            _topic, header_raw, data = frames

            if len(header_raw) != 20:
                if self.verbose:
                    print(f"[ZmqReceiver] bad header size: "
                          f"{len(header_raw)}")
                return None

            rows, cols, mat_type, channels, data_size = struct.unpack(
                "<iiiii", header_raw
            )

            if data_size != len(data):
                if self.verbose:
                    print(f"[ZmqReceiver] size mismatch: "
                          f"header={data_size} actual={len(data)}")
                return None

            buf = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)

            if img is None:
                if self.verbose:
                    print("[ZmqReceiver] imdecode failed")
                return None

            if self.verbose:
                print(f"[ZmqReceiver] decoded {cols}x{rows} "
                      f"ch={channels} bytes={data_size}")

            return img

        # ---- 情况 2：2 帧 → [topic][payload] ----
        elif len(frames) == 2:
            if self.verbose:
                print(f"[ZmqReceiver] 2-frame message, "
                      f"len={len(frames[1])}")
            return None

        # ---- 其他帧数 ----
        else:
            if self.verbose:
                print(f"[ZmqReceiver] unexpected frame count: "
                      f"{len(frames)}")
            return None

    # ---------------------------------------------------------
    def close(self):
        """释放 socket 和 context"""
        try:
            if self.socket is not None:
                self.socket.close()
                self.socket = None
        except Exception:
            pass
        try:
            if self.context is not None:
                self.context.term()
                self.context = None
        except Exception:
            pass
        if self.verbose:
            print("[ZmqReceiver] closed")

    # ---------------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        # 兜底：忘了 close 时也能释放
        self.close()