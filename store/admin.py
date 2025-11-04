from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from .models import Product, SiteSettings, Category, UserProfile, Order, OrderItem, DiscountCode

# Unregister default Group
admin.site.unregister(Group)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'admin_actions']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at']
    actions = ['delete_selected']
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #dc3545; color: white;">Delete</a>',
            reverse('admin:store_category_change', args=[obj.id]),
            reverse('admin:store_category_delete', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'stock_quantity', 'is_featured', 'is_available', 'created_at', 'admin_actions']
    list_filter = ['category', 'is_featured', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock_quantity', 'is_featured', 'is_available']
    readonly_fields = ['created_at']
    actions = ['delete_selected', 'make_featured', 'make_unavailable']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'price', 'image', 'category')
        }),
        ('تنظیمات', {
            'fields': ('is_featured', 'is_available', 'stock_quantity')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #dc3545; color: white;">Delete</a>',
            reverse('admin:store_product_change', args=[obj.id]),
            reverse('admin:store_product_delete', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = "Mark selected products as featured"
    
    def make_unavailable(self, request, queryset):
        queryset.update(is_available=False)
    make_unavailable.short_description = "Mark selected products as unavailable"

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'delivery_fee', 'free_delivery_threshold', 'free_delivery_enabled', 'contact_phone', 'admin_actions']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('site_name', 'contact_phone', 'contact_phone2', 'contact_email', 'address')
        }),
        ('تنظیمات ارسال', {
            'fields': ('delivery_fee', 'free_delivery_threshold', 'free_delivery_enabled'),
            'description': 'تنظیمات مربوط به هزینه و شرایط ارسال محصولات'
        }),
    )
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;',
            reverse('admin:store_sitesettings_change', args=[obj.id]),
            reverse('admin:store_sitesettings_delete', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'
    
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at', 'admin_actions']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at']
    actions = ['delete_selected']
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #dc3545; color: white;">Delete</a>',
            reverse('admin:store_userprofile_change', args=[obj.id]),
            reverse('admin:store_userprofile_delete', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_price', 'status', 'created_at', 'admin_actions']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    actions = ['delete_selected', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #dc3545; color: white;">Delete</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #28a745; color: white;">View Items</a>',
            reverse('admin:store_order_change', args=[obj.id]),
            reverse('admin:store_order_delete', args=[obj.id]),
            reverse('admin:store_orderitem_changelist') + f'?order__id__exact={obj.id}'
        )
    admin_actions.short_description = 'Actions'
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "Mark selected orders as delivered"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total', 'admin_actions']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__name']
    actions = ['delete_selected']
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #dc3545; color: white;">Delete</a>',
            reverse('admin:store_orderitem_change', args=[obj.id]),
            reverse('admin:store_orderitem_delete', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'used_count', 'max_usage', 'is_active', 'is_valid', 'admin_actions']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code']
    list_editable = ['is_active', 'max_usage']
    readonly_fields = ['used_count', 'created_at']
    actions = ['delete_selected', 'activate_codes', 'deactivate_codes']
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}" style="background-color: #dc3545; color: white;">Delete</a>',
            reverse('admin:store_discountcode_change', args=[obj.id]),
            reverse('admin:store_discountcode_delete', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'معتبر'
    
    def activate_codes(self, request, queryset):
        queryset.update(is_active=True)
    activate_codes.short_description = "Activate selected discount codes"
    
    def deactivate_codes(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_codes.short_description = "Deactivate selected discount codes"

# Custom admin site title
admin.site.site_header = "پنل مدیریت تارلا ارگانیک"
admin.site.site_title = "تارلا ارگانیک"
admin.site.index_title = "مدیریت فروشگاه"