from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

class AboutPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_about_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
