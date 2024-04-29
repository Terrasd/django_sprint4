from django.utils import timezone
from django.db.models import Count


def annotate_and_order_posts(queryset):
    return queryset.annotate(
        comment_count=Count('comments')).order_by('-pub_date')


def filter_published_posts(queryset):
    return queryset.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).select_related('location', 'author', 'category')
