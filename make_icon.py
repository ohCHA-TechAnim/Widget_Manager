"""애플리케이션 아이콘 생성 스크립트 (assets/app_icon.ico).

PyQt6를 사용해 16/32/48/256px PNG를 렌더링하고
PNG 내장 ICO 포맷으로 조합해 저장한다.

사용법: python make_icon.py
"""
import struct
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QRect


def _render_png(size: int) -> bytes:
    """파란 라운드 사각형 + 'W' 글자를 PNG 바이트로 렌더링한다."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 그라디언트 배경
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0.0, QColor("#6AB3F5"))
    grad.setColorAt(1.0, QColor("#2A6FBF"))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    margin = max(1, size // 10)
    radius = size * 0.2
    p.drawRoundedRect(margin, margin, size - 2 * margin, size - 2 * margin, radius, radius)

    # 큰 사이즈에서만 'W' 텍스트 표시
    if size >= 32:
        p.setPen(QColor("#FFFFFF"))
        font = QFont()
        font.setPixelSize(int(size * 0.52))
        font.setBold(True)
        font.setFamily("Arial")
        p.setFont(font)
        p.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "W")

    p.end()

    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pix.save(buf, "PNG")
    buf.close()
    return bytes(buf.data())


def create_ico(sizes: list[int], output: Path) -> None:
    """PNG 바이트 목록으로 ICO 파일을 생성한다 (Vista+ PNG 내장 포맷)."""
    images = [(s, _render_png(s)) for s in sizes]

    # ICO 헤더: reserved=0, type=1(ICO), count
    header = struct.pack('<HHH', 0, 1, len(images))

    # 각 이미지 디렉터리 항목 오프셋은 헤더(6) + 디렉터리(N×16) 이후부터 시작
    dir_offset = 6 + len(images) * 16
    offset = dir_offset

    directories = []
    for s, png in images:
        w = 0 if s >= 256 else s   # 256px는 0으로 표현
        h = 0 if s >= 256 else s
        directories.append(
            struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(png), offset)
        )
        offset += len(png)

    with open(output, 'wb') as f:
        f.write(header)
        for d in directories:
            f.write(d)
        for _, png in images:
            f.write(png)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    out = Path('assets') / 'app_icon.ico'
    out.parent.mkdir(exist_ok=True)

    create_ico([16, 32, 48, 256], out)
    print(f"아이콘 생성 완료: {out}  ({out.stat().st_size:,} bytes)")
