"""Extract EPUB structure without renumbering existing filename-based locators.

This preserves semantic marks and native image bytes, not a browser rendering.
Unsupported meaning-bearing CSS is reported rather than silently called faithful.
The caller owns staging/promotion; this module must never publish into a live corpus.
"""
from __future__ import annotations

import hashlib
import io
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit


MEANING_CSS = {"text-decoration", "text-decoration-line", "list-style-type", "display", "visibility", "content"}
BLOCKS = {"p", "div", "section", "article", "blockquote", "figure", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def member_path(base: str, href: str) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.query or "\\" in href or "\x00" in href:
        raise ValueError("EPUB reference is not a local archive member")
    target = unquote(parsed.path)
    if "\x00" in target or "\\" in target:
        raise ValueError("EPUB reference contains an encoded unsafe character")
    if target.startswith("/"):
        raise ValueError("EPUB absolute archive reference")
    result = posixpath.normpath(posixpath.join(posixpath.dirname(base), target))
    if result in {"", ".", ".."} or result.startswith("../") or "\\" in result or "\x00" in result:
        raise ValueError("EPUB reference escapes archive")
    return result


def xml(data: bytes) -> ET.Element:
    # The supplied EPUB is UTF-8. Reject other encodings rather than letting an
    # encoded declaration evade the entity guard (e.g. UTF-16 with NUL bytes).
    if b"\x00" in data:
        raise ValueError("EPUB XML must be UTF-8")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("EPUB XML must be UTF-8") from exc
    if "<!ENTITY" in text.upper():
        raise ValueError("EPUB entity declarations are unsupported")
    return ET.fromstring(text)


def declarations(text: str) -> dict[str, str]:
    return {k.strip().lower(): v.strip().lower() for part in text.split(";")
            if ":" in part for k, v in [part.split(":", 1)] if k.strip().lower() in MEANING_CSS}


def css_rules(text: str, warnings: set[str]) -> list[tuple[str, dict[str, str]]]:
    result = []
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
        values = declarations(body)
        if not values:
            continue
        for selector in selectors.split(","):
            selector = selector.strip()
            if not re.fullmatch(r"(?:[a-zA-Z][\w-]*|\*)?(?:[.#][\w-]+)*", selector) or not selector:
                warnings.add("Unsupported meaning-bearing CSS selector: " + selector)
                continue
            result.append((selector, values))
    return result


def styles(element: ET.Element, rules: list[tuple[str, dict[str, str]]]) -> dict[str, str]:
    chosen: dict[str, tuple[tuple[int, int, int], str]] = {}
    for order, (selector, values) in enumerate(rules):
        target = re.match(r"^[\w*-]+", selector)
        if target and target[0] not in {"*", tag(element)}:
            continue
        if any(value != element.get("id") for value in re.findall(r"#([\w-]+)", selector)):
            continue
        if not set(re.findall(r"\.([\w-]+)", selector)).issubset(element.get("class", "").split()):
            continue
        weight = 100 * selector.count("#") + 10 * selector.count(".") + bool(target and target[0] != "*")
        for key, value in values.items():
            priority = (int("!important" in value), int(weight), order)
            if key not in chosen or priority >= chosen[key][0]:
                chosen[key] = (priority, value.replace("!important", "").strip())
    for key, value in declarations(element.get("style", "")).items():
        priority = (int("!important" in value), 1000, len(rules))
        if key not in chosen or priority >= chosen[key][0]:
            chosen[key] = (priority, value.replace("!important", "").strip())
    return {key: value for key, (_, value) in chosen.items()}


def list_label(number: int, kind: str) -> str:
    if kind in {"disc", "circle", "square"}:
        return "-"
    if kind == "none":
        return "[unmarked list item]"
    if kind in {"lower-alpha", "upper-alpha", "a", "A"} and number > 0:
        value = ""
        while number:
            number, digit = divmod(number - 1, 26)
            value = chr(97 + digit) + value
        return (value.upper() if kind in {"upper-alpha", "A"} else value) + "."
    if kind in {"lower-roman", "upper-roman", "i", "I"} and 0 < number < 4000:
        value = ""
        for amount, token in [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
            count, number = divmod(number, amount)
            value += token * count
        return (value.lower() if kind in {"lower-roman", "i"} else value) + "."
    if kind not in {"decimal", "1"}:
        raise ValueError("Unsupported EPUB list label: " + kind)
    return str(number) + "."


def extract(source: dict, original: Path, derived_root: Path) -> tuple[list[dict], dict]:
    """Write native assets only under the caller's derived staging root."""
    original_bytes = original.read_bytes()
    if digest(original_bytes) != source["sha256"]:
        raise ValueError("EPUB original hash mismatch")
    records = []
    derived_root = derived_root.resolve()
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate EPUB archive names")
        # No extractall: filenames and references can never select filesystem writes.
        if sum(i.file_size for i in archive.infolist()) > 256 * 1024 * 1024:
            raise ValueError("EPUB uncompressed data exceeds bounded extractor limit")
        roots = [e for e in xml(archive.read("META-INF/container.xml")).iter() if tag(e) == "rootfile"]
        if len(roots) != 1:
            raise ValueError("EPUB needs one unambiguous package")
        package_path = member_path("container", roots[0].attrib["full-path"])
        package_bytes = archive.read(package_path)
        package = xml(package_bytes)
        items = {}
        for element in package.iter():
            if tag(element) != "item":
                continue
            key = element.attrib["id"]
            if key in items:
                raise ValueError("Duplicate EPUB manifest ID")
            items[key] = {**element.attrib, "path": member_path(package_path, element.attrib["href"])}
        spine = []
        for element in package.iter():
            if tag(element) == "itemref":
                spine.append((items[element.attrib["idref"]]["path"], element.get("linear", "yes")))
        spine_paths = [p for p, _ in spine]
        if len(set(spine_paths)) != len(spine_paths) or not spine_paths:
            raise ValueError("Missing or duplicate EPUB spine entries")
        content = sorted(n for n in names if n.lower().endswith((".xhtml", ".html", ".htm")))
        if not set(spine_paths).issubset(content):
            raise ValueError("EPUB spine points outside indexed documents")
        ordered = spine_paths + [p for p in content if p not in spine_paths]
        labels: dict[str, list[str]] = {}
        for item in items.values():
            if item.get("media-type") != "application/x-dtbncx+xml":
                continue
            for point in xml(archive.read(item["path"])).iter():
                if tag(point) != "navPoint":
                    continue
                label = next((e for e in point if tag(e) == "navLabel"), None)
                dest = next((e for e in point if tag(e) == "content"), None)
                if label is not None and dest is not None:
                    target = member_path(item["path"], dest.attrib["src"])
                    labels.setdefault(target, []).append(" ".join("".join(label.itertext()).split()))
        assets = {}
        source_slug = re.sub(r"[^a-z0-9]+", "-", source["source_id"].lower()).strip("-")
        for item in items.values():
            if not item.get("media-type", "").startswith("image/"):
                continue
            raw = archive.read(item["path"])
            sha = digest(raw)
            suffix = Path(item["path"]).suffix.lower()
            if not re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
                suffix = ".bin"
            relative = f"epub-assets/{source_slug}/{sha}{suffix}"
            destination = derived_root / relative
            if not destination.resolve().is_relative_to(derived_root):
                raise ValueError("EPUB asset destination escapes derived root")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and destination.read_bytes() != raw:
                raise ValueError("EPUB asset destination conflict")
            destination.write_bytes(raw)
            assets[item["path"]] = {"archive_path": item["path"], "path": relative,
                                    "sha256": sha, "media_type": item["media-type"]}
        for index, name in enumerate(content, 1):
            raw = archive.read(name)
            document = xml(raw)
            warnings: set[str] = set()
            rules = []
            for element in document.iter():
                if tag(element) == "link" and "stylesheet" in element.get("rel", "").split():
                    css = archive.read(member_path(name, element.attrib["href"])).decode("utf-8")
                    rules.extend(css_rules(css, warnings))
                elif tag(element) == "style":
                    rules.extend(css_rules("".join(element.itertext()), warnings))
            images = []

            def inner(element: ET.Element, depth: int) -> str:
                return (element.text or "") + "".join(render(child, depth) + (child.tail or "") for child in element)

            def render(element: ET.Element, depth: int = 0) -> str:
                kind = tag(element)
                if kind in {"head", "script", "style"}:
                    if kind == "script":
                        warnings.add("Script omitted from prose; original is preserved")
                    return ""
                style = styles(element, rules)
                if kind in {"ol", "ul"}:
                    children = [c for c in element if tag(c) == "li"]
                    if ((element.text or "").strip() or any(tag(c) != "li" or (c.tail or "").strip() for c in element)):
                        raise ValueError("EPUB list has content outside list items")
                    reverse = "reversed" in element.attrib
                    counter = int(element.get("start", str(len(children) if reverse else 1)))
                    default = style.get("list-style-type", element.get("type", "decimal" if kind == "ol" else "disc"))
                    lines = []
                    for child in children:
                        counter = int(child.get("value", str(counter)))
                        marker = list_label(counter, styles(child, rules).get("list-style-type", default))
                        lines.append("  " * depth + marker + " " + render(child, depth + 1).strip())
                        counter += -1 if reverse else 1
                    result = "\n" + "\n".join(lines) + "\n"
                elif kind in {"img", "image"}:
                    href = element.get("src") or element.get("{http://www.w3.org/1999/xlink}href") or element.get("href")
                    if not href:
                        raise ValueError("EPUB image lacks a reference")
                    asset = assets.get(member_path(name, href))
                    if asset is None:
                        raise ValueError("EPUB image missing from image manifest")
                    images.append({**asset, "alt": element.get("alt", "")})
                    result = "[Image: " + asset["archive_path"] + ("; alt: " + element.get("alt") if element.get("alt") else "") + "]"
                elif kind == "br":
                    result = "\n"
                else:
                    result = inner(element, depth)
                if kind in {"s", "strike", "del"} or "line-through" in style.get("text-decoration", "") + style.get("text-decoration-line", ""):
                    result = "[crossed out: " + result.strip() + "]"
                if style.get("display") == "none" or style.get("visibility") == "hidden" or "hidden" in element.attrib:
                    result = "[hidden source content: " + result.strip() + "]"
                if "content" in style:
                    warnings.add("CSS generated content requires visual inspection")
                if kind in BLOCKS or kind == "tr":
                    result = "\n\n" + result.strip() + "\n\n"
                if kind in {"td", "th"}:
                    result = " | " + result.strip()
                return result

            body = next((e for e in document.iter() if tag(e) == "body"), document)
            text = render(body)
            text = re.sub(r"[ \t]+\n", "\n", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            titles = labels.get(name, [])
            if not titles:
                titles = [" ".join("".join(e.itertext()).split()) for e in document.iter() if tag(e) in {"h1", "h2"}]
            if not titles:
                titles = [" ".join("".join(e.itertext()).split()) for e in document.iter() if tag(e) == "title"]
            text = "Chapter: " + " / ".join(titles or [name]) + "\n\n" + text
            record = {"schema_version": "1.0.0", "source_id": source["source_id"],
                      "source_sha256": source["sha256"], "source_path": source["source_path"],
                      "format": "epub", "section": index, "section_path": name,
                      "locator": f"file:{source['source_id']}:s{index:04d}",
                      "reading_order": ordered.index(name) + 1,
                      "spine_position": spine_paths.index(name) + 1 if name in spine_paths else None,
                      "spine_linear": dict(spine).get(name), "chapter_titles": titles,
                      "section_sha256": digest(raw), "package_sha256": digest(package_bytes),
                      "search_text": text, "embedded_text": text, "ocr_text": "",
                      "epub_images": images, "extraction_warnings": sorted(warnings),
                      "visual_dependency": bool(images or warnings),
                      "visual_review_status": "native_assets_available_not_reviewed" if images else "not_indicated",
                      "page_image": None,
                      "citation": {"source_id": source["source_id"], "section": index,
                                   "section_path": name, "original_sha256": source["sha256"]}}
            records.append(record)
        catalog = f"epub-assets/{source_slug}/manifest.json"
        if not (derived_root / catalog).resolve().is_relative_to(derived_root):
            raise ValueError("EPUB catalog destination escapes derived root")
        (derived_root / catalog).parent.mkdir(parents=True, exist_ok=True)
        (derived_root / catalog).write_text(json.dumps({"source_id": source["source_id"],
            "source_sha256": source["sha256"], "package_path": package_path,
            "package_sha256": digest(package_bytes), "images": list(assets.values()),
            "spine": [{"path": p, "linear": linear} for p, linear in spine]}, indent=2) + "\n")
    return records, {"status": "ok_with_warnings" if any(r["extraction_warnings"] for r in records) else "ok",
                     "section_count": len(records), "embedded_visual_asset_count": len(assets),
                     "spine_count": len(spine), "asset_manifest": catalog,
                     "asset_manifest_sha256": digest((derived_root / catalog).read_bytes()),
                     "semantics": "native_spine_titles_list_labels_strike_and_asset_links",
                     "locator_policy": "preserved_sorted_filename_section_ids"}
