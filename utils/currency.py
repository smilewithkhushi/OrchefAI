import re
from config import get_cost_profile, REGION_KEYWORDS

CURRENCY_RATES = {
    "INR": 0.012, "SGD": 0.75, "GBP": 1.27, "EUR": 1.09,
    "AED": 0.27, "USD": 1.0,
}

MULTIPLIERS = {
    "lakh": 100_000, "lakhs": 100_000, "lac": 100_000,
    "crore": 10_000_000, "crores": 10_000_000, "cr": 10_000_000,
    "k": 1_000, "thousand": 1_000,
    "million": 1_000_000, "m": 1_000_000,
}

CURRENCY_KEYWORDS = {
    "inr": "INR", "rupee": "INR", "rupees": "INR", "rs": "INR", "₹": "INR",
    "usd": "USD", "$": "USD", "dollar": "USD", "dollars": "USD",
    "sgd": "SGD", "s$": "SGD",
    "gbp": "GBP", "£": "GBP", "pound": "GBP", "pounds": "GBP",
    "eur": "EUR", "€": "EUR", "euro": "EUR", "euros": "EUR",
    "aed": "AED", "dirham": "AED", "dirhams": "AED",
}

REGION_TO_CURRENCY = {
    "india": "INR", "singapore": "SGD", "uk": "GBP",
    "uae": "AED", "usa": "USD",
}

_NUMBER_RE = re.compile(
    r'(\d[\d,]*(?:\.\d+)?)'
    r'\s*'
    r'(lakh|lakhs|lac|crore|crores|cr|k|thousand|million|m)?'
    r'\s*'
    r'(inr|rupees?|rs|usd|dollars?|sgd|gbp|pounds?|eur|euros?|aed|dirhams?|₹|\$|£|€)?',
    re.IGNORECASE,
)

_BUDGET_CONTEXT = re.compile(
    r'(?:budget|spend|cost|price|maximum|max|min|upto|up\s*to|within|around|approx)'
    r'[\s\S]{0,60}?'
    r'(\d[\d,]*(?:\.\d+)?)'
    r'\s*'
    r'(lakh|lakhs|lac|crore|crores|cr|k|thousand|million|m)?'
    r'\s*'
    r'(inr|rupees?|rs|usd|dollars?|sgd|gbp|pounds?|eur|euros?|aed|dirhams?|₹|\$|£|€)?',
    re.IGNORECASE,
)

_SYMBOL_PREFIX = re.compile(
    r'([₹$£€])\s*(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lac|crore|crores|cr|k|thousand|million|m)?',
    re.IGNORECASE,
)


def _parse_number(raw: str) -> float:
    cleaned = raw.replace(",", "")
    return float(cleaned)


def _detect_currency_from_venue(venue: str | None) -> str | None:
    if not venue:
        return None
    venue_lower = venue.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(kw in venue_lower for kw in keywords):
            return REGION_TO_CURRENCY.get(region)
    return None


def parse_budget_from_text(raw_input: str) -> tuple[float | None, str | None]:
    text = raw_input.lower()

    for pattern in [_BUDGET_CONTEXT, _SYMBOL_PREFIX, _NUMBER_RE]:
        match = pattern.search(text)
        if not match:
            continue

        groups = match.groups()
        if pattern is _SYMBOL_PREFIX:
            symbol, num_str, mult_str = groups
            currency = CURRENCY_KEYWORDS.get(symbol)
        elif pattern is _BUDGET_CONTEXT:
            num_str, mult_str, curr_str = groups
            currency = CURRENCY_KEYWORDS.get(curr_str.lower()) if curr_str else None
        else:
            num_str, mult_str, curr_str = groups
            currency = CURRENCY_KEYWORDS.get(curr_str.lower()) if curr_str else None
            if not curr_str and not mult_str:
                continue

        try:
            amount = _parse_number(num_str)
        except (ValueError, TypeError):
            continue

        if mult_str:
            multiplier = MULTIPLIERS.get(mult_str.lower(), 1)
            amount *= multiplier

        return amount, currency

    return None, None


def validate_budget(
    llm_budget_usd: float | None,
    raw_input: str,
    venue: str | None,
) -> float | None:
    local_amount, currency = parse_budget_from_text(raw_input)

    if local_amount is None:
        return llm_budget_usd

    if currency is None:
        currency = _detect_currency_from_venue(venue)
    if currency is None:
        currency = "USD"

    rate = CURRENCY_RATES.get(currency, 1.0)
    python_usd = round(local_amount * rate, 2)

    if llm_budget_usd and llm_budget_usd > 0:
        ratio = python_usd / llm_budget_usd if llm_budget_usd else float("inf")
        if 0.5 <= ratio <= 1.5:
            return llm_budget_usd

    return python_usd
