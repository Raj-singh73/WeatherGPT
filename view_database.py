"""
view_database.py - Visual Table & Database Inspector for WeatherGPT
Generates a real formatted terminal grid table, an HTML visual table, and an Excel CSV file.
"""

import sqlite3
import os
import csv
import webbrowser
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "backend" / "data" / "weathergpt.db"
CSV_PATH = BASE_DIR / "backend" / "data" / "registered_users.csv"
HTML_PATH = BASE_DIR / "database_table.html"

def format_date(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return iso_str[:19]

def render_box_table(headers, rows):
    """Renders an ASCII grid table with borders compatible with all Windows shells."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    sep_line = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    lines = [sep_line]
    # Header row
    hdr_cells = [f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)]
    lines.append("|" + "|".join(hdr_cells) + "|")
    lines.append(sep_line)

    if not rows:
        empty_msg = " No registered records in database yet. "
        total_w = sum(col_widths) + (3 * len(col_widths)) - 1
        lines.append(f"|{empty_msg:<{total_w}}|")
    else:
        for row in rows:
            cells = [f" {str(row[i]):<{col_widths[i]}} " for i in range(len(headers))]
            lines.append("|" + "|".join(cells) + "|")

    lines.append(sep_line)
    return "\n".join(lines)

def export_csv_and_html(users, logs):
    """Exports to Excel CSV and Visual HTML table."""
    # 1. Export CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Email", "Role", "Phone", "District", "Village", "Primary Crop", "Created At (Record Time)", "Last Login"])
        for u in users:
            writer.writerow([
                u["id"], u["name"], u["email"], u["role"], u["phone"] or "",
                u["district"] or "", u["village"] or "", u["primary_crop"] or "",
                format_date(u["created_at"]), format_date(u["last_login_at"])
            ])

    # 2. Export HTML
    user_rows_html = ""
    for u in users:
        user_rows_html += f"""
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition">
            <td class="p-3 font-mono font-bold text-slate-500">{u['id']}</td>
            <td class="p-3 font-bold text-slate-900">{u['name']}</td>
            <td class="p-3 text-slate-600">{u['email']}</td>
            <td class="p-3"><span class="px-2.5 py-1 rounded-full text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200">{u['role']}</span></td>
            <td class="p-3 text-slate-700">{u['phone'] or '—'}</td>
            <td class="p-3 font-medium text-slate-800">{u['district'] or '—'}{' (' + u['village'] + ')' if u['village'] else ''}</td>
            <td class="p-3 font-bold text-emerald-700">{u['primary_crop'] or '—'}</td>
            <td class="p-3 font-mono text-xs text-slate-600 bg-slate-50/50">{format_date(u['created_at'])}</td>
            <td class="p-3 font-mono text-xs text-slate-600">{format_date(u['last_login_at'])}</td>
        </tr>
        """

    log_rows_html = ""
    for l in logs:
        badge_cls = "bg-emerald-100 text-emerald-800" if l['action'] == "REGISTER" else "bg-sky-100 text-sky-800"
        log_rows_html += f"""
        <tr class="border-b border-slate-100 text-xs hover:bg-slate-50">
            <td class="p-2.5"><span class="px-2 py-0.5 rounded font-extrabold uppercase text-[10px] {badge_cls}">{l['action']}</span></td>
            <td class="p-2.5 font-mono text-slate-500">{format_date(l['timestamp'])}</td>
            <td class="p-2.5 font-semibold text-slate-800">{l['user_email'] or 'System'}</td>
            <td class="p-2.5 text-slate-600">{l['details'] or ''}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeatherGPT — Live System Database Table</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-100 text-slate-900 min-h-screen p-4 sm:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header Card -->
        <div class="bg-gradient-to-r from-slate-900 via-sky-950 to-blue-900 text-white rounded-3xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <span class="text-[10px] font-extrabold uppercase tracking-widest bg-sky-500/20 text-sky-300 border border-sky-400/30 px-2.5 py-1 rounded-full">
                    SQLite Database Table
                </span>
                <h1 class="text-2xl sm:text-3xl font-black tracking-tight mt-2 text-white">WeatherGPT Registered Users</h1>
                <p class="text-xs text-sky-200/80 mt-1">Database Location: <code class="bg-white/10 px-2 py-0.5 rounded font-mono text-sky-200">{DB_PATH}</code></p>
            </div>
            <div class="flex items-center gap-3">
                <div class="bg-white/10 px-4 py-2 rounded-2xl backdrop-blur-xs text-center">
                    <span class="text-xs text-sky-200 block">Total Users</span>
                    <span class="text-2xl font-black text-white">{len(users)}</span>
                </div>
                <button onclick="location.reload()" class="bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs px-4 py-3 rounded-2xl shadow-lg transition cursor-pointer">
                    🔄 Refresh Table
                </button>
            </div>
        </div>

        <!-- USERS SPREADSHEET TABLE -->
        <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
                <h2 class="font-extrabold text-sm text-slate-800 uppercase tracking-wider">Registered Accounts ({len(users)})</h2>
                <span class="text-xs text-slate-500">Live Sync from SQLite</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-100 text-[11px] font-extrabold text-slate-600 uppercase tracking-wider border-b border-slate-200">
                        <tr>
                            <th class="p-3">ID</th>
                            <th class="p-3">Full Name</th>
                            <th class="p-3">Email Address</th>
                            <th class="p-3">Role / Persona</th>
                            <th class="p-3">Phone</th>
                            <th class="p-3">Location</th>
                            <th class="p-3">Crop</th>
                            <th class="p-3">Created At (Record Time)</th>
                            <th class="p-3">Last Login</th>
                        </tr>
                    </thead>
                    <tbody>
                        {user_rows_html if users else '<tr><td colspan="9" class="p-8 text-center text-slate-400">No registered users in database yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- AUDIT LOGS TABLE -->
        <div class="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 bg-slate-50/70">
                <h2 class="font-extrabold text-sm text-slate-800 uppercase tracking-wider">Telemetry & Audit Activity Logs</h2>
            </div>
            <div class="overflow-x-auto max-h-72">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-100 text-[11px] font-extrabold text-slate-600 uppercase tracking-wider border-b border-slate-200">
                        <tr>
                            <th class="p-2.5">Action</th>
                            <th class="p-2.5">Timestamp</th>
                            <th class="p-2.5">User Email</th>
                            <th class="p-2.5">Activity Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {log_rows_html if logs else '<tr><td colspan="4" class="p-6 text-center text-slate-400">No activity events recorded yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</body>
</html>
"""
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    if not DB_PATH.exists():
        print(f"[!] Database file does not exist at: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    users = [dict(r) for r in conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()]
    logs = [dict(r) for r in conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 20").fetchall()]
    conn.close()

    # 1. Print formatted Box Table to console
    print("\n" + "=" * 95)
    print("                     WEATHERGPT REGISTERED USERS DATABASE TABLE")
    print(f" Database File: {DB_PATH}")
    print("=" * 95)

    headers = ["ID", "Full Name", "Email", "Role", "Phone", "Location", "Crop", "Created At (Record Time)"]
    rows = []
    for u in users:
        rows.append([
            u["id"],
            u["name"][:16],
            u["email"],
            u["role"][:12],
            u["phone"] or "—",
            (u["district"] or "—") + (f" ({u['village']})" if u["village"] else ""),
            u["primary_crop"] or "—",
            format_date(u["created_at"])
        ])

    print(render_box_table(headers, rows))

    # 2. Export HTML and CSV
    export_csv_and_html(users, logs)
    print(f"\n[+] Created Visual HTML Table: {HTML_PATH}")
    print(f"[+] Created Spreadsheet CSV:   {CSV_PATH}")

    # 3. Open HTML Table in default browser
    try:
        webbrowser.open(HTML_PATH.as_uri())
        print("[+] Opened visual table in your browser!")
    except Exception as e:
        print(f"[-] Could not launch browser automatically: {e}")

    print("=" * 95 + "\n")

if __name__ == "__main__":
    main()
