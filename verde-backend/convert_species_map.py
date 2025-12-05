"""
Convert COUNTRY_SPECIES_MAP from list format to category-based dict format
"""

# 기존 데이터를 읽어서 카테고리별로 분류
# 동물은 기존 리스트 그대로, 나머지는 대표적인 종으로 채우기

# 대륙별 대표 종 (카테고리별)
CATEGORY_SPECIES = {
    "식물": {
        "AS": [  # Asia
            "Magnolia sieboldii",      # 함박꽃나무
            "Pinus koraiensis",        # 잣나무
            "Taxus cuspidata",         # 주목
            "Rhododendron aureum",     # 금강산철쭉
            "Abies koreana",           # 구상나무
        ],
        "EU": [  # Europe
            "Taxus baccata",           # 유럽주목
            "Pinus sylvestris",        # 스코틀랜드소나무
            "Betula pendula",          # 자작나무
            "Quercus robur",           # 유럽참나무
            "Fagus sylvatica",         # 유럽너도밤나무
        ],
        "AF": [  # Africa
            "Acacia tortilis",         # 우산아카시아
            "Baobab digitata",         # 바오밥나무
            "Aloe vera",               # 알로에
            "Euphorbia tirucalli",     # 아프리카우유나무
            "Commiphora myrrha",       # 몰약나무
        ],
        "NA": [  # North America
            "Sequoia sempervirens",    # 해안레드우드
            "Pinus ponderosa",         # 폰데로사소나무
            "Quercus alba",            # 흰참나무
            "Acer saccharum",          # 설탕단풍나무
            "Betula papyrifera",       # 종이자작나무
        ],
        "SA": [  # South America
            "Bertholletia excelsa",    # 브라질너트나무
            "Hevea brasiliensis",      # 고무나무
            "Theobroma cacao",         # 카카오나무
            "Cinchona pubescens",      # 키니네나무
            "Victoria amazonica",      # 빅토리아수련
        ],
        "OC": [  # Oceania
            "Eucalyptus regnans",      # 유칼립투스
            "Acacia pycnantha",        # 골든와틀
            "Araucaria cunninghamii",  # 후프소나무
            "Ficus macrophylla",       # 모턴베이무화과
            "Banksia serrata",         # 톱잎뱅크시아
        ],
    },
    "곤충": {
        "AS": [
            "Teinopalpus imperialis",  # 황제제비나비
            "Lucanus maculifemoratus", # 넓적사슴벌레
            "Callipogon relictus",     # 장수하늘소
            "Rosalia batesi",          # 큰수염하늘소
            "Chrysochroa fulgidissima", # 비단벌레
        ],
        "EU": [
            "Lucanus cervus",          # 유럽사슴벌레
            "Cerambyx cerdo",          # 큰하늘소
            "Rosalia alpina",          # 알프스하늘소
            "Carabus auratus",         # 황금멋쟁이
            "Papilio alexanor",        # 알렉산더제비나비
        ],
        "AF": [
            "Goliathus goliatus",      # 골리앗장수풍뎅이
            "Mecynorrhina torquata",   # 목걸이꽃무지
            "Charaxes jasius",         # 아프리카왕나비
            "Mylabris oculata",        # 아프리카가뢰
            "Pachnoda marginata",      # 무늬꽃무지
        ],
        "NA": [
            "Dynastes tityus",         # 동부헤라클레스장수풍뎅이
            "Lucanus elaphus",         # 자이언트사슴벌레
            "Nicrophorus americanus",  # 미국매장벌레
            "Danaus plexippus",        # 제왕나비
            "Papilio multicaudata",    # 두꼬리제비나비
        ],
        "SA": [
            "Dynastes hercules",       # 헤라클레스장수풍뎅이
            "Megasoma elephas",        # 코끼리장수풍뎅이
            "Morpho menelaus",         # 푸른몰포나비
            "Titanus giganteus",       # 타이탄하늘소
            "Coprophanaeus lancifer",  # 뿔쇠똥구리
        ],
        "OC": [
            "Ornithoptera alexandrae", # 알렉산드라여왕나비
            "Papilio ulysses",         # 율리시스제비나비
            "Phalacrognathus muelleri",# 무지개사슴벌레
            "Lamprima aurata",         # 황금사슴벌레
            "Chrysophora chrysochlora",# 호주비단벌레
        ],
    },
    "해양생물": {
        "ALL": [  # 전 세계 공통
            "Chelonia mydas",          # 푸른바다거북
            "Caretta caretta",         # 붉은바다거북
            "Dermochelys coriacea",    # 장수거북
            "Eretmochelys imbricata",  # 대모
            "Balaenoptera musculus",   # 대왕고래
            "Megaptera novaeangliae",  # 혹등고래
            "Carcharodon carcharias",  # 백상아리
            "Manta birostris",         # 쥐가오리
            "Dugong dugon",            # 듀공
            "Trichechus manatus",      # 매너티
        ],
    },
}

# 대륙 매핑 (국가 -> 대륙)
CONTINENT_MAP = {
    "KR": "AS", "JP": "AS", "CN": "AS", "RU": "AS", "IN": "AS", "ID": "AS", "TH": "AS", "MY": "AS", "VN": "AS",
    "US": "NA", "CA": "NA", "MX": "NA",
    "BR": "SA", "AR": "SA", "PE": "SA", "CL": "SA", "CO": "SA",
    "AU": "OC", "NZ": "OC",
    "ZA": "AF", "KE": "AF", "EG": "AF", "NG": "AF",
    "GB": "EU", "FR": "EU", "DE": "EU", "IT": "EU", "ES": "EU", "SE": "EU", "NO": "EU", "PL": "EU", "TR": "EU",
}

def get_category_species(country_code, category):
    """국가와 카테고리에 맞는 대표 종 리스트 반환"""
    if category == "해양생물":
        return CATEGORY_SPECIES["해양생물"]["ALL"]

    continent = CONTINENT_MAP.get(country_code, "AS")
    return CATEGORY_SPECIES.get(category, {}).get(continent, [])

print("""
# 사용법:
# 이 스크립트는 기존 COUNTRY_SPECIES_MAP의 각 국가 리스트를
# 카테고리별 딕셔너리로 변환합니다.

# 예시:
# "US": [...species...]
# ->
# "US": {
#     "동물": [...기존 species...],
#     "식물": [...대륙별 대표 식물...],
#     "곤충": [...대륙별 대표 곤충...],
#     "해양생물": [...전세계 공통 해양생물...]
# }
""")

# 실제 변환 로직은 country_species_map.py 파일을 직접 수정하는 것이 더 안전하므로
# 여기서는 각 국가에 추가할 데이터를 출력하는 방식으로 제공
print("\n각 국가에 추가할 카테고리별 데이터:")
for country in ["US", "JP", "CN", "RU", "AU", "BR", "IN", "ZA", "CA"]:
    print(f"\n{country}:")
    for category in ["식물", "곤충", "해양생물"]:
        species_list = get_category_species(country, category)
        print(f'  "{category}": {species_list},')
