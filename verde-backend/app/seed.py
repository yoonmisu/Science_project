"""
Verde 데이터베이스 초기 샘플 데이터 시드
실행: python -m app.seed
"""

import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.species import Species
from app.models.search_query import SearchQuery
from app.models.region_biodiversity import RegionBiodiversity
from app.cache import increment_search_count

# 테이블 생성
Base.metadata.create_all(bind=engine)


def seed_korean_species(db: Session):
    """한국 생물 10종 추가"""
    korean_species = [
        {
            "name": "가시연",
            "scientific_name": "Euryale ferox",
            "category": "식물",
            "region": "한강, 낙동강 유역",
            "country": "대한민국",
            "description": "수련과에 속하는 일년생 수생식물로, 잎과 줄기에 날카로운 가시가 있는 것이 특징입니다. 한국에서는 한강과 낙동강 유역의 습지에서 자생하며, 서식지 파괴로 인해 개체수가 급감했습니다.",
            "characteristics": ["잎 지름 최대 2m", "보라색 꽃", "가시가 있는 잎", "습지 서식", "일년생"],
            "image_url": "https://example.com/euryale.jpg",
            "conservation_status": "멸종위기",
            "search_count": 150
        },
        {
            "name": "산양",
            "scientific_name": "Naemorhedus caudatus",
            "category": "동물",
            "region": "설악산, 태백산맥",
            "country": "대한민국",
            "description": "소과에 속하는 포유류로, 한국의 험준한 산악지대에 서식합니다. 천연기념물 제217호로 지정되어 있으며, 밀렵과 서식지 감소로 멸종위기에 처해 있습니다.",
            "characteristics": ["회갈색 털", "짧은 뿔", "암벽 등반 능력", "단독 생활", "초식성"],
            "image_url": "https://example.com/goral.jpg",
            "conservation_status": "멸종위기",
            "search_count": 230
        },
        {
            "name": "장수하늘소",
            "scientific_name": "Callipogon relictus",
            "category": "곤충",
            "region": "광릉숲, 강원도",
            "country": "대한민국",
            "description": "하늘소과에 속하는 대형 딱정벌레로, 한국에서 가장 큰 곤충 중 하나입니다. 참나무류의 고사목에 서식하며, 서식지 감소로 인해 희귀해졌습니다.",
            "characteristics": ["체장 최대 12cm", "검은색 광택", "큰 턱", "야행성", "참나무 서식"],
            "image_url": "https://example.com/longhorn.jpg",
            "conservation_status": "준위협",
            "search_count": 180
        },
        {
            "name": "상괭이",
            "scientific_name": "Neophocaena asiaeorientalis",
            "category": "해양생물",
            "region": "서해, 남해",
            "country": "대한민국",
            "description": "돌고래과에 속하는 소형 고래류로, 한국 연안에서 서식합니다. 등지느러미가 없는 것이 특징이며, 어업 활동과 해양 오염으로 인해 개체수가 감소하고 있습니다.",
            "characteristics": ["등지느러미 없음", "회색 체색", "연안 서식", "소형 고래", "무리 생활"],
            "image_url": "https://example.com/porpoise.jpg",
            "conservation_status": "멸종위기",
            "search_count": 120
        },
        {
            "name": "금강초롱꽃",
            "scientific_name": "Hanabusaya asiatica",
            "category": "식물",
            "region": "금강산, 설악산",
            "country": "대한민국",
            "description": "초롱꽃과에 속하는 한국 고유종으로, 금강산에서 처음 발견되어 이름이 붙여졌습니다. 보라색의 아름다운 종 모양 꽃이 특징이며, 높은 산지의 바위틈에서 자랍니다.",
            "characteristics": ["한국 고유종", "보라색 종 모양 꽃", "고산 식물", "8-9월 개화", "다년생"],
            "image_url": "https://example.com/hanabusaya.jpg",
            "conservation_status": "취약",
            "search_count": 95
        },
        {
            "name": "반달가슴곰",
            "scientific_name": "Ursus thibetanus ussuricus",
            "category": "동물",
            "region": "지리산",
            "country": "대한민국",
            "description": "곰과에 속하는 대형 포유류로, 가슴에 흰색 반달 무늬가 있는 것이 특징입니다. 한국에서는 지리산에 복원 프로젝트를 통해 개체수를 늘리고 있습니다.",
            "characteristics": ["가슴 반달 무늬", "검은색 털", "잡식성", "동면", "단독 생활"],
            "image_url": "https://example.com/moonbear.jpg",
            "conservation_status": "멸종위기",
            "search_count": 340
        },
        {
            "name": "노랑부리백로",
            "scientific_name": "Egretta eulophotes",
            "category": "동물",
            "region": "서해안 무인도",
            "country": "대한민국",
            "description": "백로과에 속하는 조류로, 번식기에 노란색 부리와 화려한 장식깃이 나타납니다. 서해안의 무인도에서 집단 번식하며, 전 세계적으로 희귀한 종입니다.",
            "characteristics": ["노란색 부리", "흰색 깃털", "집단 번식", "철새", "어류 포식"],
            "image_url": "https://example.com/egret.jpg",
            "conservation_status": "취약",
            "search_count": 88
        },
        {
            "name": "비단벌레",
            "scientific_name": "Chrysochroa fulgidissima",
            "category": "곤충",
            "region": "중부 이남 지역",
            "country": "대한민국",
            "description": "비단벌레과에 속하는 딱정벌레로, 금속성 광택의 아름다운 외관이 특징입니다. 팽나무에서 서식하며, 고대부터 장식품으로 사용되어 왔습니다.",
            "characteristics": ["금속성 녹색 광택", "체장 3-4cm", "팽나무 서식", "주행성", "목재 해충"],
            "image_url": "https://example.com/jewelbeetle.jpg",
            "conservation_status": "관심대상",
            "search_count": 65
        },
        {
            "name": "점박이물범",
            "scientific_name": "Phoca largha",
            "category": "해양생물",
            "region": "백령도",
            "country": "대한민국",
            "description": "물범과에 속하는 해양 포유류로, 회색 바탕에 검은 점무늬가 있습니다. 백령도 주변 해역에서 서식하며, 한국에서 볼 수 있는 유일한 물범 종입니다.",
            "characteristics": ["점무늬 패턴", "최대 170cm", "어류 포식", "연안 서식", "무리 생활"],
            "image_url": "https://example.com/spottedseal.jpg",
            "conservation_status": "취약",
            "search_count": 145
        },
        {
            "name": "광릉요강꽃",
            "scientific_name": "Cypripedium japonicum",
            "category": "식물",
            "region": "광릉숲",
            "country": "대한민국",
            "description": "난초과에 속하는 식물로, 꽃 모양이 요강을 닮아 이름이 붙여졌습니다. 광릉숲에서 처음 발견되었으며, 불법 채취로 인해 자생지가 크게 줄었습니다.",
            "characteristics": ["요강 모양 꽃", "흰색-분홍색", "5-6월 개화", "숲 속 서식", "다년생"],
            "image_url": "https://example.com/ladyslipper.jpg",
            "conservation_status": "멸종위기",
            "search_count": 78
        }
    ]

    for species_data in korean_species:
        species = Species(**species_data)
        db.add(species)

    db.commit()
    print(f"✓ 한국 생물 {len(korean_species)}종 추가 완료")


