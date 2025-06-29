# utils/filter.py
def is_non_actionable(message: str) -> bool:
    non_actionable_keywords = {"ok", "okay", "yes", "no", "thanks", "thank you", "cool", "got it", "👍"}
    return message.strip().lower() in non_actionable_keywords
