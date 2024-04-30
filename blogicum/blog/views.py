from django.http import Http404
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView)
from django.utils import timezone

from .queryset import annotate_and_order_posts, filter_published_posts
from .constants import POSTS_PER_PAGE
from .mixins import CommentMixin, DispatchAuthorMixin, PostMixin
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileEditForm
from .utils import get_post_data

User = get_user_model()


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=(self.request.user.username,))


class PostUpdateView(
        PostMixin, LoginRequiredMixin, DispatchAuthorMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class PostDeleteView(
        PostMixin, LoginRequiredMixin, DispatchAuthorMixin, DeleteView):
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class IndexListView(ListView):
    model = Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/index.html'

    def get_queryset(self):
        return (annotate_and_order_posts(
            filter_published_posts(self.model.objects.all())))


class ProfileListView(ListView):
    model = Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/profile.html'

    def get_queryset(self):
        queryset = self.model.objects.filter(
            author__username=self.kwargs['username'])
        queryset = annotate_and_order_posts(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = get_object_or_404(
            User, username=self.kwargs['username'])
        context['profile'] = profile_user
        context['editable'] = (
            self.request.user == profile_user
            and self.request.user.is_authenticated)
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    form_class = ProfileEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=(self.request.user.username,))


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            self.model.objects.select_related(
                'location', 'author', 'category'),
            pk=self.kwargs[self.pk_url_kwarg]
        )
        if not post.is_published and self.request.user != post.author:
            raise Http404('Этот пост снят с публикации и не доступен.')
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryPostsListView(ListView):
    model = Post
    paginate_by = POSTS_PER_PAGE
    template_name = 'blog/category.html'

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True)

        return (
            category.posts.select_related('location', 'author', 'category')
            .filter(is_published=True,
                    pub_date__lte=timezone.now())
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category.objects.values('id', 'title', 'description'),
            slug=self.kwargs['category_slug'])
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    post_obj = None

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_post_data(kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    ...
