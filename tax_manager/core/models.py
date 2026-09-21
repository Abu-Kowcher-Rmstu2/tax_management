from django.db import models
from django.utils import timezone

class Taxpayer(models.Model):
    tin = models.CharField(max_length=20, unique=True, verbose_name="TIN / ID")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    holding_or_circle = models.CharField(max_length=100, blank=True)

    address_line1 = models.CharField(max_length=255, default="", blank=True, verbose_name="House/Holding/Road/Village")
    address_line2 = models.CharField(max_length=150, default="", blank=True, verbose_name="Post Office & Post Code")
    address_line3 = models.CharField(max_length=150, default="", blank=True, verbose_name="Upazilla & District")

    is_active = models.BooleanField(default=True)

    def full_address(self):
        parts = [self.address_line1, self.address_line2, self.address_line3]
        return "\n".join([p for p in parts if p])

    def __str__(self):
        return f"{self.name} ({self.tin})"


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
        ('U/S 173', 'With Return (রিটার্ণের সাথে আদায়)'),
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


class ArrearRegister(models.Model):
    ARREAR_TYPE_CHOICES = [
        ('UNDISPUTED', 'অবিসংবাদিত (Undisputed)'),
        ('DISPUTED', 'বিসংবাদিত (Disputed)'),
    ]

    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="arrears", verbose_name="করদাতা")
    assessment_year = models.CharField(max_length=9, verbose_name="করবর্ষ")

    arrear_type = models.CharField(
        max_length=15,
        choices=ARREAR_TYPE_CHOICES,
        default='UNDISPUTED',
        verbose_name="বকেয়ার ধরন (Arrear Type)"
    )
    disposal_section = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="নিষ্পত্তির ধারা (Disposal Section)",
        help_text="যেমন: ধারা ২৭৫, ধারা ২২১(৩), আপিল/ট্রাইব্যুনাল ইত্যাদি"
    )
    disposal_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="নিষ্পত্তির তারিখ (Disposal Date)",
        help_text="দাবি নিষ্পত্তি বা আদেশের তারিখ"
    )

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
        return f"{self.taxpayer.tin} - {self.assessment_year} ({self.get_arrear_type_display()}) - বকেয়া: {self.due_amount}"


class NoticeSetting(models.Model):
    govt_title = models.CharField(max_length=255, default="গণপ্রজাতন্ত্রী বাংলাদেশ সরকার", verbose_name="সরকারের নাম")
    office_title = models.CharField(max_length=255, default="উপ কর কমিশনারের কার্যালয়", verbose_name="কার্যালয়ের নাম")
    circle_line = models.CharField(max_length=255, default="সার্কেল-১৩ (ফেনী সদর), কর অঞ্চল-নোয়াখালী।", verbose_name="সার্কেল ও অঞ্চল")
    office_address = models.CharField(max_length=500, default="৩৪২/১, ফরিদা কুদ্দুস নিবাস, কুমিল্লা বাসস্ট্যান্ড, ট্রাংক রোড, ফেনী সদর, ফেনী।", verbose_name="কার্যালয়ের ঠিকানা")

    officer_name = models.CharField(max_length=150, default="আব্দুল হক", verbose_name="কর্মকর্তার নাম")
    designation = models.CharField(max_length=150, default="উপকর কমিশনার", verbose_name="পদবী")
    sender_circle = models.CharField(max_length=150, default="সার্কেল-১৩ (ফেনী সদর)", verbose_name="সার্কেল")
    sender_zone = models.CharField(max_length=150, default="কর অঞ্চল- নোয়াখালী।", verbose_name="অঞ্চল")
    phone_number = models.CharField(max_length=50, default="০২৩৩৪৪-৭৩৬০০", verbose_name="ফোন নম্বর")
    is_active = models.BooleanField(default=True, verbose_name="সক্রিয় কনফিগারেশন")

    class Meta:
        verbose_name = "নোটিশ প্যাড ও প্রেরক সেটিংস"
        verbose_name_plural = "নোটিশ প্যাড ও প্রেরক সেটিংস"

    def __str__(self):
        return f"{self.officer_name} - {self.designation} ({self.sender_circle})"




class AdvanceTaxRegister(models.Model):
    INSTALLMENT_CHOICES = [
        ('1ST', '1st Installment (১ম কিস্তি - ১৫ সেপ্টেম্বর)'),
        ('2ND', '2nd Installment (২য় কিস্তি - ১৫ ডিসেম্বর)'),
        ('3RD', '3rd Installment (৩য় কিস্তি - ১৫ মার্চ)'),
        ('4TH', '4th Installment (৪র্থ কিস্তি - ১৫ জুন)'),
    ]

    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="advance_taxes", verbose_name="করদাতা")
    fiscal_year = models.CharField(max_length=9, default="2027-2028", verbose_name="করবর্ষ / অর্থবছর")
    installment = models.CharField(max_length=5, choices=INSTALLMENT_CHOICES, verbose_name="কিস্তি (Installment)")
    payment_date = models.DateField(default=timezone.now, verbose_name="পরিশোধের তারিখ")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="পরিশোধিত অগ্রিম কর (৳)")
    challan_no = models.CharField(max_length=60, verbose_name="চালান / ট্রানজেকশন নম্বর")
    challan_date = models.DateField(verbose_name="চালানের তারিখ")
    remarks = models.TextField(blank=True, verbose_name="মন্তব্য")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "অগ্রিম কর রেজিস্টার"
        verbose_name_plural = "অগ্রিম কর রেজিস্টারসমূহ"
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.taxpayer.name} ({self.taxpayer.tin}) - {self.get_installment_display()} - ৳{self.paid_amount}"
