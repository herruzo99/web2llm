"""A generic scraper for standard HTML documentation websites."""

import warnings
from bs4 import BeautifulSoup, element, XMLParsedAsHTMLWarning
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from markdownify import markdownify as md

from .base_scraper import BaseScraper
from ..utils import fetch_html
from ..config import WEB_SCRAPER_CONFIG

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

class GenericScraper(BaseScraper):
    """
    Scrapes a standard HTML webpage. Includes extensive debugging for fragment scraping.
    """

    def __init__(self, url: str):
        super().__init__(url)
        self.config = WEB_SCRAPER_CONFIG

    def _get_code_language(self, el: element.Tag) -> str:
        if el.get_text(strip=True).startswith('>>>'):
            return 'python'
        for parent in el.parents:
            if parent.name == 'div' and 'class' in parent.attrs:
                for class_name in parent['class']:
                    if class_name.startswith('highlight-'):
                        lang = class_name.replace('highlight-', '').strip()
                        if lang not in ['default', 'text']:
                            return lang
        class_list = el.get('class', [])
        for class_name in class_list:
            if class_name.startswith('language-'):
                return class_name.replace('language-', '').strip()
        return ''

    def _extract_links_recursive(self, element: element.Tag, base_url: str) -> list:
        list_element = element.find(['ul', 'ol', 'dl']) if element else None
        if not list_element:
            return []
        links = []
        for item in list_element.find_all(['li', 'dt'], recursive=False):
            link_tag = item.find('a', href=True, recursive=False)
            nested_list = item.find(['ul', 'ol', 'dl'], recursive=False)
            if link_tag:
                text = ' '.join(link_tag.get_text(strip=True).split())
                if text:
                    link_data = {"text": text, "href": urljoin(base_url, link_tag['href'])}
                    if nested_list:
                        link_data['children'] = self._extract_links_recursive(nested_list, base_url)
                    links.append(link_data)
            elif nested_list:
                links.extend(self._extract_links_recursive(nested_list, base_url))
        return links

    def _extract_flat_links(self, element: element.Tag, base_url: str) -> list:
        links = []
        if not element:
            return links
        for a_tag in element.find_all("a", href=True):
            text = ' '.join(a_tag.get_text(strip=True).split())
            if text:
                links.append({"text": text, "href": urljoin(base_url, a_tag['href'])})
        return links

    def scrape(self) -> tuple[str, dict]:
        html = fetch_html(self.url)
        soup = BeautifulSoup(html, 'lxml')

        title = soup.title.string.strip() if soup.title else "No Title Found"
        description_tag = soup.find("meta", attrs={"name": "description"})
        description = description_tag['content'].strip() if description_tag and description_tag.get('content') else "No description found."
        scraped_at = datetime.now(timezone.utc).isoformat()

        main_element = None
        parsed_url = urlparse(self.url)
        fragment_id = parsed_url.fragment

        if fragment_id:
            target_element = soup.find(id=fragment_id)
            if target_element:
                if target_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    section_container = target_element
                    while not section_container.find_next_sibling() and section_container.parent and section_container.parent.name != 'body':
                        section_container = section_container.parent
                    
                    stop_level = int(target_element.name[1])
                    stop_tags = [f"h{i}" for i in range(1, stop_level + 1)]

                    elements_to_extract = [section_container]
                    for sibling in section_container.find_next_siblings():
                        if sibling.name and sibling.name in stop_tags:
                            break
                        if hasattr(sibling, 'find') and sibling.find(stop_tags):
                            break
                        elements_to_extract.append(sibling)

                    main_element = soup.new_tag("div")
                    for el in elements_to_extract:
                        main_element.append(el)
                else:
                    main_element = target_element

        if not main_element:
            for selector in self.config["main_content_selectors"]:
                main_element = soup.select_one(selector)
                if main_element:
                    break

        nav_element = None
        for selector in self.config["nav_selectors"]:
            nav_element = soup.select_one(selector)
            if nav_element: break
        
        footer_element = soup.find('footer')
        navigation_links = self._extract_links_recursive(nav_element, self.url)
        footer_links = self._extract_flat_links(footer_element, self.url)

        final_title = title
        if fragment_id and main_element:
            final_title = f"{title} (Section: {fragment_id})"
        
        context_data = {
            "source_url": self.url,
            "page_title": final_title,
            "scraped_at": scraped_at,
            "navigation_links": navigation_links,
            "footer_links": footer_links
        }
        
        front_matter = (
            "---\n"
            f'title: "{final_title}"\n'
            f'source_url: "{self.url}"\n'
            f'description: "{description}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n\n"
        )

        if not main_element:
            return front_matter, context_data

        for a in main_element.select('a.headerlink'): a.decompose()
        for img in main_element.select('img[alt*="Badge"]'):
            if img.parent.name == 'a': img.parent.decompose()
            else: img.decompose()
        
        for a_tag in main_element.find_all('a', href=True):
            a_tag['href'] = urljoin(self.url, a_tag['href'])
        
        content_md = md(str(main_element), heading_style="ATX", bullets="*", code_language_callback=self._get_code_language)
        
        final_markdown = front_matter + content_md
        return final_markdown, context_data