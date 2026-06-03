# -*- coding: utf-8 -*-
"""
utils/coordinate_converter.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DCC 간 좌표계 / 단위 변환 (Qt 비의존 순수 로직).

[검증된 규약]
  Unreal : 좌수(LH), Z-up, cm
  Maya   : 우수(RH), Y-up, cm
  3ds Max: 우수(RH), Z-up
  Blender: 우수(RH), Z-up, m

[변환 범위]
  - 위치(Vector): 축 매핑 + 부호 + 단위 (정확)
  - 스케일(Scale): 축 순서만 (부호/단위 없음)
  - 회전(Rotation): 축 매핑 기반 '근사'. 오일러 순서/짐벌로 어긋날 수 있어 경고 동반.
"""

from __future__ import annotations
from typing import Tuple, Dict
import math

Vec3 = Tuple[float, float, float]

UNIT_CM: Dict[str, float] = {"unreal": 1.0, "maya": 1.0, "max": 1.0, "blender": 100.0}
ENGINES = ("unreal", "maya", "max", "blender")


def cm_to_m(v: float) -> float:
    return v / 100.0


def m_to_cm(v: float) -> float:
    return v * 100.0


def deg_to_rad(v: float) -> float:
    return v * math.pi / 180.0


def rad_to_deg(v: float) -> float:
    return v * 180.0 / math.pi


def _to_unreal_position(x, y, z, src):
    s = UNIT_CM[src]
    x, y, z = x * s, y * s, z * s
    if src == "unreal":
        return (x, y, z)
    if src == "maya":
        return (-z, x, y)
    if src in ("max", "blender"):
        return (x, -y, z)
    raise ValueError(f"unknown engine: {src}")


def _from_unreal_position(x, y, z, dst):
    if dst == "unreal":
        ux, uy, uz = x, y, z
    elif dst == "maya":
        ux, uy, uz = y, z, -x
    elif dst in ("max", "blender"):
        ux, uy, uz = x, -y, z
    else:
        raise ValueError(f"unknown engine: {dst}")
    d = UNIT_CM[dst]
    return (ux / d, uy / d, uz / d)


def convert_position(vec: Vec3, src: str, dst: str) -> Vec3:
    src, dst = src.lower(), dst.lower()
    ue = _to_unreal_position(vec[0], vec[1], vec[2], src)
    out = _from_unreal_position(ue[0], ue[1], ue[2], dst)
    return tuple(round(v, 4) for v in out)  # type: ignore[return-value]


def convert_scale(scale: Vec3, src: str, dst: str) -> Vec3:
    src, dst = src.lower(), dst.lower()

    def to_ue(s, sx, sy, sz):
        if s in ("unreal", "max", "blender"):
            return (sx, sy, sz)
        if s == "maya":
            return (sz, sx, sy)
        raise ValueError(s)

    def from_ue(s, ux, uy, uz):
        if s in ("unreal", "max", "blender"):
            return (ux, uy, uz)
        if s == "maya":
            return (uy, uz, ux)
        raise ValueError(s)

    ue = to_ue(src, *scale)
    out = from_ue(dst, *ue)
    return tuple(round(v, 6) for v in out)  # type: ignore[return-value]


def convert_rotation_approx(rot: Vec3, src: str, dst: str) -> Tuple[Vec3, str]:
    src, dst = src.lower(), dst.lower()
    approx = convert_position(rot, src, dst)
    warn = "⚠ 회전값은 근사치입니다. 오일러 순서/짐벌 차이로 어긋날 수 있으니 DCC에서 검수하세요."
    return approx, warn
