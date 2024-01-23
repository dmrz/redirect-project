from http import HTTPStatus
from typing import Protocol

from redirect.conf import RedirectPool
from redirect.dtos import RequestDataDTO


class RedirectStrategyProtocol(Protocol):
    """
    Concrete redirect strategy implementations should satisfy this protocol
    """

    redirect_pool: RedirectPool

    def get_redirect_to_dto(self) -> str:
        """
        Returns a DTO instance with host and status code that will be used for redirect using current redirect pool.
        """
        ...
