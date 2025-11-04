from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Product, SiteSettings, Category, UserProfile, DiscountCode, Order, OrderItem
import random
import string

def home(request):
    try:
        featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
    except Exception as e:
        featured_products = []
    
    return render(request, "store/index.html", {"featured_products": featured_products})

def products(request):
    try:
        products_list = Product.objects.filter(is_available=True)
        
        # Search functionality
        search_query = request.GET.get('search', '').strip()
        if search_query:
            products_list = products_list.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category_filter = request.GET.get('category', '')
        if category_filter:
            products_list = products_list.filter(category__name=category_filter)
        
        # Price filter with validation
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        
        if price_min and price_min.isdigit():
            products_list = products_list.filter(price__gte=int(price_min))
        if price_max and price_max.isdigit():
            products_list = products_list.filter(price__lte=int(price_max))
        
        categories = Category.objects.filter(is_active=True)
    except Exception as e:
        products_list = []
        categories = []
        search_query = ''
        category_filter = ''
        price_min = ''
        price_max = ''
    
    context = {
        'products': products_list,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_filter,
        'price_min': price_min,
        'price_max': price_max,
    }
    return render(request, "store/products.html", context)

def product_detail(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk, is_available=True)
        related_products = Product.objects.filter(
            category=product.category, 
            is_available=True
        ).exclude(pk=product.pk)[:4]
    except Exception as e:
        product = None
        related_products = []
    
    if not product:
        messages.error(request, 'محصول مورد نظر یافت نشد.')
        return redirect('products')
    
    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, "store/product_detail.html", context)

def about(request):
    return render(request, "store/about.html")

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            messages.error(request, 'لطفاً تمام فیلدها را پر کنید.')
            return render(request, "store/contact.html")
        
        if len(message) < 10:
            messages.error(request, 'پیام باید حداقل ۱۰ کاراکتر داشته باشد.')
            return render(request, "store/contact.html")
        
        # Here you would typically save to database or send email
        messages.success(request, 'پیام شما با موفقیت ارسال شد. به زودی با شما تماس خواهیم گرفت.')
        return redirect('contact')
    
    return render(request, "store/contact.html")

