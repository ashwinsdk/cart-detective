"""Query relevance helpers shared by discovery and verification.

These helpers decide whether a piece of text (a registry key, a search result
title, a scraped product title) actually describes the product the user asked
for. They are deliberately deterministic and dependency free.
"""

import re
from urllib.parse import urlparse

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "for",
        "with",
        "and",
        "or",
        "of",
        "in",
        "on",
        "to",
        "best",
        "good",
        "cheap",
        "new",
        "buy",
        "online",
        "india",
        "under",
        "below",
        "above",
        "over",
        "upto",
        "up",
        "around",
        "within",
        "between",
        "price",
        "rs",
        "inr",
        "usd",
        "eur",
        "gbp",
        "rupees",
        "budget",
        "men",
        "mens",
        "women",
        "womens",
        "unisex",
        "me",
        "my",
        "i",
        "want",
        "need",
        "please",
        "less",
        "than",
        "max",
        "min",
    }
)

COLORS = frozenset(
    {
        "black",
        "white",
        "red",
        "blue",
        "green",
        "yellow",
        "grey",
        "gray",
        "orange",
        "pink",
        "purple",
        "brown",
        "silver",
        "gold",
        "navy",
        "beige",
        "maroon",
    }
)

# Words that mean a different product family than any registry category.
INCOMPATIBLE_QUALIFIERS = frozenset(
    {
        "bicycle",
        "cycling",
        "cycle",
        "ski",
        "skiing",
        "snowboard",
        "hockey",
        "cricket",
        "baby",
        "toddler",
        "infant",
        "kid",
        "dog",
        "cat",
        "pet",
    }
)

# Stemmed term -> stemmed terms that may stand in for it in product titles.
SYNONYMS: dict[str, frozenset[str]] = {
    "mobile": frozenset({"phone", "smartphone", "cellphone"}),
    "phone": frozenset({"mobile", "smartphone", "cellphone"}),
    "smartphone": frozenset({"mobile", "phone"}),
    "bike": frozenset({"motorcycle", "motorbike"}),
    "motorbike": frozenset({"motorcycle", "bike"}),
    "motorcycle": frozenset({"motorbike", "bike"}),
    "laptop": frozenset({"notebook"}),
    "notebook": frozenset({"laptop"}),
    "tv": frozenset({"television"}),
    "television": frozenset({"tv"}),
    "earphone": frozenset({"earbud", "headphone"}),
    "earbud": frozenset({"earphone"}),
    "sneaker": frozenset({"shoe"}),
}

# Words that mark a product as an accessory of the thing the user wants.
ACCESSORY_WORDS = frozenset(
    {
        "cover",
        "case",
        "replacement",
        "spare",
        "sticker",
        "decal",
        "cleaner",
        "pouch",
        "protector",
        "skin",
    }
)

# Result pages that are never product pages.
BLOCKED_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "quora.com",
    "wikipedia.org",
    "pinterest.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "medium.com",
    "blogspot.com",
    "wordpress.com",
)

