# ASCII Video Player v2.0 — Otomatik Bağımlılık Kurulumlu

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import time
import os
import sys
import subprocess

VERSION = "2.0"

# =======================
# 1) İŞLEM (Plug-in alanı)
# =======================
def process_file(file_path, progress_cb, log_cb, get_ascii_chars):
    """
    Verilen videoyu kare kare ASCII'ye çevirip arayüzde canlı oynatır.
    get_ascii_chars(): o an seçili karakter paletini (str) döndüren callback.
    """

    # OpenCV'yi güvenli import et (GUI hata kutusuna düşsün)
    try:
        import cv2
    except Exception as e:
        raise RuntimeError(
            "OpenCV (opencv-python) yüklenmemiş görünüyor.\n"
            "Üst çubuktaki 'Bağımlılıkları Kontrol Et' ile kurmayı deneyebilirsin.\n\n"
            f"Ayrıntı: {e}"
        )

    def frame_to_ascii(gray_frame, width=100):
        h, w = gray_frame.shape
        aspect_ratio = h / float(w) if w else 1.0
        new_h = max(1, int(aspect_ratio * width * 0.55))
        resized = cv2.resize(gray_frame, (width, new_h))

        ascii_chars = get_ascii_chars() or " .:-=+*#%@"
        if len(ascii_chars) < 2:
            ascii_chars = " .:-=+*#%@"

        scale = (len(ascii_chars) - 1) / 255.0
        lines = []
        for row in resized:
            line = "".join(ascii_chars[int(px * scale)] for px in row)
            lines.append(line)
        return lines  # satır listesi

    cv2 = sys.modules["cv2"]  # tip ipucu: import edildi

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise RuntimeError("Video açılamadı. Dosya bozuk olabilir veya kodek eksik.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 24
    frame_dt = 1.0 / fps
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1

    log_cb(f"[INFO] Oynatma başlatıldı: {os.path.basename(file_path)} ({fps:.1f} FPS)")
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        ascii_lines = frame_to_ascii(gray, width=80)

        ascii_text = "\n".join(ascii_lines)
        log_cb("[[REPLACE]]" + ascii_text)

        frame_idx += 1
        progress_cb(frame_idx / total_frames)
        if frame_idx % int(fps) == 0:
            log_cb(f"[Frame {frame_idx}]")

        # Biraz bekleme (UI rahatlasın)
        if frame_dt > 0:
            time.sleep(frame_dt * 0.5)

    cap.release()
    log_cb("\n[INFO] Oynatma bitti ✅")
    return "Oynatma tamamlandı."


# =======================
# 2) GUI
# =======================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"ASCII Video Player 🎥  — v{VERSION}")
        self.geometry("980x600")
        self.minsize(860, 520)

        # Paletler (ters eğik çizgi için \\ kullan)
        self.ascii_set_a = "♥@%#\\♣☼+=-:. "
        self.ascii_set_b = " .:-=+☼♣\\#%@♥"

        # State
        self.selected_file = None
        self.worker = None
        self.stop_flag = False
        self._progress_ratio = 0.0
        self._log_buffer = []
        self.charset_var = tk.StringVar(value="A")  # A veya B

        # === MENÜ ÇUBUĞU ===
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        dep_menu = tk.Menu(menubar, tearoff=0)
        dep_menu.add_command(label="Bağımlılıkları Kontrol Et", command=self.check_dependencies)
        menubar.add_cascade(label="Araçlar", menu=dep_menu)

        # === ÜST BAR ===
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        # Sol: dosya & kontrol
        left = ttk.Frame(top)
        left.pack(side="left", fill="x", expand=True)

        self.btn_select = ttk.Button(left, text="Dosya Seç…", command=self.select_file)
        self.btn_select.pack(side="left")

        self.lbl_file = ttk.Label(left, text="Seçili dosya yok", width=65)
        self.lbl_file.pack(side="left", padx=10)

        self.btn_run = ttk.Button(left, text="Başlat", command=self.start_processing, state="disabled")
        self.btn_run.pack(side="left", padx=(10, 0))

        self.btn_stop = ttk.Button(left, text="Durdur", command=self.stop_processing, state="disabled")
        self.btn_stop.pack(side="left", padx=6)

        # Sağ üst: Palet seçimi
        right = ttk.Frame(top)
        right.pack(side="right")

        ttk.Label(right, text="Palet:").pack(side="left", padx=(0, 6))
        self.rb_a = ttk.Radiobutton(right, text="A", value="A", variable=self.charset_var)
        self.rb_a.pack(side="left")
        self.rb_b = ttk.Radiobutton(right, text="B", value="B", variable=self.charset_var)
        self.rb_b.pack(side="left", padx=(6, 0))

        # === PROGRESS ===
        bar = ttk.Frame(self, padding=(10, 0, 10, 10))
        bar.pack(fill="x")
        self.progress = ttk.Progressbar(bar, mode="determinate")
        self.progress.pack(fill="x")
        self.status = ttk.Label(bar, text="Hazır")
        self.status.pack(anchor="w", pady=(6, 0))

        # === ÇIKTI ALANI (yatay kaydırmalı) ===
        mid = ttk.Frame(self, padding=10)
        mid.pack(fill="both", expand=True)

        self.output = ScrolledText(mid, wrap="none", height=22, font=("Consolas", 11))
        self.output.pack(fill="both", expand=True)
        hbar = ttk.Scrollbar(mid, orient="horizontal", command=self.output.xview)
        self.output.configure(xscrollcommand=hbar.set)
        hbar.pack(fill="x", side="bottom")

        # Tema (opsiyonel)
        try:
            style = ttk.Style(self)
            if "vista" in style.theme_names():
                style.theme_use("vista")
        except Exception:
            pass

        # Uygulama açılışında bağımlılık kontrolü (sana sorar)
        # İstersen otomatik kontrol istemezsen bu satırı yorumlayabilirsin.
        self.after(200, self.check_dependencies)

    # Paleti anlık döndüren fonksiyon
    def get_ascii_chars(self):
        return self.ascii_set_a if self.charset_var.get() == "A" else self.ascii_set_b

    # ---------- Bağımlılık Kontrol & Otomatik Kurulum ----------
    def check_dependencies(self):
        missing = []

        # cv2 mevcut mu?
        try:
            import cv2  # noqa
        except Exception:
            missing.append("opencv-python")

        if not missing:
            self.status.config(text="Bağımlılıklar hazır ✅")
            return

        pkg_list = ", ".join(missing)
        if messagebox.askyesno(
            "Bağımlılık Eksik",
            f"Aşağıdaki paket(ler) eksik görünüyor:\n\n{pkg_list}\n\n"
            "Şimdi yüklemek ister misiniz?"
        ):
            self.install_packages(missing)
        else:
            self.status.config(text="Eksik paketler var ❗ Lütfen yükleyin.")

    def install_packages(self, packages):
        """Paketleri arka planda kur ve sonucu bildir."""
        def worker():
            self._set_ui_busy(True, note="Paketler yükleniyor…")
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            try:
                # Windows'ta uzun çıktı UI'yı kilitlemesin diye run + capture
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=False
                )
                output = proc.stdout
                ok = (proc.returncode == 0)
            except Exception as e:
                ok = False
                output = f"[Hata] pip çağrısı başarısız: {e}"

            # Sonuç diyaloğu
            if ok:
                messagebox.showinfo("Kurulum Bitti", f"Paketler yüklendi:\n\n{', '.join(packages)}")
                self.status.config(text="Bağımlılıklar yüklendi ✅")
            else:
                messagebox.showerror(
                    "Kurulum Hatası",
                    "Paket kurulumu başarısız oldu.\n\n"
                    "pip çıktısı aşağıdadır (kopyalayıp uzmanla paylaşabilirsiniz):\n\n"
                    + output[:4000]  # çok uzun olmasın
                )
                self.status.config(text="Kurulum başarısız ❌")

            self._set_ui_busy(False)

        threading.Thread(target=worker, daemon=True).start()

    def _set_ui_busy(self, busy: bool, note: str = ""):
        """Basit bir 'meşgul' durumu: butonları kilitle, durum yaz."""
        state = "disabled" if busy else "normal"
        for w in (self.btn_select, self.btn_run, self.btn_stop, self.rb_a, self.rb_b):
            try:
                w.config(state=state)
            except Exception:
                pass
        if note:
            self.status.config(text=note)
        else:
            self.status.config(text="Hazır")

    # ---------- UI Callbacks ----------
    def select_file(self):
        path = filedialog.askopenfilename(
            title="Video Seç",
            filetypes=[("Video", "*.mp4;*.avi;*.mov;*.mkv"), ("Tüm Dosyalar", "*.*")]
        )
        if not path:
            return
        self.selected_file = path
        self.lbl_file.config(text=path)
        self.status.config(text="Dosya seçildi. Başlatabilirsin.")
        self.btn_run.config(state="normal")

    def start_processing(self):
        if not self.selected_file:
            messagebox.showwarning("Uyarı", "Önce bir video seç.")
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Bilgi", "Zaten çalışıyor.")
            return

        self.stop_flag = False
        self.output.delete("1.0", "end")
        self.progress["value"] = 0
        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status.config(text="Çalışıyor…")

        self._progress_ratio = 0.0
        self._log_buffer = []

        self.worker = threading.Thread(target=self._run_job, daemon=True)
        self.worker.start()
        self.after(60, self._poll_worker)

    def stop_processing(self):
        if self.worker and self.worker.is_alive():
            self.stop_flag = True
            self.status.config(text="Durdurma isteniyor…")

    # ---------- Worker Orchestrasyonu ----------
    def _run_job(self):
        try:
            def progress_cb(ratio):
                if self.stop_flag:
                    raise KeyboardInterrupt()
                self._progress_ratio = max(0.0, min(1.0, float(ratio)))

            def log_cb(text):
                self._log_buffer.append(str(text))

            result = process_file(self.selected_file, progress_cb, log_cb, self.get_ascii_chars)

            def on_done():
                self._flush_logs()
                self.output.insert("end", "\n=== Nihai Çıktı ===\n")
                self.output.insert("end", result if isinstance(result, str) else str(result))
                self.output.see("end")
                self.status.config(text="Tamamlandı ✅")
                self.btn_stop.config(state="disabled")
                self.btn_run.config(state="normal")
            self._on_done = on_done

        except KeyboardInterrupt:
            def on_stop():
                self._flush_logs()
                self.status.config(text="İşlem kullanıcı tarafından durduruldu ⏹")
                self.btn_stop.config(state="disabled")
                self.btn_run.config(state="normal")
            self._on_done = on_stop

        except Exception as e:
            def on_err():
                self._flush_logs()
                self.status.config(text=f"Hata: {e}")
                messagebox.showerror("Hata", str(e))
                self.btn_stop.config(state="disabled")
                self.btn_run.config(state="normal")
            self._on_done = on_err

    def _poll_worker(self):
        self._flush_logs()
        self.progress["value"] = int(self._progress_ratio * 100)

        if self.worker and not self.worker.is_alive():
            if hasattr(self, "_on_done") and callable(self._on_done):
                self._on_done()
            return
        self.after(60, self._poll_worker)

    def _flush_logs(self):
        while self._log_buffer:
            msg = self._log_buffer.pop(0)
            if msg.startswith("[[REPLACE]]"):
                ascii_frame = msg[len("[[REPLACE]]"):]
                self.output.delete("1.0", "end")
                self.output.insert("end", ascii_frame)
                self.output.see("end")
            else:
                self.output.insert("end", msg + "\n")
                self.output.see("end")


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as e:
        import traceback
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Kritik Hata", traceback.format_exc())
