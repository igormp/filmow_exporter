import requests
import requests
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, user):
        self.page = 1
        self.total_files = 1
        self.soup = BeautifulSoup(features="html.parser")

        self.user = user
        self.movies_parsed = 0
        self.total_files = 1

        self.parse(user)

    def parse(self, user):
        self.page = 1
        last_page = self.get_last_page(user)

        while self.page <= last_page:
            url = (
                "https://filmow.com/usuario/"
                + user
                + "/filmes/ja-vi/?pagina="
                + str(self.page)
            )

            source_code = requests.get(url).text

            soup = BeautifulSoup(source_code, "html.parser")

            if soup.find("h1").text == "Vixi! - Página não encontrada":
                raise Exception

            for title in soup.find_all("li", {"class": "movie_list_item"}):
                # print(title)
                print(
                    title.findChild("span", {"class": "star-rating"}).get(
                        "data-original-title"
                    )
                )
                break
                print(self.parse_movie("https://filmow.com" + title.get("href")))
                self.movies_parsed += 1
                break
            self.page += 1
            break

    def parse_movie(self, url):
        print(url)
        movie = {"title": None, "director": None, "year": None}
        source_code = requests.get(url).text
        soup = BeautifulSoup(source_code, "html.parser")

        try:
            movie["title"] = (
                soup.find("h2", {"class": "movie-original-title"}).get_text().strip()
            )
        except AttributeError:
            movie["title"] = soup.find("h1").get_text().strip()

        try:
            movie["director"] = (
                soup.find("span", {"itemprop": "director"})
                .select("strong")[0]
                .get_text()
            )
        except AttributeError:
            try:
                movie["director"] = (
                    soup.find("span", {"itemprop": "directors"}).getText().strip()
                )
            except AttributeError:
                movie["director"] = ""

        try:
            movie["year"] = soup.find("small", {"class": "release"}).get_text()
        except AttributeError:
            movie["year"] = ""

        return movie

    def get_last_page(self, user):
        url = "https://filmow.com/usuario/" + user + "/filmes/ja-vi/"

        source_code = requests.get(url).text

        soup = BeautifulSoup(source_code, "html.parser")

        try:
            tag = list(soup.find("div", {"class": "pagination"}).find("ul").children)[
                -2
            ]
            match = re.search(r"pagina=(\d*)", str(tag)).group(1)
            return int(match)
        except:
            return 1


Parser("imp2")