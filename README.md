# 🎥 ASCII Video Creator With UI  
**Python + Tkinter GUI tabanlı video-to-ASCII oynatıcı**

ASCII Video Player, herhangi bir video dosyasını (`.mp4`, `.avi`, `.mov`, `.mkv`) alıp kare kare **ASCII karakterlerine dönüştürerek canlı olarak terminal benzeri bir pencerede oynatır.**  
Sade, eğlenceli ve genişletilebilir bir GUI (arayüz) ile gelir.  

---

## 🧩 Özellikler

✅ Tkinter GUI — modern, responsive, kolay kullanımlı  
✅ OpenCV ile video işleme  
✅ Canlı ASCII video önizleme  
✅ İki farklı karakter paleti (A / B)  
✅ Dinamik palet geçişi (oynarken bile değiştirilebilir)  
✅ Otomatik bağımlılık kontrolü ve yükleme sistemi (v2.0 ile geldi 🎉)  
✅ Çok iş parçacıklı (UI donmaz)  
✅ Hata ve durum mesajları GUI üzerinden görüntülenir
✅ Değiştirilebilir Tema (v2.1 ile geldi🎉)

## ⚙️ Gereksinimler

- **Python 3.12+**  
- **Windows / macOS / Linux**  
- İnternet bağlantısı (otomatik bağımlılık kurulumu için)

### Gerekli Python paketleri:
- `opencv-python`
- (otomatik olarak yüklenir; elle yüklemek istersen veya uyarı verirse:)
  ```bash
  pip install opencv-python
  ```

# 🛠️ KURULUM(VENV)

1️⃣ Bu depoyu klonla veya zip olarak indir:
```
git clone https://github.com/llwusill/ASCII_VIDEO_CREATOR.git
cd ascii-video-player
```

2️⃣ Python ortamını oluştur (isteğe bağlı ama önerilir):
```
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

3️⃣ Uygulamayı başlat:
```
python UI.py
```
