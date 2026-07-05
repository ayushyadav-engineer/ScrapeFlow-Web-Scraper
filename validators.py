from urllib.parse import urlparse


class URLValidator:
    """
    Validate website URLs.
    """

    @staticmethod
    def is_valid(url: str) -> bool:

        try:

            parsed = urlparse(url)

            return all(
                [
                    parsed.scheme in ("http", "https"),
                    parsed.netloc
                ]
            )

        except Exception:

            return False