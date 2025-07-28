import io
import os
from datetime import datetime, timezone

import pdfplumber
import requests
from bs4 import BeautifulSoup

from ..utils import fetch_html
from .base_scraper import BaseScraper


class PDFScraper(BaseScraper):
    """
    Scrapes a PDF from a local path or URL, with special handling for
    arXiv pages to extract better metadata.
    """

    def _find_title_heuristic(self, first_page: pdfplumber.page.Page) -> str:
        """A simple heuristic to find the title on the first page of a PDF."""
        # Find the text object with the largest font size. This is often the title.
        largest_text = ""
        max_size = 0
        for obj in first_page.chars:
            if obj.get("size", 0) > max_size:
                max_size = obj["size"]

        if max_size > 0:
            title_candidates = [obj["text"] for obj in first_page.chars if obj.get("size") == max_size]
            largest_text = "".join(title_candidates).strip()

        return largest_text

    def _get_metadata_from_arxiv(self, url: str) -> dict:
        """For an arXiv PDF URL, fetches metadata from the abstract page."""
        metadata = {"title": "", "description": ""}
        landing_page_url = url.replace("/pdf/", "/abs/")

        try:
            html = fetch_html(landing_page_url)
            soup = BeautifulSoup(html, "lxml")

            title_tag = soup.select_one("h1.title")
            if title_tag:
                metadata["title"] = title_tag.get_text(strip=True).replace("Title:", "").strip()

            desc_tag = soup.select_one("blockquote.abstract")
            if desc_tag:
                desc_text = desc_tag.get_text().replace("Abstract:", "").strip()
                metadata["description"] = " ".join(desc_text.split())
        except IOError as e:
            print(f"Warning: Could not fetch or parse arXiv landing page: {e}")
        return metadata

    def scrape(self) -> tuple[str, dict]:
        is_remote = self.source.startswith(("http://", "https://"))
        metadata = {"title": "", "description": ""}

        pdf_handle = None
        try:
            if is_remote:
                print(f"Downloading remote PDF: {self.source}")
                if "arxiv.org/pdf/" in self.source:
                    metadata.update(self._get_metadata_from_arxiv(self.source))

                response = requests.get(self.source, timeout=30)
                response.raise_for_status()
                pdf_handle = io.BytesIO(response.content)
            else:
                if not os.path.isfile(self.source):
                    raise FileNotFoundError(f"File not found: {self.source}")
                print(f"Processing local PDF file: {self.source}")
                pdf_handle = open(self.source, "rb")

            pdf_content = ""
            title = metadata.get("title")
            with pdfplumber.open(pdf_handle) as pdf:
                if not title and pdf.metadata and pdf.metadata.get("Title"):
                    title = pdf.metadata["Title"]

                if not title and len(pdf.pages) > 0:
                    title = self._find_title_heuristic(pdf.pages[0])

                if not title:
                    title = os.path.basename(self.source)

                metadata["title"] = title

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text(keep_blank_chars=True, x_tolerance=2) or ""
                    pdf_content += f"\n\n--- Page {i + 1} ---\n\n{text}"

        finally:
            if pdf_handle:
                pdf_handle.close()

        scraped_at = datetime.now(timezone.utc).isoformat()
        source_key = "source_url" if is_remote else "source_path"

        front_matter = (
            "---\n"
            f'title: "{metadata["title"]}"\n'
            f'{source_key}: "{self.source}"\n'
            f'description: "{metadata.get("description", "")}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n"
        )

        context_data = {
            source_key: self.source,
            "page_title": metadata["title"],
            "description": metadata.get("description", ""),
            "scraped_at": scraped_at,
        }

        return front_matter + pdf_content, context_data
