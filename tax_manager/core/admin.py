from django.contrib import admin
from .models import Taxpayer, TaxAssessment, TaxTransaction, TaxNotice,ArrearRegister

@admin.register(Taxpayer)
class TaxpayerAdmin(admin.ModelAdmin):
    list_display = ('tin', 'name', 'phone', 'holding_or_circle', 'address_line2', 'address_line3', 'is_active')
    search_fields = ('tin', 'name', 'phone', 'holding_or_circle', 'address_line1', 'address_line2', 'address_line3')
    list_filter = ('is_active', 'holding_or_circle')

@admin.register(TaxTransaction)
class TaxTransactionAdmin(admin.ModelAdmin):
    # 'receipt_no' সরিয়ে 'challan_no' বসানো হয়েছে:
    list_display = ('challan_no', 'taxpayer', 'transaction_type', 'amount', 'challan_date', 'payment_date', 'payment_mode')
    list_filter = ('transaction_type', 'payment_mode', 'fiscal_year', 'payment_date')
    search_fields = ('challan_no', 'taxpayer__name', 'taxpayer__tin')
    date_hierarchy = 'payment_date'

@admin.register(TaxAssessment)
class TaxAssessmentAdmin(admin.ModelAdmin):
    list_display = ('taxpayer', 'fiscal_year', 'demanded_amount', 'arrear_brought_forward')
    list_filter = ('fiscal_year',)
    search_fields = ('taxpayer__tin', 'taxpayer__name')

@admin.register(TaxNotice)
class TaxNoticeAdmin(admin.ModelAdmin):
    list_display = ('reference_no', 'taxpayer', 'notice_type', 'arrear_amount', 'issue_date', 'due_date', 'is_served')
    list_filter = ('notice_type', 'is_served')
    search_fields = ('reference_no', 'taxpayer__tin', 'taxpayer__name')

from django.contrib import admin
from .models import NoticeSetting

@admin.register(NoticeSetting)
class NoticeSettingAdmin(admin.ModelAdmin):
    list_display = ('officer_name', 'designation', 'sender_circle', 'phone_number', 'is_active')
    list_editable = ('is_active',)
    from django.contrib import admin
    from .models import ArrearRegister

@admin.register(ArrearRegister)
class ArrearRegisterAdmin(admin.ModelAdmin):
    # টেবিলে প্রদর্শিত ফিল্ডসমূহ
    list_display = (
        'get_tin',
        'get_taxpayer_name',
        'assessment_year',
        'demand',
        'fine',
        'total_arrear',
        'collection',
        'due_amount',
        'created_at',
    )

    # করবর্ষ অনুযায়ী ফিল্টারিং সাইডবার
    list_filter = ('assessment_year', 'created_at')

    # TIN ও করদাতার নাম দিয়ে সার্চ করার সুবিধা
    search_fields = ('taxpayer__tin', 'taxpayer__name', 'assessment_year')

    # স্বয়ংক্রিয়ভাবে ক্যালকুলেট হওয়া ফিল্ডগুলো যাতে অ্যাডমিন থেকে সরাসরি বিকৃত না করা যায়
    readonly_fields = ('total_arrear', 'due_amount', 'created_at', 'updated_at')

    # ড্রপডাউনে হাজার হাজার করদাতার পরিবর্তে সার্চেবল ইনপুট বক্স
    autocomplete_fields = ['taxpayer']

    ordering = ('-created_at',)

    # কাস্টম মেথড: TIN ও করদাতার নাম প্রদর্শনের জন্য
    @admin.display(description='টিআইএন (TIN)', ordering='taxpayer__tin')
    def get_tin(self, obj):
        return obj.taxpayer.tin

    @admin.display(description='করদাতার নাম', ordering='taxpayer__name')
    def get_taxpayer_name(self, obj):
        return obj.taxpayer.name
