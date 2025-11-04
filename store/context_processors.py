from .models import SiteSettings

def cart_context(request):
    cart = request.session.get('cart', {})
    cart_items_count = sum(item.get('quantity', 1) for item in cart.values())
    
    # Calculate total price for shipping
    total_price = 0
    for product_id, item_data in cart.items():
        try:
            from .models import Product
            product = Product.objects.get(id=product_id, is_available=True)
            quantity = item_data.get('quantity', 1)
            total_price += product.price * quantity
        except:
            continue
    
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
    
    # Free shipping calculation
    if free_delivery_enabled and cart_items_count > 0 and total_price >= free_delivery_threshold:
        shipping_cost = 0
    elif cart_items_count > 0:
        shipping_cost = delivery_fee
    else:
        shipping_cost = 0
    
    return {
        'cart_items_count': cart_items_count,
        'delivery_fee': delivery_fee,
        'free_delivery_threshold': free_delivery_threshold,
        'free_delivery_enabled': free_delivery_enabled,
        'shipping_cost': shipping_cost,
        'cart_total_price': total_price,
    }

def site_settings(request):
    try:
        site_settings = SiteSettings.objects.first()
        if not site_settings:
            site_settings = SiteSettings.objects.create(
                site_name="تارلا ارگانیک",
                delivery_fee=25000,
                free_delivery_threshold=500000,
                free_delivery_enabled=True,
                contact_phone="+98 935 511 1355",
                contact_email="info@tarla.ir",
                address="تهران، بزرگراه جلال آل احمد"
            )
    except Exception as e:
        # Fallback settings if database is not available
        site_settings = None
    
    return {
        'site_settings': site_settings
    }