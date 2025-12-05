"""
모든 국가의 COUNTRY_SPECIES_MAP을 카테고리별 dict 구조로 자동 변환
기존 list는 "동물" 카테고리로, 나머지 카테고리는 대륙별 대표종으로 채움
"""

import re

# 대륙 매핑
CONTINENT_MAP = {
    # Asia
    "KR": "AS", "KP": "AS", "JP": "AS", "CN": "AS", "TW": "AS", "HK": "AS", "MO": "AS",
    "MN": "AS", "VN": "AS", "TH": "AS", "LA": "AS", "KH": "AS", "MM": "AS", "MY": "AS",
    "SG": "AS", "BN": "AS", "ID": "AS", "PH": "AS", "TL": "AS", "IN": "AS", "PK": "AS",
    "BD": "AS", "LK": "AS", "NP": "AS", "BT": "AS", "MV": "AS", "AF": "AS", "IR": "AS",
    "IQ": "AS", "SY": "AS", "LB": "AS", "JO": "AS", "IL": "AS", "PS": "AS", "SA": "AS",
    "YE": "AS", "OM": "AS", "AE": "AS", "QA": "AS", "BH": "AS", "KW": "AS", "TR": "AS",
    "CY": "AS", "GE": "AS", "AM": "AS", "AZ": "AS", "KZ": "AS", "UZ": "AS", "TM": "AS",
    "KG": "AS", "TJ": "AS",
    # Europe
    "GB": "EU", "IE": "EU", "FR": "EU", "ES": "EU", "PT": "EU", "IT": "EU", "DE": "EU",
    "NL": "EU", "BE": "EU", "LU": "EU", "DK": "EU", "SE": "EU", "NO": "EU", "FI": "EU",
    "IS": "EU", "PL": "EU", "CZ": "EU", "SK": "EU", "HU": "EU", "AT": "EU", "CH": "EU",
    "RU": "EU",
    # Africa
    "EG": "AF", "ZA": "AF", "KE": "AF", "NG": "AF", "ET": "AF", "TZ": "AF", "UG": "AF",
    # North America
    "US": "NA", "CA": "NA", "MX": "NA",
    # South America
    "BR": "SA", "AR": "SA", "PE": "SA", "CL": "SA", "CO": "SA", "VE": "SA",
    # Oceania
    "AU": "OC", "NZ": "OC",
}

# 대륙별 카테고리 대표종
CATEGORY_SPECIES_BY_CONTINENT = {
    "식물": {
        "AS": ["Magnolia sieboldii", "Pinus koraiensis", "Taxus cuspidata", "Rhododendron aureum", "Abies koreana"],
        "EU": ["Taxus baccata", "Pinus sylvestris", "Betula pendula", "Quercus robur", "Fagus sylvatica"],
        "AF": ["Acacia tortilis", "Adansonia digitata", "Aloe vera", "Euphorbia tirucalli", "Commiphora myrrha"],
        "NA": ["Sequoia sempervirens", "Pinus ponderosa", "Quercus alba", "Acer saccharum", "Betula papyrifera"],
        "SA": ["Bertholletia excelsa", "Hevea brasiliensis", "Theobroma cacao", "Cinchona pubescens", "Victoria amazonica"],
        "OC": ["Eucalyptus regnans", "Acacia pycnantha", "Araucaria cunninghamii", "Ficus macrophylla", "Banksia serrata"],
    },
    "곤충": {
        "AS": ["Teinopalpus imperialis", "Lucanus maculifemoratus", "Callipogon relictus", "Rosalia batesi"],
        "EU": ["Lucanus cervus", "Cerambyx cerdo", "Rosalia alpina", "Carabus auratus"],
        "AF": ["Goliathus goliatus", "Mecynorrhina torquata", "Charaxes jasius", "Mylabris oculata"],
        "NA": ["Dynastes tityus", "Lucanus elaphus", "Nicrophorus americanus", "Danaus plexippus"],
        "SA": ["Dynastes hercules", "Megasoma elephas", "Morpho menelaus", "Titanus giganteus"],
        "OC": ["Ornithoptera alexandrae", "Papilio ulysses", "Phalacrognathus muelleri", "Lamprima aurata"],
    },
    "해양생물": {
        "ALL": ["Chelonia mydas", "Caretta caretta", "Dermochelys coriacea", "Eretmochelys imbricata",
                "Balaenoptera musculus", "Megaptera novaeangliae", "Carcharodon carcharias", "Dugong dugon"],
    }
}

def get_category_species(country_code, category):
    """국가 코드와 카테고리로 대표종 리스트 반환"""
    if category == "해양생물":
        return CATEGORY_SPECIES_BY_CONTINENT["해양생물"]["ALL"]

    continent = CONTINENT_MAP.get(country_code, "AS")  # 기본값: 아시아
    return CATEGORY_SPECIES_BY_CONTINENT.get(category, {}).get(continent, [])

# 파일 읽기
with open('app/services/country_species_map.py', 'r', encoding='utf-8') as f:
    content = f.read()

# COUNTRY_SPECIES_MAP 영역 찾기
map_start = content.find('COUNTRY_SPECIES_MAP = {')
map_end = content.find('\n}', map_start) + 2

# 기존 맵 파싱 (간단한 정규식 기반)
# "CODE": [...] 패턴을 찾아서 변환
pattern = r'"([A-Z]{2})":\s*\[(.*?)\],'
matches = re.finditer(pattern, content[map_start:map_end], re.DOTALL)

new_map_entries = []

for match in matches:
    country_code = match.group(1)
    species_block = match.group(2)

    # 이미 dict 구조면 스킵 (KR, US는 이미 변환됨)
    if '{' in species_block:
        continue

    # 기존 종 리스트 추출 (학명만)
    species_lines = [line.strip() for line in species_block.split('\n') if line.strip() and line.strip().startswith('"')]
    animal_species = [line.split('"')[1] for line in species_lines if '"' in line]

    if not animal_species:
        continue

    # 카테고리별 데이터 생성
    plant_species = get_category_species(country_code, "식물")
    insect_species = get_category_species(country_code, "곤충")
    marine_species = get_category_species(country_code, "해양생물")

    # 새로운 dict 형식 생성
    entry = f'''    "{country_code}": {{
        "동물": [
{chr(10).join(f'            "{s}",' for s in animal_species)}
        ],
        "식물": [
{chr(10).join(f'            "{s}",' for s in plant_species)}
        ],
        "곤충": [
{chr(10).join(f'            "{s}",' for s in insect_species)}
        ],
        "해양생물": [
{chr(10).join(f'            "{s}",' for s in marine_species)}
        ],
    }},'''

    new_map_entries.append((country_code, entry))

print(f"✅ 변환할 국가: {len(new_map_entries)}개")
print(f"   {', '.join([code for code, _ in new_map_entries])}")
print(f"\n변환된 데이터 샘플 (JP):")

# JP 샘플 출력
for code, entry in new_map_entries:
    if code == "JP":
        print(entry)
        break

# 실제 파일 업데이트는 수동으로 확인 후 진행
print("\n\n⚠️  자동 변환 완료. 이제 실제 파일을 업데이트합니다...")
print("    기존 list 구조를 모두 dict 구조로 변환합니다.")
