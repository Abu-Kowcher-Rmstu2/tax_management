import os
import sys
from decimal import Decimal
import django
import pandas as pd

# Windows টার্মিনালে বাংলা টেক্সট প্রিন্ট করার জন্য UTF-8 কনফিগারেশন
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ১. জ্যাঙ্গো এনভায়রনমেন্ট সেটআপ
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tax_manager.settings')
django.setup()

from core.models import Taxpayer, ArrearRegister

def clean_decimal(value):
    """কমা যুক্ত বা স্ট্রিং মানকে সঠিক Decimale রূপান্তর করা"""
    if pd.isna(value) or value is None:
        return Decimal('0.00')
    val_str = str(value).replace(',', '').strip()
    if not val_str:
        return Decimal('0.00')
    try:
        return Decimal(val_str)
    except Exception:
        return Decimal('0.00')

def import_arrears_from_excel(file_path='arrear.xlsx'):
    if not os.path.exists(file_path):
        print(f"Error: '{file_path}' ফাইলটি খুঁজে পাওয়া যায়নি!")
        return

    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path, dtype=str)

    # কলামের হেডারগুলো ক্লিন করা (স্পেস বাদ দেওয়া ও লোয়ারকেস করা)
    df.columns = df.columns.str.strip().str.lower()
    df = df.fillna('')

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for index, row in df.iterrows():
        # হেডার ম্যাপিং
        raw_tin = str(row.get('tin', '')).strip()
        name = str(row.get('name', '')).strip()
        assessment_year = str(row.get('assesmentyear') or row.get('assessmentyear', '')).strip()

        # TIN ফরম্যাট ক্লিন করা
        if raw_tin.endswith('.0'):
            raw_tin = raw_tin[:-2]

        if not raw_tin or not assessment_year:
            skipped_count += 1
            continue

        # নিউমেরিক ফিল্ড পার্সিং (কমা রিমুভ সহ)
        demand = clean_decimal(row.get('demand'))
        fine = clean_decimal(row.get('fine'))
        collection = clean_decimal(row.get('collection'))

        # করদাতা ডাটাবেজে না থাকলে স্বয়ংক্রিয়ভাবে তৈরি করা হবে
        taxpayer, _ = Taxpayer.objects.get_or_create(
            tin=raw_tin,
            defaults={
                'name': name if name else f"Taxpayer {raw_tin}",
                'is_active': True,
            }
        )

        # বকেয়া ডাটা তৈরি বা আপডেট করা
        arrear, created = ArrearRegister.objects.update_or_create(
            taxpayer=taxpayer,
            assessment_year=assessment_year,
            defaults={
                'demand': demand,
                'fine': fine,
                'collection': collection,
            }
        )

        if created:
            created_count += 1
            print(f"[CREATED] TIN: {raw_tin} | করবর্ষ: {assessment_year} | বকেয়া: ৳{arrear.due_amount}")
        else:
            updated_count += 1
            print(f"[UPDATED] TIN: {raw_tin} | করবর্ষ: {assessment_year} | বকেয়া: ৳{arrear.due_amount}")

    print("\n--- Arrear Import Summary ---")
    print(f"Newly Created : {created_count}")
    print(f"Updated       : {updated_count}")
    print(f"Skipped       : {skipped_count}")
    print("-----------------------------")

if __name__ == '__main__':
    import_arrears_from_excel()
