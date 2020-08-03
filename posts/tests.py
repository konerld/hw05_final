from django.test import TestCase, Client
from posts.models import Post, User, Group, Follow, Comment
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
from PIL import Image


class CommonFunc:
    def check_post_on_page(self, client, url, post_text, user, group):
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        if "paginator" in response.context:
            check_post = response.context["page"][0]
        else:
            check_post = response.context["post"]

        self.assertEqual(check_post.text, post_text)
        self.assertEqual(check_post.group, group)
        self.assertEqual(check_post.author, user)


class PageTest(TestCase, CommonFunc):
    def setUp(self):
        self.user = User.objects.create_user(username="skywalker")
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.non_auth_client = Client()
        self.group = Group.objects.create(
            title="test group", slug="test-slug", description="description",
        )

    def test_client_page(self):
        """
        Тест проверяет, что осле регистрации пользователя создается
        его персональная страница (profile)
        """
        response = self.auth_client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200, "Страница пользователя не найдена!")

    def test_create_post_by_auth_user(self):
        """
        Тест проверяет, что авторизованный
        пользователь может опубликовать пост (new)
        """
        response = self.auth_client.post(
            reverse("new_post"),
            data={"group": self.group.id, "text": "test"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200, "Ошибка создания поста!")
        created_post = Post.objects.all().first()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(created_post.group, self.group)
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.text, "test")

    def test_create_post_by_non_auth_user(self):
        """
        Тест проверяет, что НЕ авторизованный
        пользователь НЕ может опубликовать пост (new)
        """
        self.non_auth_client.logout()
        response = self.non_auth_client.get(reverse("new_post"))
        self.assertRedirects(
            response,
            "/auth/login/?next=/new/",
            msg_prefix="Не авторизованный пользователь"
            "не переадресовывается на страницу "
            "входа (login)!",
        )

    def test_post_exists_on_pages(self):
        """
        Тест создает пост и проверяет его отображение по всем страницам из
        спискка urls_list
        """
        text = "text in test post"
        post = Post.objects.create(text=text, author=self.user, group=self.group)

        urls_list = [
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse(
                "post", kwargs={"username": self.user.username, "post_id": post.id}
            ),
        ]

        for url in urls_list:
            with self.subTest(url=url):
                self.check_post_on_page(
                    self.auth_client, url, text, self.user, self.group
                )

    def test_auth_user_can_edit_own_post(self):
        """
        Тест проверяет, что авторизованный пользователь может отредактировать
        свой пост и его содержимое изменится на всех связанных страницах
        """
        post = Post.objects.create(
            text="old text in post", author=self.user, group=self.group
        )

        edit_urls_list = [
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse(
                "post", kwargs={"username": self.user.username, "post_id": post.id}
            ),
        ]
        new_text = "This is text after edit."
        response = self.auth_client.post(
            reverse(
                "post_edit", kwargs={"post_id": post.id, "username": self.user.username}
            ),
            data={"group": self.group.id, "text": new_text},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        for url in edit_urls_list:
            with self.subTest(url=url):
                self.check_post_on_page(
                    self.auth_client, url, new_text, self.user, self.group
                )

    def test_404(self):
        response = self.auth_client.get("/unknown/")
        self.assertEqual(
            response.status_code,
            404,
            "Страница '/unknown/' существует "
            " проверьте ошибку 404 на другой странице!",
        )

    def _create_image(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            image = Image.new("RGB", (200, 200), "white")
            image.save(f, "PNG")
        return open(f.name, mode="rb")

    def test_image(self):
        post = Post.objects.create(
            text="post with image", author=self.user, group=self.group
        )
        img_urls_list = [
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse(
                "post", kwargs={"username": self.user.username, "post_id": post.id}
            ),
            reverse("group", kwargs={"slug": self.group.slug}),
        ]
        img = self._create_image()
        response = self.auth_client.post(
            reverse(
                "post_edit",
                kwargs={"post_id": post.id, "username": self.user.username},
            ),
            data={"group": self.group.id, "text": "post with image", "image": img},
            follow=True,
        )
        self.assertEqual(response.status_code, 200, "Ошибка добавления картинки!")
        for url in img_urls_list:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(
                    response.status_code, 200, "Не найдена страница с картинкой!"
                )
                self.assertContains(response, "<img")

    def test_wrong_image(self):
        post = Post.objects.create(
            text="post with bad image", author=self.user, group=self.group
        )
        file = SimpleUploadedFile("filename.txt", b"hello world", "text/plain")
        response = self.auth_client.post(
            reverse(
                "post_edit",
                kwargs={"post_id": post.id, "username": self.user.username},
            ),
            data={"group": self.group.id, "text": "post with bad image", "image": file},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "form",
            "image",
            "Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.",
        )


class TestFollowings(TestCase, CommonFunc):
    def setUp(self):
        self.subscriber = User.objects.create_user(username="vova")
        self.bloger = User.objects.create_user(username="Alex")
        self.no_subscriber = User.objects.create_user(username="goga")
        self.auth_subscriber = Client()
        self.auth_bloger = Client()
        self.auth_no_subscriber = Client()
        self.auth_subscriber.force_login(self.subscriber)
        self.auth_no_subscriber.force_login(self.no_subscriber)
        self.post = Post.objects.create(
            text="This post for test subscribes", author=self.bloger
        )
        self.urls_list = [
            reverse("profile", kwargs={"username": self.subscriber.username}),
            reverse(
                "post",
                kwargs={"username": self.bloger.username, "post_id": self.post.id},
            ),
        ]

    def test_follow(self):
        """
        Тест проверяет, что авторизованный пользователь может
        подписываться на других пользователей.
        """
        for url in self.urls_list:
            with self.subTest(url=url):
                follow = Follow.objects.filter(user=self.subscriber, author=self.bloger)
                if follow:
                    follow.delete()
                response = self.auth_subscriber.post(
                    reverse(
                        "profile_follow", kwargs={"username": self.bloger.username}
                    ),
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        """
        Тест проверяет, что авторизованный пользователь может
        отписываться от других пользователей.
        """
        for url in self.urls_list:
            with self.subTest(url=url):
                Follow.objects.get_or_create(user=self.subscriber, author=self.bloger)
                response = self.auth_subscriber.post(
                    reverse(
                        "profile_unfollow", kwargs={"username": self.bloger.username}
                    ),
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Follow.objects.count(), 0)

    def test_post_on_subscribes_page(self):
        """
        Тест проверяет, что новая запись появляется
        в ленте тех, кто на подписан на автора
        и не появляется в ленте тех, кто не подписан на него.
        """
        post_text = "This post for test subscribes line"
        post = Post.objects.create(text=post_text, author=self.bloger)
        Follow.objects.create(user=self.subscriber, author=self.bloger)
        self.assertEqual(Follow.objects.count(), 1)
        url = reverse("follow_index")
        self.check_post_on_page(self.auth_subscriber, url, post_text, self.bloger, None)
        response = self.auth_no_subscriber.get(url)
        self.assertNotIn(
            post,
            response.context["page"],
            "Пользователь не подписан на автора, но видит его посты",
        )


class TestComment(TestCase, CommonFunc):
    def setUp(self):
        self.member = User.objects.create_user(username="balabol")
        self.guest = User.objects.create_user(username="nobody")
        self.auth_member = Client()
        self.no_auth_guest = Client()
        self.auth_member.force_login(self.member)

    def test_post_comment_by_auth_user(self):
        post = Post.objects.create(text="Test comment by auth user", author=self.member)
        response = self.auth_member.post(
            reverse(
                "add_comment", kwargs={"username": self.member, "post_id": post.id,}
            ),
            data={"text": "test comment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Comment.objects.filter(post=post, text="test comment").exists(),
            "Комментарий не создался в базе",
        )
        response = self.auth_member.get(
            reverse(
                "post", kwargs={"username": self.member.username, "post_id": post.id}
            ),
        )
        self.assertContains(response, "test comment", status_code=200)

    def test_post_comment_by_non_auth_user(self):
        post = Post.objects.create(
            text="Test comment by non auth user", author=self.member
        )
        self.no_auth_guest.logout()
        response = self.no_auth_guest.post(
            reverse(
                "add_comment",
                kwargs={"username": self.auth_member, "post_id": post.id,},
            ),
            data={"text": "You can't!"},
            follow=True,
        )
        response = self.auth_member.get(
            reverse(
                "post", kwargs={"username": self.member.username, "post_id": post.id}
            ),
        )
        self.assertNotEqual(response, "You can't!")
