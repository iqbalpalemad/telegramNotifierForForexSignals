import re

def parse_message(text: str):
    entry_pattern = r"XAUUSD.*?(BUY|SELL)\s*NOW[^0-9]*?(\d+(\.\d+)?)"
    match = re.search(entry_pattern, text, re.IGNORECASE)

    if not match:
        return None

    action, entry, _ = match.groups()
    entry = float(entry)

    tp2_pattern = r"TARGET\s*1[^0-9]*?(\d+(\.\d+)?)"
    sl_pattern = r"STOP\s*LOSS[^0-9]*?(\d+(\.\d+)?)"

    tp_match = re.search(tp2_pattern, text, re.IGNORECASE)
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
