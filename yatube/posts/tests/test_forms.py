from django.urls import reverse
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..models import Post, Group
from ..forms import PostForm

User = get_user_model()


class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст 1'
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
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text='Тестовый пост',
            ).exists()
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        base_text = self.post.text
        form_data = {
            'text': 'Редактированный пост',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True,
        )
        edited_text = Post.objects.get(id=1)
        self.assertNotEqual(base_text, edited_text)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Post.objects.count(), post_count)
