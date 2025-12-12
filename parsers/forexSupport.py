import re

def parse_message(text: str):
    pattern = r"([A-Z]{3,6})\s+(BUY|SELL)\s+NOW\s+(\d+(\.\d+)?)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None

    symbol, action, entry, _ = match.groups()
    entry = float(entry)

    if action.upper() == "BUY":
        target = entry + 3
        stop_loss = entry - 8
    else:
        target = entry - 3
        stop_loss = entry + 8

    return {
        "symbol": symbol.upper(),
        "action": action.upper(),
        "entry": entry,
        "target": round(target, 2),
        "stop_loss": round(stop_loss, 2),
    }
