from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address_line_1', 'address_line_2', 'city', 'state', 'country', 'order_note']
    
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'
        self.fields['phone'].widget.attrs['placeholder'] = 'Enter Phone Number'
        self.fields['address_line_1'].widget.attrs['placeholder'] = 'Enter Address Line 1'
        self.fields['address_line_2'].widget.attrs['placeholder'] = 'Enter Address Line 2 (Optional)'
        self.fields['city'].widget.attrs['placeholder'] = 'Enter City'
        self.fields['state'].widget.attrs['placeholder'] = 'Enter State'
        self.fields['country'].widget.attrs['placeholder'] = 'Enter Country'
        self.fields['order_note'].widget.attrs['placeholder'] = 'Enter Order Note (Optional)'
        
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
