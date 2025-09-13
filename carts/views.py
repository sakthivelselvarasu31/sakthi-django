from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Cart, CartItem
from store.models import Product, Variation
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []
    
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass
    
    if request.user.is_authenticated:
        # For authenticated users
        cart_items = CartItem.objects.filter(product=product, user=request.user)
        
        if cart_items.exists():
            # Check if exact same variations exist
            ex_var_list = []
            id_list = []
            
            for item in cart_items:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)
            
            # If same variations found, increment quantity
            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(product=product, id=item_id, user=request.user)
                item.quantity += 1
                item.save()
            else:
                # Different variations, create new cart item
                item = CartItem.objects.create(
                    product=product, 
                    quantity=1, 
                    user=request.user
                )
                if len(product_variation) > 0:
                    item.variations.add(*product_variation)
                item.save()
        else:
            # First time adding this product
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=request.user,
            )
            if len(product_variation) > 0:
                cart_item.variations.add(*product_variation)
            cart_item.save()
    else:
        # For anonymous users
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        cart_items = CartItem.objects.filter(product=product, cart=cart)
        
        if cart_items.exists():
            # Check if exact same variations exist
            ex_var_list = []
            id_list = []
            
            for item in cart_items:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)
            
            # If same variations found, increment quantity
            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(product=product, id=item_id, cart=cart)
                item.quantity += 1
                item.save()
            else:
                # Different variations, create new cart item
                item = CartItem.objects.create(
                    product=product, 
                    quantity=1, 
                    cart=cart
                )
                if len(product_variation) > 0:
                    item.variations.add(*product_variation)
                item.save()
        else:
            # First time adding this product
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.add(*product_variation)
            cart_item.save()
    
    return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        pass
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
    
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip_code')
        order_note = request.POST.get('order_note')
        
        messages.success(request, 'Order placed successfully!')
        return redirect('store')
    
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(request, 'store/checkout.html', context)


def check_cart_status(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        color = request.POST.get('color')
        size = request.POST.get('size')
        
        try:
            product = Product.objects.get(id=product_id)
            selected_variations = []
            
            if color:
                color_variation = Variation.objects.get(product=product, variation_category__iexact='color', variation_value__iexact=color)
                selected_variations.append(color_variation)
            
            if size:
                size_variation = Variation.objects.get(product=product, variation_category__iexact='size', variation_value__iexact=size)
                selected_variations.append(size_variation)
            
            in_cart = False
            
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, product=product)
            else:
                try:
                    cart = Cart.objects.get(cart_id=_cart_id(request))
                    cart_items = CartItem.objects.filter(cart=cart, product=product)
                except:
                    cart_items = []
            
            for cart_item in cart_items:
                existing_variations = list(cart_item.variations.all())
                if set(selected_variations) == set(existing_variations):
                    in_cart = True
                    break
            
            return JsonResponse({'in_cart': in_cart})
        
        except:
            return JsonResponse({'in_cart': False})
    
    return JsonResponse({'in_cart': False})
