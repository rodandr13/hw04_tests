from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group
from ..forms import PostForm

User = get_user_model()


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.user = PostPagesTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_page_object = response.context['page_obj'][0]
        self.assertEqual(first_page_object.text, self.post.text)
        self.assertEqual(first_page_object.author, self.post.author)
        self.assertEqual(first_page_object.group, self.post.group)

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_page_object = response.context['page_obj'][0]
        self.assertEqual(first_page_object.text, self.post.text)
        self.assertEqual(first_page_object.author, self.post.author)
        self.assertEqual(first_page_object.group, self.post.group)
        group_object = response.context['group']
        self.assertEqual(group_object.description, self.group.description)
        self.assertEqual(group_object.title, self.group.title)
        self.assertEqual(group_object.slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_page_object = response.context['page_obj'][0]
        self.assertEqual(first_page_object.text, self.post.text)
        self.assertEqual(first_page_object.author, self.post.author)
        self.assertEqual(first_page_object.group, self.post.group)
        author_object = response.context['author']
        self.assertEqual(author_object, self.post.author)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_page_object = response.context['post']
        self.assertEqual(first_page_object.text, self.post.text)
        self.assertEqual(first_page_object.author, self.post.author)
        self.assertEqual(first_page_object.group, self.post.group)
        self.assertEqual(first_page_object.id, self.post.id)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))

        post = PostPagesTest.post
        if post.group:
            response_index = self.authorized_client.get(reverse('posts:index'))
            response_profile = self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': self.user})
            )
            response_group = self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            )
            self.assertEqual(
                response_index.context['page_obj'][0].text, self.post.text
            )
            self.assertEqual(
                response_profile.context['page_obj'][0].text, self.post.text
            )
            self.assertEqual(
                response_group.context['page_obj'][0].text, self.post.text
            )
            self.assertEqual(
                response_group.context['page_obj'][0].group.slug,
                self.group.slug
            )

    def test_edit_post_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        first_page_object = response.context['post']
        self.assertEqual(first_page_object.id, self.post.id)
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertTrue(response.context['is_edit'])
        self.assertIsInstance(response.context['is_edit'], bool)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        for post in range(0, 17):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост{post}',
                group=cls.group,
            )

    def setUp(self):
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 7)
