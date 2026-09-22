import os
import queue
import tkinter as tk

import cv2
from PIL import Image, ImageTk

from src.pipe import PipeProcess

EXE = "/home/sevecl/Desktop/C/Firmware/Pipe/build/pipe"

# 视频显示区域最大尺寸
VIDEO_MAX_W, VIDEO_MAX_H = 320, 240

# 主线程轮询帧的间隔（毫秒）
POLL_INTERVAL_MS = 30


class UI:
    def __init__(self):
        os.environ.setdefault("DISPLAY", ":0")

        self.root = tk.Tk()
        self.root.geometry("720x480")

        # 两列四行，等分拉伸
        for c in range(2):
            self.root.columnconfigure(c, weight=1, minsize=360)
        for r in range(4):
            self.root.rowconfigure(r, weight=1)

        self.current_entry = None                 # 当前选中的输入框
        self.frame_queue = queue.Queue(maxsize=2) # 子线程 → 主线程 的帧队列

        self.pipe = PipeProcess(EXE)
        self.pipe.start()

    # ---------------- 界面 ----------------
    def test_window(self):
        tk.Label(self.root, text="左", bg="red").grid(
            row=0, column=0, sticky="nsew"
        )

        # 占位图，避免初始空白
        placeholder = Image.new("RGB", (VIDEO_MAX_W, VIDEO_MAX_H), color="black")
        self.imgtk = ImageTk.PhotoImage(placeholder)

        self.video_label = tk.Label(self.root, image=self.imgtk, bg="black")
        self.video_label.grid(row=0, column=1, sticky="nsew")

        form = tk.Frame(self.root)
        form.grid(row=3, column=0, sticky="nsew")

        entries_info = ["target", "speed", "other"]
        self.entry_map = {}

        for c, name in enumerate(entries_info):
            # 每一组再包一个小 Frame，内部上下放 Label 和 Entry
            cell = tk.Frame(form)
            cell.grid(row=c, column=0, sticky="nsew", padx=15)

            tk.Label(cell, text=name).grid(row=0, column=0, sticky="w")

            entry = tk.Entry(cell, width=20)
            entry.grid(row=1, column=0, sticky="ew")

            self.entry_map[name] = entry

            form.columnconfigure(c, weight=1) 

        self.entry1 = self.entry_map["target"]
        self.entry2 = self.entry_map["speed"]
        self.entry3 = self.entry_map["other"]

        # 统一绑定焦点事件
        for entry in (self.entry1, self.entry2, self.entry3):
            entry.bind(
                "<FocusIn>",
                lambda ev, ent=entry: self.set_current(ent),
            )

    def keyboard_window(self):
        kb = tk.Frame(self.root, bg="#cccccc")
        kb.grid(row=3, column=1, rowspan=4, sticky="nsew")

        layout = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["清空", "0", "确认"],
        ]

        for r, row in enumerate(layout):
            for c, key in enumerate(row):
                if key == "清空":
                    cmd, bg = self.press_clear, "#ff9999"
                elif key == "确认":
                    cmd, bg = self.press_confirm, "#99ff99"
                else:
                    cmd, bg = (lambda n=key: self.press_digit(n)), "#ffffff"

                tk.Button(
                    kb,
                    text=key,
                    font=("Arial", 14),
                    bg=bg,
                    command=cmd,
                ).grid(row=r, column=c, sticky="nsew", padx=3, pady=3)

        # 键盘 3 列、4 行等分拉伸
        for i in range(3):
            kb.columnconfigure(i, weight=1)
        for i in range(4):
            kb.rowconfigure(i, weight=1)

    # ---------------- 键盘逻辑 ----------------
    def set_current(self, entry):
        self.current_entry = entry

    def press_digit(self, digit):
        if self.current_entry is None:
            print("请先选择一个输入框")
            return
        if len(self.current_entry.get()) >= 9:
            return
        self.current_entry.insert("end", digit)

    def press_clear(self):
        if self.current_entry is None:
            return
        self.current_entry.delete(0, "end")

    def press_confirm(self):
        if self.current_entry is None:
            return
        if(self.current_entry == self.entry1):
            print("target:", self.current_entry.get())
        elif(self.current_entry == self.entry2):
            print("speed:", self.current_entry.get())
        elif(self.current_entry == self.entry3):
            print("other:", self.current_entry.get())

    # ---------------- 视频帧 ----------------
    def push_frame(self, frame):
        """子线程调用：把帧放进队列，绝不碰 Tk。"""
        try:
            self.frame_queue.put_nowait(frame)
        except queue.Full:
            pass  # 队列满则丢帧，保证不阻塞

    def poll_frame(self):
        """主线程调用：从队列取帧并刷新 Label。"""
        try:
            frame = self.frame_queue.get_nowait()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV BGR → RGB
            img = Image.fromarray(frame)
            img.thumbnail((VIDEO_MAX_W, VIDEO_MAX_H), Image.LANCZOS)
            self.imgtk = ImageTk.PhotoImage(img)            # 保存引用
            self.video_label.config(image=self.imgtk)       # 主线程更新，安全
        except queue.Empty:
            pass  # 没新帧则保持上一帧，不闪回背景

        self.root.after(POLL_INTERVAL_MS, self.poll_frame)

    # ---------------- 入口 ----------------
    def run(self):
        self.test_window()
        self.keyboard_window()
        self.root.after(POLL_INTERVAL_MS, self.poll_frame)
        self.root.mainloop()


if __name__ == "__main__":
    ui = UI()
    ui.run()