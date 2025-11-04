from django.urls import path, re_path
from django.http import HttpResponse
from . import views

def debug_urls(request):
    """Debug view to see all registered URLs"""
    from django.urls import get_resolver
    resolver = get_resolver()
    urls = []
    for pattern in resolver.url_patterns:
        urls.append(str(pattern))
    return HttpResponse("<br>".join(urls))

urlpatterns = [
    # Debug endpoint
    path("debug-urls/", debug_urls, name="debug_urls"),
    
    # Home
    path("", views.home, name="home"),
    
    # Products - multiple patterns to catch all cases
    path("products/", views.products, name="products"),
    re_path(r"^products$", views.products),  # Explicitly catch without slash
    
    # Product detail
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    
    # Static pages
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    
    # Cart
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:pk>/", views.update_cart, name="update_cart"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
    path("cart/apply-discount/", views.apply_discount_code, name="apply_discount"),
    path("cart/remove-discount/", views.remove_discount_code, name="remove_discount"),
    
    # Checkout
    path("checkout/", views.checkout, name="checkout"),
    path("order/confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    
    # Authentication
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
]