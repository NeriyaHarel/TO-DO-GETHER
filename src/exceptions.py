class CustomError(Exception):
    """Base class for other exceptions"""


class AccountingError(CustomError):
    """Raised when there is an accounting error"""
