import random
import string
from locust import HttpUser, task, between

# НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ (прям как будто ПСИ прохожу)

def random_url():
    path = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"https://example.com/{path}"

class ShortLinksUser(HttpUser):
    wait_time = between(0.5, 2)
    short_codes: list[str] = []

    def on_start(self):
        # ох уж эти случайные юзернеймы
        username = "user_" + "".join(random.choices(string.ascii_lowercase, k=6))
        self.client.post("/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "loadtest123",
        })
        resp = self.client.post("/auth/login", json={
            "username": username,
            "password": "loadtest123",
        })
        token = resp.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(5)
    def create_link(self):
        resp = self.client.post("/links/shorten", json={"original_url": random_url()})
        if resp.status_code == 201:
            code = resp.json().get("short_code")
            if code:
                ShortLinksUser.short_codes.append(code)
                if len(ShortLinksUser.short_codes) > 500:
                    ShortLinksUser.short_codes = ShortLinksUser.short_codes[-500:]

    @task(10)
    def redirect(self):
        if ShortLinksUser.short_codes:
            code = random.choice(ShortLinksUser.short_codes)
            self.client.get(f"/links/{code}", allow_redirects=False)

    @task(3)
    def get_stats(self):
        if ShortLinksUser.short_codes:
            code = random.choice(ShortLinksUser.short_codes)
            self.client.get(f"/links/{code}/stats")

    @task(2)
    def search(self):
        self.client.get("/links/search", params={"original_url": random_url()})

    @task(1)
    def joke(self):
        # все хотят шутки все несуществующие пользователи из нагрузочного тестирования хотят смеяться они хотят ржать!
        self.client.get("/extras/joke")

    @task(1)
    def create_link_with_alias(self):
        alias = "load_" + "".join(random.choices(string.ascii_lowercase, k=6))
        self.client.post("/links/shorten", json={
            "original_url": random_url(),
            "custom_alias": alias,
        })
