import re
from dataclasses import dataclass
from .normalization import map_symbol_to_iso, _normalize_amount_text


@dataclass
class PriceDC:
    amount: float
    currency: str


def extract_price_oracle(text: str) -> PriceDC:
    s = text.strip()
    m = re.search(r"\b(USD|EUR|GBP|JPY)\b[^\d]*([0-9][\d.,]*)", s, re.I)
    if m:
        cur = m.group(1).upper()
        amt = _normalize_amount_text(m.group(2), currency=cur)
        return PriceDC(amt, cur)
    m = re.search(r"([€£¥$])\s*([0-9][\d.,]*)", s)
    if m:
        cur = map_symbol_to_iso(m.group(1))
        amt = _normalize_amount_text(m.group(2), currency=cur)
        return PriceDC(amt, cur)
    m = re.search(r"([0-9][\d.,]*)\s*([€£¥$])", s)
    if m:
        cur = map_symbol_to_iso(m.group(2))
        amt = _normalize_amount_text(m.group(1), currency=cur)
        return PriceDC(amt, cur)
    return PriceDC(0.0, "UNK")
