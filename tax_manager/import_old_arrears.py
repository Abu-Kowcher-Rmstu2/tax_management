import os
import django
import openpyxl
from decimal import Decimal

# Django পরিবেশ সেটআপ করুন
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tax_manager.settings')
django.setup()

from core.models import Taxpayer, OldArrearRegister

def import_old_arrears_from_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File path '{file_path}' not found!")
        return

    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    success_count = 0
    skipped_count = 0

    print("Import started...\n-------------------------------------------")

    # ২য় সারি থেকে ডাটা পড়া শুরু (১ম সারি হেডার ধরে)
    for row in sheet.iter_rows(min_row=2, values_only=True):
        tin = str(row[0]).strip() if row[0] is not None else ""
        name = str(row[1]).strip() if row[1] is not None else "Unknown Taxpayer"
        assessment_year = str(row[2]).strip() if row[2] is not None else ""
        demand = Decimal(str(row[3])) if row[3] is not None else Decimal('0.00')
        fine = Decimal(str(row[4])) if row[4] is not None else Decimal('0.00')
        collection = Decimal(str(row[6])) if row[6] is not None else Decimal('0.00')

        if not tin or not assessment_year:
            continue

        # করদাতা ডাটাবেজে আছে কিনা চেক করা, না থাকলে তৈরি করা
        taxpayer, created = Taxpayer.objects.get_or_create(
            tin=tin,
            defaults={'name': name, 'is_active': True}
        )

        if created:
            print(f"New taxpayer created: {tin}")

        # OldArrearRegister এ সেভ করা
        old_arrear, arrear_created = OldArrearRegister.objects.get_or_create(
            taxpayer=taxpayer,
            assessment_year=assessment_year,
            defaults={
                'demand': demand,
                'fine': fine,
                'collection': collection,
                'arrear_type': 'UNDISPUTED',
                'is_verified': False
            }
        )

        if arrear_created:
            success_count += 1
        else:
            old_arrear.demand = demand
            old_arrear.fine = fine
            old_arrear.collection = collection
            old_arrear.save()
            skipped_count += 1

    print("-------------------------------------------")
    print(f"Import completed! Newly added: {success_count}, Updated: {skipped_count}.")

if __name__ == '__main__':
    excel_file_name = 'old_arrear_list.xlsx'  # আপনার এক্সেল ফাইলের নাম
    import_old_arrears_from_excel(excel_file_name)
