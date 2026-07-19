#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MASTER_NUMBERS = frozenset({11, 22, 33})

TAROT_ARCHETYPES = {
    0: "Wuji / Vacuum",
    1: "Magician",
    2: "High Priestess",
    3: "Empress",
    4: "Emperor",
    5: "Hierophant",
    6: "Lovers",
    7: "Chariot",
    8: "Strength",
    9: "Hermit",
    10: "Wheel",
    11: "Justice / Tensegrity",
    12: "Hanged Man",
    13: "Death / Transition",
    14: "Temperance",
    15: "Devil / Apophenia Shield",
    16: "Tower / Structural Reset",
    17: "Star",
    18: "Moon",
    19: "Sun",
    20: "Judgement",
    21: "World",
    22: "Master Builder",
}

SYMBOLIC_VECTORS = {
    23: "Sovereign Friction",
    24: "Localized Harmony",
    25: "Chariot's Logic",
    26: "Engine's Output",
    27: "Queen's Code",
    28: "Perfect Mass",
    29: "Orbit Prime",
    30: "Trinity Fold",
    31: "Prime Isolation",
    32: "Binary Collapse",
    33: "Ascended Flow",
    34: "Fibonacci Drift",
    35: "Pentagonal Trap",
    36: "Panopticon",
    37: "Ascended Observer",
    38: "Isotope Decay",
    39: "Late-Stage Syzygy",
    40: "Quarantine Zone",
    41: "Event Horizon",
    42: "Sovereign Anchor",
}


@dataclass(frozen=True)
class Frequency:
    source: str
    raw: int
    reduced: int
    archetype: str
    lens: str
    master: bool


def digit_sum(value: int) -> int:
    return sum(int(character) for character in str(abs(int(value))))


def reduce_frequency(value: int, preserve_master: bool = True) -> int:
    current = abs(int(value))
    while current > 9:
        if preserve_master and current in MASTER_NUMBERS:
            return current
        current = digit_sum(current)
    return current


def classify_frequency(raw: int, source: str = "value") -> Frequency:
    raw_value = int(raw)
    reduced = reduce_frequency(raw_value)
    if raw_value in SYMBOLIC_VECTORS:
        return Frequency(
            source=source,
            raw=raw_value,
            reduced=reduced,
            archetype=SYMBOLIC_VECTORS[raw_value],
            lens="user_defined_symbolic_vector",
            master=raw_value in MASTER_NUMBERS,
        )
    return Frequency(
        source=source,
        raw=raw_value,
        reduced=reduced,
        archetype=TAROT_ARCHETYPES.get(reduced, "Unclassified"),
        lens="symbolic_tarot_reduction",
        master=raw_value in MASTER_NUMBERS or reduced in MASTER_NUMBERS,
    )


def _frequency_map(values: dict[str, int]) -> dict[str, dict[str, Any]]:
    return {
        name: asdict(classify_frequency(raw, name))
        for name, raw in values.items()
    }


def analyze_date(value: date) -> dict[str, Any]:
    month = value.month
    day = value.day
    year = value.year
    raw_values = {
        "micro_digit_sum": digit_sum(month) + digit_sum(day),
        "micro_number_sum": month + day,
        "macro_digit_sum": digit_sum(month) + digit_sum(day) + digit_sum(year),
        "macro_number_sum": month + day + year,
        "year_digit_sum": digit_sum(year),
        "year_number": year,
        "month": month,
        "day_digit_sum": digit_sum(day),
        "day_number": day,
        "month_year_digit_sum": digit_sum(month) + digit_sum(year),
        "day_year_digit_sum": digit_sum(day) + digit_sum(year),
    }
    return {
        "kind": "shadow_garden_chronology_analysis",
        "symbolic_only": True,
        "date": value.isoformat(),
        "raw_values": raw_values,
        "frequencies": _frequency_map(raw_values),
    }


def _parse_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {name}") from exc


def analyze_timestamp(
    value: datetime,
    local_timezone: str = "America/New_York",
    comparison_timezone: str = "Asia/Singapore",
) -> dict[str, Any]:
    local_zone = _parse_zone(local_timezone)
    comparison_zone = _parse_zone(comparison_timezone)
    aware = value
    if aware.tzinfo is None:
        aware = aware.replace(tzinfo=local_zone)
    local_value = aware.astimezone(local_zone)
    comparison_value = aware.astimezone(comparison_zone)
    clock_raw = int(local_value.strftime("%H%M"))
    return {
        "kind": "shadow_garden_timestamp_analysis",
        "symbolic_only": True,
        "local_timezone": local_timezone,
        "comparison_timezone": comparison_timezone,
        "local_timestamp": local_value.isoformat(),
        "comparison_timestamp": comparison_value.isoformat(),
        "clock_24_hour": local_value.strftime("%H:%M"),
        "clock_digit_sum": asdict(classify_frequency(digit_sum(clock_raw), "clock_digit_sum")),
        "clock_raw_hhmm": clock_raw,
    }


def analyze_now(
    local_timezone: str = "America/New_York",
    comparison_timezone: str = "Asia/Singapore",
) -> dict[str, Any]:
    current = datetime.now(timezone.utc)
    return {
        "date": analyze_date(current.astimezone(_parse_zone(local_timezone)).date()),
        "timestamp": analyze_timestamp(current, local_timezone, comparison_timezone),
    }


def _parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("time must use HH:MM or HH:MM:SS") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic local chronology analysis")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--time", dest="clock_time")
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--comparison-timezone", default="Asia/Singapore")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        selected_date = date.fromisoformat(args.date)
        payload: dict[str, Any] = {
            "date": analyze_date(selected_date),
        }
        if args.clock_time:
            selected_time = _parse_time(args.clock_time)
            payload["timestamp"] = analyze_timestamp(
                datetime.combine(selected_date, selected_time),
                args.timezone,
                args.comparison_timezone,
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
