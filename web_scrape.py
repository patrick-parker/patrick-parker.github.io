"""Scrape data off of Wikipedia and Citizendium"""

from __future__ import annotations

from re import compile as regex, sub
from typing import Dict, List, Tuple, Generator

from bs4 import BeautifulSoup
from requests import get

from database import Search


class DataCommonAttrs:
    """Common attributes that will be shared by both classes"""
    
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(DataCommonAttrs, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self, url: str) -> None:
        self.url: str = url
        self.disambiguated: bool | None = None
        self.pattern: str = r"\[[\d\w]+\]"
        self.http_codes: Dict[int, str] = {
            200: "OK",
            201: "Created",
            204: "No content",
            400: "Bad request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Page does not exist",
            500: "Internal server error",
        }

    def search(self, key_word: str) -> Generator[Tag, None, None]:
        """
        The Facade function

        Returns:
            List[Tag]: A list with either all the paragraphs or key words that
                lead to another page (in case of a disambiguation)
        """
        modified_kw: str = "_".join(key_word.split())
        response: Response = get(self.url + modified_kw, timeout=20)
        if response.status_code == 200:
            self.soup = BeautifulSoup(response.text, "html.parser")
            self.top: Tag = self.get_top()
        else:
            code: int = response.status_code
            raise ValueError(f'{code}: {self.http_codes[code]}')

        result: List[Tag] = []
        if self.disambiguated:
            result = self.disambiguation()
        else:
            self.find_p()
            result = self.get_paragraphs()
        new = Search(website=self.__class__.__name__, key_word=key_word)
        new.save()
        return result

    def disambiguation(self) -> List[Tag]:
        """pass"""

        elements: ResultSet = self.top.find_all(
            DataCommonAttrs.filter_elements
        )
        for element in elements:
            if element.name == "h2":
                yield f"\n{element.text.strip()}\n"
            else:
                for link in element:
                    first_half: str = link.text.splitlines()[0].strip()
                    if first_half:
                        yield sub(self.pattern, "", first_half)

    def get_paragraphs(self) -> List[Tag]:
        """
        Will find and return the paragraphs after the top element

        Returns:
            list: A list containing the paragraphs
        """

        # Iterate through every paragraph and get their text until
        # the element is no longer a paragraph
        for element in self.top.next_siblings:
            if element.name != "p":
                break
            yield sub(self.pattern, "", element.text)

    def find_p(self) -> None:
        """
        Find the first paragraph right after the top element
        """
        for element in self.top.next_elements:
            if (
                element is not None
                and element.name == "p"
                and not element.text.isspace()
                and element.parent.name == "div"
            ):
                self.top = element.previous_element
                break

    @staticmethod
    def filter_elements(tag) -> bool:
        """Filter an element"""
        return tag.name in ["ul", "h2"]


class Wikipedia(DataCommonAttrs):
    """
    Scrape data off of Wikipedia
    """

    def __init__(self) -> None:
        super().__init__("https://en.wikipedia.org/wiki/")

    def get_top(self) -> Tag:
        """
        Will find the tag right before the first paragraphs of the page

        Returns:
            Tag: The tag that was found
        """
        self.disambiguated: bool = False if self.soup.find("div", class_="dmbox-body") is None else True
        if self.disambiguated:
            top: Tag = self.soup.find("div", class_="mw-content-ltr mw-parser-output", lang="en", dir="ltr")
        else:
            top: Tag = (
                self.soup.find("span", class_="mw-page-title-main")
                or self.soup.find("h1", id="firstHeading", class_="firstHeading mw-first-heading")
            )
        return top


class Citizendium(DataCommonAttrs):
    """This class will scrape data off of citizendium.org/wiki/"""

    def __init__(self) -> None:
        super().__init__("https://citizendium.org/wiki/")

    def get_top(self) -> Tag:
        """
        Will find the tag right before the first paragraphs of the page

        Returns:
            Tag: The tag that was found
        """
        top: Tag | None = self.soup.find(
            "div",
            align="left",
            style="background-color: #cccccc; margin:0.5em;position:relative;",
        )
        self.disambiguated = False
        if top is None:
            top = self.soup.find("div", class_="mw-parser-output")
            self.disambiguated: bool = True
        return top
