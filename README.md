# AMI-ENGINE

**Ethical Decision Engine with L0/L1/L2 Escalation, Soft Clamp, and Auditability**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## Ne Yapar?

AMI-ENGINE, **etik karar verme** için bir **regülasyon-grade** motorudur. Ham durum (raw state) alır, moral skorlar (Justice, Harm, Compassion) hesaplar, ve **üç seviyeli escalation** (L0/L1/L2) ile güvenli aksiyon üretir.

### Temel Özellikler

- **L0/L1/L2 Escalation**: Otomatik karar → Soft clamp → Human escalation
- **Soft Clamp**: Güvenlik sınırlarını aşan ham çıktıları yumuşak biçimde sınırlar
- **Auditability**: Her karar için tam trace (JSONL/CSV) + replay desteği
- **Temporal Drift**: CUS (Cumulative Uncertainty Score) ile zaman içinde belirsizlik takibi
- **Config Profiles**: Senaryo bazlı eşik ayarları (scenario_test, production_safe, vb.)

---

## Ne Yapmaz?

- ❌ **Domain-specific karar vermez**: Bu bir **karar regülatörü**; alan bilgisi adapter katmanından gelir
- ❌ **Kişisel veri işlemez**: Ham state'i domain adapter'ından alır; veri toplama/gözetim yapmaz
- ❌ **Otomatik yaptırım uygulamaz**: L2'de human escalation zorunludur
- ❌ **Gözetim/kimlik tespiti yapmaz**: Bu kullanımlar yasaktır (USAGE_POLICY.md)

---

## Kurulum

```bash
pip install ami-engine
```

## Hızlı Başlangıç

### Python API

```python
from ami_engine import moral_decision_engine, get_config

# Ham durum (domain adapter'ından gelir)
raw_state = {
    "risk": 0.7,
    "severity": 0.8,
    "context": {...}
}

# Karar al
result = moral_decision_engine(
    raw_state,
    config_override="scenario_test",  # veya get_config("scenario_test")
    context={"cus_history": []}
)

# Sonuç
action = result["action"]  # [severity, intervention, compassion, delay]
level = result["escalation"]  # 0, 1, veya 2
human_escalation = result["human_escalation"]  # True/False
```

### CLI

```bash
# Dashboard başlat
ami-engine dashboard

# Canlı test (90 saniye)
ami-engine realtime --duration 90 --profile scenario_test

# Test suite çalıştır
ami-engine tests
```

---

## L0/L1/L2 Anlamı

- **L0**: Otomatik karar — motor güvenli aksiyon üretti
- **L1**: Soft clamp uygulandı — ham çıktı sınırlandı, ama otomatik devam ediyor
- **L2**: Human escalation — insan kararı gerekli (fail-safe tetiklendi)

Her seviye trace'de `level` alanı ile işaretlenir.

---

## Trace ve Auditability

Her karar için tam trace üretilir:

- **JSONL**: `traces_live.jsonl` (her satır bir trace)
- **CSV**: `traces_live.csv` (raw vs final action karşılaştırması)
- **Dashboard**: `ami-engine dashboard` ile görselleştirme

Trace şeması: `TRACE_VERSION = "1.0"` (değişikliklerde versiyon artar).

**Replay**: `replay(trace)` ile aynı kararı tekrar üret.

---

## Config Profiles

```python
from ami_engine import get_config, list_profiles

# Mevcut profiller
print(list_profiles())  # ['base', 'scenario_test', 'production_safe', ...]

# Profile kullan
config = get_config("scenario_test")
result = moral_decision_engine(raw_state, config_override=config)
```

---

## Adapter Pattern

AMI-ENGINE domain-agnostic'tır. Domain'e bağlanmak için **adapter** katmanı gerekir:

```
Domain Input → Adapter → raw_state → AMI-ENGINE → action → Adapter → Domain Output
```

Örnek adapter'lar:
- Chat mesajları → risk skoru → raw_state
- Sensör verileri → fiziksel risk → raw_state
- Müşteri talepleri → aciliyet skoru → raw_state

---

## Dokümantasyon

- **README.md** (bu dosya): Genel bakış
- **USAGE_POLICY.md**: Kullanım politikası ve yasaklar
- **SAFETY_LIMITATIONS.md**: Güvenlik sınırları ve uyarılar
- **AUDITABILITY.md**: Denetlenebilirlik ve trace şeması
- **CHANGELOG.md**: Sürüm geçmişi

---

## Lisans

Apache-2.0 License — Detaylar için LICENSE dosyasına bakın.

---

## Katkıda Bulunma

Issue açmak ve PR göndermek için GitHub repository'ye bakın.

**Security**: Güvenlik açığı bildirimi için lütfen özel kanal kullanın (USAGE_POLICY.md'de belirtilmiştir).

---

## Versiyon

**1.0.0** — İlk stabil sürüm
