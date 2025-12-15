import re


def parse_message(text: str):
    """
    Parses complex XAUUSD signals.
    Uses Target 1 as target.
    """

    clean = text.replace(",", "").lower()

    # -----------------------------
    # SYMBOL
    # -----------------------------
    symbol_match = re.search(r"#(xauusd)", clean)
    if not symbol_match:
        return None

    symbol = symbol_match.group(1)

    # -----------------------------
    # ACTION + ENTRY
    # -----------------------------
    buy_match = re.search(r"buy+\s*\.?\s*(\d+\.?\d*)", clean)
    sell_match = re.search(r"sell+\s*\.?\s*(\d+\.?\d*)", clean)

    if buy_match:
        action = "BUY"
        entry = float(buy_match.group(1))
    elif sell_match:
        action = "SELL"
        entry = float(sell_match.group(1))
    else:
        return None

    # -----------------------------
    # TARGET 1
    # -----------------------------
    target_match = re.search(r"target\s*1\s*[:\-]?\s*(\d+\.?\d*)", clean)
    if not target_match:
        return None

    target = float(target_match.group(1))

    # -----------------------------
    # STOP LOSS
    # -----------------------------
    sl_match = re.search(r"stop\s*loss\s*[:\-]?\s*(\d+\.?\d*)", clean)
    if not sl_match:
        return None

    stop_loss = float(sl_match.group(1))

    # -----------------------------
    # FINAL OUTPUT (UNCHANGED CONTRACT)
    # -----------------------------
    return {
        "symbol": symbol.upper(),
        "action": action.upper(),
        "entry": entry,
        "target": round(target, 2),
        "stop_loss": round(stop_loss, 2),
    }
