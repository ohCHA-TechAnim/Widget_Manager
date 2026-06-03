# -*- coding: utf-8 -*-
"""
tests/test_math_utils.py
~~~~~~~~~~~~~~~~~~~~~~~~
math_utils 순수 함수 검증. Qt 불필요, `pytest` 단독 실행 가능.

목적: 리팩터링 전후로 '동작이 안 변했음'을 기계적으로 보장하는 안전망.
"""

import datetime

import pytest

from utils import math_utils as m


# ---- 각도 wrapping ----
@pytest.mark.parametrize("angle,expected", [
    (0, 0),
    (180, 180),
    (-180, 180),       # -180은 (-180,180] 규약상 180으로 접힘
    (181, -179),
    (360, 0),
    (540, 180),
    (-190, 170),
])
def test_wrap_angle_180(angle, expected):
    assert m.wrap_angle_180(angle) == pytest.approx(expected)


def test_shortest_rotator_delta_takes_short_path():
    # 350도에서 10도로: 단순 차이는 -340이지만 최단경로는 +20
    assert m.shortest_rotator_delta((350, 0, 0), (10, 0, 0)) == (20.0, 0.0, 0.0)


def test_rotator_delta_matches_legacy_formula():
    # 기존 delta_calculator의 공식과 직접 대조 ((-180, 180] 규약으로 보정)
    def legacy_component(sv, tv):
        raw = ((tv - sv + 180.0) % 360.0) - 180.0
        # -180은 +180으로 접힘 (wrap_angle_180과 동일 규약)
        return round(180.0 if raw == -180.0 else raw, 4)
    cases = [
        ((10, 20, 30), (40, 350, 5)),
        ((-90, 0, 179), (90, 1, -179)),
        ((0, 0, 0), (720, -720, 360)),
    ]
    for s, t in cases:
        expected = tuple(legacy_component(s[i], t[i]) for i in range(3))
        assert m.shortest_rotator_delta(s, t) == expected


def test_vector_delta():
    assert m.vector_delta((1, 2, 3), (4, 6, 8)) == (3.0, 4.0, 5.0)


# ---- 색상 ----
@pytest.mark.parametrize("raw,expected", [
    ("FF9494", "FFFF9494"),     # 6자리 -> FF 접두
    ("00BFFF00", "00BFFF00"),   # 8자리 그대로
    ("00BFFF", "FF00BFFF"),
    (None, ""),
    ("xyz", ""),                # 길이 안 맞으면 빈 문자열
])
def test_normalize_argb_hex(raw, expected):
    assert m.normalize_argb_hex(raw) == expected


def test_argb_to_css():
    assert m.argb_to_css("FF00BFFF") == "#00BFFF"
    assert m.argb_to_css("00BFFF") == "#00BFFF"
    assert m.argb_to_css(None) == ""


# ---- 워크데이 ----
def test_count_workdays_excludes_weekend():
    # 2026-06-01(월) ~ 2026-06-07(일): 월~금 5일
    start = datetime.date(2026, 6, 1)
    end = datetime.date(2026, 6, 7)
    assert m.count_workdays(start, end, []) == 5


def test_count_workdays_excludes_holiday():
    start = datetime.date(2026, 6, 1)
    end = datetime.date(2026, 6, 5)   # 월~금 = 5
    assert m.count_workdays(start, end, ["2026-6-3"]) == 4


def test_count_workdays_reversed_range():
    start = datetime.date(2026, 6, 5)
    end = datetime.date(2026, 6, 1)
    assert m.count_workdays(start, end, []) == 0


def test_ratio_zero_guard():
    assert m.ratio(3, 0) == 0.0
    assert m.ratio(8, 10) == pytest.approx(0.8)
