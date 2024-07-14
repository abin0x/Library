from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.contrib import messages
from .models import Book, Category, Transaction, Review, UserProfile
from .forms import UserRegistrationForm, DepositForm, BorrowBookForm, ReviewForm, UserProfileForm, BookForm
from datetime import date
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class RegisterView(View):
    def get(self, request):
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
        return render(request, 'library/register.html', {'user_form': user_form, 'profile_form': profile_form})

    def post(self, request):
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, 'Registration successful')
            return redirect('home')
        else:
            # Display form errors to help debug
            for form in [user_form, profile_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        return render(request, 'library/register.html', {'user_form': user_form, 'profile_form': profile_form})

class LoginView(View):
    def get(self, request):
        return render(request, 'library/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Login Successful')
                return redirect('book_list')
            else:
                messages.error(request, 'Invalid credentials')
        else:
            messages.error(request, 'Please provide both username and password.')

        return render(request, 'library/login.html')

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'Logout Successful')
        return redirect('home')

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'library/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        books = Book.objects.all()

        category_id = self.request.GET.get('category')
        if category_id:
            books = books.filter(categories__id=category_id)

        context['books'] = books
        context['categories'] = Category.objects.all()
        context['user'] = self.request.user 
        return context

class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['user_balance'] = self.request.user.profile.balance
        return context
    
class BorrowBookView(LoginRequiredMixin, View):
    def post(self, request):
        form = BorrowBookForm(request.POST)
        if form.is_valid():
            book_id = form.cleaned_data['book_id']
            book = get_object_or_404(Book, id=book_id)
            user_profile = request.user.profile
            if user_profile.balance >= book.borrowing_price:
                transaction = Transaction.objects.create(user=request.user, book=book, amount=book.borrowing_price)
                user_profile.balance -= book.borrowing_price
                user_profile.save()
                send_mail(
                    'Book Borrow Successful',
                    f'Hello {request.user},\n\nYou have successfully borrowed "{book}"\n\n this book of price {book.borrowing_price}.\n\nThank you!',
                    settings.DEFAULT_FROM_EMAIL,
                    [self.request.user.email]
                )
                messages.success(request, 'Book borrowed successfully')
            else:
                messages.error(request, 'Insufficient balance')
        return redirect('book_list')

class ReturnBookView(View):
    def post(self, request, *args, **kwargs):
        transaction_id = kwargs['transaction_id']
        transaction = get_object_or_404(Transaction, pk=transaction_id)
        borrowing_price = transaction.amount  
        user_profile = transaction.user.profile
        user_profile.balance += borrowing_price
        user_profile.save()
        transaction.balance_after_borrow = user_profile.balance
        transaction.return_date = date.today()
        transaction.save()
        send_mail(
            'Book Return Successful',
            f'Hello {request.user.username},\n\nYou have successfully returned the book "{transaction.book.title}".\n\nThank you!',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
        )

        messages.success(request, 'Book returned successfully')
        return redirect('borrow_history')

class BorrowHistoryView(LoginRequiredMixin, ListView):
    template_name = 'library/borrow_history.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        return self.request.user.transactions.all()

    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get('transaction_id')
        if transaction_id:
            transaction = Transaction.objects.get(pk=transaction_id)
            transaction.return_date = date.today()
            transaction.save()
        return redirect('borrow_history')

class DepositMoneyView(LoginRequiredMixin, FormView):
    template_name = 'library/deposit.html'
    form_class = DepositForm
    success_url = reverse_lazy('book_list')

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        self.request.user.profile.balance += amount
        self.request.user.profile.save()
        send_mail(
            'Deposit Successful',
            f'You have successfully deposited {amount} taka to your account',
            settings.DEFAULT_FROM_EMAIL,
            [self.request.user.email]
        )
        messages.success(self.request, 'Deposit successful')
        return super().form_valid(form)

class ReviewBookView(LoginRequiredMixin, View):
    template_name = 'library/review_book.html'

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        form = ReviewForm()
        return render(request, self.template_name, {'form': form, 'book': book})

    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()
            return redirect('book_detail', pk=book.id)
        return render(request, self.template_name, {'form': form, 'book': book})

class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        user = self.request.user
        context['user'] = user
        context['has_borrowed'] = user.profile.has_borrowed(book)
        context['reviews'] = book.reviews.all()  
        return context
    
class AddBookView(View):
    def get(self, request):
        form = BookForm()
        return render(request, 'library/add_book.html', {'form': form})

    def post(self, request):
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, 'Book added successfully')
            return redirect('book_list')
        else:
            messages.error(request, 'Failed to add book. Please check the form.')

        return render(request, 'library/add_book.html', {'form': form})

