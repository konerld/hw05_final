from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Post, Group, User, Comment, Follow
from . forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    groups = get_object_or_404(Group, slug=slug)
    posts = groups.group_posts.all()
    page_number = request.GET.get('page')
    paginator = Paginator(posts, 10)
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": groups, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    return render(request, 'post_new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    followers_sum = Follow.objects.filter(author=author).count()
    following_sum = Follow.objects.filter(user=author).count()
    params = {
                'page': page,
                'paginator': paginator,
                'author': author,
                'followers_sum': followers_sum,
                'following_sum': following_sum,
                'post_sum': posts.count()
    }
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author).first()
        params.update({'following': following,})
    return render(
        request,
        'profile.html',
        params
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm(request.POST or None,
                       instance=None
                       )
    post_sum = Post.objects.filter(author=author).count()
    followers_sum = Follow.objects.filter(author=post.author).count()
    following_sum = Follow.objects.filter(user=post.author).count()
    params = {
                'post': post,
                'author': author,
                'items': comments,
                'form': form,
                'followers_sum': followers_sum,
                'following_sum': following_sum,
                'post_sum': post_sum
    }
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author).exists()
        params.update({'following': following})
    return render(
        request,
        'post.html',
        params
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'post_new.html',
        {
            'form': form,
            'post': post
        }
    )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = CommentForm(request.POST or None,
                       instance=None
                    )
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    if request.method == 'GET':
        return redirect('post', username=username, post_id=post_id)


@login_required()
def follow_index(request):
    obj_list = Follow.objects.select_related(
        'author',
        'user').filter(user=request.user)
    author_list = [obj.author for obj in obj_list]
    post_list = Post.objects.filter(author__in=author_list)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "follow.html",
        {
            'page': page,
            'paginator': paginator,
        }
    )


@login_required()
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    obj = Follow.objects.filter(
        user=request.user,
        author=author).get_or_create(user=request.user,
                                     author=author)
    if not author.id != request.user.id:
        new = Follow(user=request.user, author=author)
        new.save()
    return redirect('profile', username=username)


@login_required()
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    obj = Follow.objects.filter(user=request.user, author=author).first()
    if obj:
        obj.delete()
    return redirect('profile', username=username)
