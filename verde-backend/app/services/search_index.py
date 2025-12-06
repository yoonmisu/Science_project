"""
Verde Species Search Index

학명과 일반명을 매핑하여 빠른 검색을 지원합니다.
IUCN API 호출 없이 로컬 데이터에서 즉시 검색 결과를 반환합니다.
"""

from typing import Dict, List, Optional, Tuple
import difflib
from dataclasses import dataclass

# 해양 포유류 학명 목록 (항상 "해양생물" 카테고리로 분류)
# 주의: 완전 수생 동물만 포함 (반수생 동물인 수달, 하마, 북극곰 등은 제외)
MARINE_MAMMAL_SPECIES = {
    # 고래류 (Cetacea) - 완전 수생
    "Balaenoptera musculus",      # 대왕고래
    "Balaenoptera physalus",      # 참고래 (긴수염고래)
    "Balaenoptera borealis",      # 보리고래
    "Balaenoptera acutorostrata", # 밍크고래
    "Balaenoptera edeni",         # 브라이드고래
    "Megaptera novaeangliae",     # 혹등고래
    "Balaena mysticetus",         # 북극고래
    "Eubalaena australis",        # 남방참고래
    "Eubalaena glacialis",        # 북대서양참고래
    "Eubalaena japonica",         # 북태평양참고래
    "Eschrichtius robustus",      # 귀신고래
    "Physeter macrocephalus",     # 향유고래
    "Kogia breviceps",            # 꼬마향유고래
    "Orcinus orca",               # 범고래
    "Tursiops truncatus",         # 큰돌고래
    "Delphinus delphis",          # 참돌고래
    "Stenella coeruleoalba",      # 줄무늬돌고래
    "Stenella longirostris",      # 긴부리돌고래
    "Grampus griseus",            # 위험돌고래
    "Globicephala melas",         # 긴지느러미고래
    "Globicephala macrorhynchus", # 짧은지느러미고래
    "Pseudorca crassidens",       # 혹범고래
    "Feresa attenuata",           # 난쟁이범고래
    "Peponocephala electra",      # 멜론머리고래
    "Lagenorhynchus obliquidens", # 태평양흰줄박이돌고래
    "Sotalia fluviatilis",        # 투쿠시
    "Inia geoffrensis",           # 아마존강돌고래
    "Lipotes vexillifer",         # 바이지
    "Neophocaena asiaeorientalis", # 상괭이
    "Neophocaena phocaenoides",   # 인도태평양상괭이
    "Sousa chinensis",            # 인도태평양혹등돌고래
    "Platanista gangetica",       # 갠지스강돌고래
    "Phocoena phocoena",          # 쇠돌고래
    "Phocoenoides dalli",         # 돌쇠돌고래
    "Delphinapterus leucas",      # 흰돌고래 (벨루가)
    "Monodon monoceros",          # 일각고래
    "Ziphius cavirostris",        # 큐비에부리고래
    "Mesoplodon densirostris",    # 블레인빌부리고래

    # 해우류 (Sirenia) - 완전 수생
    "Trichechus manatus",         # 서인도매너티
    "Trichechus inunguis",        # 아마존매너티
    "Trichechus senegalensis",    # 서아프리카매너티
    "Dugong dugon",               # 듀공

    # 기각류 (Pinnipedia) - 물범, 바다사자 등 (해양 의존)
    "Monachus monachus",          # 지중해몽크물범
    "Neomonachus schauinslandi",  # 하와이몽크물범
    "Halichoerus grypus",         # 회색물범
    "Phoca vitulina",             # 항구물범
    "Phoca largha",               # 점박이물범
    "Phoca hispida",              # 고리물범
    "Pagophilus groenlandicus",   # 하프물범
    "Erignathus barbatus",        # 턱수염물범
    "Cystophora cristata",        # 두건물범
    "Mirounga leonina",           # 남방코끼리물범
    "Mirounga angustirostris",    # 북방코끼리물범
    "Hydrurga leptonyx",          # 표범물범
    "Lobodon carcinophaga",       # 게잡이물범
    "Leptonychotes weddellii",    # 웨델물범
    "Ommatophoca rossii",         # 로스물범
    "Odobenus rosmarus",          # 바다코끼리
    "Eumetopias jubatus",         # 스텔라바다사자
    "Zalophus californianus",     # 캘리포니아바다사자
    "Otaria flavescens",          # 남미바다사자
    "Arctocephalus pusillus",     # 남아프리카물개
    "Arctocephalus gazella",      # 남극물개
    "Callorhinus ursinus",        # 북방물개

    # 해달 (Enhydra lutris)만 포함 - 거의 완전 수생
    "Enhydra lutris",             # 해달
}

# 학명 -> 정보 매핑 (일반명, 카테고리, 서식 국가)
@dataclass
class SpeciesInfo:
    scientific_name: str
    common_names: List[str]  # 영어 일반명들
    korean_name: str  # 한글 이름
    category: str  # 동물, 식물, 곤충, 해양생물
    countries: List[str]  # 서식 국가 코드


