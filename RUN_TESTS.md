# AMI-ENGINE — Testleri Çalıştırma

Proje kökünde (ami-engine klasöründe) aşağıdaki yöntemlerden birini kullanın.

---

## Yöntem 1: Batch dosyası (önerilen — PATH gerekmez)

PowerShell veya CMD’de:

```bash
.\run_tests.bat
```

Veya Windows Gezgini’nden `run_tests.bat` dosyasına çift tıklayın.  
Python kurulu ama terminalde `python` bulunamıyorsa bu yöntem çalışır.

---

## Yöntem 2: python ile (PATH’te python varsa)

```bash
python run_all_tests.py
```

**"Python bulunamadı" hatası alıyorsanız:**  
- Terminali kapatıp yeniden açın veya Cursor’ı yeniden başlatın (PATH güncellenir).  
- Veya tam yolu kullanın:  
  `"C:\Users\tsgal\AppData\Local\Programs\Python\Python312\python.exe" run_all_tests.py`

Bu script sırayla şunları yapar:
1. Engine + Replay (B.4)
2. Senaryo testleri (Phase 3 + B.4 + B.3)
3. Adversarial — extreme_compassion
4. Adversarial — justice_conflict
5. Adversarial — harm_explosion
6. Adversarial — moral_drift
7. Monte Carlo (n=500)
8. Chaos (Phase 4.3)

---

## Adım adım (ayrı ayrı)

```bash
# 1) Motor + replay doğrulaması
python engine.py

# 2) Senaryo testleri (acil, fail-safe, pasif, replay, confidence)
python tests/test_scenarios.py

# 3) Adversarial testler
python -m tests.adversarial.extreme_compassion
python -m tests.adversarial.justice_conflict
python -m tests.adversarial.harm_explosion
python -m tests.adversarial.moral_drift_simulation

# 4) Monte Carlo (örnek 1000 senaryo)
python -m tests.monte_carlo.run_example

# 5) Chaos (parametre grid + invariant doğrulama)
python -m tests.chaos.runner
```

---

## Not

- Python 3.10+ gerekir.
- Ortamda `python` yoksa `py -3` veya tam yol deneyin: `"C:\...\python.exe" run_all_tests.py`
