from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': _('Текст поста'),
            'group': 'Группа',
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError('Введите текст поста')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': _('Текст комментария')
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError('Введите текст комментария')
        return data
