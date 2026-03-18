# 🐧 Dokumentacja Systemowa: Optymalizacja Swappiness

### **Urządzenie**: Dell Wyse 3040 (Debian)

### **Data**: 18 Marca 2026

### **Cel**: Ochrona pamięci eMMC oraz optymalizacja wykorzystania 2GB RAM.

## 1. Definicja

`swappiness` to parametr jądra Linux (kernel), który określa, jak chętnie system przenosi dane z pamięci RAM do obszaru wymiany (SWAP) na dysku.
- **Zakres**: 0 - 100
- **Domyślnie**: zazwyczaj 60

## 2. Dlaczego optymalizacja jest kluczowa?

Dell Wyse 3040 korzysta z wbudowanej pamięci eMMC (Flash). Pamięć ta ma ograniczoną żywotność (cykle zapisu). Przy domyślnym ustawieniu (60), system zbyt często zapisuje dane na dysku, co:

1. **Degraduje sprzęt**: Skraca żywotność kości eMMC.

1. **Obniża wydajność**: RAM jest wielokrotnie szybszy niż wbudowana pamięć Flash.

## 3. Poziomy Swappiness - Zastosowanie

| Wartość | Zachowanie Systemu | Rekomendacja |
| :--- | :---: | :---: |
| 60 | Balans między cache plików a swapowaniem. | Standardowe PC (HDD/SSD). |
| 10 - 15 | System używa RAM tak długo, jak to możliwe. | Zalecane dla Homelab / eMMC. |
| 1 | Swap używany tylko w sytuacjach krytycznych. | Opcja "Safe" dla Dell Wyse. |
| 0 | Może całkowicie zablokować swapowanie. | Ryzykowne (może ubić procesy przy braku RAM). |

## 4. Instrukcja Zarządzania (CLI)

**Sprawdzenie aktualnej wartości**

```bash
cat /proc/sys/vm/swappiness
```

**Zmiana tymczasowa (do restartu)**

```bash
sudo sysctl vm.swappiness=1
```

**Zmiana trwała (konfiguracja systemowa)**

1. Edytuj plik konfiguracyjny:
```bash
sudo nano /etc/sysctl.conf
```
2. Dodaj/edytuj linię na końcu pliku:
```bash
vm.swappiness=1
```
3. Zastosuj zmiany bez restartu:
```bash
sudo sysctl -p
```

## 5. Troubleshooting

Jeśli po komendzie `sudo sysctl -p` wartość nadal wynosi 60, sprawdź czy inne pliki nie nadpisują konfiguracji:

```bash
ls /etc/sysctl.d/
```
> [!TIP]
> Warto również sprawdzić, czy nie są zainstalowane pakiety optymalizacyjne typu tuned, które mogą dynamicznie zmieniać te parametry.