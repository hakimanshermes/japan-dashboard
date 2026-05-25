#!/usr/bin/env python3
"""
japan-dashboard-generator.py

Parst Vault-Daten (To-dos, Budget, Git-History) und erzeugt
japan-dashboard-data.json für den Japan-Reise-Tracker iframe.

Usage:
    python3 japan-dashboard-generator.py
    # -> schreibt japan-dashboard-data.json ins selbe Verzeichnis

Quellen:
    - /home/root/mein-sync-ordner/Documents/02 Projekte/Japan 2026/Japan 2026 - To-dos.md
    - /home/root/mein-sync-ordner/Documents/02 Projekte/Japan 2026/Japan 2026 - Budget.md
    - Git-Repo unter /home/root/mein-sync-ordner/Documents
"""

import json
import os
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

# ─── Konfiguration ───────────────────────────────────────────────────────────

VAULT_ROOT = Path("/home/root/mein-sync-ordner/Documents")
OUTPUT_DIR = Path(__file__).parent.resolve()
GITHUB_OWNER = "hakimanshermes"
GITHUB_REPO  = "japan-dashboard"
GITHUB_PATH  = ""  # Dieses Repo IST das Japan-Dashboard

JAPAN_2026_PATH = VAULT_ROOT / "02 Projekte" / "Japan 2026"
TODOS_FILE      = JAPAN_2026_PATH / "Japan 2026 - To-dos.md"
BUDGET_FILE     = JAPAN_2026_PATH / "Japan 2026 - Budget.md"

REISE_START = date(2026, 9, 27)
REISE_ENDE  = date(2026, 10, 15)

# Status-Mapping
STATUS_MAP = {"✅": "erledigt", "⬜": "offen", "❌": "blockiert", "": "offen"}

# ─── Git-History ─────────────────────────────────────────────────────────────

def run_git(args, cwd=None):
    if cwd is None:
        cwd = OUTPUT_DIR  # Liest Git vom japan-dashboard-Repo
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""

def get_git_commits(limit=10):
    """Letzte N Commits des japan-dashboard-Repos"""
    log = run_git([
        "log", f"--max-count={limit}", "--format=%H|%ci|%an|%s",
    ])
    commits = []
    for line in log.splitlines():
        parts = line.split("|", maxsplit=3)
        if len(parts) != 4:
            continue
        sha, ts, author, msg = parts
        commits.append({
            "sha": sha[:7],
            "sha_full": sha,
            "date": ts[:10],
            "datetime": ts,
            "author": author,
            "message": msg,
        })
    return commits

def get_git_changed_files():
    """Letzte geänderte Dateien"""
    files = run_git([
        "diff", "--name-only", "HEAD~1"
    ])
    return [f for f in files.splitlines() if f.strip()]

def get_git_uncommitted():
    """Uncommitted Changes"""
    status = run_git([
        "status", "--short"
    ])
    return [line for line in status.splitlines() if line.strip()]

def get_git_activity(days=14):
    """Commit-Histogramm der letzten N Tage"""
    log = run_git([
        "log", f"--since={days} days ago", "--format=%ad",
        "--date=short"
    ])
    dates = [line.strip() for line in log.splitlines() if line.strip()]
    histogram = {}
    for d in dates:
        histogram[d] = histogram.get(d, 0) + 1
    return histogram

def get_total_commits():
    """Gesamtzahl Commits"""
    out = run_git([
        "rev-list", "--count", "HEAD"
    ])
    try:
        return int(out.strip())
    except (ValueError, TypeError):
        return 0

# ─── GitHub-API (optional) ───────────────────────────────────────────────────

def get_github_commits(limit=10):
    """Versucht GitHub API für Commits"""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None
    import urllib.request
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits"
    query = f"?per_page={limit}"
    req = urllib.request.Request(url + query)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            commits = []
            for item in data:
                commits.append({
                    "sha": item["sha"][:7],
                    "sha_full": item["sha"],
                    "date": item["commit"]["committer"]["date"][:10],
                    "datetime": item["commit"]["committer"]["date"],
                    "author": item["commit"]["committer"]["name"],
                    "message": item["commit"]["message"].splitlines()[0],
                })
            return commits
    except Exception:
        return None

# ─── To-dos Parsing ──────────────────────────────────────────────────────────

