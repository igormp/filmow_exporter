import re

import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, user):
        self.page = 1
        self.soup = BeautifulSoup(features="lxml")

        self.user = user

        # List containing tuples of (title, director, year, rating)
        self.movies_list = []

    async def init(self):
        self.session = aiohttp.ClientSession()
        await self.parse(self.user)

    async def parse(self, user):
        self.page = 1
        last_page = await self.__get_last_page(user)

        async def parse_page(page):
            url = (
                "https://filmow.com/usuario/"
                + user
                + "/filmes/ja-vi/?pagina="
                + str(page)
            )

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
                title, director, year = await self.__parse_movie(
                    "https://filmow.com" + movie_page
                )
                return (title, director, year, nota)

            page_res = await asyncio.gather(
                *[
                    get_movie_info(movie)
                    for movie in soup.find_all("li", {"class": "movie_list_item"})
                ]
            )

            return page_res

        self.movies_list = await asyncio.gather(
            *[parse_page(page) for page in range(1, last_page + 1)]
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
        async with self.session.get(url) as response:
            return await response.text()

    async def __parse_movie(self, url):

        title = None
        director = None
        year = None

        source_code = await self.__fetch(url)

        soup = BeautifulSoup(source_code, "lxml")

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

        return (title, director, year)

    async def __get_last_page(self, user):
        url = "https://filmow.com/usuario/" + user + "/filmes/ja-vi/"

        source_code = await self.__fetch(url)

        soup = BeautifulSoup(source_code, "lxml")

        try:
            tag = list(soup.find("div", {"class": "pagination"}).find("ul").children)[
                -2
            ]
            match = re.search(r"pagina=(\d*)", str(tag)).group(1)
            return int(match)
        except:
            return 1


def main():
    parse = Parser("imp2")

    asyncio.get_event_loop().run_until_complete(parse.init())

    parse.write_csv()


if __name__ == "__main__":
    main()
