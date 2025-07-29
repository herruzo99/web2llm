import io
import os
import sys
from datetime import datetime, timezone

import httpx
import pdfplumber
import yaml
from bs4 import BeautifulSoup

from ..utils import fetch_html
from .base_scraper import BaseScraper


class PDFScraper(BaseScraper):
    """
    Scrapes a PDF from a local path or URL, with special handling for
    arXiv pages to extract better metadata.
    """

    def __init__(self, url: str, config: dict):
        super().__init__(source=url, config=config)
        self.logger.debug("PDFScraper initialized in debug mode.")

    def _find_title_heuristic(self, first_page: pdfplumber.page.Page) -> str:
        """A simple heuristic to find the title on the first page of a PDF."""
        self.logger.debug("  - Running title heuristic on first page.")
        largest_text = ""
        max_size = 0
        for obj in first_page.chars:
            if obj.get("size", 0) > max_size:
                max_size = obj["size"]

        if max_size > 0:
            title_chars = [obj["text"] for obj in first_page.chars if obj.get("size") == max_size]
            largest_text = "".join(title_chars).strip()
            self.logger.debug(f"  - Heuristic found title '{largest_text}' with font size {max_size}.")

        return largest_text

    async def _get_metadata_from_arxiv(self, url: str) -> dict:
        """For an arXiv PDF URL, fetches metadata from the abstract page."""
        metadata = {"title": "", "description": ""}
        landing_page_url = url.replace("/pdf/", "/abs/")
        self.logger.debug(f"Detected arXiv URL. Fetching metadata from: {landing_page_url}")

        try:
            # HACK: arxiv.org is static; no need for Playwright. We override the flag.
            html = await fetch_html(landing_page_url, render_js=False, debug=self.debug)
            soup = BeautifulSoup(html, "lxml")

            title_tag = soup.select_one("h1.title")
            if title_tag:
                metadata["title"] = title_tag.get_text(strip=True).replace("Title:", "").strip()
                self.logger.debug(f"  - Found arXiv title: '{metadata['title']}'")

            desc_tag = soup.select_one("blockquote.abstract")
            if desc_tag:
                desc_text = desc_tag.get_text().replace("Abstract:", "").strip()
                metadata["description"] = " ".join(desc_text.split())
                self.logger.debug(f"  - Found arXiv abstract: '{metadata['description'][:100]}...'")
        except IOError as e:
            self.logger.debug(f"  - Could not fetch or parse arXiv landing page: {e}")
        return metadata

    async def scrape(self) -> tuple[str, dict]:
        if self.render_js:
            self.logger.warning("Warning: The --render-js flag is not applicable to PDF scraping and will be ignored.", file=sys.stderr)
        self.logger.debug(f"Starting scrape for PDF source: {self.source}")
        is_remote = self.source.startswith(("http://", "https://"))
        metadata = {"title": "", "description": ""}

        pdf_handle = None
        try:
            if is_remote:
                self.logger.debug("Source is a remote URL.")
                if "arxiv.org/pdf/" in self.source:
                    metadata.update(await self._get_metadata_from_arxiv(self.source))

                self.logger.debug(f"Downloading remote PDF: {self.source}")
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.source, timeout=30, follow_redirects=True)
                    response.raise_for_status()
                    pdf_handle = io.BytesIO(response.content)
                self.logger.debug(f"Downloaded {len(pdf_handle.getvalue())} bytes.")
            else:
                self.logger.debug("Source is a local file path.")
                if not os.path.isfile(self.source):
                    raise FileNotFoundError(f"File not found: {self.source}")
                self.logger.debug(f"Opening local PDF file: {self.source}")
                pdf_handle = open(self.source, "rb")

            pdf_content = ""
            title = metadata.get("title")
            with pdfplumber.open(pdf_handle) as pdf:
                self.logger.debug(f"pdfplumber opened PDF with {len(pdf.pages)} pages.")
                if not title and pdf.metadata and pdf.metadata.get("Title"):
                    title = pdf.metadata["Title"]
                    self.logger.debug(f"Found title in PDF metadata: '{title}'")

                if not title and len(pdf.pages) > 0:
                    title = self._find_title_heuristic(pdf.pages[0])

                if not title:
                    title = os.path.basename(self.source)
                    self.logger.debug(f"No title found. Using filename as fallback: '{title}'")

                metadata["title"] = title

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text(keep_blank_chars=True, x_tolerance=2) or ""
                    pdf_content += f"\n\n--- Page {i + 1} ---\n\n{text}"
                    self.logger.debug(f"  - Extracted {len(text)} characters from page {i + 1}.")

        finally:
            if pdf_handle and not is_remote:
                pdf_handle.close()

        scraped_at = datetime.now(timezone.utc).isoformat()
        source_key = "source_url" if is_remote else "source_path"

        front_matter_data = {
            "title": metadata["title"],
            source_key: self.source,
            "description": metadata.get("description", ""),
            "scraped_at": scraped_at,
        }
        front_matter_string = yaml.dump(front_matter_data, sort_keys=False, default_flow_style=False, indent=2)
        front_matter = f"---\n{front_matter_string}---\n"

        context_data = {
            source_key: self.source,
            "page_title": metadata["title"],
            "description": metadata.get("description", ""),
            "scraped_at": scraped_at,
        }
        self.logger.debug("PDF scrape complete.")
        return front_matter + pdf_content, context_data
