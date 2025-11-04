from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='تارلا ارگانیک', verbose_name='نام سایت')
    delivery_fee = models.PositiveIntegerField(
        default=25000, 
        validators=[MinValueValidator(0)],
        verbose_name='هزینه ارسال (تومان)'
    )
    free_delivery_threshold = models.PositiveIntegerField(
        default=500000,
        validators=[MinValueValidator(0)],
        verbose_name='حداقل مبلغ برای ارسال رایگان (تومان)'
    )
    free_delivery_enabled = models.BooleanField(default=True, verbose_name='فعالسازی ارسال رایگان')
    contact_phone = models.CharField(max_length=20, default='+98 935 511 1355', verbose_name='تلفن تماس ۱')
    contact_phone2 = models.CharField(max_length=20, blank=True, verbose_name='تلفن تماس ۲')
    contact_email = models.EmailField(default='info@tarla.ir', verbose_name='ایمیل')
    address = models.TextField(default='تهران، بزرگراه جلال آل احمد', verbose_name='آدرس')
    
    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'
    
    def __str__(self):
        return 'تنظیمات سایت'
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            existing = SiteSettings.objects.first()
            existing.site_name = self.site_name
            existing.delivery_fee = self.delivery_fee
            existing.free_delivery_threshold = self.free_delivery_threshold
            existing.free_delivery_enabled = self.free_delivery_enabled
            existing.contact_phone = self.contact_phone
            existing.contact_phone2 = self.contact_phone2
            existing.contact_email = self.contact_email
            existing.address = self.address
            return existing.save(*args, **kwargs)
        return super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='نام محصول')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    price = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='قیمت'
    )
    image = models.ImageField(upload_to='products/', verbose_name='تصویر')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='دسته‌بندی')
    is_featured = models.BooleanField(default=False, verbose_name='محصول ویژه')
    is_available = models.BooleanField(default=True, verbose_name='موجود')
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد موجودی')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def in_stock(self):
        return self.stock_quantity > 0

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, verbose_name='تلفن')
    address = models.TextField(blank=True, verbose_name='آدرس')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عضویت')
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل کاربران'
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال آماده‌سازی'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    order_number = models.CharField(max_length=20, unique=True, verbose_name='شماره سفارش')
    total_price = models.PositiveIntegerField(verbose_name='مبلغ کل')
    shipping_cost = models.PositiveIntegerField(default=0, verbose_name='هزینه ارسال')
    final_price = models.PositiveIntegerField(verbose_name='مبلغ نهایی')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ سفارش')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"سفارش {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='سفارش')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')
    price = models.PositiveIntegerField(verbose_name='قیمت واحد')
    
    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    @property
    def total(self):
        return self.quantity * self.price

class DiscountCode(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name='کد تخفیف')
    discount_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='درصد تخفیف'
    )
    max_usage = models.PositiveIntegerField(default=1, verbose_name='حداکثر استفاده')
    used_count = models.PositiveIntegerField(default=0, verbose_name='تعداد استفاده شده')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    valid_from = models.DateTimeField(verbose_name='معتبر از')
    valid_to = models.DateTimeField(verbose_name='معتبر تا')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'
    
    def __str__(self):
        return self.code
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.used_count < self.max_usage and 
                self.valid_from <= now <= self.valid_to)