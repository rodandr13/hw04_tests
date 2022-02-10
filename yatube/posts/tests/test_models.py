from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_str_for_post(self):
        post = PostModelTest.post
        post_str = post.__str__()[:15]
        expected_object_name = post.text
        self.assertEqual(post_str, expected_object_name)

    def test_str_for_group(self):
        group = PostModelTest.group
        group_str = group.__str__()
        expected_object_name = group.title
        self.assertEqual(group_str, expected_object_name)

    def test_verbose(self):
        post = PostModelTest.post
        field_verbose = {
            'text': 'Пост',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )
