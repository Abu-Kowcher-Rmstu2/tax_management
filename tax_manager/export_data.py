import os
import django
from django.core.management import call_command

# এখানে আপনার জ্যাঙ্গো সেটিংস মডিউলের সঠিক পাথ দিন (যেমন: tax_manager.settings)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tax_manager.settings')
django.setup()

# UTF-8 এনকোডিং নিশ্চিত করে dumpdata চালানো
with open('datadump.json', 'w', encoding='utf-8') as f:
    call_command(
        'dumpdata',
        natural_foreign=True,
        natural_primary=True,
        exclude=['contenttypes', 'auth.permission'],
        indent=4,
        stdout=f
    )

print("সফলভাবে সমস্ত ডাটা 'datadump.json' ফাইলে এক্সপোর্ট করা হয়েছে!")
