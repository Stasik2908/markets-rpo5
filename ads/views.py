from django.shortcuts import render, get_object_or_404, redirect
from .models import Ad, Favorite, Category, Profile, Review
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q
from django.db.models import Avg


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('ad_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def ad_list(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    ads = Ad.objects.annotate(average_rating=Avg('reviews__rating'))
    if query:
        ads = ads.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category_id:
        ads = ads.filter(category_id=category_id)

    categories = Category.objects.all()
    return render(request, 'ad_list.html', {
        'ads': ads.distinct(),  # distinct() важен, если поиск выдает дубликаты
        'categories': categories,
        'query': query,
    })


def ad_detail(request, pk):
    ad = get_object_or_404(Ad.objects.annotate(average_rating=Avg('reviews__rating')), pk=pk)
    return render(request, 'ad_detail.html', {
        'ad': ad
    })


@login_required
def ad_create(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, id=category_id)
        Ad.objects.create(
            title=request.POST.get('title'),
            category=category,
            price=request.POST.get('price') or 0,
            description=request.POST.get('description'),
            image=request.FILES.get('image'),
            author=request.user
        )
        return redirect('ad_list')
    categories = Category.objects.all()
    return render(request, 'ad_form.html', {'categories': categories})


@login_required
def ad_update(request, pk):
    ad = get_object_or_404(Ad, pk=pk, author=request.user)
    if request.method == 'POST':
        category_id = request.POST.get('category')
        ad.title = request.POST.get('title')
        ad.category = get_object_or_404(Category, id=category_id)
        ad.price = request.POST.get('price') or 0
        ad.description = request.POST.get('description')
        if request.FILES.get('image'):
            ad.image = request.FILES.get('image')
        ad.save()
        return redirect('ad_detail', pk=ad.pk)

    categories = Category.objects.all()
    return render(request, 'ad_form.html', {
        'ad': ad,
        'categories': categories
    })


@login_required
def ad_delete(request, pk):
    ad = get_object_or_404(Ad, pk=pk, author=request.user)
    ad.delete()
    return redirect('profile')


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.bio = request.POST.get('bio')
        if request.FILES.get('avatar'):
            profile.image = request.FILES.get('avatar')
        profile.save()
        return redirect('profile')

    user_ads = Ad.objects.filter(author=request.user)
    favorite_ads = request.user.favorites.all()

    return render(request, 'profile.html', {
        'user_ads': user_ads,
        'favorite_ads': favorite_ads,
        'profile': profile,
    })


@login_required
def toggle_favorite(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, ad=ad)
    if not created:
        fav.delete()
    return redirect(request.META.get('HTTP_REFERER', 'ad_list'))


#Долгожданные отзывы спасибо gemini
def add_review(request, ad_id):
    if request.method == 'POST':
        ad = get_object_or_404(Ad, id=ad_id)
        rating = request.POST.get('rating')
        text = request.POST.get('text')

        if rating and text:
            Review.objects.create(
                ad=ad,
                rating=int(rating),
                text=text
            )
    return redirect('ad_detail', pk=ad_id)