_BUDGET_RE = re.compile(
    r"\b(?:under|below|up\s*to|upto|within|max|less\s+than|around|above|over)\s*"
    r"(?:rs\.?|inr|usd|eur|gbp|\$)?\s*[\d,]+(?:\.\d+)?\s*k?\b",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?k?$")
_LISTING_RE = re.compile(
    r"\b(?:top|best)\s+\d+\b"
    r"|\b\d+\s+best\b"
    r"|\bbest\b.*\b(?:in|for|of|under)\b"
    r"|\breviews?\b"
    r"|\bvs\.?\b"
    r"|\bversus\b"
    r"|\bguide\b"
    r"|\bhow\s+to\b"
    r"|\bcompar(?:e|ison|ing)\b"
    r"|\balternatives\b"
    r"|\bwhich\b"
    r"|\bwhat\s+is\b",
    re.IGNORECASE,
)
_ACCESSORY_CUT_RE = re.compile(
    r"\s(?:with|w/|free|including|includes)\s|\s\+\s|\s&\s", re.IGNORECASE
)


def stem(word: str) -> str:
    """Cheap plural-insensitive stem, good enough for product nouns."""
    w = word.lower()
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("ches", "shes", "xes", "sses")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


def core_words(text: str, extra_ignore: list[str] | None = None) -> list[str]:
    """Product-describing words of a user query, in order.

    Budget phrases, bare numbers, colors, filler words and any ``extra_ignore``
    words (for example the user's color preferences) are removed.
    """
    ignore = {w.lower() for w in (extra_ignore or [])}
    cleaned = _BUDGET_RE.sub(" ", text.lower())
    out: list[str] = []
    for w in _words(cleaned):
        if w in STOPWORDS or w in COLORS or w in ignore or _NUMBER_RE.match(w):
            continue
        out.append(w)
    return out


def core_terms(text: str, extra_ignore: list[str] | None = None) -> list[str]:
    """Stemmed, de-duplicated version of :func:`core_words`."""
    return list(dict.fromkeys(stem(w) for w in core_words(text, extra_ignore)))


def _term_present(term: str, title_stems: set[str]) -> bool:
    if term in title_stems:
        return True
    return any(s in title_stems for s in SYNONYMS.get(term, ()))


def missing_terms(text: str, terms: list[str]) -> list[str]:
    """Return the query terms (or accepted synonyms) absent from ``text``."""
    title_stems = {stem(w) for w in _words(text)}
    return [t for t in terms if not _term_present(t, title_stems)]


def has_incompatible_qualifier(terms: list[str]) -> bool:
    return any(t in INCOMPATIBLE_QUALIFIERS for t in terms)


def is_listing_title(title: str) -> bool:
    """True for listicles, reviews, comparisons and other non-product pages."""
    return bool(_LISTING_RE.search(title))


def is_blocked_domain(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS)


_CATEGORY_PATH_RE = re.compile(
    r"^/(?:s|search|browse|category|categories|c|b|collections?(?:/[^/]+)?/?)$"
    r"|/(?:search|browse|category|categories)(?:/|$)",
    re.IGNORECASE,
)
_RETAILER_PREFIX_RE = re.compile(r"^\s*[\w\-]+\.(?:in|com|co\.uk|de)\s*:\s*", re.IGNORECASE)


def is_category_page(url: str) -> bool:
    """True for search result, category and collection pages (not single products)."""
    if not url:
        return False
    parsed = urlparse(url)
    if _CATEGORY_PATH_RE.search(parsed.path or "/"):
        return True
    return bool(re.search(r"(?:^|&)(?:k|q|query|search)=", parsed.query))


_PRODUCT_PATH_RE = re.compile(
    r"/dp/[A-Za-z0-9]{10}(?:[/?]|$)"
    r"|/gp/product/"
    r"|/p/itm[0-9a-z]+"
    r"|/(?:products?|product-page|item|items|pd|prd|buy)/[^/]+"
    r"|/p/[^/]+"
    r"|-p-\d+"
    r"|/[^/]*\d{6,}[^/]*",
    re.IGNORECASE,
)


def looks_like_product_url(url: str) -> bool:
    """True when the URL path has the shape of a single product page."""
    if not url:
        return False
    return bool(_PRODUCT_PATH_RE.search(urlparse(url).path or ""))


def strip_retailer_prefix(title: str) -> str:
    """Turn 'Amazon.in: Riding Jacket' into 'Riding Jacket'."""
    return _RETAILER_PREFIX_RE.sub("", title)


_STORE_TITLE_RE = re.compile(
    r"\bbuy\b.*\b(?:online|india)\b"
    r"|\bonline\s+(?:in|at|shopping|india)\b"
    r"|\d+%\s*off\b|\bupto\b|\btagged\b"
    r"|\b(?:affordable|best|lowest|low)\s+prices?\b"
    r"|\bcollections?\b|\bshop\b|\bdeals\b|\boffers\b|\bsale\b|\bdiscounts?\b",
    re.IGNORECASE,
)
LEADING_FLUFF = frozenset({"buy", "shop", "get", "order"})


def looks_like_store_page_title(title: str) -> bool:
    """True when a title reads like a storefront or category page headline."""
    return bool(_STORE_TITLE_RE.search(title))


def is_accessory_for(title: str, terms: list[str]) -> bool:
    """True if the title is an accessory (cover, case...) the query did not ask for."""
    main_part = _ACCESSORY_CUT_RE.split(f" {title} ")[0]
    stems = {stem(w) for w in _words(main_part)}
    return any(a in stems and a not in terms for a in ACCESSORY_WORDS)


def is_relevant_title(title: str, terms: list[str]) -> bool:
    """Decide whether a free-form product title matches the user's query terms.

    Every query term must be present (synonyms allowed). Queries with four or
    more terms may miss one. Accessories and listing pages are rejected.
    """
    if not title or not terms:
        return bool(title)
    if is_listing_title(title) or is_accessory_for(title, terms):
        return False
    allowed_missing = 1 if len(terms) >= 4 else 0
    return len(missing_terms(title, terms)) <= allowed_missing