def seed_international_species(db: Session):
    """해외 생물 10종 추가"""
    international_species = [
        {
            "name": "북극여우",
            "scientific_name": "Vulpes lagopus",
            "category": "동물",
            "region": "북극권",
            "country": "북극",
            "description": "개과에 속하는 소형 여우로, 극한의 추위에 적응한 종입니다. 겨울에는 흰색, 여름에는 갈색으로 털색이 변하며, 기후변화로 인해 서식지가 줄어들고 있습니다.",
            "characteristics": ["계절별 털색 변화", "두꺼운 털", "작은 귀", "-50°C 생존", "잡식성"],
            "image_url": "https://example.com/arcticfox.jpg",
            "conservation_status": "취약",
            "search_count": 280
        },
        {
            "name": "자이언트 팬더",
            "scientific_name": "Ailuropoda melanoleuca",
            "category": "동물",
            "region": "쓰촨성 산악지대",
            "country": "중국",
            "description": "곰과에 속하는 대형 포유류로, 검은색과 흰색의 특징적인 무늬가 있습니다. 대나무를 주식으로 하며, 중국의 보호 노력으로 개체수가 증가하고 있습니다.",
            "characteristics": ["흑백 무늬", "대나무 주식", "단독 생활", "최대 160kg", "12-14시간 식사"],
            "image_url": "https://example.com/panda.jpg",
            "conservation_status": "취약",
            "search_count": 520
        },
        {
            "name": "바다거북",
            "scientific_name": "Chelonia mydas",
            "category": "해양생물",
            "region": "열대 및 아열대 해역",
            "country": "전 세계",
            "description": "바다거북과에 속하는 대형 파충류로, 전 세계 열대 해역에서 서식합니다. 해양 오염과 서식지 파괴로 인해 모든 종이 멸종위기에 처해 있습니다.",
            "characteristics": ["최대 1.5m", "초식성", "장거리 회유", "해변 산란", "수명 80년 이상"],
            "image_url": "https://example.com/seaturtle.jpg",
            "conservation_status": "멸종위기",
            "search_count": 380
        },
        {
            "name": "오카피",
            "scientific_name": "Okapia johnstoni",
            "category": "동물",
            "region": "이투리 열대우림",
            "country": "콩고민주공화국",
            "description": "기린과에 속하는 포유류로, 다리에 얼룩말 같은 줄무늬가 있습니다. 콩고의 열대우림에만 서식하는 희귀종으로, 밀렵과 서식지 파괴로 위협받고 있습니다.",
            "characteristics": ["다리 줄무늬", "긴 혀 (최대 35cm)", "단독 생활", "야행성", "초식성"],
            "image_url": "https://example.com/okapi.jpg",
            "conservation_status": "멸종위기",
            "search_count": 125
        },
        {
            "name": "코알라",
            "scientific_name": "Phascolarctos cinereus",
            "category": "동물",
            "region": "동부 해안 지역",
            "country": "호주",
            "description": "코알라과에 속하는 유대류로, 유칼립투스 나무에서 생활합니다. 산불과 서식지 파괴로 인해 개체수가 급감하여 최근 멸종위기종으로 지정되었습니다.",
            "characteristics": ["유칼립투스 식이", "하루 20시간 수면", "유대류", "단독 생활", "나무 위 생활"],
            "image_url": "https://example.com/koala.jpg",
            "conservation_status": "멸종위기",
            "search_count": 410
        },
        {
            "name": "제왕나비",
            "scientific_name": "Danaus plexippus",
            "category": "곤충",
            "region": "북미 대륙",
            "country": "미국",
            "description": "네발나비과에 속하는 대형 나비로, 매년 수천 km를 이동하는 장거리 이주로 유명합니다. 기후변화와 서식지 감소로 개체수가 급감하고 있습니다.",
            "characteristics": ["주황색 날개", "검은 테두리", "장거리 이주", "독성 보유", "박하과 식물 선호"],
            "image_url": "https://example.com/monarch.jpg",
            "conservation_status": "멸종위기",
            "search_count": 195
        },
        {
            "name": "아이아이",
            "scientific_name": "Daubentonia madagascariensis",
            "category": "동물",
            "region": "마다가스카르 동부 열대우림",
            "country": "마다가스카르",
            "description": "아이아이과에 속하는 영장류로, 긴 가운데 손가락으로 나무 속 곤충을 꺼내 먹습니다. 마다가스카르 고유종으로, 서식지 파괴와 미신으로 인해 위협받고 있습니다.",
            "characteristics": ["긴 가운데 손가락", "큰 눈", "야행성", "잡식성", "단독 생활"],
            "image_url": "https://example.com/ayeaye.jpg",
            "conservation_status": "멸종위기",
            "search_count": 88
        },
        {
            "name": "라플레시아",
            "scientific_name": "Rafflesia arnoldii",
            "category": "식물",
            "region": "수마트라, 보르네오 열대우림",
            "country": "인도네시아",
            "description": "라플레시아과에 속하는 기생식물로, 세계에서 가장 큰 꽃을 피웁니다. 직경이 최대 1m에 달하며, 썩은 고기 냄새로 파리를 유인합니다.",
            "characteristics": ["최대 직경 1m", "기생식물", "악취", "잎/줄기/뿌리 없음", "5일간 개화"],
            "image_url": "https://example.com/rafflesia.jpg",
            "conservation_status": "취약",
            "search_count": 156
        },
        {
            "name": "흰코뿔소",
            "scientific_name": "Ceratotherium simum",
            "category": "동물",
            "region": "사바나 초원",
            "country": "남아프리카공화국",
            "description": "코뿔소과에 속하는 대형 포유류로, 지구상에서 두 번째로 큰 육상 동물입니다. 뿔을 노린 밀렵으로 인해 심각한 위협을 받고 있습니다.",
            "characteristics": ["두 개의 뿔", "최대 2.3톤", "초식성", "무리 생활", "진흙 목욕"],
            "image_url": "https://example.com/whiterhino.jpg",
            "conservation_status": "준위협",
            "search_count": 245
        },
        {
            "name": "블루링옥토퍼스",
            "scientific_name": "Hapalochlaena lunulata",
            "category": "해양생물",
            "region": "인도-태평양 해역",
            "country": "호주",
            "description": "문어과에 속하는 소형 문어로, 아름다운 파란 고리 무늬가 특징입니다. 크기는 작지만 치명적인 독을 가지고 있어 가장 위험한 해양생물 중 하나입니다.",
            "characteristics": ["파란 고리 무늬", "체장 12-20cm", "맹독성", "산호초 서식", "야행성"],
            "image_url": "https://example.com/blueringoctopus.jpg",
            "conservation_status": "관심대상",
            "search_count": 178
        }
    ]

    for species_data in international_species:
        species = Species(**species_data)
        db.add(species)

    db.commit()
    print(f"✓ 해외 생물 {len(international_species)}종 추가 완료")