# 학명 -> 영어/한글 일반명 매핑
SPECIES_NAMES_DB = {
    # === 동물 - 대형 포유류 ===
    "Panthera tigris": ("Tiger", "호랑이"),
    "Panthera tigris altaica": ("Siberian Tiger", "시베리아 호랑이"),
    "Panthera tigris amoyensis": ("South China Tiger", "화남호랑이"),
    "Panthera tigris sumatrae": ("Sumatran Tiger", "수마트라 호랑이"),
    "Panthera tigris corbetti": ("Indochinese Tiger", "인도차이나 호랑이"),
    "Panthera tigris jacksoni": ("Malayan Tiger", "말레이 호랑이"),
    "Panthera leo": ("Lion", "사자"),
    "Panthera leo persica": ("Asiatic Lion", "아시아 사자"),
    "Panthera onca": ("Jaguar", "재규어"),
    "Panthera pardus": ("Leopard", "표범"),
    "Panthera pardus tulliana": ("Anatolian Leopard", "아나톨리아 표범"),
    "Panthera uncia": ("Snow Leopard", "눈표범"),
    "Acinonyx jubatus": ("Cheetah", "치타"),
    "Lynx lynx": ("Eurasian Lynx", "유라시아 스라소니"),
    "Lynx pardinus": ("Iberian Lynx", "이베리아 스라소니"),
    "Lynx canadensis": ("Canada Lynx", "캐나다 스라소니"),
    "Puma concolor": ("Puma", "퓨마"),
    "Prionailurus bengalensis": ("Leopard Cat", "삵"),

    # === 동물 - 곰 ===
    "Ursus arctos": ("Brown Bear", "불곰"),
    "Ursus arctos horribilis": ("Grizzly Bear", "그리즐리"),
    "Ursus arctos marsicanus": ("Marsican Brown Bear", "마르시카 불곰"),
    "Ursus maritimus": ("Polar Bear", "북극곰"),
    "Ursus thibetanus": ("Asiatic Black Bear", "반달가슴곰"),
    "Helarctos malayanus": ("Sun Bear", "말레이곰"),
    "Tremarctos ornatus": ("Spectacled Bear", "안경곰"),

    # === 동물 - 유인원/원숭이 ===
    "Ailuropoda melanoleuca": ("Giant Panda", "판다"),
    "Gorilla gorilla": ("Western Gorilla", "서부고릴라"),
    "Pan troglodytes": ("Chimpanzee", "침팬지"),
    "Pongo abelii": ("Sumatran Orangutan", "수마트라 오랑우탄"),
    "Pongo pygmaeus": ("Bornean Orangutan", "보르네오 오랑우탄"),
    "Rhinopithecus roxellana": ("Golden Snub-nosed Monkey", "황금들창코원숭이"),
    "Nasalis larvatus": ("Proboscis Monkey", "코주부원숭이"),
    "Nomascus gabriellae": ("Yellow-cheeked Gibbon", "노란뺨긴팔원숭이"),
    "Hylobates moloch": ("Silvery Gibbon", "은빛긴팔원숭이"),
    "Tarsius tarsier": ("Spectral Tarsier", "안경원숭이"),
    "Leontopithecus rosalia": ("Golden Lion Tamarin", "금빛사자타마린"),
    "Saguinus oedipus": ("Cotton-top Tamarin", "흰머리타마린"),
    "Alouatta palliata": ("Mantled Howler", "맨틀흡혈원숭이"),
    "Ateles chamek": ("Black-faced Spider Monkey", "검은얼굴거미원숭이"),

    # === 동물 - 코끼리/코뿔소 ===
    "Elephas maximus": ("Asian Elephant", "아시아코끼리"),
    "Elephas maximus sumatranus": ("Sumatran Elephant", "수마트라코끼리"),
    "Loxodonta africana": ("African Elephant", "아프리카코끼리"),
    "Rhinoceros unicornis": ("Indian Rhinoceros", "인도코뿔소"),
    "Rhinoceros sondaicus": ("Javan Rhinoceros", "자바코뿔소"),
    "Dicerorhinus sumatrensis": ("Sumatran Rhinoceros", "수마트라코뿔소"),
    "Diceros bicornis": ("Black Rhinoceros", "검은코뿔소"),
    "Ceratotherium simum": ("White Rhinoceros", "흰코뿔소"),

    # === 동물 - 늑대/여우 ===
    "Canis lupus": ("Gray Wolf", "회색늑대"),
    "Cuon alpinus": ("Dhole", "승냥이"),
    "Chrysocyon brachyurus": ("Maned Wolf", "갈기늑대"),
    "Lycaon pictus": ("African Wild Dog", "아프리카들개"),
    "Speothos venaticus": ("Bush Dog", "덤불개"),
    "Vulpes vulpes": ("Red Fox", "붉은여우"),

    # === 동물 - 기타 포유류 ===
    "Gulo gulo": ("Wolverine", "울버린"),
    "Lutra lutra": ("Eurasian Otter", "수달"),
    "Pteronura brasiliensis": ("Giant Otter", "거대수달"),
    "Enhydra lutris": ("Sea Otter", "해달"),
    "Mustela nigripes": ("Black-footed Ferret", "검은발족제비"),
    "Mustela lutreola": ("European Mink", "유럽밍크"),
    "Mustela putorius": ("European Polecat", "유럽족제비"),
    "Desmana moschata": ("Russian Desman", "러시아데스만"),
    "Castor fiber": ("Eurasian Beaver", "유라시아비버"),
    "Sciurus vulgaris": ("Eurasian Red Squirrel", "유라시아청설모"),
    "Chinchilla chinchilla": ("Chinchilla", "친칠라"),
    "Erinaceus europaeus": ("European Hedgehog", "유럽고슴도치"),

    # === 동물 - 유대류 ===
    "Phascolarctos cinereus": ("Koala", "코알라"),
    "Macropus rufus": ("Red Kangaroo", "붉은캥거루"),
    "Vombatus ursinus": ("Common Wombat", "웜뱃"),
    "Sarcophilus harrisii": ("Tasmanian Devil", "태즈메이니아데빌"),
    "Dasyurus viverrinus": ("Eastern Quoll", "동부쿼올"),
    "Lasiorhinus krefftii": ("Northern Hairy-nosed Wombat", "털코웜뱃"),
    "Bettongia penicillata": ("Woylie", "브러시테일베통"),
    "Petrogale xanthopus": ("Yellow-footed Rock-wallaby", "노란발바위왈라비"),

    # === 동물 - 단공류 ===
    "Ornithorhynchus anatinus": ("Platypus", "오리너구리"),
    "Tachyglossus aculeatus": ("Short-beaked Echidna", "가시두더지"),

    # === 동물 - 사슴/영양 ===
    "Cervus nippon": ("Sika Deer", "꽃사슴"),
    "Cervus albirostris": ("White-lipped Deer", "백순록"),
    "Cervus duvaucelii": ("Barasingha", "바라싱하사슴"),
    "Axis porcinus": ("Hog Deer", "돼지사슴"),
    "Elaphurus davidianus": ("Pere David's Deer", "사불상"),
    "Hippocamelus bisulcus": ("Huemul", "우에물사슴"),
    "Blastocerus dichotomus": ("Marsh Deer", "습지사슴"),
    "Rangifer tarandus": ("Reindeer", "순록"),
    "Alces alces": ("Moose", "무스"),
    "Giraffa camelopardalis": ("Giraffe", "기린"),
    "Gazella dorcas": ("Dorcas Gazelle", "도르카스가젤"),
    "Bos gaurus": ("Gaur", "가우르"),
    "Bison bison": ("American Bison", "아메리카들소"),
    "Bison bonasus": ("European Bison", "유럽들소"),
    "Budorcas taxicolor": ("Takin", "타킨"),
    "Antilocapra americana": ("Pronghorn", "프롱혼"),
    "Equus zebra": ("Mountain Zebra", "산얼룩말"),
    "Equus grevyi": ("Grevy's Zebra", "그레비얼룩말"),
    "Saiga tatarica": ("Saiga Antelope", "사이가영양"),
    "Oryx dammah": ("Scimitar-horned Oryx", "초승달뿔오릭스"),
    "Addax nasomaculatus": ("Addax", "아닥스"),
    "Damaliscus pygargus": ("Bontebok", "본테복"),
    "Vicugna vicugna": ("Vicuña", "비쿠냐"),
    "Capra aegagrus": ("Wild Goat", "야생염소"),
    "Ovis nivicola": ("Snow Sheep", "눈양"),
    "Rupicapra pyrenaica ornata": ("Apennine Chamois", "아펜니네샤무아"),

    # === 동물 - 기타 대형 포유류 ===
    "Hippopotamus amphibius": ("Hippopotamus", "하마"),
    "Tapirus terrestris": ("South American Tapir", "남미맥"),
    "Tapirus bairdii": ("Baird's Tapir", "베어드맥"),
    "Manis javanica": ("Sunda Pangolin", "순다천산갑"),
    "Moschus moschiferus": ("Siberian Musk Deer", "시베리아사향노루"),
    "Naemorhedus caudatus": ("Long-tailed Goral", "산양"),
    "Capricornis crispus": ("Japanese Serow", "일본산양"),
    "Macaca fuscata": ("Japanese Macaque", "일본원숭이"),
    "Myrmecophaga tridactyla": ("Giant Anteater", "큰개미핥기"),
    "Priodontes maximus": ("Giant Armadillo", "큰아르마딜로"),
    "Bradypus variegatus": ("Brown-throated Sloth", "갈색목나무늘보"),
    "Pseudoryx nghetinhensis": ("Saola", "사올라"),
    "Babyrousa babyrussa": ("Babirusa", "바비루사"),

    # === 조류 ===
    "Grus japonensis": ("Red-crowned Crane", "두루미"),
    "Grus americana": ("Whooping Crane", "아메리카흰두루미"),
    "Grus leucogeranus": ("Siberian Crane", "시베리아흰두루미"),
    "Grus antigone": ("Sarus Crane", "사루스두루미"),
    "Grus grus": ("Common Crane", "검은두루미"),
    "Nipponia nippon": ("Crested Ibis", "따오기"),
    "Ciconia boyciana": ("Oriental Stork", "황새"),
    "Haliaeetus leucocephalus": ("Bald Eagle", "흰머리수리"),
    "Haliaeetus pelagicus": ("Steller's Sea Eagle", "참수리"),
    "Haliaeetus albicilla": ("White-tailed Eagle", "흰꼬리수리"),
    "Aquila chrysaetos": ("Golden Eagle", "검독수리"),
    "Aquila adalberti": ("Spanish Imperial Eagle", "스페인제국독수리"),
    "Falco peregrinus": ("Peregrine Falcon", "매"),
    "Gypaetus barbatus": ("Bearded Vulture", "수염수리"),
    "Gymnogyps californianus": ("California Condor", "캘리포니아콘도르"),
    "Harpia harpyja": ("Harpy Eagle", "하피수리"),
    "Bubo bubo": ("Eurasian Eagle-Owl", "수리부엉이"),
    "Strigops habroptilus": ("Kakapo", "카카포"),
    "Apteryx haastii": ("Great Spotted Kiwi", "큰점박이키위"),
    "Casuarius casuarius": ("Southern Cassowary", "화식조"),
    "Aptenodytes forsteri": ("Emperor Penguin", "황제펭귄"),
    "Pygoscelis adeliae": ("Adélie Penguin", "아델리펭귄"),
    "Megadyptes antipodes": ("Yellow-eyed Penguin", "노란눈펭귄"),
    "Pezoporus wallicus": ("Ground Parrot", "땅앵무"),
    "Cacatua sulphurea": ("Yellow-crested Cockatoo", "노란볏앵무"),
    "Ara ararauna": ("Blue-and-yellow Macaw", "청황금강앵무"),
    "Ara militaris": ("Military Macaw", "군용앵무"),
    "Buceros bicornis": ("Great Hornbill", "큰코뿔새"),

    # === 파충류 ===
    "Crocodylus porosus": ("Saltwater Crocodile", "바다악어"),
    "Crocodylus siamensis": ("Siamese Crocodile", "시암악어"),
    "Crocodylus acutus": ("American Crocodile", "아메리카악어"),
    "Crocodylus niloticus": ("Nile Crocodile", "나일악어"),
    "Crocodylus mindorensis": ("Philippine Crocodile", "필리핀악어"),
    "Crocodylus rhombifer": ("Cuban Crocodile", "쿠바악어"),
    "Crocodylus moreletii": ("Morelet's Crocodile", "모렐레악어"),
    "Crocodylus palustris": ("Mugger Crocodile", "인도악어"),
    "Alligator mississippiensis": ("American Alligator", "아메리카앨리게이터"),
    "Alligator sinensis": ("Chinese Alligator", "중국악어"),
    "Gavialis gangeticus": ("Gharial", "가리알"),
    "Tomistoma schlegelii": ("False Gharial", "거짓가리알"),
    "Varanus komodoensis": ("Komodo Dragon", "코모도왕도마뱀"),
    "Varanus salvator": ("Asian Water Monitor", "물왕도마뱀"),
    "Varanus griseus": ("Desert Monitor", "사막왕도마뱀"),
    "Heloderma suspectum": ("Gila Monster", "힐라괴물도마뱀"),
    "Heloderma horridum": ("Beaded Lizard", "구슬도마뱀"),
    "Iguana iguana": ("Green Iguana", "그린이구아나"),
    "Cyclura cornuta": ("Rhinoceros Iguana", "코뿔소이구아나"),
    "Brachylophus fasciatus": ("Fiji Banded Iguana", "피지줄무늬이구아나"),
    "Sphenodon punctatus": ("Tuatara", "투아타라"),
    "Testudo hermanni": ("Hermann's Tortoise", "헤르만육지거북"),
    "Gopherus flavomarginatus": ("Bolson Tortoise", "볼슨거북"),
    "Geochelone elegans": ("Indian Star Tortoise", "인도별거북"),
    "Geochelone platynota": ("Burmese Star Tortoise", "버마별거북"),
    "Astrochelys radiata": ("Radiated Tortoise", "방사거북"),
    "Astrochelys yniphora": ("Ploughshare Tortoise", "쟁기거북"),
    "Aldabrachelys gigantea": ("Aldabra Giant Tortoise", "알다브라자이언트거북"),
    "Chelonoidis niger": ("Galápagos Tortoise", "갈라파고스거북"),
    "Python reticulatus": ("Reticulated Python", "그물무늬비단뱀"),
    "Python molurus": ("Indian Python", "인도비단뱀"),
    "Python bivittatus": ("Burmese Python", "버마비단뱀"),
    "Boa constrictor": ("Boa Constrictor", "보아뱀"),
    "Eunectes murinus": ("Green Anaconda", "그린아나콘다"),
    "Ophiophagus hannah": ("King Cobra", "킹코브라"),
    "Naja naja": ("Indian Cobra", "인도코브라"),
    "Bungarus caeruleus": ("Common Krait", "크레이트뱀"),
    "Oxyuranus microlepidotus": ("Inland Taipan", "내륙타이판"),
    "Crotalus adamanteus": ("Eastern Diamondback Rattlesnake", "동부다이아몬드백방울뱀"),
    "Varanus giganteus": ("Perentie", "페렌티왕도마뱀"),
    "Pseudechis australis": ("Mulga Snake", "뮬가뱀"),
    "Python natalensis": ("Southern African Python", "남아프리카비단뱀"),
    "Gopherus agassizii": ("Desert Tortoise", "사막거북"),
    "Leiopelma hochstetteri": ("Hochstetter's Frog", "호크스테터개구리"),

    # === 양서류 ===
    "Ambystoma mexicanum": ("Axolotl", "아홀로틀"),
    "Bombina bombina": ("Fire-bellied Toad", "배붉은두꺼비"),
    "Bombina orientalis": ("Oriental Fire-bellied Toad", "무당개구리"),
    "Salamandra salamandra": ("Fire Salamander", "불도롱뇽"),
    "Andrias japonicus": ("Japanese Giant Salamander", "일본장수도롱뇽"),
    "Andrias davidianus": ("Chinese Giant Salamander", "중국장수도롱뇽"),
    "Cryptobranchus alleganiensis": ("Hellbender", "헬벤더"),
    "Rana temporaria": ("Common Frog", "유럽개구리"),
    "Rana dybowskii": ("Dybowski's Frog", "북방산개구리"),
    "Hyla arborea": ("European Tree Frog", "유럽청개구리"),
    "Hyla japonica": ("Japanese Tree Frog", "청개구리"),
    "Dendrobates tinctorius": ("Dyeing Poison Frog", "염색화살개구리"),
    "Dendrobates auratus": ("Green and Black Poison Frog", "청록화살개구리"),
    "Phyllobates terribilis": ("Golden Poison Frog", "황금화살개구리"),
    "Oophaga pumilio": ("Strawberry Poison Frog", "딸기화살개구리"),
    "Bufo bufo": ("Common Toad", "유럽두꺼비"),
    "Bufo gargarizans": ("Asiatic Toad", "두꺼비"),
    "Rhinella marina": ("Cane Toad", "사탕수수두꺼비"),
    "Pipa pipa": ("Surinam Toad", "수리남비파두꺼비"),
    "Xenopus laevis": ("African Clawed Frog", "아프리카발톱개구리"),
    "Rhacophorus reinwardtii": ("Reinwardt's Flying Frog", "날개청개구리"),
    "Rhacophorus nigropalmatus": ("Wallace's Flying Frog", "월리스날개청개구리"),
    "Neurergus kaiseri": ("Luristan Newt", "루리스탄영원"),
    "Tylototriton verrucosus": ("Crocodile Newt", "악어영원"),
    "Cynops pyrrhogaster": ("Japanese Fire Belly Newt", "일본배불뚝영원"),

    # === 어류 ===
    "Latimeria chalumnae": ("Coelacanth", "실러캔스"),
    "Acipenser sturio": ("European Sturgeon", "유럽철갑상어"),
    "Acipenser baerii": ("Siberian Sturgeon", "시베리아철갑상어"),
    "Acipenser sinensis": ("Chinese Sturgeon", "중국철갑상어"),
    "Acipenser oxyrinchus": ("Atlantic Sturgeon", "대서양철갑상어"),
    "Huso huso": ("Beluga Sturgeon", "벨루가철갑상어"),
    "Polyodon spathula": ("Paddlefish", "패들피시"),
    "Pristis pristis": ("Largetooth Sawfish", "큰이톱상어"),
    "Arapaima gigas": ("Arapaima", "아라파이마"),
    "Osteoglossum bicirrhosum": ("Silver Arowana", "은룡"),
    "Scleropages formosus": ("Asian Arowana", "아시아아로와나"),
    "Pangasianodon gigas": ("Mekong Giant Catfish", "메콩자이언트메기"),
    "Silurus glanis": ("Wels Catfish", "웰스메기"),

    # === 해양 포유류 ===
    "Balaenoptera musculus": ("Blue Whale", "대왕고래"),
    "Megaptera novaeangliae": ("Humpback Whale", "혹등고래"),
    "Balaena mysticetus": ("Bowhead Whale", "북극고래"),
    "Eubalaena australis": ("Southern Right Whale", "남방참고래"),
    "Orcinus orca": ("Orca", "범고래"),
    "Tursiops truncatus": ("Bottlenose Dolphin", "큰돌고래"),
    "Delphinus delphis": ("Common Dolphin", "참돌고래"),
    "Sotalia fluviatilis": ("Tucuxi", "투쿠시"),
    "Inia geoffrensis": ("Amazon River Dolphin", "아마존강돌고래"),
    "Lipotes vexillifer": ("Baiji", "바이지"),
    "Neophocaena asiaeorientalis": ("Finless Porpoise", "상괭이"),
    "Sousa chinensis": ("Indo-Pacific Humpback Dolphin", "인도태평양혹등돌고래"),
    "Platanista gangetica": ("Ganges River Dolphin", "갠지스강돌고래"),
    "Phocoena phocoena": ("Harbour Porpoise", "쇠돌고래"),
    "Trichechus manatus": ("West Indian Manatee", "서인도매너티"),
    "Dugong dugon": ("Dugong", "듀공"),
    "Monachus monachus": ("Mediterranean Monk Seal", "지중해몽크물범"),
    "Monachus schauinslandi": ("Hawaiian Monk Seal", "하와이몽크물범"),
    "Halichoerus grypus": ("Grey Seal", "회색물범"),
    "Phoca vitulina": ("Harbour Seal", "항구물범"),
    "Phoca largha": ("Spotted Seal", "점박이물범"),
    "Mirounga leonina": ("Southern Elephant Seal", "남방코끼리물범"),
    "Hydrurga leptonyx": ("Leopard Seal", "표범물범"),
    "Odobenus rosmarus": ("Walrus", "바다코끼리"),
    "Eumetopias jubatus": ("Steller Sea Lion", "스텔라바다사자"),
    "Otaria flavescens": ("South American Sea Lion", "남미바다사자"),

    # === 해양 생물 - 거북/상어 ===
    "Chelonia mydas": ("Green Sea Turtle", "푸른바다거북"),
    "Caretta caretta": ("Loggerhead Sea Turtle", "붉은바다거북"),
    "Dermochelys coriacea": ("Leatherback Sea Turtle", "장수거북"),
    "Eretmochelys imbricata": ("Hawksbill Sea Turtle", "대모거북"),
    "Podocnemis expansa": ("Giant South American Turtle", "남미거북"),
    "Carcharodon carcharias": ("Great White Shark", "백상아리"),
    "Rhincodon typus": ("Whale Shark", "고래상어"),
    "Carcharias taurus": ("Sand Tiger Shark", "모래호랑이상어"),
    "Manta birostris": ("Giant Oceanic Manta Ray", "쥐가오리"),
    "Cheilinus undulatus": ("Humphead Wrasse", "나폴레옹피시"),
    "Hippocampus erectus": ("Lined Seahorse", "줄해마"),
    "Hippocampus bargibanti": ("Pygmy Seahorse", "피그미해마"),
    "Epinephelus itajara": ("Atlantic Goliath Grouper", "대서양골리앗그루퍼"),
    "Epinephelus lanceolatus": ("Giant Grouper", "대왕바리"),
    "Salmo salar": ("Atlantic Salmon", "대서양연어"),

    # === 식물 ===
    "Ginkgo biloba": ("Ginkgo", "은행나무"),
    "Metasequoia glyptostroboides": ("Dawn Redwood", "메타세쿼이아"),
    "Sequoia sempervirens": ("Coast Redwood", "해안삼나무"),
    "Sequoiadendron giganteum": ("Giant Sequoia", "자이언트세쿼이아"),
    "Wollemia nobilis": ("Wollemi Pine", "울레미소나무"),
    "Araucaria araucana": ("Monkey Puzzle Tree", "원숭이퍼즐나무"),
    "Araucaria cunninghamii": ("Hoop Pine", "후프소나무"),
    "Fitzroya cupressoides": ("Patagonian Cypress", "파타고니아편백"),
    "Agathis australis": ("Kauri", "카우리"),
    "Pinus koraiensis": ("Korean Pine", "잣나무"),
    "Pinus sibirica": ("Siberian Pine", "시베리아잣나무"),
    "Pinus sylvestris": ("Scots Pine", "구주소나무"),
    "Pinus pinea": ("Stone Pine", "이탈리아잣나무"),
    "Pinus longaeva": ("Great Basin Bristlecone Pine", "브리슬콘소나무"),
    "Pinus halepensis": ("Aleppo Pine", "알레포소나무"),
    "Abies koreana": ("Korean Fir", "구상나무"),
    "Cedrus libani": ("Cedar of Lebanon", "레바논삼나무"),
    "Larix sibirica": ("Siberian Larch", "시베리아낙엽송"),
    "Cryptomeria japonica": ("Japanese Cedar", "삼나무"),
    "Taxus baccata": ("European Yew", "유럽주목"),
    "Taxus cuspidata": ("Japanese Yew", "주목"),
    "Taxodium distichum": ("Bald Cypress", "낙우송"),
    "Taxodium mucronatum": ("Montezuma Cypress", "몬테수마삼나무"),
    "Tsuga heterophylla": ("Western Hemlock", "서부헴록"),
    "Thuja plicata": ("Western Red Cedar", "서부삼나무"),
    "Cathaya argyrophylla": ("Cathaya", "카타야"),
    "Cycas revoluta": ("Sago Palm", "소철"),
    "Cycas beddomei": ("Beddome's Cycad", "베돔소철"),
    "Encephalartos woodii": ("Wood's Cycad", "우드소철"),

    # === 식물 - 활엽수/꽃 ===
    "Quercus robur": ("English Oak", "유럽참나무"),
    "Quercus alba": ("White Oak", "흰참나무"),
    "Quercus ilex": ("Holm Oak", "홀름참나무"),
    "Fagus sylvatica": ("European Beech", "유럽너도밤나무"),
    "Acer saccharum": ("Sugar Maple", "설탕단풍"),
    "Betula papyrifera": ("Paper Birch", "종이자작나무"),
    "Betula pubescens": ("Downy Birch", "솜털자작나무"),
    "Betula ermanii": ("Erman's Birch", "에르만자작나무"),
    "Castanea sativa": ("Sweet Chestnut", "유럽밤나무"),
    "Magnolia sieboldii": ("Siebold's Magnolia", "함박꽃나무"),
    "Prunus speciosa": ("Oshima Cherry", "왕벚나무"),
    "Prunus africana": ("African Cherry", "아프리카체리"),
    "Ficus macrophylla": ("Moreton Bay Fig", "모레턴베이무화과"),
    "Sorbus domestica": ("Service Tree", "마가목"),
    "Ilex aquifolium": ("European Holly", "유럽호랑가시"),
    "Olea europaea": ("Olive", "올리브"),
    "Liquidambar orientalis": ("Oriental Sweetgum", "동양풍나무"),
    "Davidia involucrata": ("Dove Tree", "손수건나무"),
    "Eucalyptus regnans": ("Mountain Ash", "산재나무"),
    "Acacia pycnantha": ("Golden Wattle", "금빛아카시아"),
    "Acacia tortilis": ("Umbrella Thorn Acacia", "우산가시아카시아"),
    "Acacia nilotica": ("Gum Arabic Tree", "아라비아고무나무"),
    "Adansonia digitata": ("Baobab", "바오밥나무"),
    "Banksia serrata": ("Old Man Banksia", "노인뱅크시아"),
    "Xanthorrhoea preissii": ("Grass Tree", "풀나무"),
    "Metrosideros excelsa": ("Pohutukawa", "포후투카와"),
    "Protea cynaroides": ("King Protea", "왕프로테아"),
    "Aloe dichotoma": ("Quiver Tree", "화살통나무"),
    "Welwitschia mirabilis": ("Welwitschia", "웰위치아"),
    "Prosopis alba": ("White Carob", "흰캐롭"),
    "Polylepis racemosa": ("Queñua", "케누아"),
    "Ceiba pentandra": ("Kapok", "카폭나무"),
    "Ceroxylon quindiuense": ("Quindio Wax Palm", "킨디오왁스야자"),

    # === 식물 - 열대/특수 ===
    "Rafflesia arnoldii": ("Rafflesia", "라플레시아"),
    "Amorphophallus titanum": ("Titan Arum", "타이탄아룸"),
    "Victoria amazonica": ("Amazon Water Lily", "빅토리아수련"),
    "Nepenthes rajah": ("Rajah Pitcher Plant", "라자벌레잡이풀"),
    "Nepenthes khasiana": ("Pitcher Plant", "벌레잡이풀"),
    "Bertholletia excelsa": ("Brazil Nut", "브라질너트"),
    "Hevea brasiliensis": ("Rubber Tree", "고무나무"),
    "Theobroma cacao": ("Cacao Tree", "카카오나무"),
    "Cinchona pubescens": ("Quinine Tree", "키니네나무"),
    "Cinchona officinalis": ("Cinchona", "신코나"),
    "Swietenia macrophylla": ("Mahogany", "마호가니"),
    "Caesalpinia echinata": ("Brazilwood", "브라질우드"),
    "Euterpe oleracea": ("Açaí Palm", "아사이야자"),
    "Phoenix dactylifera": ("Date Palm", "대추야자"),
    "Aquilaria malaccensis": ("Agarwood", "침향"),
    "Aquilaria crassna": ("Agarwood", "침향"),
    "Santalum album": ("Sandalwood", "백단향"),
    "Pterocarpus santalinus": ("Red Sanders", "자단"),
    "Dalbergia cochinchinensis": ("Thailand Rosewood", "태국로즈우드"),
    "Hopea odorata": ("Hopea", "호페아"),
    "Shorea leprosula": ("Light Red Meranti", "메란티"),
    "Dipterocarpus alatus": ("Yang", "양나무"),
    "Dipterocarpus grandiflorus": ("Apitong", "아피통"),
    "Fokienia hodginsii": ("Fokienia", "포키니아"),
    "Khaya ivorensis": ("African Mahogany", "아프리카마호가니"),
    "Triplochiton scleroxylon": ("Obeche", "오베체"),
    "Agave tequilana": ("Blue Agave", "블루아가베"),
    "Dahlia imperialis": ("Tree Dahlia", "나무달리아"),
    "Paeonia suffruticosa": ("Tree Peony", "모란"),
    "Rhododendron niveum": ("Rhododendron", "진달래"),
    "Espeletia grandiflora": ("Frailejon", "프라일레혼"),
    "Hoodia gordonii": ("Hoodia", "후디아"),
    "Rhodiola rosea": ("Golden Root", "황금뿌리"),
    "Panax ginseng": ("Korean Ginseng", "인삼"),

    # === 곤충 ===
    "Dynastes hercules": ("Hercules Beetle", "헤라클레스장수풍뎅이"),
    "Dynastes tityus": ("Eastern Hercules Beetle", "동부헤라클레스장수풍뎅이"),
    "Dynastes hyllus": ("Hyllus Beetle", "힐루스장수풍뎅이"),
    "Dynastes neptunus": ("Neptune Beetle", "넵튠장수풍뎅이"),
    "Megasoma elephas": ("Elephant Beetle", "코끼리장수풍뎅이"),
    "Titanus giganteus": ("Titan Beetle", "타이탄딱정벌레"),
    "Chalcosoma atlas": ("Atlas Beetle", "아틀라스장수풍뎅이"),
    "Lucanus cervus": ("European Stag Beetle", "유럽사슴벌레"),
    "Lucanus elaphus": ("Giant Stag Beetle", "거대사슴벌레"),
    "Lucanus maculifemoratus": ("Miyama Stag Beetle", "미야마사슴벌레"),
    "Phalacrognathus muelleri": ("Rainbow Stag Beetle", "무지개사슴벌레"),
    "Lamprima aurata": ("Golden Stag Beetle", "황금사슴벌레"),
    "Chiasognathus grantii": ("Darwin's Stag Beetle", "다윈사슴벌레"),
    "Goliathus goliatus": ("Goliath Beetle", "골리앗딱정벌레"),
    "Mecynorrhina torquata": ("Giant African Flower Beetle", "아프리카꽃풍뎅이"),
    "Cerambyx cerdo": ("Great Capricorn Beetle", "하늘소"),
    "Callipogon relictus": ("Callipogon", "장수하늘소"),
    "Rosalia alpina": ("Rosalia Longicorn", "로잘리아하늘소"),
    "Rosalia coelestis": ("Blue Rosalia", "푸른로잘리아하늘소"),
    "Rosalia batesi": ("Bates's Rosalia", "베이츠로잘리아"),
    "Euryscaphus wheeleri": ("Wheeler's Beetle", "휠러딱정벌레"),
    "Carabus smaragdinus": ("Emerald Ground Beetle", "에메랄드딱정벌레"),
    "Scarabaeus sacer": ("Sacred Scarab", "신성한풍뎅이"),
    "Nicrophorus americanus": ("American Burying Beetle", "아메리카매장벌레"),
    "Morpho menelaus": ("Blue Morpho", "블루모르포나비"),
    "Morpho rhetenor": ("Rhetenor Morpho", "레테노르모르포나비"),
    "Morpho catenarius": ("Chain Morpho", "체인모르포나비"),
    "Morpho polyphemus": ("White Morpho", "흰모르포나비"),
    "Morpho cypris": ("Cypris Morpho", "사이프리스모르포나비"),
    "Ornithoptera alexandrae": ("Queen Alexandra's Birdwing", "알렉산드라여왕새날개나비"),
    "Ornithoptera croesus": ("Wallace's Golden Birdwing", "월리스황금새날개나비"),
    "Teinopalpus imperialis": ("Kaiser-i-Hind", "카이저힌드나비"),
    "Troides helena": ("Common Birdwing", "일반새날개나비"),
    "Troides minos": ("Southern Birdwing", "남부새날개나비"),
    "Troides aeacus": ("Golden Birdwing", "황금새날개나비"),
    "Trogonoptera brookiana": ("Rajah Brooke's Birdwing", "브룩라자나비"),
    "Papilio ulysses": ("Blue Mountain Swallowtail", "블루마운틴호랑나비"),
    "Papilio blumei": ("Peacock Swallowtail", "공작호랑나비"),
    "Papilio buddha": ("Malabar Banded Swallowtail", "말라바르호랑나비"),
    "Papilio dardanus": ("African Swallowtail", "아프리카호랑나비"),
    "Sasakia charonda": ("Japanese Emperor", "오색나비"),
    "Bhutanitis lidderdalii": ("Bhutan Glory", "부탄영광나비"),
    "Charaxes jasius": ("Two-tailed Pasha", "두꼬리파샤나비"),
    "Charaxes brutus": ("White-barred Emperor", "흰줄황제나비"),
    "Elymnias caudata": ("Tailed Palmfly", "꼬리야자나비"),
    "Danaus plexippus": ("Monarch Butterfly", "제왕나비"),
    "Parnassius apollo": ("Apollo Butterfly", "아폴로나비"),
    "Bombus affinis": ("Rusty Patched Bumblebee", "녹슨점박이호박벌"),
    "Bombus occidentalis": ("Western Bumblebee", "서부호박벌"),
    "Bombus distinguendus": ("Great Yellow Bumblebee", "큰노랑호박벌"),
    "Deinacrida heteracantha": ("Wetapunga", "웨타풍가"),
}


