"""Render the readable structure of a DOCX without fetching external resources."""

import base64
from pathlib import Path
from zipfile import ZipFile

import mammoth
import nh3

DOCX_LIMIT = 24 * 1024**2
SAFE_IMAGES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

def filter_attribute(tag: str, attr: str, value: str) -> str | None:
    if tag == "a" and attr == "href":
        return value if value.lower().startswith(("https://", "http://", "#")) else None
    return value


CLEANER = nh3.Cleaner(
    tags={
        "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4",
        "h5", "h6", "hr", "img", "li", "ol", "p", "pre", "s", "strong", "sub",
        "sup", "table", "tbody", "td", "th", "thead", "tr", "ul",
    },
    attributes={
        "*": {"id"}, "a": {"href"}, "img": {"alt", "src"}, "ol": {"start"},
        "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"},
    },
    url_schemes={"https", "http", "data"},
    url_relative=lambda url: url if url.startswith("#") else None,
    attribute_filter=filter_attribute,
)


def render_docx(path: Path) -> str:
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if (
            len(entries) > 1000
            or sum(entry.file_size for entry in entries) > 96 * 1024**2
            or "word/document.xml" not in archive.namelist()
            or any(entry.file_size > 8 * 1024**2 for entry in entries if entry.filename.endswith(".xml"))
        ):
            raise ValueError("DOCX 结构或解压大小超出限制")

    remaining = DOCX_LIMIT

    @mammoth.images.img_element
    def image_source(image):
        nonlocal remaining
        if image.content_type not in SAFE_IMAGES:
            return {}
        with image.open() as stream:
            data = stream.read(min(6 * 1024**2, remaining) + 1)
        if len(data) > min(6 * 1024**2, remaining):
            return {}
        remaining -= len(data)
        encoded = base64.b64encode(data).decode("ascii")
        return {"src": f"data:{image.content_type};base64,{encoded}"}

    with path.open("rb") as source:
        result = mammoth.convert_to_html(
            source,
            convert_image=image_source,
            include_embedded_style_map=False,
            external_file_access=False,
            id_prefix="docx-",
            style_map="p[style-name='Title'] => h1:fresh\np[style-name='Subtitle'] => h2:fresh",
        )
    return CLEANER.clean(result.value)
