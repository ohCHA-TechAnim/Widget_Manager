# -*- coding: utf-8 -*-
"""
utils/math_utils.py
~~~~~~~~~~~~~~~~~~~
Qt 비의존 순수 계산/포맷 유틸리티 모음.

여기 있는 함수들은 모두 입력 -> 출력만 있고 부작용/Qt 의존이 없습니다.
따라서 pytest로 단독 검증이 가능하며, 모델/컨트롤러/뷰 어디서든 import해 재사용합니다.
"""

from __future__ import annotations

import datetime
from typing import Iterable, Tuple

Vec3 = Tuple[float, float, float]


# ----------------------------------------------------------------------
# 각도 / 회전
# ----------------------------------------------------------------------
def wrap_angle_180(angle: float) -> float:
    """임의의 각도를 (-180, 180] 범위 최단 표현으로 정규화. -180은 180으로 접힘."""
    result = ((angle + 180.0) % 360.0) - 180.0
    return 180.0 if result == -180.0 else result


def shortest_rotator_delta(start: Vec3, target: Vec3, ndigits: int = 4) -> Vec3:
    """회전(Pitch, Yaw, Roll) 최단 경로 오프셋. 각 축에 wrap_angle_180 적용."""
    return tuple(  # type: ignore[return-value]
        round(wrap_angle_180(t - s), ndigits) for s, t in zip(start, target)
    )


def vector_delta(start: Vec3, target: Vec3, ndigits: int = 4) -> Vec3:
    """위치(Vector) 단순 오프셋 (target - start)."""
    return tuple(  # type: ignore[return-value]
        round(t - s, ndigits) for s, t in zip(start, target)
    )


# ----------------------------------------------------------------------
# 색상
# ----------------------------------------------------------------------
def normalize_argb_hex(rgb_val: str | None) -> str:
    """
    openpyxl 셀 색상값을 항상 8자리(AARRGGBB) hex 문자열로 정규화.
    유효하지 않으면 빈 문자열.
    """
    if not rgb_val:
        return ""
    s = str(rgb_val)
    if len(s) == 8:
        return s
    if len(s) == 6:
        return "FF" + s
    return ""


def argb_to_css(rgb_val: str | None) -> str:
    """8자리 ARGB hex -> CSS '#RRGGBB'. 유효하지 않으면 빈 문자열."""
    norm = normalize_argb_hex(rgb_val)
    return f"#{norm[2:]}" if norm else ""


# ----------------------------------------------------------------------
# 일정 / 워크데이
# ----------------------------------------------------------------------
def is_holiday_key(year: int, month: int, day: int, holidays: Iterable[str]) -> bool:
    """'YYYY-M-D' 키가 휴일 목록에 있는지."""
    return f"{year}-{month}-{day}" in set(holidays)


def count_workdays(
    start: datetime.date,
    end: datetime.date,
    holidays: Iterable[str],
) -> int:
    """
    start~end(양끝 포함) 사이 평일이면서 휴일이 아닌 날의 수.
    주말(토=5, 일=6) 및 holidays('YYYY-M-D')는 제외.
    """
    if end < start:
        return 0
    holiday_set = set(holidays)
    count = 0
    for i in range((end - start).days + 1):
        cd = start + datetime.timedelta(days=i)
        if cd.weekday() < 5 and f"{cd.year}-{cd.month}-{cd.day}" not in holiday_set:
            count += 1
    return count


def ratio(part: int, whole: int) -> float:
    """0 나눗셈 방어 비율. whole이 0이면 0.0."""
    return part / whole if whole > 0 else 0.0