def seed_region_biodiversity(db: Session):
    """지역 생물다양성 데이터 추가"""
    regions = [
        {
            "region_name": "대한민국",
            "country": "대한민국",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "total_species_count": 100000,
            "endangered_count": 267,
            "plant_count": 4500,
            "animal_count": 18000,
            "insect_count": 15000,
            "marine_count": 3200
        },
        {
            "region_name": "미국",
            "country": "미국",
            "latitude": 38.8951,
            "longitude": -77.0364,
            "total_species_count": 200000,
            "endangered_count": 1600,
            "plant_count": 18000,
            "animal_count": 45000,
            "insect_count": 91000,
            "marine_count": 8500
        },
        {
            "region_name": "영국",
            "country": "영국",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "total_species_count": 70000,
            "endangered_count": 1188,
            "plant_count": 3000,
            "animal_count": 15000,
            "insect_count": 24000,
            "marine_count": 4500
        },
        {
            "region_name": "일본",
            "country": "일본",
            "latitude": 35.6762,
            "longitude": 139.6503,
            "total_species_count": 90000,
            "endangered_count": 3716,
            "plant_count": 7000,
            "animal_count": 20000,
            "insect_count": 32000,
            "marine_count": 5800
        },
        {
            "region_name": "중국",
            "country": "중국",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "total_species_count": 340000,
            "endangered_count": 958,
            "plant_count": 35000,
            "animal_count": 68000,
            "insect_count": 150000,
            "marine_count": 12000
        },
        {
            "region_name": "호주",
            "country": "호주",
            "latitude": -33.8688,
            "longitude": 151.2093,
            "total_species_count": 600000,
            "endangered_count": 1900,
            "plant_count": 25000,
            "animal_count": 80000,
            "insect_count": 300000,
            "marine_count": 32000
        },
        {
            "region_name": "브라질",
            "country": "브라질",
            "latitude": -15.8267,
            "longitude": -47.9218,
            "total_species_count": 500000,
            "endangered_count": 1173,
            "plant_count": 56000,
            "animal_count": 120000,
            "insect_count": 200000,
            "marine_count": 8000
        },
        {
            "region_name": "인도네시아",
            "country": "인도네시아",
            "latitude": -6.2088,
            "longitude": 106.8456,
            "total_species_count": 300000,
            "endangered_count": 583,
            "plant_count": 28000,
            "animal_count": 65000,
            "insect_count": 150000,
            "marine_count": 15000
        }
    ]

    for region_data in regions:
        region = RegionBiodiversity(**region_data)
        db.add(region)

    db.commit()
    print(f"✓ 지역 생물다양성 데이터 {len(regions)}개 추가 완료")


