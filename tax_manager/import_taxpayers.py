import os
import sys
import django
import pandas as pd

# Force standard output to UTF-8 to handle Bengali characters in Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tax_manager.settings')
django.setup()

from core.models import Taxpayer

def import_taxpayers_from_excel(file_path='taxpayers.xlsx'):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found in the current directory.")
        return

    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path, dtype=str)

    df.columns = df.columns.str.strip().str.lower()
    df = df.fillna('')

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for index, row in df.iterrows():
        raw_tin = str(row.get('tin', '')).strip()
        name = str(row.get('name', '')).strip()
        phone = str(row.get('phone', '')).strip()
        email = str(row.get('email', '')).strip()
        circle = str(row.get('circle', '')).strip()
        addr1 = str(row.get('addr1', '')).strip()
        addr2 = str(row.get('addr2', '')).strip()
        addr3 = str(row.get('addr3', '')).strip()

        if circle.endswith('.0'):
            circle = circle[:-2]
        if raw_tin.endswith('.0'):
            raw_tin = raw_tin[:-2]
        if phone.endswith('.0'):
            phone = phone[:-2]

        if not raw_tin:
            skipped_count += 1
            continue

        taxpayer, created = Taxpayer.objects.update_or_create(
            tin=raw_tin,
            defaults={
                'name': name,
                'phone': phone,
                'email': email,
                'holding_or_circle': circle,
                'address_line1': addr1,
                'address_line2': addr2,
                'address_line3': addr3,
                'is_active': True,
            }
        )

        if created:
            created_count += 1
            print(f"[CREATED] {raw_tin} - {name}")
        else:
            updated_count += 1
            print(f"[UPDATED] {raw_tin} - {name}")

    print("\n--- Import Summary ---")
    print(f"Newly Created : {created_count}")
    print(f"Updated       : {updated_count}")
    print(f"Skipped (No TIN): {skipped_count}")
    print("----------------------")

if __name__ == '__main__':
    import_taxpayers_from_excel()
