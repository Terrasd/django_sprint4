from django.db import models
from django.contrib.auth import get_user_model

from .constants import MAX_LENGTH, MAX_LENGTH_ADMIN_PANEL

User = get_user_model()


class BaseModel(models.Model):
    """Абстрактная модель. Добавляет флаг is_published и дату публикации."""

    is_published = (
        models.BooleanField(
            default=True,
            verbose_name='Опубликовано',
            help_text='Снимите галочку, чтобы скрыть публикацию.'))
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Добавлено')

    class Meta:
        abstract = True


class Location(BaseModel):
    name = models.CharField(
        max_length=MAX_LENGTH, verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name',)

    def __str__(self):
        return self.name[:MAX_LENGTH_ADMIN_PANEL]


class Category(BaseModel):
    title = models.CharField(max_length=MAX_LENGTH, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, цифры, дефис и подчёркивание.')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title',)

    def __str__(self):
        return self.title[:MAX_LENGTH_ADMIN_PANEL]


class Post(BaseModel):
    title = models.CharField(max_length=MAX_LENGTH, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text='Если установить дату и время в будущем — '
                  'можно делать отложенные публикации.')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='post',
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name='Категория'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images',
        blank=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title[:MAX_LENGTH_ADMIN_PANEL]


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='публикация'
    )
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Добавлено')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор комментария')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return f'Комментарий пользователя {self.author} к посту {self.post}'
