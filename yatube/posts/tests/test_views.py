import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


from ..models import Post, Group, Follow
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.other_user = User.objects.create(username='OtherUser')
        cls.author = User.objects.create_user('TestAuthor')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.other_group = Group.objects.create(
            title='Заголовок второй группы',
            slug='other-slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_other_client = Client()
        self.authorized_other_client.force_login(self.other_user)
        cache.clear()

    def get_post_field_values(self, response, object):
        if object == 'page_obj':
            first_page_object = response.context[object][0]
            values = (
                (first_page_object.text, self.post.text),
                (first_page_object.author, self.post.author),
                (first_page_object.group, self.post.group),
                (first_page_object.image, self.post.image),
            )
            return values
        elif object == 'post':
            first_page_object = response.context[object]
            values = (
                (first_page_object.text, self.post.text),
                (first_page_object.author, self.post.author),
                (first_page_object.group, self.post.group),
                (first_page_object.id, self.post.id),
                (first_page_object.image, self.post.image),
            )
            return values

    def test_pages_uses_correct_template(self):
        page_urls = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list',
                     kwargs={'slug': self.post.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile', kwargs={'username': self.user}),
             'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
             'posts/post_detail.html'),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             'posts/create_post.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
        )
        for url, expect in page_urls:
            with self.subTest(reverse_name=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, expect)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_values = self.get_post_field_values(response, 'page_obj')
        for value, expect in post_values:
            with self.subTest(value=value):
                self.assertEqual(value, expect)

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post_values = self.get_post_field_values(response, 'page_obj')
        for value, expect in post_values:
            with self.subTest(value=value):
                self.assertEqual(value, expect)
        group_object = response.context['group']
        self.assertEqual(group_object.description, self.group.description)
        self.assertEqual(group_object.title, self.group.title)
        self.assertEqual(group_object.slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post_values = self.get_post_field_values(response, 'page_obj')
        for value, expect in post_values:
            with self.subTest(value=value):
                self.assertEqual(value, expect)
        author_object = response.context['author']
        self.assertEqual(author_object, self.user)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post_values = self.get_post_field_values(response, 'post')
        for value, expect in post_values:
            with self.subTest(value=value):
                self.assertEqual(value, expect)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNone(response.context.get('is_edit', None))
        other_group = Group.objects.filter(slug=self.other_group.slug)
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
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
        self.assertFalse(
            other_group[0].posts.filter(text='Тестовый пост', ).exists()
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

    def test_cache_for_index_page(self):
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_after_del = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content,
                         response_after_del.content)

    def test_profile_follow_unfollow(self):
        follow_author_before = self.user.follower.filter(
            author=self.author).count()
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        follow_author_after = self.user.follower.filter(
            author=self.author).count()
        self.assertEqual(
            follow_author_after,
            follow_author_before + 1
        )
        following_author = self.user.follower.filter(author=self.author)
        following_author.delete()
        self.assertEqual(
            follow_author_before,
            follow_author_after - 1
        )

    def test_post_for_followers(self):
        self.post = Post.objects.create(
            author=self.author,
            text='Пост для фолловеров',
        )
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')).context['page_obj']
        response_other_user = self.authorized_other_client.get(
            reverse('posts:follow_index')).context['page_obj']
        self.assertNotEqual(len(response), len(response_other_user))


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

        batch_size = 17
        posts = (Post(
            text=f'Пост № {i}',
            author=cls.user,
            group=cls.group) for i in range(batch_size)
        )
        Post.objects.bulk_create(posts, batch_size)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        cache.clear()

    def test_paginator_first_pages(self):
        pages = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        for value in pages:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_second_pages(self):
        pages = (
            (reverse('posts:index'),
             {'page': '2'}),
            (reverse('posts:profile', kwargs={'username': self.user}),
             {'page': '2'}),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             {'page': '2'}),
        )
        for value, args in pages:
            with self.subTest(value=value):
                response = self.authorized_client.get(value, args)
                self.assertEqual(len(response.context['page_obj']), 7)
