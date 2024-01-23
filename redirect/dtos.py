from dataclasses import dataclass
from http import HTTPStatus


@dataclass(slots=True)
class RequestDataDTO:
    """
    This is used to decouple our service layer logic from web framework we use
    """

    headers: dict[str, str]
    scheme: str
    host: str
    raw_path: str


@dataclass(slots=True)
class RedirectToDTO:
    host: str
    status: HTTPStatus
