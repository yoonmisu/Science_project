"""
Country-Species Mapping for IUCN Red List
Curated list of representative endangered species by country

종 개수 분포 (5단계 시각화용):
- 그룹 1 (3-5개): 소규모 국가
- 그룹 2 (6-8개): 중소 국가
- 그룹 3 (9-11개): 중간 국가
- 그룹 4 (12-14개): 대형 국가
- 그룹 5 (15-18개): 생물다양성 핫스팟
"""

# ========================================
# 국가별 대표 멸종위기종 학명 리스트
# ========================================

COUNTRY_SPECIES_MAP = {
    # ========================================
    # 그룹 5: 생물다양성 핫스팟 (15-18개)
    # ========================================
    "BR": {  # 브라질 - 아마존 열대우림
        "동물": [
            "Panthera onca",
            "Tapirus terrestris",
            "Ara ararauna",
            "Pteronura brasiliensis",
            "Myrmecophaga tridactyla",
            "Priodontes maximus",
            "Bradypus variegatus",
            "Leontopithecus rosalia",
            "Trichechus manatus",
            "Chelonia mydas",
            "Harpia harpyja",
            "Speothos venaticus",
            "Chrysocyon brachyurus",
            "Blastocerus dichotomus",
            "Ateles chamek",
            "Podocnemis expansa",
            # 파충류
            "Eunectes murinus",  # 그린아나콘다
            "Boa constrictor",  # 보아뱀
            "Crocodylus acutus",  # 아메리카악어
            # 양서류
            "Dendrobates tinctorius",  # 염색화살개구리
            "Phyllobates terribilis",  # 황금화살개구리
            "Pipa pipa",  # 수리남비파두꺼비
            # 어류
            "Arapaima gigas",  # 아라파이마
            "Osteoglossum bicirrhosum",  # 은룡
        ],
        "식물": [
            "Bertholletia excelsa",
            "Hevea brasiliensis",
            "Theobroma cacao",
            "Cinchona pubescens",
            "Victoria amazonica",
            "Swietenia macrophylla",
            "Caesalpinia echinata",
            "Euterpe oleracea",
        ],
        "곤충": [
            "Dynastes hercules",
            "Megasoma elephas",
            "Morpho menelaus",
            "Titanus giganteus",
            "Morpho rhetenor",
            "Dynastes neptunus",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Eretmochelys imbricata",
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
            "Trichechus manatus",
            "Sotalia fluviatilis",
            "Inia geoffrensis",
            "Epinephelus itajara",
        ],
    },

    "ID": {  # 인도네시아 - 열대 생물다양성
        "동물": [
            "Pongo abelii",
            "Pongo pygmaeus",
            "Panthera tigris sumatrae",
            "Rhinoceros sondaicus",
            "Dicerorhinus sumatrensis",
            "Elephas maximus sumatranus",
            "Varanus komodoensis",
            "Manis javanica",
            "Crocodylus porosus",
            "Chelonia mydas",
            "Nasalis larvatus",
            "Tarsius tarsier",
            "Babyrousa babyrussa",
            "Hylobates moloch",
            "Cacatua sulphurea",
            # 파충류
            "Varanus salvator",  # 물왕도마뱀
            "Python reticulatus",  # 그물무늬비단뱀
            "Tomistoma schlegelii",  # 거짓가리알
            # 양서류
            "Rhacophorus nigropalmatus",  # 월리스날개청개구리
            # 어류
            "Scleropages formosus",  # 아시아아로와나
        ],
        "식물": [
            "Rafflesia arnoldii",
            "Amorphophallus titanum",
            "Shorea leprosula",
            "Dipterocarpus grandiflorus",
            "Nepenthes rajah",
            "Hopea odorata",
            "Aquilaria malaccensis",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Troides helena",
            "Chalcosoma atlas",
            "Ornithoptera croesus",
            "Papilio blumei",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Eretmochelys imbricata",
            "Balaenoptera musculus",
            "Dugong dugon",
            "Rhincodon typus",
            "Manta birostris",
            "Cheilinus undulatus",
            "Hippocampus bargibanti",
        ],
    },

    "AU": {  # 호주 - 고유종 다양성
        "동물": [
            "Phascolarctos cinereus",
            "Macropus rufus",
            "Vombatus ursinus",
            "Ornithorhynchus anatinus",
            "Tachyglossus aculeatus",
            "Crocodylus porosus",
            "Chelonia mydas",
            "Carcharodon carcharias",
            "Dugong dugon",
            "Dasyurus viverrinus",
            "Sarcophilus harrisii",
            "Lasiorhinus krefftii",
            "Bettongia penicillata",
            "Petrogale xanthopus",
            "Pezoporus wallicus",
            "Casuarius casuarius",
            # 파충류
            "Varanus giganteus",  # 페렌티왕도마뱀
            "Oxyuranus microlepidotus",  # 내륙타이판
            "Pseudechis australis",  # 뮬가뱀
        ],
        "식물": [
            "Eucalyptus regnans",
            "Acacia pycnantha",
            "Araucaria cunninghamii",
            "Ficus macrophylla",
            "Banksia serrata",
            "Xanthorrhoea preissii",
            "Wollemia nobilis",
        ],
        "곤충": [
            "Ornithoptera alexandrae",
            "Papilio ulysses",
            "Phalacrognathus muelleri",
            "Lamprima aurata",
            "Euryscaphus wheeleri",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Eretmochelys imbricata",
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
            "Carcharodon carcharias",
            "Dugong dugon",
            "Rhincodon typus",
            "Epinephelus lanceolatus",
        ],
    },

    # ========================================
    # 그룹 4: 대형 국가 (12-14개)
    # ========================================
    "US": {  # 미국
        "동물": [
            "Haliaeetus leucocephalus",
            "Ursus arctos horribilis",
            "Lynx canadensis",
            "Puma concolor",
            "Canis lupus",
            "Mustela nigripes",
            "Grus americana",
            "Gymnogyps californianus",
            "Alligator mississippiensis",
            "Bison bison",
            "Antilocapra americana",
            "Falco peregrinus",
            # 파충류
            "Gopherus agassizii",  # 사막거북
            "Heloderma suspectum",  # 힐라괴물도마뱀
            "Crotalus adamanteus",  # 동부다이아몬드백방울뱀
            # 양서류
            "Cryptobranchus alleganiensis",  # 헬벤더
            "Ambystoma mexicanum",  # 아홀로틀 (미국 남부)
            # 어류
            "Polyodon spathula",  # 패들피시
            "Acipenser oxyrinchus",  # 대서양철갑상어
        ],
        "식물": [
            "Sequoia sempervirens",
            "Sequoiadendron giganteum",
            "Pinus longaeva",
            "Quercus alba",
            "Acer saccharum",
            "Taxodium distichum",
        ],
        "곤충": [
            "Dynastes tityus",
            "Lucanus elaphus",
            "Nicrophorus americanus",
            "Danaus plexippus",
            "Bombus affinis",
        ],
        "해양생물": [
            "Caretta caretta",
            "Chelonia mydas",
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
            "Trichechus manatus",
            "Monachus schauinslandi",
            "Enhydra lutris",
            "Hippocampus erectus",
        ],
    },

    "CN": {  # 중국
        "동물": [
            "Ailuropoda melanoleuca",
            "Panthera tigris amoyensis",
            "Panthera uncia",
            "Rhinopithecus roxellana",
            "Ursus thibetanus",
            "Moschus moschiferus",
            "Grus japonensis",
            "Nipponia nippon",
            "Crocodylus siamensis",
            "Elaphurus davidianus",
            "Cervus albirostris",
            "Budorcas taxicolor",
            "Alligator sinensis",
            # 양서류
            "Andrias davidianus",  # 중국장수도롱뇽
            "Bombina orientalis",  # 무당개구리
            "Tylototriton verrucosus",  # 악어영원
            # 어류
            "Acipenser sinensis",  # 중국철갑상어
            "Pangasianodon gigas",  # 메콩자이언트메기
        ],
        "식물": [
            "Ginkgo biloba",
            "Metasequoia glyptostroboides",
            "Cathaya argyrophylla",
            "Davidia involucrata",
            "Paeonia suffruticosa",
            "Cycas revoluta",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Lucanus maculifemoratus",
            "Callipogon relictus",
            "Bhutanitis lidderdalii",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Balaenoptera musculus",
            "Lipotes vexillifer",
            "Neophocaena asiaeorientalis",
            "Sousa chinensis",
        ],
    },

    "IN": {  # 인도
        "동물": [
            "Panthera tigris",
            "Panthera leo persica",
            "Elephas maximus",
            "Rhinoceros unicornis",
            "Panthera pardus",
            "Ursus thibetanus",
            "Bos gaurus",
            "Cuon alpinus",
            "Gavialis gangeticus",
            "Grus antigone",
            "Buceros bicornis",
            "Cervus duvaucelii",
            "Axis porcinus",
            # 파충류
            "Crocodylus palustris",  # 인도악어
            "Python molurus",  # 인도비단뱀
            "Ophiophagus hannah",  # 킹코브라
            "Naja naja",  # 인도코브라
            "Geochelone elegans",  # 인도별거북
        ],
        "식물": [
            "Aquilaria malaccensis",
            "Santalum album",
            "Pterocarpus santalinus",
            "Cycas beddomei",
            "Nepenthes khasiana",
            "Rhododendron niveum",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Troides minos",
            "Papilio buddha",
            "Elymnias caudata",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Eretmochelys imbricata",
            "Balaenoptera musculus",
            "Dugong dugon",
            "Platanista gangetica",
        ],
    },

    "RU": {  # 러시아
        "동물": [
            "Panthera tigris altaica",
            "Ursus maritimus",
            "Panthera uncia",
            "Grus leucogeranus",
            "Haliaeetus pelagicus",
            "Ursus arctos",
            "Mustela lutreola",
            "Balaena mysticetus",
            "Moschus moschiferus",
            "Saiga tatarica",
            "Ovis nivicola",
            "Desmana moschata",
            # 양서류
            "Salamandra salamandra",  # 불도롱뇽
            "Rana temporaria",  # 유럽개구리
            # 어류
            "Acipenser baerii",  # 시베리아철갑상어
            "Huso huso",  # 벨루가철갑상어
            "Silurus glanis",  # 웰스메기
        ],
        "식물": [
            "Pinus sibirica",
            "Larix sibirica",
            "Betula ermanii",
            "Rhodiola rosea",
            "Panax ginseng",
        ],
        "곤충": [
            "Callipogon relictus",
            "Rosalia coelestis",
            "Parnassius apollo",
            "Carabus smaragdinus",
        ],
        "해양생물": [
            "Balaena mysticetus",
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
            "Odobenus rosmarus",
            "Phoca largha",
            "Eumetopias jubatus",
        ],
    },

    "ZA": {  # 남아프리카
        "동물": [
            "Panthera leo",
            "Loxodonta africana",
            "Diceros bicornis",
            "Ceratotherium simum",
            "Panthera pardus",
            "Acinonyx jubatus",
            "Lycaon pictus",
            "Hippopotamus amphibius",
            "Giraffa camelopardalis",
            "Carcharodon carcharias",
            "Equus zebra",
            "Damaliscus pygargus",
            # 파충류
            "Crocodylus niloticus",  # 나일악어
            "Python natalensis",  # 남아프리카비단뱀
            # 양서류
            "Xenopus laevis",  # 아프리카발톱개구리
        ],
        "식물": [
            "Encephalartos woodii",
            "Aloe dichotoma",
            "Protea cynaroides",
            "Welwitschia mirabilis",
            "Hoodia gordonii",
        ],
        "곤충": [
            "Goliathus goliatus",
            "Mecynorrhina torquata",
            "Charaxes jasius",
            "Papilio dardanus",
        ],
        "해양생물": [
            "Carcharodon carcharias",
            "Chelonia mydas",
            "Dermochelys coriacea",
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
            "Carcharias taurus",
        ],
    },

    # ========================================
    # 그룹 3: 중간 국가 (9-11개)
    # ========================================
    "JP": {  # 일본
        "동물": [
            "Grus japonensis",
            "Ursus thibetanus",
            "Lutra lutra",
            "Prionailurus bengalensis",
            "Nipponia nippon",
            "Haliaeetus pelagicus",
            "Falco peregrinus",
            "Cervus nippon",
            "Macaca fuscata",
            "Capricornis crispus",
            # 양서류
            "Andrias japonicus",  # 일본장수도롱뇽
            "Hyla japonica",  # 청개구리
            "Cynops pyrrhogaster",  # 일본배불뚝영원
            "Rana dybowskii",  # 북방산개구리
        ],
        "식물": [
            "Magnolia sieboldii",
            "Pinus koraiensis",
            "Cryptomeria japonica",
            "Prunus speciosa",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Lucanus maculifemoratus",
            "Sasakia charonda",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
        ],
    },

    "KR": {  # 한국
        "동물": [
            "Grus japonensis",
            "Naemorhedus caudatus",
            "Ursus thibetanus",
            "Lutra lutra",
            "Moschus moschiferus",
            "Mustela lutreola",
            "Falco peregrinus",
            "Haliaeetus pelagicus",
            "Ciconia boyciana",
            # 양서류
            "Hyla japonica",  # 청개구리
            "Bombina orientalis",  # 무당개구리
            "Bufo gargarizans",  # 두꺼비
            "Rana dybowskii",  # 북방산개구리
        ],
        "식물": [
            "Magnolia sieboldii",
            "Pinus koraiensis",
            "Taxus cuspidata",
            "Abies koreana",
        ],
        "곤충": [
            "Lucanus maculifemoratus",
            "Callipogon relictus",
            "Rosalia batesi",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Balaenoptera musculus",
            "Neophocaena asiaeorientalis",
        ],
    },

    "MX": {  # 멕시코
        "동물": [
            "Panthera onca",
            "Tapirus bairdii",
            "Trichechus manatus",
            "Alouatta palliata",
            "Ara militaris",
            "Chelonia mydas",
            "Crocodylus acutus",
            "Gopherus flavomarginatus",
            "Ambystoma mexicanum",
            "Antilocapra americana",
        ],
        "식물": [
            "Agave tequilana",
            "Dahlia imperialis",
            "Ceiba pentandra",
            "Taxodium mucronatum",
        ],
        "곤충": [
            "Dynastes hyllus",
            "Danaus plexippus",
            "Morpho polyphemus",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dermochelys coriacea",
            "Rhincodon typus",
            "Trichechus manatus",
            "Vaquita",
        ],
    },

    "CA": {  # 캐나다
        "동물": [
            "Ursus maritimus",
            "Rangifer tarandus",
            "Canis lupus",
            "Ursus arctos",
            "Lynx canadensis",
            "Gulo gulo",
            "Puma concolor",
            "Alces alces",
            "Balaena mysticetus",
            "Haliaeetus leucocephalus",
        ],
        "식물": [
            "Tsuga heterophylla",
            "Thuja plicata",
            "Acer saccharum",
            "Betula papyrifera",
        ],
        "곤충": [
            "Danaus plexippus",
            "Bombus occidentalis",
            "Nicrophorus americanus",
        ],
        "해양생물": [
            "Balaenoptera musculus",
            "Megaptera novaeangliae",
            "Orcinus orca",
            "Enhydra lutris",
        ],
    },

    "DE": {  # 독일
        "동물": [
            "Lynx lynx",
            "Canis lupus",
            "Lutra lutra",
            "Castor fiber",
            "Ursus arctos",
            "Mustela lutreola",
            "Aquila chrysaetos",
            "Haliaeetus albicilla",
            "Grus grus",
            "Bombina bombina",
        ],
        "식물": [
            "Taxus baccata",
            "Quercus robur",
            "Fagus sylvatica",
            "Sorbus domestica",
        ],
        "곤충": [
            "Lucanus cervus",
            "Cerambyx cerdo",
            "Rosalia alpina",
        ],
        "해양생물": [
            "Halichoerus grypus",
            "Phoca vitulina",
            "Phocoena phocoena",
        ],
    },

    "FR": {  # 프랑스
        "동물": [
            "Ursus arctos",
            "Lynx lynx",
            "Canis lupus",
            "Lutra lutra",
            "Vulpes vulpes",
            "Gypaetus barbatus",
            "Aquila chrysaetos",
            "Testudo hermanni",
            "Monachus monachus",
            "Phoca vitulina",
        ],
        "식물": [
            "Taxus baccata",
            "Pinus sylvestris",
            "Quercus robur",
            "Castanea sativa",
        ],
        "곤충": [
            "Lucanus cervus",
            "Cerambyx cerdo",
            "Parnassius apollo",
        ],
        "해양생물": [
            "Caretta caretta",
            "Tursiops truncatus",
            "Delphinus delphis",
        ],
    },

    "GB": {  # 영국
        "동물": [
            "Lutra lutra",
            "Mustela putorius",
            "Sciurus vulgaris",
            "Halichoerus grypus",
            "Erinaceus europaeus",
            "Falco peregrinus",
            "Bubo bubo",
            "Salmo salar",
            "Phocoena phocoena",
        ],
        "식물": [
            "Taxus baccata",
            "Quercus robur",
            "Fagus sylvatica",
            "Ilex aquifolium",
        ],
        "곤충": [
            "Lucanus cervus",
            "Bombus distinguendus",
        ],
        "해양생물": [
            "Halichoerus grypus",
            "Phoca vitulina",
            "Phocoena phocoena",
        ],
    },

    # ========================================
    # 그룹 2: 중소 국가 (6-8개)
    # ========================================
    "KE": {  # 케냐
        "동물": [
            "Loxodonta africana",
            "Panthera leo",
            "Panthera pardus",
            "Diceros bicornis",
            "Acinonyx jubatus",
            "Giraffa camelopardalis",
            "Hippopotamus amphibius",
            "Equus grevyi",
        ],
        "식물": [
            "Acacia tortilis",
            "Adansonia digitata",
            "Prunus africana",
        ],
        "곤충": [
            "Goliathus goliatus",
            "Charaxes brutus",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dugong dugon",
        ],
    },

    "TH": {  # 태국
        "동물": [
            "Panthera tigris corbetti",
            "Elephas maximus",
            "Panthera pardus",
            "Bos gaurus",
            "Cuon alpinus",
            "Prionailurus bengalensis",
            "Crocodylus siamensis",
        ],
        "식물": [
            "Hopea odorata",
            "Dipterocarpus alatus",
            "Aquilaria crassna",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Troides aeacus",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dugong dugon",
        ],
    },

    "VN": {  # 베트남
        "동물": [
            "Panthera tigris",
            "Elephas maximus",
            "Rhinoceros sondaicus",
            "Pseudoryx nghetinhensis",
            "Crocodylus siamensis",
            "Manis javanica",
            "Nomascus gabriellae",
        ],
        "식물": [
            "Aquilaria crassna",
            "Dalbergia cochinchinensis",
            "Fokienia hodginsii",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Troides helena",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dugong dugon",
        ],
    },

    "EG": {  # 이집트
        "동물": [
            "Panthera pardus",
            "Gazella dorcas",
            "Oryx dammah",
            "Addax nasomaculatus",
            "Crocodylus niloticus",
            "Caretta caretta",
        ],
        "식물": [
            "Phoenix dactylifera",
            "Acacia nilotica",
        ],
        "곤충": [
            "Scarabaeus sacer",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dugong dugon",
            "Tursiops truncatus",
        ],
    },

    "AR": {  # 아르헨티나
        "동물": [
            "Panthera onca",
            "Puma concolor",
            "Chrysocyon brachyurus",
            "Myrmecophaga tridactyla",
            "Hippocamelus bisulcus",
            "Chinchilla chinchilla",
            "Eubalaena australis",
        ],
        "식물": [
            "Araucaria araucana",
            "Fitzroya cupressoides",
            "Prosopis alba",
        ],
        "곤충": [
            "Morpho catenarius",
            "Dynastes hercules",
        ],
        "해양생물": [
            "Eubalaena australis",
            "Mirounga leonina",
            "Otaria flavescens",
        ],
    },

    "MY": {  # 말레이시아
        "동물": [
            "Panthera tigris jacksoni",
            "Elephas maximus",
            "Dicerorhinus sumatrensis",
            "Panthera pardus",
            "Helarctos malayanus",
            "Manis javanica",
            "Pongo pygmaeus",
        ],
        "식물": [
            "Rafflesia arnoldii",
            "Nepenthes rajah",
            "Shorea leprosula",
        ],
        "곤충": [
            "Trogonoptera brookiana",
            "Chalcosoma atlas",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dugong dugon",
        ],
    },

    # ========================================
    # 그룹 1: 소규모 국가 (3-5개)
    # ========================================
    "NZ": {  # 뉴질랜드
        "동물": [
            "Apteryx haastii",
            "Strigops habroptilus",
            "Sphenodon punctatus",  # 투아타라 (파충류)
            "Megadyptes antipodes",
            # 양서류
            "Leiopelma hochstetteri",  # 호크스테터개구리
        ],
        "식물": [
            "Agathis australis",
            "Metrosideros excelsa",
        ],
        "곤충": [
            "Deinacrida heteracantha",
        ],
        "해양생물": [
            "Megaptera novaeangliae",
            "Carcharodon carcharias",
        ],
    },

    "NO": {  # 노르웨이
        "동물": [
            "Ursus maritimus",
            "Ursus arctos",
            "Canis lupus",
            "Gulo gulo",
            "Rangifer tarandus",
        ],
        "식물": [
            "Pinus sylvestris",
            "Betula pubescens",
        ],
        "곤충": [
            "Parnassius apollo",
        ],
        "해양생물": [
            "Balaenoptera musculus",
            "Orcinus orca",
        ],
    },

    "SE": {  # 스웨덴
        "동물": [
            "Ursus arctos",
            "Canis lupus",
            "Lynx lynx",
            "Gulo gulo",
            "Alces alces",
        ],
        "식물": [
            "Pinus sylvestris",
            "Quercus robur",
        ],
        "곤충": [
            "Lucanus cervus",
        ],
        "해양생물": [
            "Halichoerus grypus",
        ],
    },

    "IT": {  # 이탈리아
        "동물": [
            "Ursus arctos marsicanus",
            "Canis lupus",
            "Rupicapra pyrenaica ornata",
            "Caretta caretta",
            "Monachus monachus",
        ],
        "식물": [
            "Pinus pinea",
            "Olea europaea",
            "Quercus ilex",
        ],
        "곤충": [
            "Rosalia alpina",
        ],
        "해양생물": [
            "Caretta caretta",
            "Monachus monachus",
        ],
    },

    "ES": {  # 스페인
        "동물": [
            "Lynx pardinus",
            "Ursus arctos",
            "Aquila adalberti",
            "Gypaetus barbatus",
            "Monachus monachus",
        ],
        "식물": [
            "Quercus ilex",
            "Pinus halepensis",
        ],
        "곤충": [
            "Lucanus cervus",
        ],
        "해양생물": [
            "Caretta caretta",
            "Monachus monachus",
        ],
    },

    "PL": {  # 폴란드
        "동물": [
            "Bison bonasus",
            "Canis lupus",
            "Lynx lynx",
            "Castor fiber",
        ],
        "식물": [
            "Taxus baccata",
            "Quercus robur",
        ],
        "곤충": [
            "Lucanus cervus",
        ],
        "해양생물": [
            "Halichoerus grypus",
        ],
    },

    "TR": {  # 터키
        "동물": [
            "Panthera pardus tulliana",
            "Ursus arctos",
            "Canis lupus",
            "Capra aegagrus",
            "Monachus monachus",
        ],
        "식물": [
            "Cedrus libani",
            "Liquidambar orientalis",
        ],
        "곤충": [
            "Lucanus cervus",
        ],
        "해양생물": [
            "Caretta caretta",
            "Monachus monachus",
        ],
    },

    "PE": {  # 페루
        "동물": [
            "Panthera onca",
            "Tremarctos ornatus",
            "Tapirus terrestris",
            "Pteronura brasiliensis",
        ],
        "식물": [
            "Cinchona officinalis",
            "Polylepis racemosa",
        ],
        "곤충": [
            "Dynastes hercules",
        ],
        "해양생물": [
            "Chelonia mydas",
        ],
    },

    "CL": {  # 칠레
        "동물": [
            "Puma concolor",
            "Hippocamelus bisulcus",
            "Vicugna vicugna",
            "Chinchilla chinchilla",
        ],
        "식물": [
            "Araucaria araucana",
            "Fitzroya cupressoides",
        ],
        "곤충": [
            "Chiasognathus grantii",
        ],
        "해양생물": [
            "Balaenoptera musculus",
        ],
    },

    "CO": {  # 콜롬비아
        "동물": [
            "Panthera onca",
            "Tremarctos ornatus",
            "Tapirus terrestris",
            "Saguinus oedipus",
            # 양서류
            "Oophaga pumilio",  # 딸기화살개구리
            "Dendrobates auratus",  # 청록화살개구리
        ],
        "식물": [
            "Ceroxylon quindiuense",
            "Espeletia grandiflora",
        ],
        "곤충": [
            "Morpho cypris",
        ],
        "해양생물": [
            "Chelonia mydas",
        ],
    },

    "NG": {  # 나이지리아
        "동물": [
            "Gorilla gorilla",
            "Pan troglodytes",
            "Loxodonta africana",
            "Panthera leo",
            "Hippopotamus amphibius",
        ],
        "식물": [
            "Triplochiton scleroxylon",
            "Khaya ivorensis",
        ],
        "곤충": [
            "Goliathus goliatus",
        ],
        "해양생물": [
            "Chelonia mydas",
        ],
    },
}

