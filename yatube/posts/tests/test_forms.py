import shutil
import tempfile
from http import HTTPStatus

from django.urls import reverse
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings

from ..models import Post, Group, Comment
from ..forms import PostForm

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUserForm')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.other_group = Group.objects.create(
            title='Заголовок новой группы',
            slug='new-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTest.user)
        cache.clear()

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'author': self.user,
            'text': self.post.text,
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        last_post = Post.objects.order_by('pub_date').last()
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text=self.post.text,
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(last_post.image.name,
                         'posts/' + form_data['image'].name)
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_text_in_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Редактированный пост',
            'group': self.other_group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(self.other_group, post.group)
        self.assertEqual(Post.objects.count(), post_count)

    def test_comment_for_auth_user(self):
        post = Post.objects.create(
            text='Test post.',
            author=self.user,
        )
        comments_count = post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
            'post': post.id,
            'author': self.user.id
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.comments.count(), comments_count + 1)
