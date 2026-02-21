# VibeGraph QA – Frontend Manual Verification Checklist

> **Tarih:** 2026-02-21  
> **Hazırlayan:** Tester Agent  
> **Ön koşul:** `python main.py start .` ile sistem açık, tarayıcıda `http://localhost:8000`

---

## Feature 1: 🔍 Node Arama (SearchBar)

| # | Senaryo | Input / Aksiyon | Beklenen Sonuç | ✅/❌ |
|---|---------|-----------------|----------------|-------|
| 1.1 | Kısmi eşleşme | Arama kutusuna `"main"` yaz | Dropdown'da `main` node'u görünür | |
| 1.2 | Alt-string eşleşme | `"ana"` yaz | `analyzer`, `analyze_file` vb. eşleşir | |
| 1.3 | Boş arama | Input'u temizle | Dropdown kapanır, sonuç yok | |
| 1.4 | Sonuca tıklama - zoom | Sonuçtan `main` öğesine tıkla | Kamera animasyonla o node'a zoom yapar | |
| 1.5 | Sonuca tıklama - sidebar | Sonuçtan bir node tıkla | Sidebar'da o node'un dosyası seçili olur | |
| 1.6 | ESC kapanma | Dropdown açıkken ESC tuşuna bas | Dropdown kapanır, input temizlenir | |
| 1.7 | Ctrl+K odaklanma | Herhangi bir yerdeyken Ctrl+K bas | Arama input'una focus olur | |
| 1.8 | Performans | 50+ node'lu dosyayı analiz et | Yazarken lag olmamalı (< 100ms hissedilmeli) | |
| 1.9 | Eşleşme yok | `"zzzznonexist"` yaz | "No matching nodes found" mesajı görünür | |
| 1.10 | Ok tuşları | Dropdown açıkken ↑↓ yap, Enter bas | Highlighted item değişir, Enter ile seçilir | |

---

## Feature 2: 💬 AI Sohbet Kutusu (ChatDrawer)

| # | Senaryo | Input / Aksiyon | Beklenen Sonuç | ✅/❌ |
|---|---------|-----------------|----------------|-------|
| 2.1 | FAB görünürlüğü | Sayfa yüklenince | 💬 FAB butonu sağ altta görünür | |
| 2.2 | Drawer açılışı | 💬 butonuna tıkla | Chat drawer açılır, input'a focus | |
| 2.3 | Kontekst badge | Bir node seçiliyken drawer aç | "Asking about: **NodeName**" badge'i görünür | |
| 2.4 | Genel soru | Node seçmeden `"Python nedir?"` sor | AI yanıt verir (node konteksti olmadan) | |
| 2.5 | Node kontekstli soru | `main` tıkla → drawer aç → `"Bu ne yapar?"` | Cevap `main` fonksiyonunun kodunu açıklar | |
| 2.6 | Markdown rendering | AI'dan markdown cevap geldiğinde | Kod blokları, **bold**, listeler düzgün render | |
| 2.7 | Loading animasyonu | Soru gönderilince | Typing dots (●●●) animasyonu görünür | |
| 2.8 | Chat history | Aynı node'da 3 soru sor | Önceki soru-cevaplar görünür, scroll çalışır | |
| 2.9 | Dosya değişimi reset | Sidebar'dan farklı dosya seç | Chat mesajları sıfırlanır | |
| 2.10 | API hatası | Backend kapalıyken soru sor | ⚠️ hata mesajı kullanıcıya gösterilir | |
| 2.11 | Drawer kapatma | ✕ butonuna tıkla | Drawer kapanır, FAB geri gelir | |
| 2.12 | Enter ile gönder | Textarea'da Enter'a bas | Mesaj gönderilir (Shift+Enter = yeni satır) | |

---

## Feature 3: 🎯 Guided Learning Path

