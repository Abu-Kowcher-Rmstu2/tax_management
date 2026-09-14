from django.contrib import admin
from .models import Taxpayer, TaxAssessment, TaxTransaction, TaxNotice

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
