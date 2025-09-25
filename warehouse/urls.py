from django.urls import path

from . import views


app_name = 'warehouse'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('catalog/', views.catalog, name='catalog'),
    path('scan/', views.scan_view, name='scan'),
    path('inbound/', views.inbound_view, name='inbound'),
    path('outbound/', views.outbound_view, name='outbound'),
    path('inventory/', views.inventory_summary, name='inventory'),
    path('near-expiry/', views.near_expiry, name='near_expiry'),
    path('popular/', views.popular_items, name='popular_items'),
    path('locations/', views.locations, name='locations'),
    path('locations/new/', views.location_new, name='location_new'),
    path('packaging/', views.item_packaging_list, name='packaging_list'),
    path('packaging/<int:pk>/', views.item_packaging_update, name='packaging_update'),
]
