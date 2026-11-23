# Çekirdek, SMT ve False Sharing Donanım Testi

Windows üzerinde gerçek işlemci topolojisini (P-çekirdekleri, E-çekirdekleri ve SMT mantıksal işlemci eşleşmeleri) okuyarak üç temel deneyi çalıştıran .NET (C#) kıyaslama aracı:

1. **Test 1 — Çekirdek Yerleşimi:** 1 P-çekirdeği, aynı P-çekirdeğindeki 2 SMT mantıksal işlemcisi, iki ayrı P-çekirdeği ve E-çekirdeklerinin karşılaştırılması.
2. **Test 2 — False Sharing (Önbellek Satırı Çakışması):** İki ayrı P-çekirdeğinde çalışan thread'lerin sayaçlarının aynı 64-byte önbellek satırında (offset 0 & 8) ve ayrı satırlarda (offset 0 & 64) bulunmasının normal yazma ve atomik yazma (`Interlocked.Exchange`) üzerindeki etkisi.
3. **Test 3 — 64-Byte Sınır Taraması:** Sayaçlar arası mesafeyi `8, 16, 32, 48, 56, 64, 128` byte şeklinde tarayarak 64-byte önbellek satırı sınırını canlı gözlemleme.

## Çalıştırma

```powershell
dotnet run -c Release
```

## Örnek Ölçüm Sonuçları (Intel Core i7-13620H — 6P + 4E, 16 Mantıksal İşlemci)

- **1 P-Çekirdeği vs 1 E-Çekirdeği (80M işlem):** `106,9 ms` vs `269,5 ms` (~2,5x fark)
- **Atomik False Sharing (15M/thread, 2 ayrı P-çekirdeği):**
  - Aynı 64-byte satır (`offset 0 & 8`): `318,4 ms`
  - Ayrı 64-byte satır (`offset 0 & 64`): `85,9 ms` (**3,71x daha hızlı**)
- **64-Byte Sınır Taraması (10M/thread, Atomik):**
  - `56 byte` mesafe: `249,9 ms` (aynı satır)
  - `64 byte` mesafe: `59,6 ms` (ayrı satır — **4,2x hızlanma**)
