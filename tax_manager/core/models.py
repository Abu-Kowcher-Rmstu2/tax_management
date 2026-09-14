
# Create your models here.
from django.db import models
from django.utils import timezone

class Taxpayer(models.Model):
    tin = models.CharField(max_length=20, unique=True, verbose_name="TIN / ID")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    holding_or_circle = models.CharField(max_length=100, blank=True)

    # default="" এবং blank=True যোগ করা হয়েছে:
    address_line1 = models.CharField(max_length=255, default="", blank=True, verbose_name="House/Holding/Road/Village")
    address_line2 = models.CharField(max_length=150, default="", blank=True, verbose_name="Post Office & Post Code")
    address_line3 = models.CharField(max_length=150, default="", blank=True, verbose_name="Upazilla & District")

    is_active = models.BooleanField(default=True)

    def full_address(self):
        parts = [self.address_line1, self.address_line2, self.address_line3]
        return "\n".join([p for p in parts if p])

    def __str__(self):
        return f"{self.name} ({self.tin})"


# এই মডেলটি মিসিং ছিল, নিশ্চিত করুন এটি আছে:
class TaxAssessment(models.Model):
    """কর নির্ধারণ ও প্রারম্ভিক বকেয়া লেজার"""
    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="assessments")
    fiscal_year = models.CharField(max_length=9, help_text="e.g. 2025-2026")
    demanded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="নির্ধারিত চলতি দাবি")
    arrear_brought_forward = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="পূর্ববর্তী বকেয়া")

    class Meta:
        unique_together = ('taxpayer', 'fiscal_year')

    def __str__(self):
        return f"{self.taxpayer.tin} - {self.fiscal_year}"


class TaxTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('ADVANCE', 'Advance Tax (অগ্রিম কর)'),
        ('ARREAR', 'Arrear Tax (বকেয়া কর)'),
        ('REGULAR', 'Current Demand (চলতি কর)'),
        ('U/S 173','With Return(রিটার্ণের সাথে আদায়)'),
    ]
    PAYMENT_MODES = [
        ('CHALLAN', 'ট্রেজারি চালান (Treasury Challan)'),
        ('PAY_ORDER', 'পে-অর্ডার / ব্যাংক ড্রাফট'),
        ('ONLINE', 'ই-পেমেন্ট / এ-চালান (A-Challan)'),
        ('CASH', 'নগদ গ্রহণ (Cash)'),
    ]

    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="transactions")
    fiscal_year = models.CharField(max_length=9, help_text="e.g. 2025-2026")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    # receipt_no বাদ দেওয়া হয়েছে, এখন চালান নম্বরই প্রধান ট্র্যাকিং নম্বর
    challan_no = models.CharField(max_length=50, blank=True, verbose_name="চালান / ভাউচার নম্বর")
    challan_date = models.DateField(null=True, blank=True, verbose_name="চালানের তারিখ")
    payment_date = models.DateField(default=timezone.now, verbose_name="পরিশোধের তারিখ")

    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="আদায়ের পরিমাণ")
    payment_mode = models.CharField(max_length=15, choices=PAYMENT_MODES, default='CHALLAN')
    bank_and_branch = models.CharField(max_length=150, blank=True, verbose_name="ব্যাংক ও শাখার নাম")
    remarks = models.TextField(blank=True, verbose_name="মন্তব্য")
    created_at = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        ref = self.challan_no if self.challan_no else f"Txn-{self.id}"
        return f"{ref} - {self.taxpayer.name} (৳{self.amount})"

class TaxNotice(models.Model):
    NOTICE_TYPES = [
        ('ARREAR_DEMAND', 'Arrear Demand Notice'),
        ('ADVANCE_REMINDER', 'Advance Tax Reminder'),
        ('SHOW_CAUSE', 'Show Cause Notice'),
    ]

    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="notices")
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPES)
    reference_no = models.CharField(max_length=60, unique=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    arrear_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_served = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.reference_no} - {self.taxpayer.name}"



        from django.db import models

        class Taxpayer(models.Model):
            # Existing model reference
            tin = models.CharField(max_length=12, unique=True, verbose_name="টিআইএন")
            name = models.CharField(max_length=255, verbose_name="করদাতার নাম")
            # ... your existing fields ...

            def __str__(self):
                return f"{self.name} ({self.tin})"


class ArrearRegister(models.Model):
    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="arrears", verbose_name="করদাতা")
    assessment_year = models.CharField(max_length=9, verbose_name="করবর্ষ") # e.g., 2023-2024
    demand = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="দাবি (Demand)")
    fine = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="জরিমানা/সুদ (Fine)")
    total_arrear = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="মোট বকেয়া দাবি")
    collection = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="মোট আদায়")
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="অবশিষ্ট বকেয়া")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "বকেয়া কর রেজিস্টার"
        verbose_name_plural = "বকেয়া কর রেজিস্টারসমূহ"
        unique_together = ('taxpayer', 'assessment_year')

    def save(self, *args, **kwargs):
        self.total_arrear = self.demand + self.fine
        self.due_amount = self.total_arrear - self.collection
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.taxpayer.tin} - {self.assessment_year} (বকেয়া: {self.due_amount})"
