import logging
import re

class SensitiveDataRedactingFilter(logging.Filter):
    """
    Redacts passwords, bearer tokens, and 12-digit APAAR numbers from logs.
    """
    PATTERNS = [
        (re.compile(r'(password[\'\":\s=]+)[\'"]?[^\'\"\s,]+[\'"]?', re.IGNORECASE), r'\1"[REDACTED_SECRET]"'),
        (re.compile(r'(token[\'\":\s=]+)[\'"]?[^\'\"\s,]+[\'"]?', re.IGNORECASE), r'\1"[REDACTED_TOKEN]"'),
        (re.compile(r'(secret[\'\":\s=]+)[\'"]?[^\'\"\s,]+[\'"]?', re.IGNORECASE), r'\1"[REDACTED_SECRET]"'),
        (re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'), r'••••-••••-XXXX'),  # 12-digit APAAR
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in self.PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        return True

def setup_secure_logging():
    logger = logging.getLogger()
    filt = SensitiveDataRedactingFilter()
    for handler in logger.handlers:
        handler.addFilter(filt)
