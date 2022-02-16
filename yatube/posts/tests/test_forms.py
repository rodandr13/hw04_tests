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
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTest.user)
        cache.clear()

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст 1',
            'group': self.group.id
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
