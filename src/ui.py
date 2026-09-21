import tkinter as tk
from src.pipe import PipeProcess

EXE = "/home/sevecl/Desktop/C/Firmware/Pipe/build/pipe"

class UI:
    def __init__(self, exe=EXE):
        self.pipe = PipeProcess(exe)
        self.pipe.start()
    
        self.root = tk.Tk()
        self.root.title("数字输入")
        self.root.geometry("300x420")
    
        self.entry_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.entry_var, font=("Helvetica", 24),
                    justify="right").pack(fill="x", padx=10, pady=10, ipady=10)

        keypad = tk.Frame(self.root)
        keypad.pack(padx=10, pady=5)
        layout = [["1","2","3"],["4","5","6"],["7","8","9"]]
        for r, row in enumerate(layout):
            for c, ch in enumerate(row):
                tk.Button(keypad, text=ch, font=("Helvetica", 20), width=4, height=2,
                            command=lambda d=ch: self.press(d)).grid(row=r, column=c, padx=4, pady=4)
    
        bottom = tk.Frame(self.root)
        bottom.pack(padx=10, pady=10)
        tk.Button(bottom, text="0", font=("Helvetica", 20), width=4, height=2,
                    command=lambda: self.press("0")).grid(row=0, column=0, padx=4)
        tk.Button(bottom, text="清", font=("Helvetica", 20), width=4, height=2,
                    command=self.clear).grid(row=0, column=1, padx=4)
        tk.Button(bottom, text="确认", font=("Helvetica", 20), width=4, height=2,
                    command=self.confirm).grid(row=0, column=2, padx=4)

    def press(self,digit):
        if len(self.entry_var.get()) < 9:
            self.entry_var.set(self.entry_var.get() + digit)

    def clear(self):
        self.entry_var.set("")

    def confirm(self):
        value = self.entry_var.get()
        ok = self.pipe.send(value)
        print("sent:" if ok else "失败:", value)   

    def on_close(self):
        self.pipe.stop()
        self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
