# Japan-Reise Dashboard 2026

Web-basiertes Tracking-Dashboard für unsere Japan-Reise (27. Sep – 15. Okt 2026).

🔗 **Live-Dashboard**: https://hakimanshermes.github.io/japan-dashboard/japan-tracker.html

## Features

- **Countdown** bis Reisestart
- **Fortschrittsübersicht** aller Aufgaben (66+ Tasks)
- **Offene Aufgaben** mit Filter & Suche
- **Budget-Tracking** in CHF und JPY
- **Blocker-Liste** für kritische Hindernisse
- **Deadline-Timeline**
- **Git-History** – Versionsverlauf direkt im Dashboard
- **GitHub-Integration** – Link zu Repositories & Commits
- **Responsive** – Mobil & Desktop

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `japan-tracker.html` | Das Dashboard selbst (Dark-Theme, 3 Tabs ) |
| `japan-dashboard-generator.py` | Python-Generator parst Vault-Daten und erzeugt JSON |
| `japan-dashboard-data.json` | Generierte Daten für das Dashboard |
| `README.md` | Diese Datei |

## Tabs

1. **Dashboard** – Übersicht mit Countdown, Progress, Budget, Blocker, Deadlines, Kategorien
2. **Aufgaben** – Alle 66+ Aufgaben mit Filter (Suche, Status, Kategorie, Priorität)
3. **Verlauf** – Letzte Git-Commits, geänderte Dateien, uncommitted Changes

## Aktualisierung

```bash
# Parst Vault-Daten neu und erzeugt JSON
python3 japan-dashboard-generator.py

# Dann commiten & pushen
git add japan-dashboard-data.json
git commit -m "Update Dashboard-Daten"
git push
```

## Datenquellen

- Obsidian Vault: `02 Projekte/Japan 2026/Japan 2026 - To-dos.md`
- Obsidian Vault: `02 Projekte/Japan 2026/Japan 2026 - Budget.md`
- Git-History des Vault-Ordners

---
*Erstellt von Jacek & Kimi. Letzte Update: 25. Mai 2026*
