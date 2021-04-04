import re

import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer
import time
import cchardet


class Exporter:
    def __init__(self, user):
        self.page = 1
        self.soup = BeautifulSoup(features="lxml")

        self.user = user

        self.total_pages = 1

        self.pages_done = 0

        # List containing tuples of (title, director, year, rating)
        self.movies_list = []

    async def init(self):
        self.session = aiohttp.ClientSession()

        valid = await self.valid_user()

        if not valid:
            return False

        print("Starting to parse user data...")
        # await self.parse()

    async def valid_user(self):
        print("Checking user...")
        url = "https://filmow.com/usuario/" + self.user
        source_code = await self.__fetch(url)

        soup = BeautifulSoup(source_code, "lxml")

        if soup.find("h1").text == "Vixi! - Página não encontrada":
            return False

        return True

    async def parse(self):
        self.page = 1
        self.total_pages = await self.__get_last_page()

        print(f"Parsing all {self.total_pages} pages...")

        async def parse_page(page):
            url = (
                "https://filmow.com/usuario/"
                + self.user
                + "/filmes/ja-vi/?pagina="
                + str(page)
            )
            print("Parsing page", page)
            source_code = await self.__fetch(url)

            soup = BeautifulSoup(source_code, "lxml")

            if soup.find("h1").text == "Vixi! - Página não encontrada":
                raise Exception

            async def get_movie_info(movie):
                try:
                    nota = (
                        movie.findChild("span", {"class": "star-rating"})
                        .get("title")
                        .split(" ")[1]
                    )
                except AttributeError:
                    nota = None

                movie_page = movie.findChild("a", {"class": "tip-movie"}).get("href")
                title, director, year = await self.parse_movie(
                    "https://filmow.com" + movie_page
                )
                return (title, director, year, nota)

            page_res = await asyncio.gather(
                *[
                    get_movie_info(movie)
                    for movie in soup.find_all("li", {"class": "movie_list_item"})
                ]
            )

            self.pages_done += 1

            return page_res

        self.movies_list = await asyncio.gather(
            *[parse_page(page) for page in range(1, self.total_pages + 1)]
        )

        # flatten our list
        self.movies_list = [item for sublist in self.movies_list for item in sublist]

        await self.session.close()

    def get_df(self):
        cols = ["Title", "Directors", "Year", "Rating"]
        df = pd.DataFrame(self.movies_list, columns=cols)
        return df

    def write_csv(self):
        df = self.get_df()
        df.to_csv(self.user + ".csv", index=False)

    async def __fetch(self, url):
        # async with self.session.get(url, allow_redirects=False) as response:
        async with self.session.get(url) as response:
            return await response.text()

    # @profile
    async def parse_movie(self, url):
        title = None
        director = None
        year = None

        source_code = await self.__fetch(url)

        strainer = SoupStrainer(["h1", "h2", "span", "small"])
        soup = BeautifulSoup(source_code, "lxml", parse_only=strainer)

        try:
            title = (
                soup.find("h2", {"class": "movie-original-title"}).get_text().strip()
            )
        except AttributeError:
            title = soup.find("h1").get_text().strip()

        try:
            director = (
                soup.find("span", {"itemprop": "director"})
                .select("strong")[0]
                .get_text()
            )
        except AttributeError:
            try:
                director = (
                    soup.find("span", {"itemprop": "directors"}).getText().strip()
                )
            except AttributeError:
                director = None

        try:
            year = soup.find("small", {"class": "release"}).get_text()
        except AttributeError:
            year = None
        print(title, director, year)
        return (title, director, year)

    async def __get_last_page(self):
        url = "https://filmow.com/usuario/" + self.user + "/filmes/ja-vi/"

        print("Getting total page number...")
        source_code = await self.__fetch(url)

        soup = BeautifulSoup(source_code, "lxml")

        try:
            tag = list(soup.find("div", {"class": "pagination"}).find("ul").children)[
                -2
            ]
            match = re.search(r"pagina=(\d*)", str(tag)).group(1)
            return int(match)
        except Exception:
            return 1

    async def display_status(self):
        while self.pages_done < self.total_pages:
            await asyncio.sleep(1)
            print("done: ", self.pages_done)


def main():
    parse = Exporter("imp2")
    # start = time.time()
    # asyncio.get_event_loop().run_until_complete(
    #     # asyncio.wait([parse.init(), parse.display_status()])
    #     asyncio.wait([parse.init()])
    # )
    # print(f"Took {time.time() - start} seconds")
    # parse.write_csv()
    p = "https://filmow.com/o-exterminador-do-futuro-2-o-julgamento-final-t766/"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([parse.init()]))
    loop.run_until_complete(asyncio.wait([parse.parse_movie(p)]))


if __name__ == "__main__":
    main()
