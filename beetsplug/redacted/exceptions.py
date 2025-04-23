"""Custom exceptions for the Redacted client."""


class RedactedError(Exception):
    """Base exception for Redacted API errors."""

    pass


class RedactedRateLimitError(RedactedError):
    """Exception raised when the API rate limit is exceeded."""

    def __init__(self, message: str) -> None:
        """Initialize the rate limit error.

        Args:
            message: Error message.
        """
        super().__init__(message)