def parse_todos(filepath):
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    tasks = []
    current_section = ""

    for line in lines:
        line = line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue

        if not line.startswith("|") or "---" in line:
            continue

        # Robuster Split an |, ignoriert leere Zellen am Anfang/Ende
        parts = [p.strip() for p in line.split("|")]
        # Filtere leere Zellen am Anfang/Ende
        while parts and not parts[0]:
            parts.pop(0)
        while parts and not parts[-1]:
            parts.pop()

        if len(parts) < 5:
            continue
        if "Aufgabe" in parts[0]:
            continue
        if "status" in parts[0].lower():
            continue

        aufgabe = parts[0]
        status_raw = parts[1] if len(parts) > 1 else "⬜"
        prio_raw   = parts[2] if len(parts) > 2 else ""
        zeitfenster= parts[3] if len(parts) > 3 else ""
        notizen    = parts[4] if len(parts) > 4 else ""

        if not re.search(r"[a-zA-Z0-9öäüÖÄÜß]", aufgabe):
            continue  # nur Header-Zeile/Abfall

        status = STATUS_MAP.get(status_raw, "offen")
        prioritaet = "niedrig"
        if "🔴" in prio_raw or "rot" in prio_raw.lower() or "hoch" in prio_raw.lower():
            prioritaet = "hoch"
        elif "🟡" in prio_raw or "mittel" in prio_raw.lower():
            prioritaet = "mittel"

        deadline = None
        dl_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", zeitfenster)
        if not dl_match and "07.2026" in zeitfenster:
            deadline = "2026-07-27"
        elif not dl_match and "03.09." in zeitfenster:
            deadline = "2026-09-03"
        elif dl_match:
            d, m, y = dl_match.groups()
            deadline = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

        # Kategorie aus Abschnitt extrahieren
        kat_map = {
            "Kritisch / früh erledigen": "hotels_buchungen",
            "Ausrüstung / Vorbereitung": "ausruestung",
            "Gepäck / Logistik": "gepaeck_logistik",
            "Transfers / Verkehr": "transport_bahn",
            "Route / Programm-Entscheidungen": "route_programm",
            "Einreise / Zoll / Flughafen": "einreise_zoll",
            "Dokumente / Finanzen / Sicherheit": "dokumente_sicherheit",
            "Neue Lücken aus Audit": "dokumente_sicherheit",
        }
        kategorie = "dokumente_sicherheit"
        for prefix, k in kat_map.items():
            if prefix in current_section:
                kategorie = k
                break

        tasks.append({
            "id": f"J-{len(tasks)+1:03d}",
            "aufgabe": aufgabe,
            "kategorie": kategorie,
            "status": status,
            "prioritaet": prioritaet,
            "zeitfenster": zeitfenster,
            "deadline": deadline,
            "notizen": notizen,
            "zustaendig": "Adam",
            "ursprungDatei": str(filepath.relative_to(VAULT_ROOT)),
        })

    return tasks

    # Zusätzlich: manuell gefundete Kritische-Blocker aus der Überschriftzeile ergänzen
    critical = []
    # Zählen der Status
    return tasks

def count_by_status(tasks):
    erledigt = sum(1 for t in tasks if t["status"] == "erledigt")
    offen = sum(1 for t in tasks if t["status"] == "offen")
    blockiert = sum(1 for t in tasks if t["status"] == "blockiert")
    # Hochpriorisierte offene
    hoch_offen = [t for t in tasks if t["prioritaet"] == "hoch" and t["status"] in ("offen", "blockiert")]
    return {
        "erledigt": erledigt,
        "offen": offen,
        "blockiert": blockiert,
        "gesamt": len(tasks),
        "gesamtProzent": round(100 * erledigt / len(tasks), 1) if len(tasks) else 0,
        "hoch_offen": hoch_offen,
    }

def count_by_priority(tasks):
    hoch = sum(1 for t in tasks if t["prioritaet"] == "hoch")
    mittel = sum(1 for t in tasks if t["prioritaet"] == "mittel")
    niedrig = sum(1 for t in tasks if t["prioritaet"] == "niedrig")
    return {"hoch": hoch, "mittel": mittel, "niedrig": niedrig}

def count_by_kategorie(tasks):
    kats = {}
    for t in tasks:
        k = t["kategorie"]
        if k not in kats:
            kats[k] = {"gesamt": 0, "erledigt": 0, "offen": 0, "blockiert": 0}
        kats[k]["gesamt"] += 1
        if t["status"] in kats[k]:
            kats[k][t["status"]] += 1
    return kats