def seed_search_queries(db: Session):
    """검색어 초기 데이터 추가"""
    search_queries = [
        {
            "query_text": "영국 식물 멸종위기 종류",
            "category": "식물",
            "region": "영국",
            "search_count": 45
        },
        {
            "query_text": "미국 곤충 생물 다양성",
            "category": "곤충",
            "region": "미국",
            "search_count": 38
        },
        {
            "query_text": "대한민국 해양 생물 다양성",
            "category": "해양생물",
            "region": "대한민국",
            "search_count": 52
        },
        {
            "query_text": "일본 식물 멸종위기 종류",
            "category": "식물",
            "region": "일본",
            "search_count": 41
        },
        {
            "query_text": "대한민국 곤충 멸종위기 종류",
            "category": "곤충",
            "region": "대한민국",
            "search_count": 36
        },
        {
            "query_text": "호주 동물 멸종위기",
            "category": "동물",
            "region": "호주",
            "search_count": 67
        },
        {
            "query_text": "중국 팬더 서식지",
            "category": "동물",
            "region": "중국",
            "search_count": 89
        },
        {
            "query_text": "반달가슴곰",
            "category": None,
            "region": None,
            "search_count": 125
        },
        {
            "query_text": "바다거북 보호",
            "category": "해양생물",
            "region": None,
            "search_count": 73
        },
        {
            "query_text": "북극여우 기후변화",
            "category": "동물",
            "region": "북극",
            "search_count": 58
        }
    ]

    for query_data in search_queries:
        search_query = SearchQuery(**query_data)
        db.add(search_query)

        # Redis Sorted Set에도 추가
        increment_search_count(
            query_data["query_text"],
            query_data.get("category")
        )
        # 카운트만큼 추가 증가
        for _ in range(query_data["search_count"] - 1):
            increment_search_count(
                query_data["query_text"],
                query_data.get("category")
            )

    db.commit()
    print(f"✓ 검색어 데이터 {len(search_queries)}개 추가 완료")


def clear_data(db: Session):
    """기존 데이터 삭제"""
    db.query(SearchQuery).delete()
    db.query(Species).delete()
    db.query(RegionBiodiversity).delete()
    db.commit()
    print("✓ 기존 데이터 삭제 완료")


def main():
    """메인 시드 함수"""
    print("\n" + "=" * 50)
    print("🌿 Verde 데이터베이스 시드 시작")
    print("=" * 50 + "\n")

    db = SessionLocal()

    try:
        # 기존 데이터 삭제
        clear_data(db)

        # 데이터 추가
        seed_korean_species(db)
        seed_international_species(db)
        seed_region_biodiversity(db)
        seed_search_queries(db)

        print("\n" + "=" * 50)
        print("✅ 모든 시드 데이터 추가 완료!")
        print("=" * 50 + "\n")

        # 통계 출력
        species_count = db.query(Species).count()
        region_count = db.query(RegionBiodiversity).count()
        search_count = db.query(SearchQuery).count()

        print(f"📊 데이터 통계:")
        print(f"   - 생물종: {species_count}종")
        print(f"   - 지역: {region_count}개")
        print(f"   - 검색어: {search_count}개\n")

    except Exception as e:
        print(f"\n❌ 시드 실패: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