| # | Senaryo | Input / Aksiyon | Beklenen Sonuç | ✅/❌ |
|---|---------|-----------------|----------------|-------|
| 3.1 | Learn butonu | Header'da | 🎯 Learn butonu görünür | |
| 3.2 | Overlay açılışı | Learn butonuna tıkla | Learning Path overlay açılır | |
| 3.3 | API çağrısı | Overlay açılınca | Spinner → API'den step listesi gelir | |
| 3.4 | Step listesi | Veriler yüklenince | Sıralı step listesi (1, 2, 3...) görünür | |
| 3.5 | Step tıklama | Step 2'ye tıkla | Kamera ilgili node'a zoom yapar | |
| 3.6 | İleri butonu | "Next →" tıkla | Sonraki step'e geçer, progress bar güncellenir | |
| 3.7 | Geri butonu | "← Previous" tıkla | Önceki step'e döner | |
| 3.8 | İlk step'te geri | Step 1'deyken "← Previous" | Buton disabled olmalı | |
| 3.9 | Son step'te ileri | Son step'teyken "Next →" | Buton disabled olmalı | |
| 3.10 | Progress bar | Step 3/5'teyken | Progress bar %60 dolmalı | |
| 3.11 | Farklı dosya | Sidebar'dan başka dosya seçip Learn | Yeni dosyaya ait farklı learning path gelir | |
| 3.12 | API hatası | Backend kapalı/hatalı | "Failed to load: ..." hata mesajı görünür | |
| 3.13 | Overlay kapatma | ✕ veya backdrop tıkla | Overlay kapanır | |
| 3.14 | Dosya adı gösterimi | Overlay header'da | Geçerli dosya adı gösterilir | |
| 3.15 | Büyük dosya | 15+ node barındıran dosyada | Performans düşmeden path yüklenir | |

---

## Feature 4: 📊 Dependency Map (FileSidebar Deps Tab)

| # | Senaryo | Input / Aksiyon | Beklenen Sonuç | ✅/❌ |
|---|---------|-----------------|----------------|-------|
| 4.1 | Tab gösterimi | Sidebar'a bak | 📁 Files ve 🔗 Deps tab'ları görünür | |
| 4.2 | Tab geçişi | "🔗 Deps" tab'ına tıkla | İçerik dependency listesine geçer | |
| 4.3 | Import bilgileri | Deps tab'ında | Her dosyanın import ettiği modüller listelenir | |
| 4.4 | Lokal/harici ayrımı | Import listesinde | Proje içi importlar ayırt edilebilir olmalı | |
| 4.5 | Dosyaya tıklama | Dep listesinden bir dosyaya tıkla | Files tab'ında o dosya seçilir, graf güncellenir | |
| 4.6 | Used-by bilgisi | Dep detaylarında | "← used by" kısmı hangi dosyaların import ettiğini gösterir | |
| 4.7 | Veri yoksa | `graph_data.json`'da `file_dependencies` yoksa | "No dependency data" mesajı görünür | |
| 4.8 | Files tab'a dönüş | "📁 Files" tab'ına geri tıkla | Dosya listesi geri gelir, crash yok | |
| 4.9 | Circular dependency | A→B→A import zinciri | Crash olmamalı, normal listelemeli | |

---

## Build & Integration Kontrolü

| # | Kontrol | Komut / Aksiyon | Beklenen | ✅/❌ |
|---|---------|-----------------|----------|-------|
| B.1 | Vite build | `cd explorer && npx vite build` | Hatasız tamamlanır, `dist/` oluşur | |
| B.2 | Import kontrolü | Build çıktısını incele | Tüm component'ler bundle'da yer alır | |
| B.3 | Health endpoint | `GET /api/health` | `{"status":"ok","vibe":"checked"}` | |
| B.4 | Chat endpoint | `POST /api/chat` | 200, `{"answer":...}` | |
| B.5 | Learning path endpoint | `POST /api/learning-path` | 200, `{"steps":[...]}` | |
| B.6 | Snippet endpoint | `POST /api/snippet` | 200, `{"snippet":...}` | |
| B.7 | Explain endpoint | `POST /api/explain` | 200, `{"explanation":...}` | |

---

## Regression: Mevcut Özellikler

| # | Özellik | Kontrol | ✅/❌ |
|---|---------|---------|-------|
| R.1 | Graph yükleme | Sayfa açılınca graf görünür | |
| R.2 | Auto-layout | Node'lar üst üste binmez (dagre layout) | |
| R.3 | Node tıklama | Tıklanınca ExplanationPanel açılır | |
| R.4 | Ghost Runner | Play butonuna basınca simülasyon başlar | |
| R.5 | Code Panel | Node seçilince alt panelde kod görünür | |
| R.6 | Dosya seçimi | Sidebar'dan dosya tıklayınca graf güncellenir | |
| R.7 | Sınıf vs Fonksiyon | Farklı renklerle render edilir (🏗️ vs ⚡) | |

---

## Notlar
- **API Key gerekli:** Feature 2, 3 backend testleri gerçek AI yanıtı için `GROQ_API_KEY` gerektirir. Mock testler `test_backend_endpoints.py`'de yapılır.
- **Otomatik testler:** `python -m pytest tests/ -v` ile çalıştırılabilir (API key gerekmez, mock kullanır).
