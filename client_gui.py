import socket
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, messagebox

# ================== DEFAULT ==================
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000

# ================== PINK PASTEL THEME ==================
BG_MAIN = "#fff1f2"        # hồng pastel rất nhạt (nền chính)
BG_CARD = "#ffffff"       # trắng
BG_LOG  = "#ffffff"       # trắng

FG_MAIN = "#374151"       # chữ chính (xám đậm)
FG_SUB  = "#6b7280"       # chữ phụ

ACCENT_PINK = "#f9a8d4"   # hồng pastel
ACCENT_PINK_DARK = "#ec4899"
ACCENT_GREEN = "#86efac"  # xanh pastel
ACCENT_BLUE = "#93c5fd"   # xanh pastel
ERROR_COLOR = "#fca5a5"   # đỏ pastel


class GuessClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("🎲 Guess The Number | Multiplayer")
        self.master.geometry("900x580")
        self.master.configure(bg=BG_MAIN)

        # ================== TITLE ==================
        title = tk.Label(
            master,
            text="🎲 Guess The Number 🌸",
            font=("Segoe UI", 20, "bold"),
            fg=ACCENT_PINK_DARK,
            bg=BG_MAIN
        )
        title.pack(pady=(12, 2))

        subtitle = tk.Label(
            master,
            text="Game đoán số nhiều người chơi",
            font=("Segoe UI", 11),
            fg=FG_SUB,
            bg=BG_MAIN
        )
        subtitle.pack(pady=(0, 12))

        # ================== CONNECTION CARD ==================
        card = tk.Frame(master, bg=BG_CARD)
        card.pack(padx=22, pady=10, fill=tk.X)

        def label(text):
            return tk.Label(
                card,
                text=text,
                bg=BG_CARD,
                fg=FG_SUB,
                font=("Segoe UI", 10, "bold")
            )

        label("👤 Tên").grid(row=0, column=0, padx=6, pady=8)
        self.username_var = tk.StringVar()
        tk.Entry(card, textvariable=self.username_var, width=14).grid(row=0, column=1)

        label("🌐 IP Server").grid(row=0, column=2, padx=6)
        self.host_var = tk.StringVar(value=DEFAULT_HOST)
        tk.Entry(card, textvariable=self.host_var, width=14).grid(row=0, column=3)

        label("🔢 Port").grid(row=0, column=4, padx=6)
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        tk.Entry(card, textvariable=self.port_var, width=8).grid(row=0, column=5)

        self.btn_connect = tk.Button(
            card,
            text="🔗 KẾT NỐI",
            bg=ACCENT_PINK,
            fg=FG_MAIN,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=16,
            command=self.connect
        )
        self.btn_connect.grid(row=0, column=6, padx=12)

        # ================== STATUS ==================
        self.status = tk.Label(
            master,
            text="🔴 Chưa kết nối",
            fg="#dc2626",
            bg=BG_MAIN,
            font=("Segoe UI", 10, "bold")
        )
        self.status.pack(pady=6)

        # ================== LOG ==================
        self.log_box = scrolledtext.ScrolledText(
            master,
            height=16,
            bg=BG_LOG,
            fg=FG_MAIN,
            insertbackground=FG_MAIN,
            font=("Consolas", 11),
            relief="flat",
            borderwidth=1
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=22, pady=10)
        self.log_box.config(state=tk.DISABLED)

        # màu chữ log
        self.log_box.tag_config("win", foreground="#16a34a")
        self.log_box.tag_config("hint", foreground="#2563eb")
        self.log_box.tag_config("time", foreground="#ca8a04")

        # ================== INPUT ==================
        bottom = tk.Frame(master, bg=BG_MAIN)
        bottom.pack(fill=tk.X, padx=22, pady=12)

        tk.Label(
            bottom,
            text="🎯 Số đoán:",
            fg=FG_MAIN,
            bg=BG_MAIN,
            font=("Segoe UI", 11, "bold")
        ).pack(side=tk.LEFT)

        self.guess_var = tk.StringVar()
        self.guess_entry = tk.Entry(
            bottom,
            textvariable=self.guess_var,
            font=("Segoe UI", 12),
            width=24
        )
        self.guess_entry.pack(side=tk.LEFT, padx=8)
        self.guess_entry.bind("<Return>", lambda e: self.send())

        self.btn_send = tk.Button(
            bottom,
            text="💌 GỬI",
            bg=ACCENT_GREEN,
            fg=FG_MAIN,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=22,
            command=self.send
        )
        self.btn_send.pack(side=tk.LEFT)

        # ================== NETWORK ==================
        self.sock = None
        self.queue = queue.Queue()
        self.set_input(False)

        self.master.after(100, self.update_ui)

    # ================== GUI HELPERS ==================
    def log(self, msg):
        self.log_box.config(state=tk.NORMAL)

        if "ĐÚNG" in msg or "🎉" in msg:
            self.log_box.insert(tk.END, msg + "\n", "win")
        elif "LỚN HƠN" in msg or "NHỎ HƠN" in msg:
            self.log_box.insert(tk.END, msg + "\n", "hint")
        elif "⏰" in msg:
            self.log_box.insert(tk.END, msg + "\n", "time")
        else:
            self.log_box.insert(tk.END, msg + "\n")

        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def set_input(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.guess_entry.config(state=state)
        self.btn_send.config(state=state)

    # ================== CONNECT ==================
    def connect(self):
        if self.sock:
            messagebox.showinfo("Thông báo", "Đã kết nối rồi.")
            return

        name = self.username_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu tên", "Vui lòng nhập tên.")
            return

        try:
            host = self.host_var.get().strip()
            port = int(self.port_var.get().strip())
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
            self.sock.sendall((name + "\n").encode("utf-8"))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kết nối được server:\n{e}")
            self.sock = None
            return

        self.status.config(text="🟢 Đã kết nối", fg="#16a34a")
        self.btn_connect.config(state=tk.DISABLED)
        self.set_input(True)
        self.log(f"Đã kết nối tới {host}:{port}")

        threading.Thread(target=self.listen_server, daemon=True).start()

    # ================== RECEIVE ==================
    def listen_server(self):
        try:
            with self.sock.makefile("r", encoding="utf-8") as f:
                for line in f:
                    self.queue.put(line.rstrip("\n"))
        except Exception:
            self.queue.put("❌ Mất kết nối server")
        finally:
            self.queue.put("[SYSTEM] DISCONNECTED")

    def update_ui(self):
        while not self.queue.empty():
            msg = self.queue.get()
            self.log(msg)
            if msg.startswith("[SYSTEM]"):
                self.status.config(text="🔴 Chưa kết nối", fg="#dc2626")
                self.btn_connect.config(state=tk.NORMAL)
                self.set_input(False)
                self.sock = None
        self.master.after(100, self.update_ui)

    # ================== SEND ==================
    def send(self):
        if not self.sock:
            return
        msg = self.guess_var.get().strip()
        if msg:
            try:
                self.sock.sendall((msg + "\n").encode("utf-8"))
            except Exception as e:
                messagebox.showerror("Lỗi", f"Gửi thất bại:\n{e}")
            self.guess_var.set("")


def main():
    root = tk.Tk()
    GuessClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
