# AMI-ENGINE: Safety & Limitations

**Version**: 1.0  
**Last Updated**: 2026-02-13

---

## Güvenlik Sınırları

### 1. Domain Verisi Olmadan Klinik/Operasyon Kararı Vermez

AMI-ENGINE **domain-agnostic** bir karar regülatörüdür. Klinik veya operasyonel kararlar için:

- ✅ **Gerekli**: Domain uzmanı + adapter katmanı
- ❌ **Yetersiz**: Sadece AMI-ENGINE

**Örnek:** Bir hasta durumu için karar vermek için:
- Domain adapter: Tıbbi verileri → risk skorlarına dönüştürür
- AMI-ENGINE: Risk skorlarından → escalation seviyesi belirler
- Domain adapter: Escalation seviyesine göre → tıbbi protokol uygular

### 2. Bu Bir Karar REGÜLATÖRÜ; Alan Kararı Değil

AMI-ENGINE **"nasıl karar verilir"** sorusunu yanıtlar, **"ne kararı verilir"** sorusunu değil.

- ✅ **Yapar**: Etik skorlama, escalation, güvenlik sınırları
- ❌ **Yapmaz**: Domain-specific karar mantığı (örn. "bu hasta için hangi ilaç?")

### 3. Varsayılan Config Bilinçli Olarak Sıkı

`base` config profile'ı **güvenlik odaklı** ayarlanmıştır:

- Yüksek eşikler (J_MIN, H_MAX)
- Agresif fail-safe tetikleme
- Düşük confidence threshold'ları

**Production için:** `production_safe` veya domain'e özel config kullanın.

---

## Teknik Sınırlar

### 1. Determinism ve Replay

- **Deterministic mod**: `deterministic=True` ile aynı input → aynı output
- **Replay**: `replay(trace)` ile aynı kararı tekrar üret
- **Hash**: `compute_trace_hash(trace)` ile trace bütünlüğü kontrol edilebilir

**Sınır:** Non-deterministic mod (`deterministic=False`) ile replay tutarsız olabilir.

### 2. Temporal Drift (CUS)

- **CUS History**: `context={"cus_history": [...]}` ile zaman içinde belirsizlik takibi
- **Preemptive Escalation**: Yüksek CUS artışında erken escalation

**Sınır:** CUS history yoksa temporal drift hesaplanamaz.

### 3. Soft Clamp

- **Etki**: Ham çıktıyı güvenlik sınırlarına çeker
- **Garanti Yok**: Soft clamp her zaman fark yaratmayabilir (ham çıktı zaten sınırda ise)

**Sınır:** %100 clamp garantisi yok; trace'lerde `soft_clamp=True` ve `raw_action != final_action` kontrol edilmeli.

---

## Bilinen Sınırlamalar

### 1. Action Space

- **Sabit boyut**: 4 bileşen (severity, intervention, compassion, delay)
- **Değer aralığı**: [0, 1] (normalize edilmiş)

**Domain uyumu:** Domain adapter'ı bu formatı domain'e çevirmelidir.

### 2. Config Override

- **String profile**: `config_override="scenario_test"` → `get_config()` çağrılır
- **Dict override**: `config_override={"J_MIN": 0.3, ...}` → direkt kullanılır

**Sınır:** Kısmi override yok; ya tam dict ya da profile adı.

### 3. Trace Schema Versioning

- **Mevcut**: `TRACE_VERSION = "1.0"`
- **Değişiklik**: Schema değişirse versiyon artar

**Uyumluluk:** Eski trace'ler `replay()` ile çalışmaya devam eder (backward compatibility).

---

## Güvenlik Uyarıları

### 1. Input Validation

AMI-ENGINE `raw_state` formatını **varsayar**. Yanlış format:

- Fail-safe tetiklenir
- `human_escalation=True` döner
- Güvenli varsayılan aksiyon üretilir

**Öneri:** Domain adapter'ında input validation yapın.

### 2. Output Validation

AMI-ENGINE'in ürettiği `action` her zaman [0,1]⁴ aralığındadır. Ama:

- Domain adapter'ı bu değerleri **domain'e uygun** şekilde yorumlamalıdır
- L2 seviyesinde **mutlaka** human review gerekir

### 3. Trace Güvenliği

Trace'ler **hassas bilgi içerebilir** (domain adapter'ından gelen raw_state).

- **Güvenlik**: Trace'leri güvenli saklayın (encryption, access control)
- **GDPR/KVKK**: Kişisel veri içeren trace'ler için yasal gereksinimler uygulanmalı

---

## Performans Sınırları

- **Latency**: Ortalama 1-5ms (trace dahil)
- **Throughput**: Saniyede 100-1000 karar (donanıma bağlı)
- **Memory**: Trace buffer için ~1KB/trace

**Ölçüm:** Trace'lerde `latency_ms` alanı ile gerçek performans izlenebilir.

---

## Destek ve Güncellemeler

- **Breaking Changes**: MAJOR versiyon artışında (örn. 1.0 → 2.0)
- **Backward Compatibility**: MINOR/PATCH versiyonlarda korunur
- **Deprecation**: Eski API'ler bir MINOR versiyon boyunca uyarı ile kullanılabilir

Detaylar için **CHANGELOG.md**'ye bakın.

---

**Son Güncelleme**: 2026-02-13
