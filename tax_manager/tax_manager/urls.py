"""
URL configuration for tax_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # Core Action Routes
    path('taxpayers/add/', views.add_taxpayer_view, name='add_taxpayer'),
    path('taxpayers/', views.taxpayer_list_view, name='taxpayer_list'),
    path('taxpayers/<int:pk>/edit/', views.edit_taxpayer_view, name='edit_taxpayer'), # এডিট ও আপডেট

    path('collection/new/', views.add_collection_view, name='add_collection'),
    path('collections/view/', views.view_collections_view, name='view_collections'),
    path('registers/advance/', views.advance_register_view, name='advance_register'),
    path('registers/advance/add/', views.add_advance_tax_view, name='add_advance_tax'),
    path('registers/arrear/', views.arrear_register_view, name='arrear_register'),
    path('notices/', views.notice_section_view, name='notice_section'),
    path('api/taxpayers/search/', views.search_taxpayer_api, name='search_taxpayer_api'),
    path('arrears/', views.arrear_list, name='arrear_list'),
    path('arrears/add/', views.add_arrear, name='add_arrear'),
    path('arrears/pay/<int:arrear_id>/', views.collect_arrear_payment, name='collect_arrear_payment'),
    path('api/search-taxpayer/', views.search_taxpayer_by_tin, name='search_taxpayer_by_tin'),
    path('notices/arrear/search/', views.generate_arrear_notice_view, name='generate_arrear_notice'),
    path('notices/arrear/print/<int:taxpayer_id>/', views.print_arrear_notice_view, name='print_arrear_notice'),
    path('notices/183/create/', views.notice_183_create_view, name='notice_183_create'),
    path('notices/183/print/<int:taxpayer_id>/', views.notice_183_print_view, name='notice_183_print'),
    path('notices/183-5/create/', views.notice_183_5_create_view, name='notice_183_5_create'),
    path('notices/183-5/print/<int:taxpayer_id>/', views.notice_183_5_print_view, name='notice_183_5_print'),
    path('notices/280/create/', views.notice_280_create_view, name='notice_280_create'),
    path('notices/280/print/<int:taxpayer_id>/', views.notice_280_print_view, name='notice_280_print'),
    path('notices/212/create/', views.notice_212_create_view, name='notice_212_create'),
    path('notices/212/print/<int:taxpayer_id>/', views.notice_212_print_view, name='notice_212_print'),
    path('notices/179/create/', views.notice_179_create_view, name='notice_179_create'),
    path('notices/179/print/<int:taxpayer_id>/', views.notice_179_print_view, name='notice_179_print'),

]
