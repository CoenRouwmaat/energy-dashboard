"""Enumerations for the NED API's query parameters.

Values transcribed from the official parameter table at
https://ned.nl/nl/handleiding-api (NED API manual) and cross-checked against
the OpenAPI schema at https://api.ned.nl/v1/docs.json.
"""

from enum import IntEnum


class Granularity(IntEnum):
    """Time resolution of returned records."""

    TEN_MINUTES = 3
    FIFTEEN_MINUTES = 4
    HOUR = 5
    DAY = 6
    MONTH = 7
    YEAR = 8


class GranularityTimeZone(IntEnum):
    """Timezone convention used for bucketing records by `Granularity`.

    Note: day/month/year aggregates are only computed for CET and are only
    returned when this is `CET`; `UTC` returns no rows for those
    granularities.
    """

    UTC = 0
    CET = 1


class Classification(IntEnum):
    """Whether a record is a forecast or a near-realtime/current value."""

    FORECAST = 1
    CURRENT = 2


class Activity(IntEnum):
    """Type of activity the volume/capacity figures represent."""

    PROVIDING = 1
    CONSUMING = 2
    IMPORT = 3
    EXPORT = 4
    STORAGE_IN = 5
    STORAGE_OUT = 6
    STORAGE = 7


class Point(IntEnum):
    """Geographic point (country, province, or named offshore wind farm)."""

    NETHERLANDS = 0
    GRONINGEN = 1
    FRIESLAND = 2
    DRENTHE = 3
    OVERIJSSEL = 4
    FLEVOLAND = 5
    GELDERLAND = 6
    UTRECHT = 7
    NOORD_HOLLAND = 8
    ZUID_HOLLAND = 9
    ZEELAND = 10
    NOORD_BRABANT = 11
    LIMBURG = 12
    OFFSHORE = 14
    WINDPARK_LUCHTERDUINEN = 28
    WINDPARK_PRINCES_AMALIA = 29
    WINDPARK_EGMOND_AAN_ZEE = 30
    WINDPARK_GEMINI = 31
    WINDPARK_BORSSELE_I_II = 33
    WINDPARK_BORSSELE_III_IV = 34
    WINDPARK_HOLLANDSE_KUST_ZUID = 35
    WINDPARK_HOLLANDSE_KUST_NOORD = 36


class EnergyType(IntEnum):
    """Energy carrier / source type."""

    ALL = 0
    WIND = 1
    SOLAR = 2
    BIOGAS = 3
    HEAT_PUMP = 4
    COFIRING = 8
    GEOTHERMAL = 9
    OTHER = 10
    WASTE = 11
    BIO_OIL = 12
    BIOMASS = 13
    WOOD = 14
    WIND_OFFSHORE = 17
    FOSSIL_GAS_POWER = 18
    FOSSIL_HARD_COAL = 19
    NUCLEAR = 20
    WASTE_POWER = 21
    WIND_OFFSHORE_B = 22
    NATURAL_GAS = 23
    BIOMETHANE = 24
    BIOMASS_POWER = 25
    OTHER_POWER = 26
    ELECTRICITY_MIX = 27
    GAS_MIX = 28
    GAS_DISTRIBUTION = 31
    WKK_TOTAL = 35
    SOLAR_THERMAL = 50
    WIND_OFFSHORE_C = 51
    INDUSTRIAL_CONSUMERS_GAS_COMBINATION = 53
    INDUSTRIAL_CONSUMERS_POWER_GAS_COMBINATION = 54
    LOCAL_DISTRIBUTION_COMPANIES_COMBINATION = 55
    ALL_CONSUMING_GAS = 56
    ELECTRICITY_LOAD = 59
