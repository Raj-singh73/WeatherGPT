"""
view_database.py - Instant Database Inspector for WeatherGPT
Run this anytime to inspect all registered users and activity logs stored in your system's SQLite database.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "backend" / "data" / "weathergpt.db"

def format_date(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M:%S %p UTC")
    except Exception:
        return iso_str[:19]

def view_database():
    print("=" * 80)
    print("           WEATHERGPT SYSTEM DATABASE INSPECTOR (SQLite)")
    print(f" Database File: {DB_PATH}")
    print("=" * 80)

    if not DB_PATH.exists():
        print("[!] Database file has not been created yet.")
        print("    Start the backend server (python backend/main.py) to initialize it.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # 1. Registered Users
    users = conn.execute("""
        SELECT id, name, email, role, phone, district, village, primary_crop, created_at, last_login_at
        FROM users
        ORDER BY id ASC
    """).fetchall()

    print(f"\n[+] REGISTERED USERS ({len(users)} Total Saved in Your System):")
    print("-" * 80)
    if not users:
        print("  No registered accounts yet. Register on http://localhost:5173 to see data appear here!")
    else:
        for u in users:
            print(f"  * ID: {u['id']} | Name: {u['name']} ({u['role']})")
            print(f"    Email:      {u['email']}")
            print(f"    Phone:      {u['phone'] or 'Not provided'}")
            print(f"    Location:   {u['district'] or 'N/A'}" + (f" ({u['village']})" if u['village'] else ""))
            print(f"    Crop:       {u['primary_crop'] or 'N/A'}")
            print(f"    Created At: {format_date(u['created_at'])} (RECORD TIME)")
            print(f"    Last Login: {format_date(u['last_login_at'])}")
            print("-" * 80)

    # 2. Activity & Audit Logs
    logs = conn.execute("""
        SELECT id, action, user_email, details, timestamp
        FROM activity_logs
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    print(f"\n[+] RECENT SYSTEM ACTIVITY LOGS ({len(logs)} Latest Events):")
    print("-" * 80)
    if not logs:
        print("  No activity events recorded yet.")
    else:
        for l in logs:
            print(f"  [{l['action']}] {format_date(l['timestamp'])} | User: {l['user_email'] or 'System'}")
            if l['details']:
                print(f"    Details: {l['details']}")

    print("\n" + "=" * 80)
    conn.close()

if __name__ == "__main__":
    view_database()