# Authentication Views
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            try:
                UserProfile.objects.create(user=user)
            except:
                pass
            login(request, user)
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد!')
            return redirect('home')
        else:
            messages.error(request, 'لطفاً اطلاعات را صحیح وارد کنید.')
    else:
        form = UserCreationForm()
    
    return render(request, 'store/auth/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'خوش آمدید {user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
        else:
            messages.error(request, 'نام کاربری یا رمز عبور صحیح نیست.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'store/auth/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('home')

@login_required
def profile_view(request):
    return render(request, 'store/auth/profile.html')

# Discount Code System
def apply_discount_code(request):
    if request.method == 'POST':
        discount_code = request.POST.get('discount_code', '').strip().upper()
        
        if not discount_code:
            messages.error(request, 'لطفاً کد تخفیف را وارد کنید.')
            return redirect('cart')
        
        try:
            discount = DiscountCode.objects.get(
                code=discount_code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            
            if discount.used_count >= discount.max_usage:
                messages.error(request, 'این کد تخفیف منقضی شده است.')
            else:
                # Store discount in session
                request.session['discount_code'] = {
                    'code': discount.code,
                    'percent': discount.discount_percent,
                    'id': discount.id
                }
                messages.success(request, f'کد تخفیف {discount.discount_percent}% اعمال شد!')
                
        except DiscountCode.DoesNotExist:
            messages.error(request, 'کد تخفیف معتبر نیست.')
        
        return redirect('cart')

def remove_discount_code(request):
    if 'discount_code' in request.session:
        del request.session['discount_code']
        messages.success(request, 'کد تخفیف حذف شد.')
    return redirect('cart')

# Cart Logic with Discount System
def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    cart_items_count = 0
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=product_id, is_available=True)
            quantity = item_data.get('quantity', 1)
            
            # Validate quantity
            if quantity < 1:
                quantity = 1
            if quantity > 99:
                quantity = 99
            
            # Check stock
            if quantity > product.stock_quantity:
                quantity = product.stock_quantity
                messages.warning(request, f'تعداد {product.name} به دلیل محدودیت موجودی کاهش یافت.')
            
            item_total = product.price * quantity
            total_price += item_total
            cart_items_count += quantity
            
            cart_items.append({
                'id': product_id,
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
        except Product.DoesNotExist:
            # Remove invalid products from cart
            if product_id in cart:
                del cart[product_id]
                request.session['cart'] = cart
            continue
    
    # Get delivery settings
    try:
        site_settings = SiteSettings.objects.first()
        if site_settings:
            delivery_fee = site_settings.delivery_fee
            free_delivery_threshold = site_settings.free_delivery_threshold
            free_delivery_enabled = site_settings.free_delivery_enabled
        else:
            delivery_fee = 25000
            free_delivery_threshold = 500000
            free_delivery_enabled = True
    except:
        delivery_fee = 25000
        free_delivery_threshold = 500000
        free_delivery_enabled = True
    
    # Calculate discount
    discount_amount = 0
    discount_percent = 0
    discount_code = request.session.get('discount_code')
    
    if discount_code and total_price > 0:
        discount_percent = discount_code['percent']
        discount_amount = (total_price * discount_percent) // 100
    
    # Calculate shipping cost
    if free_delivery_enabled and total_price >= free_delivery_threshold and cart_items_count > 0:
        shipping_cost = 0
    elif cart_items_count > 0:
        shipping_cost = delivery_fee
    else:
        shipping_cost = 0
    
    subtotal = total_price - discount_amount
    final_price = max(0, subtotal + shipping_cost)
    
    # Calculate remaining amount for free delivery
    if free_delivery_enabled and total_price < free_delivery_threshold:
        remaining_amount = free_delivery_threshold - total_price
    else:
        remaining_amount = 0
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'discount_percent': discount_percent,
        'discount_code': discount_code,
        'final_price': final_price,
        'cart_items_count': cart_items_count,
        'free_delivery_threshold': free_delivery_threshold,
        'free_delivery_enabled': free_delivery_enabled,
        'delivery_fee': delivery_fee,
        'remaining_amount': remaining_amount
    }
    return render(request, "store/cart.html", context)

def add_to_cart(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid method")
        
    try:
        product = get_object_or_404(Product, pk=pk, is_available=True)
        cart = request.session.get('cart', {})
        
        product_id = str(product.id)
        
        # Check stock
        current_quantity = cart.get(product_id, {}).get('quantity', 0)
        if current_quantity + 1 > product.stock_quantity:
            messages.error(request, f'موجودی {product.name} کافی نیست.')
            return redirect('products')
        
        if product_id in cart:
            cart[product_id]['quantity'] = current_quantity + 1
        else:
            cart[product_id] = {'quantity': 1}
        
        request.session['cart'] = cart
        messages.success(request, f'{product.name} به سبد خرید اضافه شد')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'{product.name} به سبد خرید اضافه شد'})
        
        return redirect('products')
    except Exception as e:
        messages.error(request, 'خطا در افزودن محصول به سبد خرید')
        return redirect('products')

def update_cart(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid method")
        
    try:
        product = get_object_or_404(Product, pk=pk, is_available=True)
        cart = request.session.get('cart', {})
        product_id = str(product.id)
        
        action = request.POST.get('action')
        quantity = request.POST.get('quantity')
        
        if product_id in cart:
            current_quantity = cart[product_id].get('quantity', 1)
            
            if action == 'increase':
                if current_quantity + 1 <= product.stock_quantity:
                    cart[product_id]['quantity'] = current_quantity + 1
                    messages.success(request, f'تعداد {product.name} افزایش یافت')
                else:
                    messages.error(request, f'موجودی {product.name} کافی نیست.')
            
            elif action == 'decrease':
                if current_quantity > 1:
                    cart[product_id]['quantity'] = current_quantity - 1
                    messages.success(request, f'تعداد {product.name} کاهش یافت')
                else:
                    messages.warning(request, 'حداقل تعداد محصول ۱ می‌باشد')
            
            elif quantity and quantity.isdigit():
                new_quantity = int(quantity)
                if 1 <= new_quantity <= 99:
                    if new_quantity <= product.stock_quantity:
                        cart[product_id]['quantity'] = new_quantity
                        messages.success(request, f'تعداد {product.name} به {new_quantity} عدد تغییر یافت')
                    else:
                        messages.error(request, f'موجودی {product.name} کافی نیست.')
                        cart[product_id]['quantity'] = product.stock_quantity
                else:
                    messages.error(request, 'تعداد باید بین ۱ تا ۹۹ باشد.')
        
        request.session['cart'] = cart
        return redirect('cart')
    except Exception as e:
        messages.error(request, 'خطا در بروزرسانی سبد خرید')
        return redirect('cart')

def remove_from_cart(request, pk):
    if request.method != 'POST' and request.method != 'GET':
        return HttpResponseBadRequest("Invalid method")
        
    try:
        cart = request.session.get('cart', {})
        product_id = str(pk)
        
        if product_id in cart:
            product = get_object_or_404(Product, pk=pk)
            del cart[product_id]
            request.session['cart'] = cart
            messages.success(request, f'{product.name} از سبد خرید حذف شد')
        
        return redirect('cart')
    except Exception as e:
        messages.error(request, 'خطا در حذف محصول از سبد خرید')
        return redirect('cart')

def clear_cart(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid method")
        
    request.session['cart'] = {}
    if 'discount_code' in request.session:
        del request.session['discount_code']
    messages.success(request, 'سبد خرید پاک شد')
    return redirect('cart')

def checkout(request):
    cart = request.session.get('cart', {})
    cart_items_count = sum(item.get('quantity', 1) for item in cart.values())
    
    if cart_items_count == 0:
        messages.warning(request, 'سبد خرید شما خالی است')
        return redirect('products')
    
    try:
        # Calculate totals
        total_price = 0
        cart_items = []
        
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.get(id=product_id, is_available=True)
                quantity = item_data.get('quantity', 1)
                item_total = product.price * quantity
                total_price += item_total
                
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.price,
                    'total': item_total
                })
            except Product.DoesNotExist:
                continue
        
        if not cart_items:
            messages.error(request, 'سبد خرید شما خالی است')
            return redirect('cart')
        
        # Get shipping cost
        try:
            site_settings = SiteSettings.objects.first()
            if site_settings:
                delivery_fee = site_settings.delivery_fee
                free_delivery_threshold = site_settings.free_delivery_threshold
                free_delivery_enabled = site_settings.free_delivery_enabled
            else:
                delivery_fee = 25000
                free_delivery_threshold = 500000
                free_delivery_enabled = True
        except:
            delivery_fee = 25000
            free_delivery_threshold = 500000
            free_delivery_enabled = True
        
        # Calculate discount
        discount_amount = 0
        discount_code = request.session.get('discount_code')
        if discount_code and total_price > 0:
            discount_amount = (total_price * discount_code['percent']) // 100
        
        # Calculate shipping
        if free_delivery_enabled and total_price >= free_delivery_threshold:
            shipping_cost = 0
        else:
            shipping_cost = delivery_fee
        
        subtotal = total_price - discount_amount
        final_price = max(0, subtotal + shipping_cost)
        
        # Generate unique order number
        def generate_order_number():
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = ''.join(random.choices(string.digits, k=4))
            return f'TL{timestamp}{random_str}'
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            order_number=generate_order_number(),
            total_price=total_price,
            shipping_cost=shipping_cost,
            final_price=final_price,
            status='pending'
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )
        
        # Clear cart and discount
        request.session['cart'] = {}
        if 'discount_code' in request.session:
            del request.session['discount_code']
        
        # Redirect to confirmation page
        return redirect('order_confirmation', order_id=order.id)
        
    except Exception as e:
        messages.error(request, 'خطا در ثبت سفارش. لطفاً دوباره تلاش کنید.')
        return redirect('cart')
    
def order_confirmation(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'store/order_confirmation.html', context)
    except Exception as e:
        messages.error(request, 'سفارش یافت نشد.')
        return redirect('home')