def build_search_index() -> Tuple[Dict[str, List[str]], Dict[str, Dict]]:
    """
    검색 인덱스를 구축합니다.

    Returns:
        (keyword_index, species_data)
        - keyword_index: 키워드 -> 학명 리스트
        - species_data: 학명 -> SpeciesInfo
    """
    from app.services.country_species_map import COUNTRY_SPECIES_MAP

    # 키워드 -> 학명 매핑
    keyword_index: Dict[str, List[str]] = {}

    # 학명 -> 상세 정보
    species_data: Dict[str, Dict] = {}

    # COUNTRY_SPECIES_MAP에서 모든 종 수집
    for country_code, categories in COUNTRY_SPECIES_MAP.items():
        for category, species_list in categories.items():
            for scientific_name in species_list:
                if scientific_name not in species_data:
                    # 종 정보 초기화
                    names = SPECIES_NAMES_DB.get(scientific_name, (scientific_name, scientific_name))
                    common_name, korean_name = names if isinstance(names, tuple) else (names, names)

                    # 해양 포유류는 항상 "해양생물" 카테고리로 분류
                    final_category = "해양생물" if scientific_name in MARINE_MAMMAL_SPECIES else category

                    species_data[scientific_name] = {
                        "scientific_name": scientific_name,
                        "common_name": common_name,
                        "korean_name": korean_name,
                        "category": final_category,
                        "countries": [country_code]
                    }

                    # 키워드 인덱스 구축
                    keywords = set()

                    # 학명의 각 부분 (소문자)
                    for part in scientific_name.lower().split():
                        keywords.add(part)

                    # 영어 일반명 (소문자)
                    for part in common_name.lower().split():
                        keywords.add(part)

                    # 한글 이름
                    keywords.add(korean_name)

                    # 전체 이름도 추가
                    keywords.add(scientific_name.lower())
                    keywords.add(common_name.lower())

                    for kw in keywords:
                        if kw not in keyword_index:
                            keyword_index[kw] = []
                        if scientific_name not in keyword_index[kw]:
                            keyword_index[kw].append(scientific_name)
                else:
                    # 국가 추가
                    if country_code not in species_data[scientific_name]["countries"]:
                        species_data[scientific_name]["countries"].append(country_code)

    return keyword_index, species_data


