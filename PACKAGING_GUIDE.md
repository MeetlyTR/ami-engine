# AMI-ENGINE Paketleme Kılavuzu

**Version**: 1.0  
**Last Updated**: 2026-02-13

---

## Paket Yapısı

Mevcut yapı korunarak paketleme yapılmıştır:

```
ami-engine/
├── ami_engine/          # Public API wrapper
│   ├── __init__.py      # Public exports
│   └── cli.py           # CLI entry point
├── core/                # Core modules (internal)
├── config_profiles/     # Config profiles
├── visualization/       # Dashboard
├── tools/               # Utility scripts
├── learning/            # Learning modules
├── simulation/          # Simulation modules
├── tests/               # Test suite
├── engine.py            # Main engine (backward compatibility)
├── config.py            # Config (backward compatibility)
├── pyproject.toml       # Package metadata
├── MANIFEST.in          # Include files
└── README.md            # Documentation
```

---

## Kurulum (Development)

### 1. Editable Install (Geliştirme)

```bash
pip install -e .
```

Bu şekilde kod değişiklikleri anında yansır.

### 2. Normal Install

```bash
pip install .
```

---

## Paket Oluşturma (Distribution)

### 1. Source Distribution (sdist)

```bash
python -m build --sdist
```

Çıktı: `dist/ami-engine-1.0.0.tar.gz`

### 2. Wheel Distribution

```bash
python -m build --wheel
```

Çıktı: `dist/ami_engine-1.0.0-py3-none-any.whl`

### 3. Her İkisi Birden

```bash
python -m build
```

---

## PyPI'ye Yayınlama

### 1. TestPyPI (Önce Test Et)

```bash
# TestPyPI'ye yükle
python -m twine upload --repository testpypi dist/*

# TestPyPI'den kur
pip install --index-url https://test.pypi.org/simple/ ami-engine
```

### 2. Production PyPI

```bash
# PyPI'ye yükle
python -m twine upload dist/*
```

**Not:** PyPI hesabı ve API token gerekir.

---

## CLI Kullanımı

Kurulumdan sonra:

```bash
# Dashboard başlat
ami-engine dashboard

# Canlı test
ami-engine realtime --duration 90 --profile scenario_test

# Test suite
ami-engine tests
```

---

## Public API

```python
from ami_engine import (
    moral_decision_engine,
    replay,
    TraceCollector,
    build_decision_trace,
    get_config,
    list_profiles,
)
```

---

## Backward Compatibility

Mevcut kodlar çalışmaya devam eder:

```python
# Eski import'lar hala çalışır (kökteki dosyalar korunur)
from engine import moral_decision_engine
from config_profiles import get_config
```

---

## Versiyonlama

SemVer kullanılır: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: Yeni özellikler (backward compatible)
- **PATCH**: Bug fix'ler

Versiyon `pyproject.toml` içinde `version = "1.0.0"` olarak belirtilir.

---

## Dokümantasyon Dosyaları

Paket içinde şu dosyalar dahil edilir (MANIFEST.in ile):

- README.md
- LICENSE
- USAGE_POLICY.md
- SAFETY_LIMITATIONS.md
- AUDITABILITY.md
- CHANGELOG.md

---

## Geliştirme Bağımlılıkları

```bash
pip install -e ".[dev]"
```

Bu şu paketleri kurar:
- pytest
- pytest-cov
- black
- ruff

---

## Test

```bash
# Test suite çalıştır
ami-engine tests

# veya direkt
python run_all_tests.py
```

---

## Sorun Giderme

### Import Hatası

Eğer `ami_engine` import edilemiyorsa:

```bash
# Editable install yap
pip install -e .
```

### CLI Çalışmıyor

```bash
# PATH kontrolü
which ami-engine

# Yeniden kur
pip install --force-reinstall -e .
```

---

**Son Güncelleme**: 2026-02-13
