class AdsError(Exception):
    """Base ADS service error."""


class AdsDataNotFound(AdsError):
    """Raised when requested ADS data does not exist."""


class AdsDatabaseUnavailable(AdsError):
    """Raised when the ADS MySQL database cannot be reached or queried."""
