import time
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse

from .models import (
    Taxpayer,
    TaxTransaction,
    TaxNotice,
    TaxAssessment,
    ArrearRegister,
    NoticeSetting,
    AdvanceTaxRegister,
)


# Helper function to convert English digits to Bengali digits
def to_bengali_digits(number):
    if number is None:
        return ""
    en_to_bn = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    return str(number).translate(en_to_bn)


# ------------------------------------------------------------------
# Auth Views
# ------------------------------------------------------------------
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        user = authenticate(request, username=user_name, password=pass_word)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'ইউজারনেম অথবা পাসওয়ার্ড সঠিক নয়।')

    return render(request, 'core/home.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------
@login_required(login_url='home')
def dashboard_view(request):
    total_taxpayers = Taxpayer.objects.filter(is_active=True).count()

    total_advance_tax = TaxTransaction.objects.filter(
        transaction_type='ADVANCE'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_arrear_collected = TaxTransaction.objects.filter(
        transaction_type='ARREAR'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_arrear_demand = TaxAssessment.objects.aggregate(
        total=Sum('arrear_brought_forward')
    )['total'] or Decimal('0.00')

    net_arrear_due = max(0.00, float(total_arrear_demand) - float(total_arrear_collected))
    pending_notices_count = TaxNotice.objects.filter(is_served=False).count()

    recent_transactions = TaxTransaction.objects.select_related('taxpayer').order_by('-payment_date')[:5]
    recent_notices = TaxNotice.objects.select_related('taxpayer').order_by('-issue_date')[:5]

    context = {
        'total_taxpayers': total_taxpayers,
        'total_advance_tax': total_advance_tax,
        'total_arrear_collected': total_arrear_collected,
        'net_arrear_due': net_arrear_due,
        'pending_notices_count': pending_notices_count,
        'recent_transactions': recent_transactions,
        'recent_notices': recent_notices,
    }
    return render(request, 'core/dashboard.html', context)


# ------------------------------------------------------------------
# Taxpayer Management
# ------------------------------------------------------------------
@login_required(login_url='home')
def add_taxpayer_view(request):
    if request.method == 'POST':
        tin = request.POST.get('tin', '').strip()
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        circle = request.POST.get('circle', '').strip()

        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        address_line3 = request.POST.get('address_line3', '').strip()

        if Taxpayer.objects.filter(tin=tin).exists():
            messages.error(request, f'TIN নম্বর {tin} ইতিমধ্যেই ডাটাবেজে রয়েছে!')
            return render(request, 'core/add_taxpayer.html')

        Taxpayer.objects.create(
            tin=tin,
            name=name,
            phone=phone,
            email=email,
            holding_or_circle=circle,
            address_line1=address_line1,
            address_line2=address_line2,
            address_line3=address_line3,
            is_active=True
        )
        messages.success(request, f'করদাতা "{name}" (TIN: {tin}) সফলভাবে নিবন্ধন করা হয়েছে।')
        return redirect('dashboard')

    return render(request, 'core/add_taxpayer.html')


@login_required(login_url='home')
def taxpayer_list_view(request):
    query = request.GET.get('q', '').strip()
    circle_filter = request.GET.get('circle', '').strip()

    taxpayers = Taxpayer.objects.all().order_by('-id')

    if query:
        taxpayers = taxpayers.filter(
            Q(tin__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(address_line1__icontains=query) |
            Q(address_line2__icontains=query) |
            Q(address_line3__icontains=query)
        )

    if circle_filter:
        taxpayers = taxpayers.filter(holding_or_circle__icontains=circle_filter)

    circles = Taxpayer.objects.values_list('holding_or_circle', flat=True).distinct()

    context = {
        'taxpayers': taxpayers,
        'query': query,
        'circle_filter': circle_filter,
        'circles': [c for c in circles if c],
        'total_found': taxpayers.count(),
    }
    return render(request, 'core/taxpayer_list.html', context)


@login_required(login_url='home')
def edit_taxpayer_view(request, pk):
    taxpayer = get_object_or_404(Taxpayer, pk=pk)

    if request.method == 'POST':
        tin = request.POST.get('tin', '').strip()
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        circle = request.POST.get('circle', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        address_line3 = request.POST.get('address_line3', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if Taxpayer.objects.filter(tin=tin).exclude(pk=pk).exists():
            messages.error(request, f'TIN নম্বর {tin} ইতিমধ্যেই অন্য একজন করদাতার নামে নিবন্ধিত!')
        else:
            taxpayer.tin = tin
            taxpayer.name = name
            taxpayer.phone = phone
            taxpayer.email = email
            taxpayer.holding_or_circle = circle
            taxpayer.address_line1 = address_line1
            taxpayer.address_line2 = address_line2
            taxpayer.address_line3 = address_line3
            taxpayer.is_active = is_active
            taxpayer.save()

            messages.success(request, f'করদাতা "{name}"-এর তথ্য সফলভাবে আপডেট করা হয়েছে।')
            return redirect('taxpayer_list')

    return render(request, 'core/edit_taxpayer.html', {'taxpayer': taxpayer})


@login_required(login_url='home')
def search_taxpayer_api(request):
    tin = request.GET.get('tin', '').strip()
    if not tin:
        return JsonResponse({'success': False, 'message': 'দয়া করে একটি TIN নম্বর প্রদান করুন।'})

    taxpayer = Taxpayer.objects.filter(tin=tin).first()
    if taxpayer:
        return JsonResponse({
            'success': True,
            'id': taxpayer.id,
            'name': taxpayer.name,
            'tin': taxpayer.tin,
            'circle': taxpayer.holding_or_circle,
            'phone': taxpayer.phone,
            'address': taxpayer.full_address()
        })
    else:
        return JsonResponse({'success': False, 'message': f'TIN "{tin}" দিয়ে কোনো করদাতা ডাটাবেজে পাওয়া যায়নি!'})


def search_taxpayer_by_tin(request):
    tin = request.GET.get('tin', '').strip()
    taxpayer = Taxpayer.objects.filter(tin=tin).first()
    if taxpayer:
        return JsonResponse({
            'success': True,
            'taxpayer_id': taxpayer.id,
            'name': taxpayer.name,
        })
    return JsonResponse({'success': False, 'message': 'করদাতা পাওয়া যায়নি'})


# ------------------------------------------------------------------
# Collections
# ------------------------------------------------------------------
@login_required(login_url='home')
def add_collection_view(request):
    taxpayers = Taxpayer.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        transaction_type = request.POST.get('transaction_type')
        fiscal_year = request.POST.get('fiscal_year', '').strip()
        challan_no = request.POST.get('challan_no', '').strip()
        payment_date = request.POST.get('payment_date')
        challan_date = request.POST.get('challan_date') or None
        amount = Decimal(request.POST.get('amount') or '0.00')
        payment_mode = request.POST.get('payment_mode')
        bank_and_branch = request.POST.get('bank_and_branch', '').strip()
        remarks = request.POST.get('remarks', '').strip()

        taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

        TaxTransaction.objects.create(
            taxpayer=taxpayer,
            transaction_type=transaction_type,
            fiscal_year=fiscal_year,
            challan_no=challan_no,
            challan_date=challan_date,
            payment_date=payment_date,
            amount=amount,
            payment_mode=payment_mode,
            bank_and_branch=bank_and_branch,
            remarks=remarks
        )

        if transaction_type == 'ARREAR':
            arrear_entry = ArrearRegister.objects.filter(
                taxpayer=taxpayer,
                assessment_year=fiscal_year
            ).first()

            if arrear_entry:
                arrear_entry.collection += amount
                arrear_entry.save()

        type_text = "অগ্রিম কর" if transaction_type == 'ADVANCE' else "বকেয়া কর"
        messages.success(request, f'করদাতা {taxpayer.name}-এর {type_text} বাবদ ৳{amount} আদায় সফলভাবে সংরক্ষিত হয়েছে।')
        return redirect('dashboard')

    return render(request, 'core/add_collection.html', {'taxpayers': taxpayers})


@login_required(login_url='home')
def view_collections_view(request):
    tin_query = request.GET.get('tin', '').strip()
    type_query = request.GET.get('type', '').strip()
    year_query = request.GET.get('year', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    collections = TaxTransaction.objects.select_related('taxpayer').order_by('-payment_date', '-id')

    if tin_query:
        collections = collections.filter(taxpayer__tin__icontains=tin_query)
    if type_query:
        collections = collections.filter(transaction_type=type_query)
    if year_query:
        collections = collections.filter(fiscal_year__icontains=year_query)
    if start_date:
        collections = collections.filter(payment_date__gte=start_date)
    if end_date:
        collections = collections.filter(payment_date__lte=end_date)

    total_amount = collections.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    available_years = TaxTransaction.objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')

    context = {
        'collections': collections,
        'tin_query': tin_query,
        'type_query': type_query,
        'year_query': year_query,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'total_count': collections.count(),
        'available_years': available_years,
    }
    return render(request, 'core/view_collections.html', context)


# ------------------------------------------------------------------
# Advance Tax Register
# ------------------------------------------------------------------
@login_required(login_url='home')
def advance_register_view(request):
    tin_query = request.GET.get('tin', '').strip()
    installment_query = request.GET.get('installment', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    records = AdvanceTaxRegister.objects.select_related('taxpayer').all().order_by('-payment_date')

    if tin_query:
        records = records.filter(taxpayer__tin__icontains=tin_query)
    if installment_query:
        records = records.filter(installment=installment_query)
    if start_date:
        records = records.filter(payment_date__gte=start_date)
    if end_date:
        records = records.filter(payment_date__lte=end_date)

    total_amount = records.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')

    context = {
        'records': records,
        'total_amount': total_amount,
        'total_count': records.count(),
        'tin_query': tin_query,
        'installment_query': installment_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'core/register_advance.html', context)


@login_required(login_url='home')
def add_advance_tax_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        fiscal_year = request.POST.get('fiscal_year', '2026-2027').strip()
        installment = request.POST.get('installment')
        payment_date = request.POST.get('payment_date')
        paid_amount = Decimal(request.POST.get('paid_amount') or '0.00')
        challan_no = request.POST.get('challan_no', '').strip()
        challan_date = request.POST.get('challan_date')
        remarks = request.POST.get('remarks', '').strip()

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা ডাটাবেজে পাওয়া যায়নি!')
            return render(request, 'core/advance_tax_form.html')

        AdvanceTaxRegister.objects.create(
            taxpayer=taxpayer,
            fiscal_year=fiscal_year,
            installment=installment,
            payment_date=payment_date,
            paid_amount=paid_amount,
            challan_no=challan_no,
            challan_date=challan_date,
            remarks=remarks
        )

        TaxTransaction.objects.create(
            taxpayer=taxpayer,
            fiscal_year=fiscal_year,
            transaction_type='ADVANCE',
            challan_no=challan_no,
            challan_date=challan_date,
            payment_date=payment_date,
            amount=paid_amount,
            remarks=f"অগ্রিম কর ({installment}) - {remarks}"
        )

        messages.success(request, f'করদাতা {taxpayer.name}-এর অগ্রিম কর (৳ {paid_amount}) সফলভাবে সংরক্ষণ করা হয়েছে।')
        return redirect('advance_register')

    return render(request, 'core/advance_tax_form.html')


# ------------------------------------------------------------------
# Arrear Register
# ------------------------------------------------------------------
@login_required(login_url='home')
def arrear_register_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        assessment_year = request.POST.get('assessment_year', '').strip()
        arrear_type = request.POST.get('arrear_type', 'UNDISPUTED')
        disposal_section = request.POST.get('disposal_section', '').strip()
        disposal_date = request.POST.get('disposal_date') or None

        demand = Decimal(request.POST.get('demand') or '0.00')
        fine = Decimal(request.POST.get('fine') or '0.00')
        collection = Decimal(request.POST.get('collection') or '0.00')

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা পাওয়া যায়নি!')
            return redirect('arrear_register')

        if not assessment_year:
            messages.error(request, 'করবর্ষ অবশ্যই পূরণ করতে হবে!')
            return redirect('arrear_register')

        arrear, created = ArrearRegister.objects.update_or_create(
            taxpayer=taxpayer,
            assessment_year=assessment_year,
            defaults={
                'arrear_type': arrear_type,
                'disposal_section': disposal_section,
                'disposal_date': disposal_date,
                'demand': demand,
                'fine': fine,
                'collection': collection,
            }
        )

        status_msg = "নতুন বকেয়া তৈরি" if created else "বকেয়া তথ্য হালনাগাদ"
        messages.success(request, f'করদাতা {taxpayer.name}-এর {assessment_year} করবর্ষের {status_msg} সফলভাবে সম্পন্ন হয়েছে।')
        return redirect('arrear_list')

    tin_query = request.GET.get('tin', '').strip()
    year_query = request.GET.get('year', '').strip()

    records = ArrearRegister.objects.select_related('taxpayer').order_by('-created_at')

    if tin_query:
        records = records.filter(taxpayer__tin__icontains=tin_query)
    if year_query:
        records = records.filter(assessment_year__icontains=year_query)

    total_arrear_demand = records.aggregate(total=Sum('total_arrear'))['total'] or Decimal('0.00')
    total_collected = records.aggregate(total=Sum('collection'))['total'] or Decimal('0.00')
    total_due = records.aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')

    context = {
        'records': records,
        'tin_query': tin_query,
        'year_query': year_query,
        'total_arrear_demand': total_arrear_demand,
        'total_collected': total_collected,
        'total_due': total_due,
        'total_count': records.count(),
    }
    return render(request, 'core/arrear_form.html', context)


@login_required(login_url='home')
def add_arrear(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        assessment_year = request.POST.get('assessment_year', '').strip()
        arrear_type = request.POST.get('arrear_type', 'UNDISPUTED')
        disposal_section = request.POST.get('disposal_section', '').strip()
        disposal_date = request.POST.get('disposal_date') or None

        demand = Decimal(request.POST.get('demand') or '0.00')
        fine = Decimal(request.POST.get('fine') or '0.00')
        collection = Decimal(request.POST.get('collection') or '0.00')

        taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

        arrear, created = ArrearRegister.objects.update_or_create(
            taxpayer=taxpayer,
            assessment_year=assessment_year,
            defaults={
                'arrear_type': arrear_type,
                'disposal_section': disposal_section,
                'disposal_date': disposal_date,
                'demand': demand,
                'fine': fine,
                'collection': collection,
            }
        )
        messages.success(request, f"{taxpayer.name}-এর {assessment_year} করবর্ষের বকেয়া সফলভাবে সংরক্ষিত হয়েছে।")
        return redirect('arrear_list')

    return render(request, 'core/arrear_form.html')


@login_required(login_url='home')
def collect_arrear_payment(request, arrear_id):
    arrear = get_object_or_404(ArrearRegister, id=arrear_id)
    if request.method == 'POST':
        pay_amount = Decimal(request.POST.get('pay_amount') or '0.00')
        arrear.collection += pay_amount
        arrear.save()
        messages.success(request, f"৳ {pay_amount} সফলভাবে আদায় হিসেবে যুক্ত হয়েছে।")
        return redirect('arrear_list')

    return render(request, 'core/collect_payment.html', {'arrear': arrear})


@login_required(login_url='home')
def arrear_list(request):
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    arrear_type = request.GET.get('arrear_type', '').strip()
    tin_query = request.GET.get('tin', '').strip()

    arrears = ArrearRegister.objects.select_related('taxpayer').all().order_by('-created_at')

    for item in arrears:
        total_paid = TaxTransaction.objects.filter(
            taxpayer=item.taxpayer,
            fiscal_year=item.assessment_year,
            transaction_type='ARREAR'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        if item.collection != total_paid:
            item.collection = total_paid
            item.save()

    if start_date:
        arrears = arrears.filter(disposal_date__gte=start_date)
    if end_date:
        arrears = arrears.filter(disposal_date__lte=end_date)
    if arrear_type:
        arrears = arrears.filter(arrear_type=arrear_type)
    if tin_query:
        arrears = arrears.filter(taxpayer__tin__icontains=tin_query)

    total_demand = arrears.aggregate(total=Sum('total_arrear'))['total'] or Decimal('0.00')
    total_collection = arrears.aggregate(total=Sum('collection'))['total'] or Decimal('0.00')
    total_due = arrears.aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')

    context = {
        'arrears': arrears,
        'start_date': start_date,
        'end_date': end_date,
        'arrear_type': arrear_type,
        'tin_query': tin_query,
        'total_demand': total_demand,
        'total_collection': total_collection,
        'total_due': total_due,
        'total_count': arrears.count(),
    }
    return render(request, 'core/arrear_list.html', context)


# ------------------------------------------------------------------
# Notice Section Views
# ------------------------------------------------------------------
@login_required(login_url='home')
def notice_section_view(request):
    notices = TaxNotice.objects.select_related('taxpayer').order_by('-issue_date')
    pending_count = notices.filter(is_served=False).count()
    return render(request, 'core/notice_section.html', {'notices': notices, 'pending_count': pending_count})


@login_required(login_url='home')
def generate_arrear_notice_view(request):
    tin_query = request.GET.get('tin', '').strip()
    taxpayer = None
    arrear_records = []
    total_due = Decimal('0.00')

    if tin_query:
        taxpayer = Taxpayer.objects.filter(tin=tin_query).first()
        if taxpayer:
            arrear_records = ArrearRegister.objects.filter(
                taxpayer=taxpayer,
                due_amount__gt=0
            ).order_by('assessment_year')

            total_due = sum((record.due_amount for record in arrear_records), Decimal('0.00'))

            if not arrear_records.exists():
                messages.warning(request, f'করদাতা {taxpayer.name}-এর কোনো অবশিষ্ট বকেয়া নেই!')
        else:
            messages.error(request, f'TIN: {tin_query} দিয়ে কোনো করদাতা খুঁজে পাওয়া যায়নি!')

    context = {
        'tin_query': tin_query,
        'taxpayer': taxpayer,
        'arrear_records': arrear_records,
        'total_due': total_due,
    }
    return render(request, 'core/notice_search.html', context)


@login_required(login_url='home')
def print_arrear_notice_view(request, taxpayer_id):
    taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)
    arrear_records = ArrearRegister.objects.filter(taxpayer=taxpayer, due_amount__gt=0).order_by('assessment_year')

    req_issue_date = request.GET.get('issue_date')
    req_deadline_date = request.GET.get('deadline_date')

    today = datetime.strptime(req_issue_date, '%Y-%m-%d').date() if req_issue_date else date.today()
    deadline_date = datetime.strptime(req_deadline_date, '%Y-%m-%d').date() if req_deadline_date else (today + timedelta(days=15))

    issue_date_bn = to_bengali_digits(today.strftime('%d/%m/%Y')) + ' খ্রি.'
    deadline_date_bn = to_bengali_digits(deadline_date.strftime('%d/%m/%Y')) + ' খ্রি.'
    file_no_bn = to_bengali_digits(taxpayer.tin)

    total_demand = sum((r.demand for r in arrear_records), Decimal('0.00'))
    total_fine = sum((r.fine for r in arrear_records), Decimal('0.00'))
    grand_total = sum((r.due_amount for r in arrear_records), Decimal('0.00'))

    notice_setting = NoticeSetting.objects.filter(is_active=True).first()

    TaxNotice.objects.update_or_create(
        taxpayer=taxpayer,
        reference_no=taxpayer.tin,
        defaults={
            'arrear_amount': grand_total,
            'issue_date': today,
            'due_date': deadline_date,
            'is_served': True,
        }
    )

    context = {
        'taxpayer': taxpayer,
        'arrear_records': arrear_records,
        'file_no': file_no_bn,
        'issue_date': issue_date_bn,
        'deadline_date': deadline_date_bn,
        'total_demand': total_demand,
        'total_fine': total_fine,
        'grand_total': grand_total,
        'setting': notice_setting,
    }
    return render(request, 'core/arrear_notice_print.html', context)


@login_required(login_url='home')
def notice_183_create_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        assessment_year = request.POST.get('assessment_year', '').strip()
        issue_date = request.POST.get('issue_date') or str(date.today())
        hearing_date = request.POST.get('hearing_date')
        hearing_time = request.POST.get('hearing_time', '').strip()

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা খুঁজে পাওয়া যায়নি!')
            return redirect('notice_183_create')

        timestamp_suffix = int(time.time())
        unique_ref = f"{taxpayer.tin}-183-{assessment_year}-{timestamp_suffix}"

        TaxNotice.objects.create(
            taxpayer=taxpayer,
            notice_type='SHOW_CAUSE',
            reference_no=unique_ref,
            issue_date=issue_date,
            due_date=hearing_date,
            arrear_amount=Decimal('0.00'),
            is_served=True,
            notes=f"ধারা ১৮৩(৩) শুনানির নোটিশ | করবর্ষ: {assessment_year} | শুনানির সময়: {hearing_time}"
        )

        query_string = f"?ay={assessment_year}&issue={issue_date}&hearing_date={hearing_date}&hearing_time={hearing_time}"
        return redirect(f"/notices/183/print/{taxpayer.id}/{query_string}")

    return render(request, 'core/notice_183_form.html')


@login_required(login_url='home')
def notice_183_print_view(request, taxpayer_id):
    taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

    assessment_year = request.GET.get('ay', '')
    req_issue = request.GET.get('issue')
    req_hearing_date = request.GET.get('hearing_date')
    hearing_time = request.GET.get('hearing_time', '')

    today = datetime.strptime(req_issue, '%Y-%m-%d').date() if req_issue else date.today()
    hearing_dt = datetime.strptime(req_hearing_date, '%Y-%m-%d').date() if req_hearing_date else date.today()

    issue_date_bn = to_bengali_digits(today.strftime('%d-%m-%Y')) + ' খ্রি.'
    hearing_date_bn = to_bengali_digits(hearing_dt.strftime('%d-%m-%Y')) + ' খ্রি.'
    hearing_time_bn = to_bengali_digits(hearing_time)
    tin_bn = to_bengali_digits(taxpayer.tin)
    ay_bn = to_bengali_digits(assessment_year)
    phone_bn = to_bengali_digits(taxpayer.phone or '')

    notice_setting = NoticeSetting.objects.filter(is_active=True).first()

    context = {
        'taxpayer': taxpayer,
        'tin_bn': tin_bn,
        'ay_bn': ay_bn,
        'phone_bn': phone_bn,
        'issue_date_bn': issue_date_bn,
        'hearing_date_bn': hearing_date_bn,
        'hearing_time_bn': hearing_time_bn,
        'setting': notice_setting,
    }
    return render(request, 'core/notice_183_print.html', context)


@login_required(login_url='home')
def notice_183_5_create_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        assessment_year = request.POST.get('assessment_year', '').strip()
        issue_date = request.POST.get('issue_date') or str(date.today())
        hearing_date = request.POST.get('hearing_date')
        hearing_time = request.POST.get('hearing_time', '').strip()

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা খুঁজে পাওয়া যায়নি!')
            return redirect('notice_183_5_create')

        timestamp_suffix = int(time.time())
        unique_ref = f"{taxpayer.tin}-183-5-{assessment_year}-{timestamp_suffix}"

        TaxNotice.objects.create(
            taxpayer=taxpayer,
            notice_type='SHOW_CAUSE',
            reference_no=unique_ref,
            issue_date=issue_date,
            due_date=hearing_date,
            arrear_amount=Decimal('0.00'),
            is_served=True,
            notes=f"ধারা ১৮৩(৫) পুনঃশুনানির নোটিশ | করবর্ষ: {assessment_year} | শুনানির সময়: {hearing_time}"
        )

        query_string = f"?ay={assessment_year}&issue={issue_date}&hearing_date={hearing_date}&hearing_time={hearing_time}"
        return redirect(f"/notices/183-5/print/{taxpayer.id}/{query_string}")

    return render(request, 'core/notice_183_5_form.html')


@login_required(login_url='home')
def notice_183_5_print_view(request, taxpayer_id):
    taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

    assessment_year = request.GET.get('ay', '')
    req_issue = request.GET.get('issue')
    req_hearing_date = request.GET.get('hearing_date')
    hearing_time = request.GET.get('hearing_time', '')

    today = datetime.strptime(req_issue, '%Y-%m-%d').date() if req_issue else date.today()
    hearing_dt = datetime.strptime(req_hearing_date, '%Y-%m-%d').date() if req_hearing_date else date.today()

    issue_date_bn = to_bengali_digits(today.strftime('%d-%m-%Y')) + ' খ্রি.'
    hearing_date_bn = to_bengali_digits(hearing_dt.strftime('%d-%m-%Y')) + ' খ্রি.'
    hearing_time_bn = to_bengali_digits(hearing_time)
    tin_bn = to_bengali_digits(taxpayer.tin)
    ay_bn = to_bengali_digits(assessment_year)
    phone_bn = to_bengali_digits(taxpayer.phone or '')

    notice_setting = NoticeSetting.objects.filter(is_active=True).first()

    context = {
        'taxpayer': taxpayer,
        'tin_bn': tin_bn,
        'ay_bn': ay_bn,
        'phone_bn': phone_bn,
        'issue_date_bn': issue_date_bn,
        'hearing_date_bn': hearing_date_bn,
        'hearing_time_bn': hearing_time_bn,
        'setting': notice_setting,
    }
    return render(request, 'core/notice_183_5_print.html', context)


@login_required(login_url='home')
def notice_280_create_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        assessment_year = request.POST.get('assessment_year', '').strip()
        issue_date = request.POST.get('issue_date') or str(date.today())
        hearing_date = request.POST.get('hearing_date')
        hearing_time = request.POST.get('hearing_time', '').strip()

        failure_section = request.POST.get('failure_section', '').strip()
        penalty_section = request.POST.get('penalty_section', '').strip()
        reasons_1 = request.POST.getlist('reasons_1')
        reasons_2 = request.POST.getlist('reasons_2')
        custom_reason_1 = request.POST.get('custom_reason_1', '').strip()
        custom_reason_2 = request.POST.get('custom_reason_2', '').strip()

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা খুঁজে পাওয়া যায়নি!')
            return redirect('notice_280_create')

        timestamp_suffix = int(time.time())
        unique_ref = f"{taxpayer.tin}-280-{assessment_year}-{timestamp_suffix}"

        TaxNotice.objects.create(
            taxpayer=taxpayer,
            notice_type='SHOW_CAUSE',
            reference_no=unique_ref,
            issue_date=issue_date,
            due_date=hearing_date,
            arrear_amount=Decimal('0.00'),
            is_served=True,
            notes=f"ধারা ২৮০ কারণ দর্শানো নোটিশ | করবর্ষ: {assessment_year} | শুনানির সময়: {hearing_time}"
        )

        request.session['notice_280_data'] = {
            'failure_section': failure_section,
            'penalty_section': penalty_section,
            'reasons_1': reasons_1,
            'reasons_2': reasons_2,
            'custom_reason_1': custom_reason_1,
            'custom_reason_2': custom_reason_2,
        }

        query_string = f"?ay={assessment_year}&issue={issue_date}&hearing_date={hearing_date}&hearing_time={hearing_time}"
        return redirect(f"/notices/280/print/{taxpayer.id}/{query_string}")

    return render(request, 'core/notice_280_form.html')


@login_required(login_url='home')
def notice_280_print_view(request, taxpayer_id):
    taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

    assessment_year = request.GET.get('ay', '')
    req_issue = request.GET.get('issue')
    req_hearing_date = request.GET.get('hearing_date')
    hearing_time = request.GET.get('hearing_time', '')

    today = datetime.strptime(req_issue, '%Y-%m-%d').date() if req_issue else date.today()
    hearing_dt = datetime.strptime(req_hearing_date, '%Y-%m-%d').date() if req_hearing_date else date.today()

    issue_date_bn = to_bengali_digits(today.strftime('%d-%m-%Y')) + ' খ্রি.'
    hearing_date_bn = to_bengali_digits(hearing_dt.strftime('%d-%m-%Y')) + ' খ্রি.'
    hearing_time_bn = to_bengali_digits(hearing_time)
    tin_bn = to_bengali_digits(taxpayer.tin)
    ay_bn = to_bengali_digits(assessment_year)
    phone_bn = to_bengali_digits(taxpayer.phone or '')

    notice_data = request.session.get('notice_280_data', {})
    notice_setting = NoticeSetting.objects.filter(is_active=True).first()

    context = {
        'taxpayer': taxpayer,
        'tin_bn': tin_bn,
        'ay_bn': ay_bn,
        'phone_bn': phone_bn,
        'issue_date_bn': issue_date_bn,
        'hearing_date_bn': hearing_date_bn,
        'hearing_time_bn': hearing_time_bn,
        'setting': notice_setting,
        'notice_data': notice_data,
        'failure_section_bn': to_bengali_digits(notice_data.get('failure_section', '')),
        'penalty_section_bn': to_bengali_digits(notice_data.get('penalty_section', '')),
    }
    return render(request, 'core/notice_280_print.html', context)

    # ------------------------------------------------------------------
    # Section 212 Notice Views (IT-90)
    # ------------------------------------------------------------------
@login_required(login_url='home')
def notice_212_create_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        assessment_year = request.POST.get('assessment_year', '').strip()
        income_year_end = request.POST.get('income_year_end', '').strip()
        issue_date = request.POST.get('issue_date') or str(date.today())
        evasion_reasons = request.POST.get('evasion_reasons', '').strip()

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা খুঁজে পাওয়া যায়নি!')
            return redirect('notice_212_create')

        timestamp_suffix = int(time.time())
        unique_ref = f"{taxpayer.tin}-212-{assessment_year}-{timestamp_suffix}"

        TaxNotice.objects.create(
            taxpayer=taxpayer,
            notice_type='SHOW_CAUSE',
            reference_no=unique_ref,
            issue_date=issue_date,
            due_date=date.today() + timedelta(days=22),
            arrear_amount=Decimal('0.00'),
            is_served=True,
            notes=f"ধারা ২১২ নোটিশ | করবর্ষ: {assessment_year}"
        )

        request.session['notice_212_data'] = {
            'income_year_end': income_year_end,
            'evasion_reasons': evasion_reasons,
        }

        query_string = f"?ay={assessment_year}&issue={issue_date}"
        return redirect(f"/notices/212/print/{taxpayer.id}/{query_string}")

    return render(request, 'core/notice_212_form.html')


@login_required(login_url='home')
def notice_212_print_view(request, taxpayer_id):
    taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

    assessment_year = request.GET.get('ay', '')
    req_issue = request.GET.get('issue')

    today = datetime.strptime(req_issue, '%Y-%m-%d').date() if req_issue else date.today()

    issue_date_bn = to_bengali_digits(today.strftime('%d-%m-%Y')) + ' খ্রি.'
    tin_bn = to_bengali_digits(taxpayer.tin)
    ay_bn = to_bengali_digits(assessment_year)
    phone_bn = to_bengali_digits(taxpayer.phone or '')

    notice_data = request.session.get('notice_212_data', {})
    notice_setting = NoticeSetting.objects.filter(is_active=True).first()

    income_year_end_bn = to_bengali_digits(notice_data.get('income_year_end', ''))

    context = {
        'taxpayer': taxpayer,
        'tin_bn': tin_bn,
        'ay_bn': ay_bn,
        'phone_bn': phone_bn,
        'issue_date_bn': issue_date_bn,
        'setting': notice_setting,
        'notice_data': notice_data,
        'income_year_end_bn': income_year_end_bn,
    }
    return render(request, 'core/notice_212_print.html', context)

# ------------------------------------------------------------------
# Section 179 Notice Views (IT-13)
# ------------------------------------------------------------------
@login_required(login_url='home')
def notice_179_create_view(request):
    if request.method == 'POST':
        taxpayer_id = request.POST.get('taxpayer_id')
        tin = request.POST.get('tin', '').strip()
        assessment_year = request.POST.get('assessment_year', '').strip()
        issue_date = request.POST.get('issue_date') or str(date.today())
        hearing_date = request.POST.get('hearing_date')
        hearing_time = request.POST.get('hearing_time', '').strip()

        notice_reference_details = request.POST.get('notice_reference_details', '').strip()
        doc_details = request.POST.getlist('doc_details')
        custom_doc_details = request.POST.get('custom_doc_details', '').strip()

        taxpayer = None
        if taxpayer_id:
            taxpayer = Taxpayer.objects.filter(id=taxpayer_id).first()
        if not taxpayer and tin:
            taxpayer = Taxpayer.objects.filter(tin=tin).first()

        if not taxpayer:
            messages.error(request, f'টিআইএন "{tin}" দিয়ে কোনো করদাতা খুঁজে পাওয়া যায়নি!')
            return redirect('notice_179_create')

        timestamp_suffix = int(time.time())
        unique_ref = f"{taxpayer.tin}-179-{assessment_year}-{timestamp_suffix}"

        TaxNotice.objects.create(
            taxpayer=taxpayer,
            notice_type='SHOW_CAUSE',
            reference_no=unique_ref,
            issue_date=issue_date,
            due_date=hearing_date,
            arrear_amount=Decimal('0.00'),
            is_served=True,
            notes=f"ধারা ১৭৯ নোটিশ | করবর্ষ: {assessment_year} | শুনানির সময়: {hearing_time}"
        )

        request.session['notice_179_data'] = {
            'notice_reference_details': notice_reference_details,
            'doc_details': doc_details,
            'custom_doc_details': custom_doc_details,
        }

        query_string = f"?ay={assessment_year}&issue={issue_date}&hearing_date={hearing_date}&hearing_time={hearing_time}"
        return redirect(f"/notices/179/print/{taxpayer.id}/{query_string}")

    return render(request, 'core/notice_179_form.html')


@login_required(login_url='home')
def notice_179_print_view(request, taxpayer_id):
    taxpayer = get_object_or_404(Taxpayer, id=taxpayer_id)

    assessment_year = request.GET.get('ay', '')
    req_issue = request.GET.get('issue')
    req_hearing_date = request.GET.get('hearing_date')
    hearing_time = request.GET.get('hearing_time', '')

    today = datetime.strptime(req_issue, '%Y-%m-%d').date() if req_issue else date.today()
    hearing_dt = datetime.strptime(req_hearing_date, '%Y-%m-%d').date() if req_hearing_date else date.today()

    issue_date_bn = to_bengali_digits(today.strftime('%d/%m/%Y')) + ' খ্রি.'
    hearing_date_bn = to_bengali_digits(hearing_dt.strftime('%d/%m/%Y')) + ' খ্রি.'
    hearing_time_bn = to_bengali_digits(hearing_time)
    tin_bn = to_bengali_digits(taxpayer.tin)
    ay_bn = to_bengali_digits(assessment_year)
    phone_bn = to_bengali_digits(taxpayer.phone or '')

    notice_data = request.session.get('notice_179_data', {})
    notice_setting = NoticeSetting.objects.filter(is_active=True).first()

    context = {
        'taxpayer': taxpayer,
        'tin_bn': tin_bn,
        'ay_bn': ay_bn,
        'phone_bn': phone_bn,
        'issue_date_bn': issue_date_bn,
        'hearing_date_bn': hearing_date_bn,
        'hearing_time_bn': hearing_time_bn,
        'setting': notice_setting,
        'notice_data': notice_data,
    }
    return render(request, 'core/notice_179_print.html', context)
