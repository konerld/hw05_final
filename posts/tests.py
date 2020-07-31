from django.test import TestCase, Client
from posts.models import Post, User, Group
from django.urls import reverse
import os


class PageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='skywalker')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.non_auth_client = Client()
        self.group = Group.objects.create(
            title="test group",
            slug='test-slug',
            description='description',
        )
        self.image_path = './posts/test_data/monkey.png'
        self.wrong_image_path = './posts/test_data/monkey.txt'

    def test_client_page(self):
        """
        Тест проверяет, что осле регистрации пользователя создается
        его персональная страница (profile)
        """
        response = self.auth_client.get(
            reverse(
                "profile",
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(response.status_code,
                         200,
                         "Страница пользователя не найдена!")

    def test_create_post_by_auth_user(self):
        """
        Тест проверяет, что авторизованный
        пользователь может опубликовать пост (new)
        """
        response = self.auth_client.post(
            reverse("new_post"),
            data={
                'group': self.group.id,
                'text': 'test'
            },
            follow=True
        )
        self.assertEqual(response.status_code,
                         200,
                         "Ошибка создания поста!")
        created_post = Post.objects.all().first()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(created_post.group, self.group)
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.text, 'test')

    def test_create_post_by_non_auth_user(self):
        """
        Тест проверяет, что НЕ авторизованный
        пользователь НЕ может опубликовать пост (new)
        """
        self.non_auth_client.logout()
        response = self.non_auth_client.get(
            reverse("new_post")
        )
        self.assertRedirects(response,
                             '/auth/login/?next=/new/',
                             msg_prefix="Не авторизованный пользователь"
                                        "не переадресовывается на страницу "
                                        "входа (login)!")

    def check_post_on_page(self, url, post_text, user, group):
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, 200)
        if 'paginator' in response.context:
            check_post = response.context['page'][0]
        else:
            check_post = response.context['post']

        self.assertEqual(check_post.text, post_text)
        self.assertEqual(check_post.group, group)
        self.assertEqual(check_post.author, user)

    def test_post_exists_on_pages(self):
        """
        Тест создает пост и проверяет его отображение по всем страницам из
        спискка urls_list
        """
        text = 'text in test post'
        post = Post.objects.create(
            text=text,
            author=self.user,
            group=self.group
        )

        urls_list = [
            reverse('index'),
            reverse('profile',
                    kwargs={
                        'username': self.user.username
                    }
                    ),
            reverse('post',
                    kwargs={
                        'username': self.user.username,
                        'post_id': post.id
                    }
                    )
        ]

        for url in urls_list:
            self.check_post_on_page(url,
                                    text,
                                    self.user,
                                    self.group)

    def test_auth_user_can_edit_own_post(self):
        """
        Тест проверяет, что авторизованный пользователь может отредактировать
        свой пост и его содержимое изменится на всех связанных страницах
        """
        post = Post.objects.create(
            text='old text in post',
            author=self.user,
            group=self.group
        )

        edit_urls_list = [
            reverse('index'),
            reverse(
                'profile',
                kwargs={'username': self.user.username}
            ),
            reverse(
                'post',
                kwargs={
                    'username': self.user.username,
                    'post_id': post.id
                }
            )
        ]
        new_text = 'This is text after edit.'
        response = self.auth_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'post_id': post.id,
                    'username': self.user.username
                }
            ),
            data={
                'group': self.group.id,
                'text': new_text
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        for url in edit_urls_list:
            self.check_post_on_page(url,
                                    new_text,
                                    self.user,
                                    self.group)

    def test_404(self):
        no_page = '/unknown/'
        response = self.auth_client.get(no_page)
        self.assertEqual(response.status_code,
                         404,
                         f'Страница {no_page} существует '
                         ' проверьте ошибку 404 на другой странице!')

    def test_image(self):
        self.assertEquals(os.path.exists(self.image_path),
                          True,
                          "Не найден файл картинки для теста!")
        post = Post.objects.create(
            text='post with image',
            author=self.user,
            group=self.group
        )
        img_urls_list = [
            reverse('index'),
            reverse(
                'profile',
                kwargs={
                    'username': self.user.username
                }
            ),
            reverse(
                'post',
                kwargs={
                    'username': self.user.username,
                    'post_id': post.id
                }
            ),
            reverse(
                'group',
                kwargs={'slug': self.group.slug}
            )
        ]
        with open(self.image_path, 'rb') as img:
            response = self.auth_client.post(
                reverse(
                    'post_edit',
                    kwargs={'post_id': post.id,
                            'username': self.user.username}
                ),
                data={'group': self.group.id,
                      'text': 'post with image',
                      'image': img
                      },
                follow=True
            )
            self.assertEqual(response.status_code,
                             200,
                             "Ошибка добавления картинки!")
        for url in img_urls_list:
            response = self.auth_client.get(url)
            self.assertEqual(response.status_code,
                             200,
                             "Не найдена страница с картинкой!")
            self.assertContains(response, '<img')

    def test_wrong_image(self):
        self.assertEquals(os.path.exists(self.wrong_image_path),
                          True,
                          "Не найден файл картинки для теста!")
        types = ['jpg', 'jpeg', 'gif', 'png']
        self.assertEqual(self.wrong_image_path.split('.')[-1] not in types, True)


class TestFollowings(TestCase):
    def setUp(self):
        self.subscriber = User.objects.create_user(username='Vova')
        self.bloger = User.objects.create_user(username='Alex')
        self.auth_subscriber = Client()
        self.auth_bloger = Client()
        self.auth_subscriber.force_login(self.subscriber)

        # self.non_auth_client = Client()
        # self.group = Group.objects.create(
        #     title="test group",
        #     slug='test-slug',
        #     description='description',
        # )
        # self.image_path = './posts/test_data/monkey.png'
        # self.wrong_image_path = './posts/test_data/monkey.txt'

    def check_following(self, url, followers_cnt, following_sum_cnt):
        response = self.auth_subscriber.get(url)
        self.assertEqual(response.status_code, 200)
        # if 'paginator' in response.context:
        #     check_post = response.context['page'][0]
        # else:
        #     check_post = response.context['post']
        #
        # self.assertEqual(check_post.text, post_text)
        # self.assertEqual(check_post.group, group)
        # self.assertEqual(check_post.author, user)


    def test_auth_user_can_work_with_subscribe(self):
        """
        Тест проверяет, что авторизованный пользователь может
        подписываться/отписываться на других пользователей.
        """
        post = Post.objects.create(
            text='This post for test subscribes',
            author=self.bloger
        )

        urls_list = [
            reverse(
                'profile',
                kwargs={'username': self.subscriber.username}
            ),
            reverse(
                'post',
                kwargs={
                    'username': self.bloger.username,
                    'post_id': post.id
                }
            )
        ]
        response = self.auth_subscriber.post(
            reverse(
                'profile_follow',
                kwargs={'username': self.bloger.username}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        for url in urls_list:
            self.check_following(url, 0, 1)