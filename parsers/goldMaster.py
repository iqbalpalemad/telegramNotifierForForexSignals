import re

def parse_message(text: str):
    pattern = r"XAUUSD\s*(BUY|SELL)\s*NOW\s*(\d+(\.\d+)?)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None

    action, entry, _ = match.groups()
    entry = float(entry)

    tp2_pattern = r"TARGET\s*2.*?\(?\s*(\d+(\.\d+)?)\s*\)?"
    tp_match = re.search(tp2_pattern, text, re.IGNORECASE)
    sl_pattern = r"STOP\s*LOSS.*?\(?\s*(\d+(\.\d+)?)\s*\)?"
    sl_match = re.search(sl_pattern, text, re.IGNORECASE)

    target = float(tp_match.group(1)) if tp_match else (entry + 8 if action.upper() == "BUY" else entry - 8)
    stop_loss = float(sl_match.group(1)) if sl_match else (entry - 8 if action.upper() == "BUY" else entry + 8)

    return {
        "symbol": "XAUUSD",
        "action": action.upper(),
        "entry": entry,
        "target": round(target, 2),
        "stop_loss": round(stop_loss, 2),
    }
