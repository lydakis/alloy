from dataclasses import dataclass
import re


@dataclass(eq=True, frozen=True)
class Price:
    amount: float
    currency: str


_MINOR_UNITS = {"JPY": 0}


def map_symbol_to_iso(sym: str) -> str:
    return {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}.get(sym, "UNK")


def _normalize_amount_text(raw: str, *, currency: str) -> float:
    s = raw.strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        if re.match(r"^\d{1,3}(,\d{3})+$", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        v = 0.0
    digits = _MINOR_UNITS.get(currency, 2)
    return round(v, digits)


def normalize_price(p) -> Price:
    if hasattr(p, "amount") and hasattr(p, "currency"):
        amt = getattr(p, "amount")
        cur_raw = str(getattr(p, "currency"))
    else:
        amt = p["amount"]
        cur_raw = str(p["currency"])
    cur_sym_map = {"$", "€", "£", "¥"}
    cur = cur_raw
    if cur in cur_sym_map:
        cur = map_symbol_to_iso(cur)
    else:
        cur = cur_raw.upper()
    return Price(amount=_normalize_amount_text(str(amt), currency=cur), currency=cur)
