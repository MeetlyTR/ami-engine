# AMI-ENGINE Release Checklist

**Version**: 1.0.0  
**Target Date**: 2026-02-13

---

## ✅ Tamamlanan Adımlar

### 1. Paketleme Altyapısı
- [x] `pyproject.toml` oluşturuldu (setuptools, SemVer 1.0.0)
- [x] `MANIFEST.in` oluşturuldu (doküman dosyaları dahil)
- [x] `LICENSE` (Apache-2.0) eklendi
- [x] `ami_engine/__init__.py` (Public API wrapper) oluşturuldu
- [x] `ami_engine/cli.py` (CLI entry point) oluşturuldu

### 2. Dokümantasyon
- [x] `README.md` (genel bakış, kurulum, hızlı başlangıç)
- [x] `USAGE_POLICY.md` (yasak kullanımlar, human-in-the-loop)
- [x] `SAFETY_LIMITATIONS.md` (güvenlik sınırları, teknik sınırlar)
- [x] `AUDITABILITY.md` (trace şeması, replay, hash)
- [x] `CHANGELOG.md` (sürüm geçmişi)
- [x] `PACKAGING_GUIDE.md` (paketleme kılavuzu)

### 3. Public API Sabitleme
- [x] `moral_decision_engine()` export edildi
- [x] `replay()` export edildi
- [x] `TraceCollector`, `build_decision_trace` export edildi
- [x] `get_config()`, `list_profiles()` export edildi

### 4. CLI
- [x] `ami-engine dashboard` komutu
- [x] `ami-engine realtime` komutu
- [x] `ami-engine tests` komutu

---

## 🔄 Yapılacaklar (Release Öncesi)

### 1. Test ve Doğrulama
- [ ] `pip install -e .` ile editable install test et
- [ ] `ami-engine dashboard` çalışıyor mu?
- [ ] `ami-engine realtime --duration 10` çalışıyor mu?
- [ ] `ami-engine tests` çalışıyor mu?
- [ ] Public API import'ları çalışıyor mu?

### 2. PyPI Hazırlığı
- [ ] GitHub repository URL'lerini güncelle (`pyproject.toml` içinde)
- [ ] PyPI hesabı oluştur (veya mevcut hesabı kullan)
- [ ] API token oluştur (PyPI → Account Settings → API tokens)

### 3. Build ve Test
- [ ] `python -m build` ile paket oluştur
- [ ] `python -m twine check dist/*` ile kontrol et
- [ ] TestPyPI'ye yükle ve test et
- [ ] TestPyPI'den kur ve çalıştır

### 4. Final Release
- [ ] Production PyPI'ye yükle
- [ ] GitHub release oluştur
- [ ] Dokümantasyonu güncelle (gerekirse)

---

## 📋 Release Notları

### Version 1.0.0 (2026-02-13)

**İlk Stabil Sürüm**

- Public API sabitlendi
- CLI eklendi
- Dokümantasyon tamamlandı
- Paketleme altyapısı hazır

---

## 🚀 Hızlı Başlangıç (Release Sonrası)

```bash
# Kurulum
pip install ami-engine

# Dashboard
ami-engine dashboard

# Test
ami-engine tests
```

---

**Son Güncelleme**: 2026-02-13
