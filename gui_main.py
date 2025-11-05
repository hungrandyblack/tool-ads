import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import csv
import time

# IMPORT worker_task thực tế của bạn
# worker_task phải nhận 1 arg (tuple): (i, email, pwd, CONFIG, proxy) và return result
from worker_task import worker_task
from config import CONFIG  # ensure you have this or adjust import

def load_accounts(csv_file):
    accounts = []
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                email = row[0].strip()
                password = row[1].strip()
                proxy = row[2].strip() if len(row) > 2 else None
                accounts.append((email, password, proxy))
    return accounts

def log_print(log_widget, text):
    log_widget.insert(tk.END, text + "\n")
    log_widget.see(tk.END)

def run_tasks_threaded(csv_file, concurrency, log_widget):
    """Chạy các worker thực sự bằng ThreadPoolExecutor."""
    if not Path(csv_file).exists():
        log_print(log_widget, f"❌ Không tìm thấy file: {csv_file}")
        return

    accounts = load_accounts(csv_file)
    if not accounts:
        log_print(log_widget, "❌ Danh sách tài khoản rỗng.")
        return

    tasks = []
    for i, (email, pwd, proxy) in enumerate(accounts):
        tasks.append((i, email, pwd, CONFIG, proxy))

    actual_concurrency = min(concurrency, len(tasks))
    log_print(log_widget, f"🚀 Bắt đầu chạy {len(tasks)} tài khoản với concurrency = {actual_concurrency}\n")

    # ThreadPoolExecutor để chạy worker_task (mỗi worker khởi Chrome riêng)
    with ThreadPoolExecutor(max_workers=actual_concurrency) as ex:
        future_to_task = {ex.submit(worker_task, task): task for task in tasks}
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                res = future.result()
                # res có thể là dict hoặc string - in cho dễ đọc
                log_print(log_widget, f"{res}")
            except Exception as e:
                log_print(log_widget, f"[ERR] task {task[0]} raised: {e}")

    log_print(log_widget, "\n✅ Hoàn thành tất cả tiến trình.")

def choose_csv(entry_widget):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)

def start_program(csv_entry, concurrency_entry, log_widget, start_btn):
    csv_file = csv_entry.get().strip()
    if not csv_file:
        messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn file CSV.")
        return

    try:
        concurrency = int(concurrency_entry.get().strip())
        if concurrency < 1:
            raise ValueError
    except ValueError:
        messagebox.showwarning("Lỗi nhập", "Số luồng phải là số nguyên >= 1.")
        return

    # disable button để tránh bấm nhiều lần
    start_btn.config(state=tk.DISABLED)

    def runner():
        try:
            run_tasks_threaded(csv_file, concurrency, log_widget)
        finally:
            # enable lại nút khi hoàn tất
            start_btn.config(state=tk.NORMAL)

    threading.Thread(target=runner, daemon=True).start()

def main():
    root = tk.Tk()
    root.title("Multi Login Tool (GUI)")
    root.geometry("820x600")

    tk.Label(root, text="File CSV tài khoản (email,password,proxy):").pack(anchor="w", padx=10, pady=(10,0))
    csv_frame = tk.Frame(root)
    csv_entry = tk.Entry(csv_frame, width=80)
    csv_entry.insert(0, "accounts_with_proxy.csv")
    csv_entry.pack(side=tk.LEFT, padx=5)
    tk.Button(csv_frame, text="Chọn file", command=lambda: choose_csv(csv_entry)).pack(side=tk.LEFT)
    csv_frame.pack(padx=10, pady=5, anchor="w")

    tk.Label(root, text="Số luồng Chrome (concurrency):").pack(anchor="w", padx=10, pady=(10,0))
    concurrency_entry = tk.Entry(root, width=8)
    concurrency_entry.insert(0, "2")
    concurrency_entry.pack(padx=10, pady=5, anchor="w")

    start_btn = tk.Button(root, text="🚀 Bắt đầu", bg="#4CAF50", fg="white",
                          command=lambda: start_program(csv_entry, concurrency_entry, log_widget, start_btn))
    start_btn.pack(pady=8)

    tk.Label(root, text="LOG:").pack(anchor="w", padx=10)
    log_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=25)
    log_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    root.mainloop()

if __name__ == "__main__":
    # nếu build exe bằng pyinstaller, không cần multiprocessing.freeze_support() dùng thread-based approach
    main()