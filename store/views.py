from django.shortcuts import render,get_object_or_404,redirect
from Category.models import Category
from .models import Product, ReviewRating, ProductGallery, Variation
from carts.views import _cart_id
from carts.models import CartItem, Cart
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True).order_by('id')
        paginator = Paginator(products, 1)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
    
        products = Product.objects.all().filter(is_available=True)
        paginator = Paginator(products, 10)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    context = {
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        
        # Get selected variations from POST data
        selected_variations = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=single_product, variation_category__iexact=key, variation_value__iexact=value)
                    selected_variations.append(variation)
                except:
                    pass
        
        # Check if EXACT same variations are in cart
        in_cart = False
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, product=single_product)
            
            for cart_item in cart_items:
                existing_variations = list(cart_item.variations.all())
                if selected_variations == existing_variations:
                    in_cart = True
                    break
        else:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, product=single_product)
                
                for cart_item in cart_items:
                    existing_variations = list(cart_item.variations.all())
                    if selected_variations == existing_variations:
                        in_cart = True
                        break
            except:
                in_cart = False
        
    except Exception as e:
        raise e
    
    # Get product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    
    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
                is_available=True
            )
            product_count = products.count()
        else:
            products = Product.objects.none()
            product_count = 0
    else:
        products = Product.objects.none()
        product_count = 0
        
    context = {
        'products': products,
        'product_count': product_count,
        'keyword': keyword if 'keyword' in request.GET else '',
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)

        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.review = form.cleaned_data['review']
                data.rating = form.cleaned_data['rating']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)

