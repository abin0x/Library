from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Review, Book

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('balance',)

class DepositForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

class BorrowBookForm(forms.Form):
    book_id = forms.IntegerField(widget=forms.HiddenInput())

class ReturnBookForm(forms.Form):
    pass

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review']

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'description', 'image', 'borrowing_price', 'categories']
