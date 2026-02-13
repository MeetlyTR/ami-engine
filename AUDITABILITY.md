# AMI-ENGINE: Auditability & Trace Schema

**Version**: 1.0  
**Last Updated**: 2026-02-13

---

## Trace Şeması

### Version

**TRACE_VERSION**: `"1.0"`

Schema değişikliklerinde versiyon artar. Eski trace'ler `replay()` ile çalışmaya devam eder (backward compatibility).

---

## Trace Format

### JSONL (JSON Lines)

Her satır bir karar trace'i:

```json
{
  "t": 0,
  "cus": 0.84,
  "raw_action": [0.0, 1.0, 1.0, 0.0],
  "final_action": [0.0, 1.0, 0.58, 0.29],
  "soft_clamp": true,
  "level": 1,
  "human_escalation": false,
  "run_id": 1770968490928,
  "batch_id": 0,
  "profile_state": "chaos",
  "config_profile": "scenario_test",
  "created_at": 1770968490.9358613,
  "latency_ms": 6.49,
  "J": 0.94,
  "H": 0.0,
  "confidence": 0.12
}
```

### CSV Export

Dashboard'dan veya `tools/csv_export.py` ile CSV formatında export:

**Kolonlar (26 adet):**
- Temel: index, t, cus, delta_cus, cus_mean, level, soft_clamp, human_escalation, latency_ms, phase
- Metadata: run_id, batch_id, profile_state, config_profile, created_at
- Model: J, H, confidence
- **Raw action**: raw_severity, raw_intervention, raw_compassion, raw_delay
- **Final action**: final_severity, final_intervention, final_compassion, final_delay

---

## Trace Alanları

### Zorunlu Alanlar

- `t`: Timestamp veya step index
- `level`: Escalation seviyesi (0, 1, veya 2)
- `raw_action`: Ham aksiyon (motorun ilk ürettiği)
- `final_action`: Final aksiyon (clamp sonrası)

### Opsiyonel Alanlar

- `cus`: Cumulative Uncertainty Score (temporal drift için)
- `soft_clamp`: Soft clamp uygulandı mı? (True/False)
- `human_escalation`: İnsan kararı gerekli mi? (True/False)
- `latency_ms`: Karar süresi (ms)
- `J`, `H`: Justice ve Harm skorları
- `confidence`: Güven skoru
- `run_id`: Test run kimliği (timestamp-ms)
- `batch_id`: Batch sıra numarası
- `profile_state`: State profili (easy/medium/chaos)
- `config_profile`: Config profili (scenario_test/production_safe)
- `created_at`: Wall-clock zaman damgası

---

## Determinism ve Hash

### Deterministic Mode

```python
result = moral_decision_engine(raw_state, deterministic=True)
```

Aynı `raw_state` → aynı `action` (reproducible).

### Trace Hash

```python
from engine import compute_trace_hash

hash_value = compute_trace_hash(trace)
```

**Kullanım:**
- Trace bütünlüğü kontrolü
- Duplicate detection
- Audit log'larında referans

**Format:** SHA-256 hex string (64 karakter)

---

## Replay

### Aynı Kararı Tekrar Üret

```python
from ami_engine import replay

# Trace'den aynı kararı üret
new_result = replay(trace)

# Yeni trace ile karşılaştır
assert new_result["action"] == trace["final_action"]
```

**Sınır:** Non-deterministic mod ile replay tutarsız olabilir.

---

## Dashboard ve Görselleştirme

### Streamlit Dashboard

```bash
ami-engine dashboard
```

**Özellikler:**
- JSONL/CSV yükleme
- CUS timeline, soft clamp map, action drift grafikleri
- Level timeline (L0/L1/L2 dağılımı)
- Latency analizi
- Soft clamp filtre
- CSV export (raw vs final karşılaştırması)

**URL:** `http://localhost:8501`

---

## Audit Log Best Practices

### 1. Trace Saklama

- **Format**: JSONL (her satır bir trace)
- **Encoding**: UTF-8
- **Compression**: Gzip (uzun süreli saklama için)

### 2. Trace Retention

- **Production**: En az 90 gün (yasal gereksinimlere göre)
- **Development**: İsteğe bağlı
- **Archive**: Eski trace'ler `archive/` klasörüne taşınabilir

### 3. Trace Güvenliği

- **Encryption**: Hassas bilgi içeren trace'ler için
- **Access Control**: Trace'lere erişim kısıtlanmalı
- **GDPR/KVKK**: Kişisel veri içeren trace'ler için yasal gereksinimler

### 4. Trace Analizi

- **Dashboard**: Görsel analiz
- **CSV Export**: Excel/veri analizi araçları ile
- **Python API**: `load_traces_from_jsonl()` ile programatik analiz

---

## Trace Schema Evolution

### Versioning Strategy

- **MAJOR** (1.0 → 2.0): Breaking changes (eski trace'ler replay edilemez)
- **MINOR** (1.0 → 1.1): Yeni alanlar eklenir (backward compatible)
- **PATCH** (1.0.0 → 1.0.1): Bug fix'ler (schema değişmez)

### Migration

Eski trace'ler için migration script'leri sağlanır (CHANGELOG.md'de belirtilir).

---

## Örnek Audit Workflow

```python
from ami_engine import moral_decision_engine, replay, compute_trace_hash
from core.trace_collector import TraceCollector

# Karar al
collector = TraceCollector(jsonl_path="audit.log")
result = moral_decision_engine(raw_state)
trace = build_decision_trace(result)
collector.push(trace)

# Hash ile bütünlük kontrolü
hash_val = compute_trace_hash(trace)
print(f"Trace hash: {hash_val}")

# Replay ile doğrulama
replayed = replay(trace)
assert replayed["action"] == trace["final_action"]
```

---

## Compliance

### GDPR/KVKK

- Trace'ler kişisel veri içerebilir → **domain adapter sorumluluğu**
- Trace retention policy uygulanmalı
- Right to deletion: Trace'ler silinebilir olmalı

### Audit Requirements

- **Trace completeness**: Her karar trace'lenmeli
- **Trace integrity**: Hash ile kontrol edilebilir
- **Trace accessibility**: Dashboard/CSV ile erişilebilir

---

**Son Güncelleme**: 2026-02-13
