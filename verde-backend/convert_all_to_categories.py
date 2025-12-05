#!/usr/bin/env python3
"""
COUNTRY_SPECIES_MAP과 CONTINENT_SPECIES_MAP을 카테고리별 dict 구조로 변환
"""

# 대륙 매핑
CONTINENT_MAP = {
    "KR": "AS", "KP": "AS", "JP": "AS", "CN": "AS", "RU": "AS", "IN": "AS", "ID": "AS",
    "TH": "AS", "MY": "AS", "VN": "AS", "US": "NA", "CA": "NA", "MX": "NA", "BR": "SA",
    "AR": "SA", "PE": "SA", "CL": "SA", "CO": "SA", "AU": "OC", "NZ": "OC", "ZA": "AF",
    "KE": "AF", "EG": "AF", "NG": "AF", "GB": "EU", "FR": "EU", "DE": "EU", "IT": "EU",
    "ES": "EU", "SE": "EU", "NO": "EU", "PL": "EU", "TR": "EU",
}

# 대륙별 카테고리 대표종
PLANTS = {
    "AS": ["Magnolia sieboldii", "Pinus koraiensis", "Taxus cuspidata", "Rhododendron aureum", "Abies koreana"],
    "EU": ["Taxus baccata", "Pinus sylvestris", "Betula pendula", "Quercus robur", "Fagus sylvatica"],
    "AF": ["Acacia tortilis", "Adansonia digitata", "Aloe vera", "Euphorbia tirucalli", "Commiphora myrrha"],
    "NA": ["Sequoia sempervirens", "Pinus ponderosa", "Quercus alba", "Acer saccharum", "Betula papyrifera"],
    "SA": ["Bertholletia excelsa", "Hevea brasiliensis", "Theobroma cacao", "Cinchona pubescens", "Victoria amazonica"],
    "OC": ["Eucalyptus regnans", "Acacia pycnantha", "Araucaria cunninghamii", "Ficus macrophylla", "Banksia serrata"],
}

INSECTS = {
    "AS": ["Teinopalpus imperialis", "Lucanus maculifemoratus", "Callipogon relictus", "Rosalia batesi"],
    "EU": ["Lucanus cervus", "Cerambyx cerdo", "Rosalia alpina", "Carabus auratus"],
    "AF": ["Goliathus goliatus", "Mecynorrhina torquata", "Charaxes jasius", "Mylabris oculata"],
    "NA": ["Dynastes tityus", "Lucanus elaphus", "Nicrophorus americanus", "Danaus plexippus"],
    "SA": ["Dynastes hercules", "Megasoma elephas", "Morpho menelaus", "Titanus giganteus"],
    "OC": ["Ornithoptera alexandrae", "Papilio ulysses", "Phalacrognathus muelleri", "Lamprima aurata"],
}

MARINE = ["Chelonia mydas", "Caretta caretta", "Dermochelys coriacea", "Eretmochelys imbricata",
          "Balaenoptera musculus", "Megaptera novaeangliae", "Carcharodon carcharias", "Dugong dugon"]

def format_species_list(species_list, indent=12):
    """종 리스트를 포맷팅"""
    lines = []
    for species in species_list:
        lines.append(f'{" " * indent}"{species}",')
    return '\n'.join(lines)

def convert_country_to_dict(country_code, animal_species):
    """국가 데이터를 dict 형식으로 변환"""
    continent = CONTINENT_MAP.get(country_code, "AS")

    plant_species = PLANTS.get(continent, PLANTS["AS"])
    insect_species = INSECTS.get(continent, INSECTS["AS"])
    marine_species = MARINE

    return f'''    "{country_code}": {{
        "동물": [
{format_species_list(animal_species)}
        ],
        "식물": [
{format_species_list(plant_species)}
        ],
        "곤충": [
{format_species_list(insect_species)}
        ],
        "해양생물": [
{format_species_list(marine_species)}
        ],
    }}'''

def convert_continent_to_dict(continent_code, animal_species):
    """대륙 데이터를 dict 형식으로 변환"""
    # 대륙 코드를 대륙 매핑 값으로 변환
    continent_key = continent_code  # AS, EU, AF, NA, SA, OC, AN

    plant_species = PLANTS.get(continent_key, PLANTS.get("AS", []))
    insect_species = INSECTS.get(continent_key, INSECTS.get("AS", []))
    marine_species = MARINE

    return f'''    "{continent_code}": {{
        "동물": [
{format_species_list(animal_species)}
        ],
        "식물": [
{format_species_list(plant_species)}
        ],
        "곤충": [
{format_species_list(insect_species)}
        ],
        "해양생물": [
{format_species_list(marine_species)}
        ],
    }}'''

# 파일 읽기
print("📖 파일 읽는 중...")
with open('app/services/country_species_map.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 새 파일 생성
new_lines = []
i = 0
in_country_map = False
in_continent_map = False
skip_until_bracket = 0

while i < len(lines):
    line = lines[i]

    # COUNTRY_SPECIES_MAP 시작
    if 'COUNTRY_SPECIES_MAP = {' in line:
        new_lines.append(line)
        in_country_map = True
        i += 1
        continue

    # CONTINENT_SPECIES_MAP 시작
    if 'CONTINENT_SPECIES_MAP = {' in line:
        new_lines.append(line)
        in_continent_map = True
        in_country_map = False
        i += 1
        continue

    # 맵 종료
    if in_country_map or in_continent_map:
        if line.strip() == '}' or line.strip() == '};':
            in_country_map = False
            in_continent_map = False
            new_lines.append(line)
            i += 1
            continue

        # 국가/대륙 항목 시작 감지
        if line.strip().startswith('"') and ':' in line:
            # 코드 추출
            code = line.strip().split('"')[1]

            # 이미 dict 형식인지 확인
            if '{' in line:
                # 이미 dict 형식 - 그대로 복사
                new_lines.append(line)
                i += 1
                continue

            # list 형식 - 변환 필요
            if '[' in line:
                # 종 리스트 수집
                species_list = []
                i += 1

                while i < len(lines):
                    if ']' in lines[i]:
                        # 리스트 종료
                        break

                    # 학명 추출
                    species_line = lines[i].strip()
                    if species_line and species_line.startswith('"'):
                        species_name = species_line.split('"')[1]
                        species_list.append(species_name)

                    i += 1

                # dict 형식으로 변환
                if in_continent_map:
                    converted = convert_continent_to_dict(code, species_list)
                else:
                    converted = convert_country_to_dict(code, species_list)

                new_lines.append(converted + ',\n')
                i += 1
                continue

    # 기본: 라인 그대로 복사
    new_lines.append(line)
    i += 1

# 파일 쓰기
print("💾 파일 저장 중...")
with open('app/services/country_species_map.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ 완료! 모든 국가와 대륙 데이터가 카테고리별로 변환되었습니다.")
print(f"   파일: app/services/country_species_map.py")
