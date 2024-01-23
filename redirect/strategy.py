from dataclasses import dataclass, field
from typing import Callable

import roundrobin

from redirect.conf import RedirectPool, WeightedHost
from redirect.dtos import RedirectToDTO


@dataclass(slots=True)
class WeightedRoundRobinRedirectStrategy:
    """
    Implements redirect strategy using weighted round robin algorithm, so host with
    weight 2 is used twice as frequently for redirect as host with weight 1.
    """

    redirect_pool: RedirectPool
    _weighted_round_robin: Callable[[], WeightedHost] = field(init=False)

    def __post_init__(self):
        # Disclaimer: this library is merely used as a demonstration of not reinventing the wheel
        self._weighted_round_robin = roundrobin.smooth(
            [(wh, wh.weight) for wh in self.redirect_pool.weighted_hosts]
        )

    def get_redirect_to_dto(self) -> RedirectToDTO:
        weighted_host = self._weighted_round_robin()
        return RedirectToDTO(weighted_host.host, self.redirect_pool.status)