# 전역 인덱스 (서버 시작 시 로드)
KEYWORD_INDEX: Dict[str, List[str]] = {}
SPECIES_DATA: Dict[str, Dict] = {}


def load_search_index():
    """검색 인덱스를 로드합니다."""
    global KEYWORD_INDEX, SPECIES_DATA
    KEYWORD_INDEX, SPECIES_DATA = build_search_index()


def fuzzy_match_keyword(query: str, threshold: float = 0.6) -> List[str]:
    """
    퍼지 매칭으로 유사한 키워드를 찾습니다.

    Args:
        query: 검색어
        threshold: 유사도 임계값 (0.0 ~ 1.0)

    Returns:
        매칭된 학명 리스트
    """
    query_lower = query.lower()
    matches = set()

    for keyword, species_list in KEYWORD_INDEX.items():
        # 너무 짧은 키워드는 부분 매칭 제외 (3글자 미만)
        if len(keyword) < 3:
            continue

        # 정확한 포함 매칭 (검색어가 키워드에 포함되어야 함)
        # 단, 키워드가 검색어보다 짧은 경우만 역방향 매칭 허용
        if query_lower in keyword:
            matches.update(species_list)
            continue

        # 역방향 매칭: 키워드가 검색어에 포함되려면 최소 4글자 이상
        if len(keyword) >= 4 and keyword in query_lower:
            matches.update(species_list)
            continue

        # 퍼지 매칭
        ratio = difflib.SequenceMatcher(None, query_lower, keyword).ratio()
        if ratio >= threshold:
            matches.update(species_list)

    return list(matches)


