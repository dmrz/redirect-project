from http import HTTPStatus
import operator
from pathlib import Path
import tomllib

from typing import Annotated, TypedDict
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).parent.parent


class WeightedHost(BaseModel):
    host: str
    weight: Annotated[int, Field(gt=0)]


class RedirectPool(BaseModel):
    pool_id: str
    weighted_hosts: list[WeightedHost]
    status: Annotated[HTTPStatus, Field(gt=300, lt=400)] = HTTPStatus.FOUND
    is_default: bool = False

    @field_validator("weighted_hosts", mode="before")
    @classmethod
    def parse_weighted_hosts(cls, v: dict[str, int]) -> list[WeightedHost]:
        return [WeightedHost(host=host, weight=weight) for host, weight in v.items()]


class RedirectPoolRawConfig(TypedDict):
    weighted_hosts: dict[str, int]
    status: int
    is_default: bool | None


class Settings(BaseSettings):
    redirect_pools_config_path: Path = Field(
        PROJECT_ROOT / "redirect_pools_config.toml"
    )
    redirect_pool_id_header: str = Field("X-Redirect-Pool-ID")

    _redirect_pools: list[RedirectPool]
    _default_redirect_pool: RedirectPool

    @model_validator(mode="after")
    def setup_redirect_pools(self):
        with self.redirect_pools_config_path.open("rb") as f:
            config: RedirectPoolRawConfig
            self._redirect_pools = [
                RedirectPool(pool_id=pool_id, **config)
                for pool_id, config in tomllib.load(f).items()
            ]

        # Finds first redirect pool with is_default set to True
        default_redirect_pool: RedirectPool | None = next(
            filter(operator.attrgetter("is_default"), self.redirect_pools), None
        )
        if default_redirect_pool is None:
            raise ValueError(
                "Please make sure you have at least one redirect pool with is_default = true in config"
            )
        self._default_redirect_pool = default_redirect_pool

    @property
    def redirect_pools(self) -> dict[str, RedirectPool]:
        return self._redirect_pools

    @property
    def default_redirect_pool(self) -> RedirectPool:
        return self._default_redirect_pool