# 국가 코드와 이름 매핑
COUNTRY_NAMES = {
    "KR": "South Korea",
    "US": "United States",
    "JP": "Japan",
    "CN": "China",
    "RU": "Russia",
    "AU": "Australia",
    "BR": "Brazil",
    "IN": "India",
    "ZA": "South Africa",
    "CA": "Canada",
    "MX": "Mexico",
    "AR": "Argentina",
    "GB": "United Kingdom",
    "FR": "France",
    "DE": "Germany",
    "IT": "Italy",
    "ID": "Indonesia",
    "KE": "Kenya",
    "EG": "Egypt",
    "TH": "Thailand",
    "MY": "Malaysia",
    "NZ": "New Zealand",
    "SE": "Sweden",
    "NO": "Norway",
    "PL": "Poland",
    "ES": "Spain",
    "TR": "Turkey",
    "VN": "Vietnam",
    "PE": "Peru",
    "CL": "Chile",
    "CO": "Colombia",
    "NG": "Nigeria",
}

# ========================================
# 대륙별 대표 멸종위기종 (Regional Fallback)
# 종 개수를 다양하게 설정하여 색상 구분
# ========================================

CONTINENT_SPECIES_MAP = {
    "AS": {  # 아시아 - 12개 (그룹 4)
        "동물": [
            "Panthera tigris",
            "Ailuropoda melanoleuca",
            "Panthera uncia",
            "Elephas maximus",
            "Pongo abelii",
            "Rhinoceros sondaicus",
            "Grus japonensis",
            "Ursus thibetanus",
            "Naemorhedus caudatus",
            "Crocodylus siamensis",
            "Moschus moschiferus",
            "Gavialis gangeticus",
        ],
        "식물": [
            "Ginkgo biloba",
            "Rafflesia arnoldii",
            "Aquilaria malaccensis",
            "Pinus koraiensis",
            "Cycas revoluta",
        ],
        "곤충": [
            "Teinopalpus imperialis",
            "Lucanus maculifemoratus",
            "Troides helena",
            "Callipogon relictus",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Caretta caretta",
            "Dermochelys coriacea",
            "Balaenoptera musculus",
            "Dugong dugon",
            "Lipotes vexillifer",
        ],
    },

    "EU": {  # 유럽 - 8개 (그룹 2)
        "동물": [
            "Ursus arctos",
            "Lynx lynx",
            "Canis lupus",
            "Lynx pardinus",
            "Bison bonasus",
            "Lutra lutra",
            "Monachus monachus",
            "Castor fiber",
        ],
        "식물": [
            "Taxus baccata",
            "Pinus sylvestris",
            "Quercus robur",
        ],
        "곤충": [
            "Lucanus cervus",
            "Rosalia alpina",
        ],
        "해양생물": [
            "Caretta caretta",
            "Monachus monachus",
            "Phocoena phocoena",
        ],
    },

    "AF": {  # 아프리카 - 14개 (그룹 4)
        "동물": [
            "Loxodonta africana",
            "Panthera leo",
            "Diceros bicornis",
            "Panthera pardus",
            "Acinonyx jubatus",
            "Giraffa camelopardalis",
            "Gorilla gorilla",
            "Pan troglodytes",
            "Hippopotamus amphibius",
            "Lycaon pictus",
            "Crocodylus niloticus",
            "Equus grevyi",
            "Ceratotherium simum",
            "Addax nasomaculatus",
        ],
        "식물": [
            "Adansonia digitata",
            "Aloe dichotoma",
            "Encephalartos woodii",
            "Prunus africana",
        ],
        "곤충": [
            "Goliathus goliatus",
            "Mecynorrhina torquata",
            "Charaxes jasius",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dermochelys coriacea",
            "Carcharodon carcharias",
            "Dugong dugon",
        ],
    },

    "NA": {  # 북미 - 10개 (그룹 3)
        "동물": [
            "Haliaeetus leucocephalus",
            "Ursus arctos horribilis",
            "Ursus maritimus",
            "Canis lupus",
            "Puma concolor",
            "Lynx canadensis",
            "Grus americana",
            "Mustela nigripes",
            "Alligator mississippiensis",
            "Bison bison",
        ],
        "식물": [
            "Sequoia sempervirens",
            "Sequoiadendron giganteum",
            "Pinus longaeva",
        ],
        "곤충": [
            "Danaus plexippus",
            "Nicrophorus americanus",
        ],
        "해양생물": [
            "Balaenoptera musculus",
            "Trichechus manatus",
            "Enhydra lutris",
        ],
    },

    "SA": {  # 남미 - 15개 (그룹 5)
        "동물": [
            "Panthera onca",
            "Tapirus terrestris",
            "Pteronura brasiliensis",
            "Myrmecophaga tridactyla",
            "Tremarctos ornatus",
            "Ara ararauna",
            "Leontopithecus rosalia",
            "Bradypus variegatus",
            "Inia geoffrensis",
            "Trichechus manatus",
            "Harpia harpyja",
            "Chrysocyon brachyurus",
            "Priodontes maximus",
            "Blastocerus dichotomus",
            "Chinchilla chinchilla",
        ],
        "식물": [
            "Bertholletia excelsa",
            "Victoria amazonica",
            "Araucaria araucana",
            "Swietenia macrophylla",
            "Cinchona officinalis",
        ],
        "곤충": [
            "Dynastes hercules",
            "Morpho menelaus",
            "Titanus giganteus",
            "Megasoma elephas",
        ],
        "해양생물": [
            "Chelonia mydas",
            "Dermochelys coriacea",
            "Eubalaena australis",
            "Inia geoffrensis",
            "Trichechus manatus",
        ],
    },

    "OC": {  # 오세아니아 - 6개 (그룹 2)
        "동물": [
            "Phascolarctos cinereus",
            "Ornithorhynchus anatinus",
            "Apteryx haastii",
            "Strigops habroptilus",
            "Sarcophilus harrisii",
            "Casuarius casuarius",
        ],
        "식물": [
            "Eucalyptus regnans",
            "Wollemia nobilis",
        ],
        "곤충": [
            "Ornithoptera alexandrae",
        ],
        "해양생물": [
            "Dugong dugon",
            "Carcharodon carcharias",
        ],
    },

    "AN": {  # 남극 - 4개 (그룹 1)
        "동물": [
            "Aptenodytes forsteri",
            "Pygoscelis adeliae",
            "Mirounga leonina",
            "Hydrurga leptonyx",
        ],
        "식물": [],
        "곤충": [],
        "해양생물": [
            "Balaenoptera musculus",
            "Orcinus orca",
        ],
    },
}
