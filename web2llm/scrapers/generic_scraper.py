import copy
import warnings
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning, element
from markdownify import markdownify as md

from ..config import WEB_SCRAPER_CONFIG
from ..utils import fetch_html
from .base_scraper import BaseScraper

# Some sites have malformed HTML that generates this warning. It's safe to ignore.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class GenericScraper(BaseScraper):
    """Scrapes a standard HTML webpage, with special handling for content fragments."""

    def __init__(self, url: str):
        super().__init__(source=url)
        self.config = WEB_SCRAPER_CONFIG

    def _get_code_language(self, el: element.Tag) -> str:
        if el.get_text(strip=True).startswith(">>>"):
            return "python"

        # Check parent divs for `highlight-<lang>` classes
        for parent in el.parents:
            if parent.name == "div" and "class" in parent.attrs:
                for class_name in parent["class"]:
                    if class_name.startswith("highlight-"):
                        lang = class_name.replace("highlight-", "").strip()
                        if lang not in ["default", "text"]:
                            return lang

        # Check the element itself for `language-<lang>` classes
        class_list = el.get("class", [])
        for class_name in class_list:
            if class_name.startswith("language-"):
                return class_name.replace("language-", "").strip()
        return ""

    def _extract_links_recursive(self, element: element.Tag, base_url: str) -> list:
        list_element = element.find(["ul", "ol", "dl"]) if element else None
        if not list_element:
            return []

        links = []
        for item in list_element.find_all(["li", "dt"], recursive=False):
            link_tag = item.find("a", href=True, recursive=False)
            nested_list = item.find(["ul", "ol", "dl"], recursive=False)

            if link_tag:
                text = " ".join(link_tag.get_text(strip=True).split())
                if text:
                    link_data = {
                        "text": text,
                        "href": urljoin(base_url, link_tag["href"]),
                    }
                    if nested_list:
                        link_data["children"] = self._extract_links_recursive(
                            nested_list, base_url
                        )
                    links.append(link_data)
            elif nested_list:
                links.extend(self._extract_links_recursive(nested_list, base_url))
        return links

    def _extract_flat_links(self, element: element.Tag, base_url: str) -> list:
        links = []
        if not element:
            return links
        for a_tag in element.find_all("a", href=True):
            text = " ".join(a_tag.get_text(strip=True).split())
            if text:
                links.append({"text": text, "href": urljoin(base_url, a_tag["href"])})
        return links

    def _get_fragment_element(self, soup, fragment_id):
        """Finds the content associated with a URL fragment (e.g., #some-id)."""
        target_element = soup.find(id=fragment_id)
        if not target_element:
            return None

        # If the target is not a header, it's its own self-contained section.
        if target_element.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return copy.copy(target_element)

        # If the target is a header, we collect its content until the next header of the same or higher level.
        stop_level = int(target_element.name[1])
        stop_tags = [f"h{i}" for i in range(1, stop_level + 1)]

        main_element = soup.new_tag("div")
        main_element.append(copy.copy(target_element))

        # Iterate through siblings of the target element, respecting hierarchy.
        for sibling in target_element.find_next_siblings():
            if isinstance(sibling, NavigableString):
                main_element.append(copy.copy(sibling))
                continue

            # If the sibling itself is a stop tag, we're done.
            if sibling.name in stop_tags:
                break

            # The tricky case: the sibling might CONTAIN a stop tag.
            if sibling.find(stop_tags):
                safe_sibling = copy.deepcopy(sibling)
                nested_stop_tag = safe_sibling.find(stop_tags)

                # Prune the copy: remove the stop tag and everything after it.
                for tag in nested_stop_tag.find_next_siblings():
                    tag.decompose()
                nested_stop_tag.decompose()

                main_element.append(safe_sibling)
                break
            else:
                main_element.append(copy.copy(sibling))

        return main_element

    def scrape(self) -> tuple[str, dict]:
        html = fetch_html(self.source)
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.string.strip() if soup.title else "No Title Found"
        description_tag = soup.find("meta", attrs={"name": "description"})
        description = (
            description_tag["content"].strip()
            if description_tag and description_tag.get("content")
            else ""
        )

        main_element = None
        parsed_url = urlparse(self.source)
        fragment_id = parsed_url.fragment

        if fragment_id:
            main_element = self._get_fragment_element(soup, fragment_id)

        if not main_element:
            for selector in self.config["main_content_selectors"]:
                main_element = soup.select_one(selector)
                if main_element:
                    break

        final_title = title
        if fragment_id and main_element:
            h1 = main_element.find(["h1", "h2", "h3"])
            if h1:
                final_title = f"{title} (Section: {h1.get_text(strip=True)})"
            else:
                final_title = f"{title} (Section: #{fragment_id})"

        scraped_at = datetime.now(timezone.utc).isoformat()

        front_matter = (
            "---\n"
            f'title: "{final_title}"\n'
            f'source_url: "{self.source}"\n'
            f'description: "{description}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n\n"
        )

        nav_element = None
        for selector in self.config["nav_selectors"]:
            nav_element = soup.select_one(selector)
            if nav_element:
                break

        context_data = {
            "source_url": self.source,
            "page_title": final_title,
            "scraped_at": scraped_at,
            "navigation_links": self._extract_links_recursive(nav_element, self.source),
            "footer_links": self._extract_flat_links(soup.find("footer"), self.source),
        }

        if not main_element:
            return front_matter, context_data

        # Clean up common clutter before converting to markdown
        for a in main_element.select("a.headerlink"):
            a.decompose()
        for img in main_element.select('img[alt*="Badge"]'):
            if img.parent.name == "a":
                img.parent.decompose()
            else:
                img.decompose()

        # Make relative links absolute
        for a_tag in main_element.find_all("a", href=True):
            a_tag["href"] = urljoin(self.source, a_tag["href"])

        content_md = md(
            str(main_element),
            heading_style="ATX",
            bullets="*",
            code_language_callback=self._get_code_language,
        )

        return front_matter + content_md, context_data
