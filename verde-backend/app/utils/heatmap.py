"""
Verde 히트맵 색상 시스템 (녹색 계열)

왜 녹색인가?
- Verde = 스페인어로 "녹색"
- 생물 다양성의 풍요로움을 표현
- 자연 친화적 브랜드 이미지

색상 팔레트:
🟢 #E8F5E9 (매우 연한 녹색) - 낮음 (0-50종)
🟢 #81C784 (연한 녹색) - 보통 (51-150종)
🟢 #4CAF50 (중간 녹색) - 높음 (151-300종)
🟢 #2E7D32 (진한 녹색) - 매우 높음 (301종+)
"""

import math
from typing import Dict, List


# 녹색 팔레트 (기존 빨간색에서 변경)
GREEN_PALETTE = {
    "very_light": "#E8F5E9",
    "light": "#81C784",
    "medium": "#4CAF50",
    "dark": "#2E7D32"
}


def calculate_heatmap_intensity(endangered_count: int, max_count: int) -> float:
    """
    히트맵 강도 계산 (로그 스케일)

    왜 로그 스케일?
    - 극단적인 차이를 완화
    - 10종과 20종의 차이를 명확히 보여주면서
    - 200종과 400종의 차이는 상대적으로 줄여서 표시

    계산 예시:
    - 한국 124종, 최대 342종
    - 강도 = log(124 + 1) / log(342 + 1) = 0.65
    - 색상 = #4CAF50 (중간 녹색)

    Args:
        endangered_count: 해당 지역의 멸종위기종 수
        max_count: 전체 지역 중 최대 멸종위기종 수

    Returns:
        0.0 ~ 1.0 사이의 강도 값
    """
    if endangered_count == 0 or max_count == 0:
        return 0.0

    intensity = math.log(endangered_count + 1) / math.log(max_count + 1)
    return round(intensity, 2)


def get_green_color_code(intensity: float) -> str:
    """
    강도에 따른 녹색 색상 코드 반환

    입력: 0.0 ~ 1.0 사이의 강도 값
    출력: 16진수 색상 코드

    예시:
    >>> get_green_color_code(0.65)
    '#4CAF50'

    >>> get_green_color_code(0.15)
    '#E8F5E9'

    Args:
        intensity: 0.0 ~ 1.0 사이의 강도 값

    Returns:
        16진수 색상 코드 (예: #4CAF50)
    """
    if intensity >= 0.75:
        return GREEN_PALETTE["dark"]      # #2E7D32
    elif intensity >= 0.50:
        return GREEN_PALETTE["medium"]    # #4CAF50
    elif intensity >= 0.25:
        return GREEN_PALETTE["light"]     # #81C784
    else:
        return GREEN_PALETTE["very_light"] # #E8F5E9


def get_green_color_by_count(endangered_count: int) -> str:
    """
    멸종위기종 수에 따른 직접 색상 반환 (간단한 버전)

    계산 방식:
    - 0-50: 매우 연한 녹색
    - 51-150: 연한 녹색
    - 151-300: 중간 녹색
    - 301+: 진한 녹색

    Args:
        endangered_count: 멸종위기종 수

    Returns:
        16진수 색상 코드
    """
    if endangered_count >= 301:
        return GREEN_PALETTE["dark"]
    elif endangered_count >= 151:
        return GREEN_PALETTE["medium"]
    elif endangered_count >= 51:
        return GREEN_PALETTE["light"]
    else:
        return GREEN_PALETTE["very_light"]


def get_color_label(intensity: float) -> str:
    """
    강도에 따른 한글 레이블 반환

    Args:
        intensity: 0.0 ~ 1.0 사이의 강도 값

    Returns:
        한글 레이블 (낮음/보통/높음/매우 높음)
    """
    if intensity >= 0.75:
        return "매우 높음"
    elif intensity >= 0.50:
        return "높음"
    elif intensity >= 0.25:
        return "보통"
    else:
        return "낮음"


def get_heatmap_legend() -> Dict:
    """
    프론트엔드용 범례 데이터 반환

    반환 형식:
    {
        "levels": [
            {"min": 0, "max": 50, "color": "#E8F5E9", "label": "낮음"},
            {"min": 51, "max": 150, "color": "#81C784", "label": "보통"},
            ...
        ],
        "palette": "green",
        "description": "멸종위기종이 많을수록 진한 녹색"
    }

    사용 예시:
    >>> legend = get_heatmap_legend()
    >>> print(legend["description"])
    멸종위기종이 많을수록 진한 녹색

    Returns:
        범례 데이터 딕셔너리
    """
    return {
        "levels": [
            {
                "min": 0,
                "max": 50,
                "color": GREEN_PALETTE["very_light"],
                "label": "낮음",
                "description": "멸종위기종이 적은 지역"
            },
            {
                "min": 51,
                "max": 150,
                "color": GREEN_PALETTE["light"],
                "label": "보통",
                "description": "중간 수준의 보호 필요"
            },
            {
                "min": 151,
                "max": 300,
                "color": GREEN_PALETTE["medium"],
                "label": "높음",
                "description": "보호가 필요한 지역"
            },
            {
                "min": 301,
                "max": 9999,
                "color": GREEN_PALETTE["dark"],
                "label": "매우 높음",
                "description": "집중 보호가 필요한 지역"
            }
        ],
        "palette": "green",
        "palette_name": "Verde Green",
        "description": "멸종위기종이 많을수록 진한 녹색",
        "brand_message": "Verde = 스페인어로 '녹색', 생물 다양성의 풍요로움을 표현"
    }


def calculate_country_heatmap_data(country_stats: List[Dict]) -> List[Dict]:
    """
    국가별 통계 데이터를 히트맵 데이터로 변환

    작동 방식:
    1. 전체 국가 중 최대 멸종위기종 수 찾기
    2. 각 국가별로 강도 계산
    3. 색상 코드 할당
    4. 히트맵 데이터 반환

    예시:
    >>> country_stats = [
    ...     {"country": "한국", "endangered_count": 124},
    ...     {"country": "일본", "endangered_count": 89},
    ...     {"country": "중국", "endangered_count": 342}
    ... ]
    >>> heatmap_data = calculate_country_heatmap_data(country_stats)
    >>> print(heatmap_data[0])
    {
        "country": "한국",
        "endangered_count": 124,
        "intensity": 0.65,
        "color_code": "#4CAF50",
        "label": "높음"
    }

    Args:
        country_stats: 국가별 통계 리스트
            [{"country": str, "endangered_count": int}, ...]

    Returns:
        히트맵 데이터 리스트
    """
    if not country_stats:
        return []

    # 최대값 찾기
    max_count = max(
        (stat.get("endangered_count", 0) for stat in country_stats),
        default=1
    )

    heatmap_data = []
    for stat in country_stats:
        endangered_count = stat.get("endangered_count", 0)
        intensity = calculate_heatmap_intensity(endangered_count, max_count)
        color_code = get_green_color_code(intensity)
        label = get_color_label(intensity)

        heatmap_data.append({
            **stat,  # 기존 데이터 유지
            "intensity": intensity,
            "color_code": color_code,
            "label": label,
            "max_count": max_count  # 디버깅용
        })

    return heatmap_data


# 하위 호환성을 위한 별칭 (기존 코드에서 사용 중일 수 있음)
get_color_code = get_green_color_code
calculate_intensity = calculate_heatmap_intensity
