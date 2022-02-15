from django.test import TestCase
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
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Описание тестовое в посте',
        )

    def test_str_for_post_and_group(self):
        models = (
            (PostModelTest.post, self.post.text[:15]),
            (PostModelTest.group, self.group.title),
        )
        for value, expect in models:
            with self.subTest(field=value):
                self.assertEqual(str(value), expect)

    def test_verbose(self):
        post = PostModelTest.post
        field_verbose = (
            ('text', 'Пост'),
            ('pub_date', 'Дата публикации'),
            ('author', 'Автор'),
            ('group', 'Группа'),
        )
        for value, expect in field_verbose:
            with self.subTest(field=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expect
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = (
            ('text', 'Введите текст поста'),
            ('group', 'Выберите группу'),
        )
        for field, expected_value in field_help_text:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )
