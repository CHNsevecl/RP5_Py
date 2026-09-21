import subprocess
import pathlib
import threading

class PipeProcess:
    def __init__(self, exe_path):
        self.exe = pathlib.Path(exe_path)
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            [str(self.exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        return self.proc

    def send(self, value: str) -> bool:
        """往 C++ 写一行，成功返回 True"""
        if self.proc is None:
            return False
        try:
            self.proc.stdin.write(value + "\n")
            self.proc.stdin.flush()
            return True
        except BrokenPipeError:
            return False

    def _read_stdout(self):
        for line in self.proc.stdout:
            # pass    # 不打印，纯消耗
            print("C++:", line.strip())

    def stop(self):
        if self.proc is None:
            return
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.terminate()