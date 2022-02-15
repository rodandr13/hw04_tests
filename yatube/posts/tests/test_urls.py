from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class StaticPageURLTesting(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth', )
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticPageURLTesting.user)
        cache.clear()

    def test_urls_uses_correct_template_guest_users(self):
        pages = (
            (reverse('posts:index'),
             'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user}),
             'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
             'posts/post_detail.html'),
        )
        for url, expect in pages:
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expect)

    def test_urls_uses_correct_template_auth_user(self):
        page_urls = (
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             'posts/create_post.html'),
            (reverse('posts:post_create'),
             'posts/create_post.html'),
        )
        for url, expect in page_urls:
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, expect)

    def test_urls_uses_correct_template_edit_author(self):
        author = StaticPageURLTesting.post.author
        authorized_client = self.user
        self.assertEqual(author, authorized_client)

    def test_urls_exists_at_desired_location(self):
        url_status_codes = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': self.user}): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse('posts:post_create'): HTTPStatus.FOUND,
        }
        for url, code in url_status_codes.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_server_responds_404_unexisted_page(self):
        response = self.authorized_client.get('/unixisted-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
