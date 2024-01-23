# service layer
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Type

from redirect.conf import Settings
from redirect.dtos import RedirectToDTO, RequestDataDTO
from redirect.protocols import RedirectStrategyProtocol


@dataclass(slots=True)
class RedirectService:
    """
    This service implements necessary logic for conducting a redirect.
    """

    redirect_strategy_impl: Type[RedirectStrategyProtocol]
    settings: Settings = field(default_factory=Settings)

    _redirect_pool_strategy_map: dict[str, RedirectStrategyProtocol] = field(init=False)

    def __post_init__(self):
        self._redirect_pool_strategy_map = {
            redirect_pool.pool_id: self.redirect_strategy_impl(redirect_pool)
            for redirect_pool in self.settings.redirect_pools
        }

    def _check_possible_redirect_loop(
        self, request_data_dto: RequestDataDTO, redirect_to_dto: RedirectToDTO
    ) -> None:
        """
        Raises an exception if there's a possible redirect loop, otherwise does nothing.
        """
        if request_data_dto.host == redirect_to_dto.host:
            raise RedirectLoopException

    def get_redirect_to(
        self, request_data_dto: RequestDataDTO
    ) -> tuple[str, HTTPStatus]:
        """
        Returns a new location where client will be redirected to and status code used for response for the given request data
        """
        redirect_pool_id: str | None = request_data_dto.headers.get(
            self.settings.redirect_pool_id_header
        )
        # We do this check to guard both missing pool id or unknown pool id cases
        if redirect_pool_id not in self._redirect_pool_strategy_map:
            redirect_pool_id = self.settings.default_redirect_pool.pool_id

        redirect_strategy = self._redirect_pool_strategy_map.get(redirect_pool_id)
        redirect_to_dto = redirect_strategy.get_redirect_to_dto()

        self._check_possible_redirect_loop(request_data_dto, redirect_to_dto)

        # We preserve request scheme, host and path with query string parameters
        redirect_to_location = f"{request_data_dto.scheme}://{redirect_to_dto.host}{request_data_dto.raw_path}"

        return (
            redirect_to_location,
            redirect_to_dto.status,
        )


class RedirectLoopException(Exception):
    """
    Raised when possible redirect loop is detected
    """
