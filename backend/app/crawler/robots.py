from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsChecker:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.robots_url = urljoin(
            self.base_url + "/",
            "robots.txt",
        )

        self.parser = RobotFileParser()
        self.parser.set_url(self.robots_url)

        self.loaded = False

    async def load(self) -> None:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=10.0,
            ) as client:
                response = await client.get(self.robots_url)

                if response.status_code == 200:
                    self.parser.parse(
                        response.text.splitlines()
                    )
                else:
                    self.parser.parse([])

        except httpx.HTTPError:
            self.parser.parse([])

        self.loaded = True

    def can_fetch(
        self,
        url: str,
        user_agent: str = "*",
    ) -> bool:
        if not self.loaded:
            raise RuntimeError(
                "RobotsChecker must be loaded before checking URLs"
            )

        return self.parser.can_fetch(
            user_agent,
            url,
        )