def search_species(
    query: str,
    category: Optional[str] = None,
    fuzzy_threshold: float = 0.6
) -> List[Dict]:
    """
    종을 검색합니다.

    Args:
        query: 검색어 (한글/영어/학명)
        category: 카테고리 필터 (선택)
        fuzzy_threshold: 퍼지 매칭 임계값

    Returns:
        검색 결과 리스트 [{scientific_name, common_name, korean_name, category, countries, match_score}, ...]
    """
    if not KEYWORD_INDEX:
        load_search_index()

    query_lower = query.lower()
    # 매칭된 종 + 매칭 점수
    matched_species: Dict[str, int] = {}  # scientific_name -> match_score

    def add_match(sci_name: str, score: int):
        """종을 매칭 목록에 추가 (점수가 높은 것 우선)"""
        if sci_name not in matched_species or matched_species[sci_name] < score:
            matched_species[sci_name] = score

    # 1. 정확한 키워드 매칭 (최고 우선순위: 100점)
    if query_lower in KEYWORD_INDEX:
        for sci_name in KEYWORD_INDEX[query_lower]:
            add_match(sci_name, 100)

    # 2. 한글 검색어 - 한글 이름에서 정확히 포함 (90점)
    for scientific_name, info in SPECIES_DATA.items():
        korean_name = info.get("korean_name", "")
        if query in korean_name:
            add_match(scientific_name, 90)
        elif korean_name and korean_name in query:
            add_match(scientific_name, 85)

    # 3. 키워드 정확 포함 매칭 (80점)
    for keyword, species_list in KEYWORD_INDEX.items():
        if len(keyword) < 3:  # 너무 짧은 키워드 제외
            continue

        if query_lower == keyword:  # 정확 일치
            for sci_name in species_list:
                add_match(sci_name, 100)
        elif query_lower in keyword:  # 검색어가 키워드에 포함
            for sci_name in species_list:
                add_match(sci_name, 75)
        elif len(keyword) >= 4 and keyword in query_lower:  # 키워드가 검색어에 포함 (최소 4글자)
            for sci_name in species_list:
                add_match(sci_name, 70)

    # 4. 퍼지 매칭 (낮은 우선순위: 50점)
    if len(matched_species) < 3:
        for keyword, species_list in KEYWORD_INDEX.items():
            if len(keyword) < 3:
                continue
            ratio = difflib.SequenceMatcher(None, query_lower, keyword).ratio()
            if ratio >= fuzzy_threshold:
                for sci_name in species_list:
                    add_match(sci_name, int(ratio * 50))

    # 결과 수집 및 정렬
    results = []
    for scientific_name, score in matched_species.items():
        info = SPECIES_DATA.get(scientific_name, {})

        # 카테고리 필터
        if category and info.get("category") != category:
            continue

        # 카테고리 우선순위 보너스 (동물 > 식물 > 해양생물 > 곤충)
        category_bonus = {
            "동물": 20,
            "식물": 15,
            "해양생물": 10,
            "곤충": 5
        }.get(info.get("category", "동물"), 0)

        results.append({
            "scientific_name": scientific_name,
            "common_name": info.get("common_name", scientific_name),
            "korean_name": info.get("korean_name", ""),
            "category": info.get("category", "동물"),
            "countries": info.get("countries", []),
            "match_score": score + category_bonus
        })

    # 점수 순으로 정렬 (높은 점수가 먼저)
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results


def get_species_countries(query: str, category: Optional[str] = None) -> Tuple[List[str], str, Optional[str], Optional[str]]:
    """
    종 검색 후 서식 국가 목록을 반환합니다.

    ⚠️ 개선: 정확히 매칭된 종의 국가만 반환 (유사 종 제외)

    Args:
        query: 검색어
        category: 카테고리 필터

    Returns:
        (국가 코드 리스트, 매칭된 종 이름, 카테고리, 매칭된 학명)
    """
    results = search_species(query, category)

    if not results:
        return [], "", None, None

    # 가장 높은 점수의 종 정보만 사용 (유사 종 제외)
    best_match = results[0]
    matched_name = best_match.get("korean_name") or best_match.get("common_name") or best_match.get("scientific_name")
    matched_category = best_match.get("category")
    matched_scientific_name = best_match.get("scientific_name")

    # ⚠️ 핵심 변경: 가장 높은 점수의 종 국가만 반환 (다른 유사 종 제외)
    # 이전: 점수 차이가 30점 이내인 모든 종의 국가를 수집
    # 변경: 최고 매칭 종의 국가만 반환하여 정확도 향상
    all_countries = list(best_match.get("countries", []))

    return all_countries, matched_name, matched_category, matched_scientific_name