def get_next_deadlines(tasks, limit=5):
    now = date.today()
    deadlines = []
    for t in tasks:
        if t["deadline"] and t["status"] in ("offen", "blockiert"):
            try:
                d = date.fromisoformat(t["deadline"])
                days = (d - now).days
                deadlines.append({
                    "datum": t["deadline"],
                    "aufgabe": t["aufgabe"],
                    "kategorie": t["kategorie"],
                    "tageVerbleibend": days,
                })
            except (ValueError, TypeError):
                continue
    deadlines.sort(key=lambda x: x["tageVerbleibend"])
    return deadlines[:limit]

# ─── Budget Parsing ──────────────────────────────────────────────────────────

def parse_budget(filepath):
    text = filepath.read_text(encoding="utf-8")
    # Suche nach Gesamt-Zahlen in Budget-Tabellen
    total_match = re.search(r"\|\s*\*\*Gesamt\*\*.*\*\*¥([\d,.]+)\*\*", text)
    gesamt = 0
    if total_match:
        raw = total_match.group(1).replace(".", "").replace(",", "")
        try:
            gesamt = int(raw)
        except ValueError:
            gesamt = 0

    return {
        "gesamtkostenJPY": gesamt,
        "gesamtkostenEUR": round(gesamt / 184.71, 2) if gesamt else 0,
        "unbezahltJPY": 0,
        "unbezahltEUR": 0,
        "status": "im_limit",
        "anmerkung": "Nur Tagesbudget-Eintritte+Essen; Hotels separat bezahlt/pauschal"
    }

# ─── Generator ───────────────────────────────────────────────────────────────

def generate():
    tasks = parse_todos(TODOS_FILE)
    counts = count_by_status(tasks)
    prio_counts = count_by_priority(tasks)
    kat_counts = count_by_kategorie(tasks)
    deadlines = get_next_deadlines(tasks)
    budget = parse_budget(BUDGET_FILE)

    git_commits = get_git_commits(limit=10)
    gh_commits = get_github_commits(limit=10)
    commits = gh_commits if gh_commits is not None else git_commits
    commits_source = "github_api" if gh_commits is not None else "git_local"

    changed_files = get_git_changed_files()
    uncommitted = get_git_uncommitted()
    activity = get_git_activity()
    total_commits = get_total_commits()

    heute = date.today()
    tage_bis = (REISE_START - heute).days

    data = {
        "_meta": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "generatorVersion": "1.2.0",
            "commitsSource": commits_source,
        },
        "reiseStart": REISE_START.isoformat(),
        "reiseEnde": REISE_ENDE.isoformat(),
        "tageBisReise": tage_bis,
        "progress": {
            "gesamtAufgaben": counts["gesamt"],
            "erledigt": counts["erledigt"],
            "offen": counts["offen"],
            "blockiert": counts["blockiert"],
            "gesamtProzent": counts["gesamtProzent"],
            "prioHoch": prio_counts["hoch"],
            "prioMittel": prio_counts["mittel"],
            "prioNiedrig": prio_counts["niedrig"],
        },
        "kategorien": kat_counts,
        "blocker": counts["hoch_offen"][:6],
        "deadlines": deadlines,
        "budget": budget,
        "git": {
            "commits": commits,
            "totalCommits": total_commits,
            "changedFiles": changed_files,
            "uncommittedCount": len(uncommitted),
            "uncommittedDetails": uncommitted,
            "activity": activity,
            "githubUrl": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/commits/main/{GITHUB_PATH.replace(' ', '%20')}",
            "repoUrl": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}",
        },
        "tasks": [t for t in tasks if t["status"] != "erledigt"],
    }

    output = OUTPUT_DIR / "japan-dashboard-data.json"
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ {output}")
    print(f"   Tasks: {counts['gesamt']} | Erledigt: {counts['erledigt']} | Offen: {counts['offen']}")
    print(f"   Commits ({commits_source}): {len(commits)} letzte geladen")
    print(f"   Hochpriorisiert offen: {len(counts['hoch_offen'])}")
    print(f"   Uncommitted Changes: {len(uncommitted)}")

if __name__ == "__main__":
    generate()
