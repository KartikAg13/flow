"""World-model types: one Pydantic model per seed row. build() validates every seed with these."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Slug = Annotated[str, Field(pattern=r"^[a-z0-9_]+$")]
Url = Annotated[str, Field(pattern=r"^https?://")]


class Row(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a typo'd key in a seed fails the build


class Cited(Row):
    source: str = Field(min_length=3)
    source_url: Url


class Commodity(Row):
    id: Slug
    name: str
    family: str
    unit: str


class Supplier(Row):
    iso: str = Field(pattern=r"^[A-Z]{2}$")
    name: str
    lat: float | None = None
    lon: float | None = None


class Chokepoint(Cited):
    id: Slug
    name: str
    lat: float
    lon: float
    transit_volume: float = Field(ge=0)
    transit_unit: str
    year: int


class Port(Cited):
    id: Slug
    name: str
    country_iso: str
    coast: str | None = None
    state: str
    lat: float
    lon: float
    commodities: list[Slug] = []


class Refinery(Cited):
    id: Slug
    name: str
    operator: str
    state: str
    lat: float
    lon: float
    capacity: float = Field(gt=0)
    capacity_unit: str
    year: int
    nearest_port: Slug


class LngTerminal(Cited):
    id: Slug
    name: str
    operator: str
    state: str
    lat: float
    lon: float
    capacity_mtpa: float = Field(gt=0)
    year: int
    port: Slug


class FertilizerPlant(Cited):
    id: Slug
    name: str
    operator: str
    state: str
    lat: float
    lon: float
    nearest_port: Slug | None = None
    products: list[Slug] = []


class SprSite(Cited):
    id: Slug
    name: str
    state: str
    lat: float
    lon: float
    capacity_mmt: float = Field(gt=0)
    year: int


class Factor(Cited):
    id: Slug
    value: float
    unit: str
    year: int


class StateStat(Cited):
    """One published number for one state: fuel sales, fertilizer sales, urea output, holdings."""

    state: str
    metric: Slug
    value: float = Field(ge=0)
    unit: str
    year: int


class FuelSegment(Cited):
    """Share of national diesel or petrol use by one user segment (trucks, two-wheelers, ...)."""

    fuel: Slug
    segment: str
    share: float = Field(ge=0, le=1)
    year: int


class Import(Cited):
    commodity: Slug
    supplier_iso: str
    supplier_name: str
    volume: float = Field(ge=0)
    unit: str
    year: int
    share_of_india_imports: float = Field(ge=0, le=1)


class Route(Cited):
    id: str
    commodity: Slug
    supplier_iso: str
    origin: str | None = None  # export terminal, e.g. Ras Tanura; None when the supplier is "Other"
    origin_lat: float | None = None
    origin_lon: float | None = None
    chokepoints: list[Slug] = []
    indian_port: Slug
    indian_facility: Slug | None = None
    volume: float | None = Field(default=None, ge=0)
    unit: str | None = None
    year: int


class Pipeline(Cited):
    """An oil or gas pipeline. Bypass lines carry one supplier's exports around chokepoints
    (start/end are abroad); domestic lines link Indian sites, listed in flow order."""

    id: Slug
    name: str
    fluid: Slug  # crude | gas
    scope: Slug  # bypass | domestic
    operator: str
    supplier_iso: str | None = None
    bypasses: list[Slug] = []
    sites: list[str] = []  # graph node ids, e.g. port:vadinar, refinery:mathura
    start_name: str | None = None
    start_lat: float | None = None
    start_lon: float | None = None
    end_name: str | None = None
    end_lat: float | None = None
    end_lon: float | None = None
    capacity: float = Field(gt=0)
    capacity_unit: str
    length_km: float | None = None
    status: str
    year: int


class SeaPath(Cited):
    """One way by sea for a leg (a route id, or pipeline>port for a bypass outlet), with the
    chokepoints it passes and its length. Precomputed by scripts/write_seeds.py."""

    id: str
    leg: str
    passes: list[Slug] = []
    nm: float = Field(gt=0)
