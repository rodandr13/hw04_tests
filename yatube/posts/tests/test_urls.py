from http import HTTPStatus

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
        self.user = StaticPageURLTesting.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template_guest_users(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/auth/',
            'posts/post_detail.html': '/posts/1/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_auth_user(self):
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_uses_correct_template_edit_author(self):
        author = StaticPageURLTesting.post.author
        authorized_client = self.user
        self.assertEqual(author, authorized_client)

    def test_urls_exists_at_desired_location(self):
        url_status_codes = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/auth/': 200,
            '/posts/1/': 200,
            '/create/': 302,
            '/posts/1/edit/': 302,
        }
        for url, code in url_status_codes.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_server_responds_404_unexisted_page(self):
        response = self.authorized_client.get('/unixisted-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
