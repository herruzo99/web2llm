import copy
import warnings
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import yaml
from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning, element
from markdownify import markdownify as md

from ..errors import ContentNotFoundError
from ..utils import fetch_html
from .base_scraper import BaseScraper

# Some sites have malformed HTML that generates this warning. It's safe to ignore.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class GenericScraper(BaseScraper):
    """Scrapes a standard HTML webpage, with special handling for content fragments."""

    def __init__(self, url: str, config: dict):
        super().__init__(source=url, config=config)
        self.scraper_config = self.config.get("web_scraper", {})
        self.logger.debug("GenericScraper initialized in debug mode.")

    def _process_and_reference_links(self, main_element: element.Tag, base_url: str) -> dict[str, str]:
        """
        Finds all links, replaces them with a reference number `[1]`,
        and returns a map of reference numbers to URLs.
        """
        url_to_ref_map = {}
        ref_counter = 1
        all_links = main_element.find_all("a", href=True)

        for a_tag in all_links:
            href = a_tag.get("href", "")
            if not href or href.startswith(("mailto:", "tel:", "#")):
                continue

            abs_url = urljoin(base_url, href)
            if abs_url not in url_to_ref_map:
                url_to_ref_map[abs_url] = ref_counter
                ref_counter += 1

        self.logger.debug(f"Found {len(url_to_ref_map)} unique links to reference.")

        for a_tag in all_links:
            href = a_tag.get("href", "")
            if not href or href.startswith(("mailto:", "tel:", "#")):
                a_tag.unwrap()
                continue

            abs_url = urljoin(base_url, href)
            ref_num = url_to_ref_map.get(abs_url)

            link_text = a_tag.get_text(strip=True)
            if not link_text:
                a_tag.decompose()
                continue

            replacement_text = f"{link_text} [{ref_num}]"
            new_text_node = NavigableString(replacement_text)
            a_tag.replace_with(new_text_node)

        context_references = {str(v): k for k, v in url_to_ref_map.items()}
        return context_references

    def _get_code_language(self, el: element.Tag) -> str:
        if el.get_text(strip=True).startswith(">>>"):
            return "python"
        for parent in el.parents:
            if parent.name == "div" and "class" in parent.attrs:
                for class_name in parent["class"]:
                    if class_name.startswith("highlight-"):
                        lang = class_name.replace("highlight-", "").strip()
                        if lang not in ["default", "text", "sh", "shell", "bash"]:
                            return lang
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
                    link_data = {"text": text, "href": urljoin(base_url, link_tag["href"])}
                    if nested_list:
                        link_data["children"] = self._extract_links_recursive(nested_list, base_url)
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

    def _get_fragment_element(self, soup: BeautifulSoup, fragment_id: str) -> element.Tag | None:
        target_element = soup.find(id=fragment_id)
        if not target_element:
            self.logger.debug(f"Fragment ID '{fragment_id}' not found in the document.")
            return None
        if target_element.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.logger.debug(f"Fragment ID is on a <{target_element.name}> tag; treating as self-contained.")
            return copy.copy(target_element)
        content_start_node = target_element
        while content_start_node.parent and content_start_node.parent.name != "body":
            if list(content_start_node.find_next_siblings()):
                break
            content_start_node = content_start_node.parent
        self.logger.debug(f"Identified effective content start node: <{content_start_node.name}>")
        stop_level = int(target_element.name[1])
        stop_tags = [f"h{i}" for i in range(1, stop_level + 1)]
        self.logger.debug(f"Original target is <h{stop_level}>. Capturing content until next <h1...h{stop_level}>.")
        section_container = soup.new_tag("div")
        section_container.append(copy.copy(content_start_node))
        for sibling in content_start_node.find_next_siblings():
            if not hasattr(sibling, "name") or not sibling.name:
                continue
            if sibling.name in stop_tags or sibling.find(stop_tags):
                self.logger.debug(f"  - Found stop condition at <{sibling.name}>. Halting capture.")
                break
            section_container.append(copy.copy(sibling))
        self.logger.debug(f"Finished gathering fragment. Container has {len(section_container.contents)} direct children.")
        return section_container

    async def scrape(self) -> tuple[str, dict]:
        self.logger.debug(f"Starting scrape for URL: {self.source}")
        parsed_url = urlparse(self.source)
        fragment_id = parsed_url.fragment

        main_content_selectors = self.scraper_config.get("main_content_selectors", [])
        selectors_to_wait_for = None if fragment_id else main_content_selectors

        html = await fetch_html(self.source, render_js=self.render_js, wait_for_selectors=selectors_to_wait_for, debug=self.debug)
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.string.strip() if soup.title else "No Title Found"
        description_tag = soup.find("meta", attrs={"name": "description"})
        description = description_tag["content"].strip() if description_tag and description_tag.get("content") else ""

        main_element = None
        if fragment_id:
            main_element = self._get_fragment_element(soup, fragment_id)

        if not main_element:
            for selector in main_content_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    break
        if not main_element:
            if not self.render_js:
                raise ContentNotFoundError(
                    "No main content found using standard selectors. "
                    "The page may require JavaScript to render. Try again with the --render-js flag."
                )
            else:
                raise ContentNotFoundError(
                    "No main content found, even after rendering with a browser. "
                    "The page structure may be unsupported or the selectors in your config are incorrect."
                )

        final_title = title
        if fragment_id and main_element:
            h1 = main_element.find(["h1", "h2", "h3"])
            if h1:
                final_title = f"{title} (Section: {h1.get_text(strip=True)})"
            else:
                final_title = f"{title} (Section: #{fragment_id})"

        for a in main_element.select("a.headerlink"):
            a.decompose()
        for img in main_element.select('img[alt*="Badge"]'):
            if img.parent.name == "a":
                img.parent.decompose()
            else:
                img.decompose()

        link_references = self._process_and_reference_links(main_element, self.source)

        front_matter_data = {
            "title": final_title,
            "source_url": self.source,
            "description": description,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        if link_references:
            front_matter_data["link_references"] = link_references

        front_matter_string = yaml.dump(front_matter_data, sort_keys=False, default_flow_style=False, indent=2)
        front_matter = f"---\n{front_matter_string}---\n\n"

        content_md = md(
            str(main_element),
            heading_style="ATX",
            bullets="*",
            code_language_callback=self._get_code_language,
            wrap=False,
            wrap_last_p=False,
        )
        if not content_md:
            raise ContentNotFoundError(
                "Main content found but empty. The page structure may be unsupported or the selectors in your config are incorrect."
            )

        nav_element = soup.select_one("nav")
        nav_links = self._extract_links_recursive(nav_element, self.source)
        footer_links = self._extract_flat_links(soup.find("footer"), self.source)

        context_data = {
            "source_url": self.source,
            "page_title": final_title,
            "scraped_at": front_matter_data["scraped_at"],
            "navigation_links": nav_links,
            "footer_links": footer_links,
        }

        self.logger.debug(f"Converted main content to Markdown ({len(content_md)} chars).")
        self.logger.debug("Scrape complete.")
        return front_matter + content_md, context_data
