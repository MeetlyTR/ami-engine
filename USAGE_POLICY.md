# AMI-ENGINE Usage Policy

**Version**: 1.0  
**Last Updated**: 2026-02-13

---

## Özet

AMI-ENGINE bir **etik karar regülatörü**dür. Bu doküman, kütüphanenin **yasak ve uygunsuz kullanımlarını** tanımlar.

---

## Yasak Kullanımlar

### 1. Gözetim ve Kimlik Tespiti

**YASAK:**
- Halka açık kamera görüntülerinden kişi/plaka tespiti
- Toplu gözetim sistemleri
- Kişisel veri toplama ve işleme (KVKK/GDPR ihlali riski)

**Neden:** AMI-ENGINE domain-agnostic'tır; veri toplama yapmaz. Bu tip kullanımlar adapter katmanında olur ve **domain'in sorumluluğundadır**.

### 2. Otomatik Yaptırım ve Cezalandırma

**YASAK:**
- L2 (human escalation) olmadan otomatik yaptırım
- Kişi hedefleme ve cezalandırma otomasyonu
- İnsan müdahalesi olmadan karar uygulama

**Neden:** L2 seviyesinde `human_escalation=True` zorunludur. Bu, "insan kararı gerekli" anlamına gelir.

### 3. Kişisel Veri İşleme

**YASAK:**
- KVKK/GDPR kapsamındaki kişisel verileri işleme
- Sağlık verileri, finansal veriler gibi hassas bilgileri direkt işleme

**Not:** Domain adapter'ı bu verileri **anonim skorlara** dönüştürmelidir (örn. risk skoru, aciliyet skoru).

---

## Uygunsuz Kullanımlar (Önerilmez)

### 1. Domain Bilgisi Olmadan Klinik/Operasyon Kararı

**Uyarı:** AMI-ENGINE domain bilgisi içermez. Klinik veya operasyonel kararlar için **domain uzmanı** ve **adapter katmanı** şarttır.

### 2. Varsayılan Config ile Production

**Uyarı:** Varsayılan config (`base`) bilinçli olarak **sıkı** ayarlanmıştır. Production için `production_safe` veya domain'e özel config kullanın.

---

## Doğru Kullanım Örnekleri

### ✅ Chat Moderasyonu (Risk Skoru)

```python
# Adapter: Chat mesajı → risk skoru
risk_score = analyze_message(message)  # Domain adapter
raw_state = {"risk": risk_score, "severity": 0.5, ...}
result = moral_decision_engine(raw_state)
# L2 ise → human moderator çağır
```

### ✅ Sensör/IoT (Fiziksel Risk)

```python
# Adapter: Sensör verileri → fiziksel risk
physical_risk = analyze_sensors(temp, pressure, ...)  # Domain adapter
raw_state = {"risk": physical_risk, "severity": 0.8, ...}
result = moral_decision_engine(raw_state)
# L2 ise → operatör çağır
```

### ✅ Müşteri Talepleri (Aciliyet)

```python
# Adapter: Müşteri talebi → aciliyet skoru
urgency = analyze_request(request)  # Domain adapter
raw_state = {"risk": urgency, "severity": 0.6, ...}
result = moral_decision_engine(raw_state)
# L2 ise → human agent çağır
```

---

## Human-in-the-Loop Şartı

**Zorunlu:** L2 seviyesinde (`level == 2` veya `human_escalation == True`) **mutlaka** insan kararı alınmalıdır.

```python
result = moral_decision_engine(raw_state)
if result["human_escalation"]:
    # ZORUNLU: İnsan kararı al
    human_decision = await get_human_review(result)
    # Human decision'ı uygula
```

---

## Kısıt İhlali → Fail-Safe Zorunluluğu

Eğer adapter katmanı AMI-ENGINE'in beklediği format dışında veri gönderirse:

- Motor **fail-safe** moduna geçer
- `human_escalation=True` döner
- Güvenli varsayılan aksiyon (`safe_action`) üretilir

**Bu durumda:** Adapter katmanını düzeltmek ve trace'leri incelemek gerekir.

---

## Support Policy

- **Community Support**: GitHub Issues üzerinden
- **Best Effort**: Mümkün olduğunca hızlı yanıt
- **No SLA**: Garanti edilmiş yanıt süresi yok
- **Security Contact**: Güvenlik açığı için özel kanal (GitHub Security Advisory)

---

## Yasal Uyarı

Bu kütüphane **"AS IS"** sağlanır. Kullanım sorumluluğu **kullanıcıya** aittir. Domain'e özel yasal/etik gereksinimler (KVKK, GDPR, HIPAA, vb.) **domain adapter katmanında** ele alınmalıdır.

---

**Son Güncelleme**: 2026-02-13
