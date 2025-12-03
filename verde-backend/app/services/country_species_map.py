"""
Country-Species Mapping for IUCN Red List
Curated list of representative endangered species by country
"""

# 국가별 대표 멸종위기종 학명 리스트
# 각 국가당 10-20개 종의 학명을 정의
COUNTRY_SPECIES_MAP = {
    "KR": [
        # 한국 대표 멸종위기종
        "Grus japonensis",          # 두루미 (Red-crowned Crane)
        "Naemorhedus caudatus",     # 산양 (Long-tailed Goral)
        "Ursus thibetanus",         # 반달가슴곰 (Asiatic Black Bear)
        "Lutra lutra",              # 수달 (Eurasian Otter)
        "Moschus moschiferus",      # 사향노루 (Siberian Musk Deer)
        "Mustela lutreola",         # 유럽밍크 (European Mink)
        "Falco peregrinus",         # 매 (Peregrine Falcon)
        "Haliaeetus pelagicus",     # 흰꼬리수리 (Steller's Sea Eagle)
        "Ciconia boyciana",         # 황새 (Oriental Stork)
        "Pelodiscus sinensis",      # 자라 (Chinese Softshell Turtle)
    ],
    
    "US": [
        # 미국 대표 멸종위기종
        "Haliaeetus leucocephalus",  # 흰머리수리 (Bald Eagle)
        "Ursus arctos horribilis",   # 그리즐리 곰 (Grizzly Bear)
        "Lynx canadensis",           # 캐나다스라소니 (Canada Lynx)
        "Puma concolor",             # 퓨마 (Cougar/Mountain Lion)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Mustela nigripes",          # 검은발족제비 (Black-footed Ferret)
        "Grus americana",            # 아메리카두루미 (Whooping Crane)
        "Gymnogyps californianus",   # 캘리포니아콘도르 (California Condor)
        "Caretta caretta",           # 붉은바다거북 (Loggerhead Sea Turtle)
        "Alligator mississippiensis", # 미시시피악어 (American Alligator)
    ],
    
    "JP": [
        # 일본 대표 멸종위기종
        "Grus japonensis",           # 두루미 (Red-crowned Crane)
        "Ursus thibetanus",          # 반달가슴곰 (Asiatic Black Bear)
        "Lutra lutra",               # 수달 (Eurasian Otter)
        "Prionailurus bengalensis",  # 삵 (Leopard Cat)
        "Nipponia nippon",           # 따오기 (Crested Ibis)
        "Haliaeetus pelagicus",      # 흰꼬리수리 (Steller's Sea Eagle)
        "Falco peregrinus",          # 매 (Peregrine Falcon)
        "Dermochelys coriacea",      # 장수거북 (Leatherback Turtle)
        "Trichechus manatus",        # 매너티 (West Indian Manatee)
        "Balaenoptera musculus",     # 대왕고래 (Blue Whale)
    ],
    
    "CN": [
        # 중국 대표 멸종위기종
        "Ailuropoda melanoleuca",    # 자이언트판다 (Giant Panda)
        "Panthera tigris amoyensis", # 남중국호랑이 (South China Tiger)
        "Panthera uncia",            # 눈표범 (Snow Leopard)
        "Rhinopithecus roxellana",   # 황금원숭이 (Golden Snub-nosed Monkey)
        "Ursus thibetanus",          # 반달가슴곰 (Asiatic Black Bear)
        "Moschus moschiferus",       # 사향노루 (Siberian Musk Deer)
        "Grus japonensis",           # 두루미 (Red-crowned Crane)
        "Nipponia nippon",           # 따오기 (Crested Ibis)
        "Lipotes vexillifer",        # 양쯔강돌고래 (Baiji)
        "Crocodylus siamensis",      # 샴악어 (Siamese Crocodile)
    ],
    
    "RU": [
        # 러시아 대표 멸종위기종
        "Panthera tigris altaica",   # 시베리아호랑이 (Siberian Tiger)
        "Ursus maritimus",           # 북극곰 (Polar Bear)
        "Panthera uncia",            # 눈표범 (Snow Leopard)
        "Grus leucogeranus",         # 시베리아흰두루미 (Siberian Crane)
        "Haliaeetus pelagicus",      # 흰꼬리수리 (Steller's Sea Eagle)
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Mustela lutreola",          # 유럽밍크 (European Mink)
        "Balaena mysticetus",        # 북극고래 (Bowhead Whale)
        "Moschus moschiferus",       # 사향노루 (Siberian Musk Deer)
        "Saiga tatarica",            # 사이가영양 (Saiga Antelope)
    ],
    
    "AU": [
        # 호주 대표 멸종위기종
        "Phascolarctos cinereus",    # 코알라 (Koala)
        "Macropus rufus",            # 붉은캥거루 (Red Kangaroo)
        "Vombatus ursinus",          # 웜뱃 (Common Wombat)
        "Ornithorhynchus anatinus",  # 오리너구리 (Platypus)
        "Tachyglossus aculeatus",    # 바늘두더지 (Echidna)
        "Crocodylus porosus",        # 바다악어 (Saltwater Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Carcharodon carcharias",    # 백상아리 (Great White Shark)
        "Dugong dugon",              # 듀공 (Dugong)
        "Dasyurus viverrinus",       # 동부쿼 (Eastern Quoll)
    ],
    
    "BR": [
        # 브라질 대표 멸종위기종
        "Panthera onca",             # 재규어 (Jaguar)
        "Tapirus terrestris",        # 맥 (Brazilian Tapir)
        "Ara ararauna",              # 파란금강앵무 (Blue-and-yellow Macaw)
        "Pteronura brasiliensis",    # 대수달 (Giant Otter)
        "Myrmecophaga tridactyla",   # 큰개미핥기 (Giant Anteater)
        "Priodontes maximus",        # 큰아르마딜로 (Giant Armadillo)
        "Bradypus variegatus",       # 나무늘보 (Brown-throated Sloth)
        "Leontopithecus rosalia",    # 골든라이언타마린 (Golden Lion Tamarin)
        "Trichechus manatus",        # 매너티 (West Indian Manatee)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
    ],
    
    "IN": [
        # 인도 대표 멸종위기종
        "Panthera tigris",           # 벵골호랑이 (Bengal Tiger)
        "Panthera leo persica",      # 아시아사자 (Asiatic Lion)
        "Elephas maximus",           # 아시아코끼리 (Asian Elephant)
        "Rhinoceros unicornis",      # 인도코뿔소 (Indian Rhinoceros)
        "Panthera pardus",           # 표범 (Leopard)
        "Ursus thibetanus",          # 반달가슴곰 (Asiatic Black Bear)
        "Bos gaurus",                # 가울 (Gaur)
        "Cuon alpinus",              # 붉은개 (Dhole)
        "Gavialis gangeticus",       # 인도악어 (Gharial)
        "Grus antigone",             # 사루스두루미 (Sarus Crane)
    ],
    
    "ZA": [
        # 남아프리카공화국 대표 멸종위기종
        "Panthera leo",              # 사자 (Lion)
        "Loxodonta africana",        # 아프리카코끼리 (African Elephant)
        "Diceros bicornis",          # 검은코뿔소 (Black Rhinoceros)
        "Ceratotherium simum",       # 흰코뿔소 (White Rhinoceros)
        "Panthera pardus",           # 표범 (Leopard)
        "Acinonyx jubatus",          # 치타 (Cheetah)
        "Lycaon pictus",             # 아프리카들개 (African Wild Dog)
        "Hippopotamus amphibius",    # 하마 (Hippopotamus)
        "Giraffa camelopardalis",    # 기린 (Giraffe)
        "Carcharodon carcharias",    # 백상아리 (Great White Shark)
    ],

    "CA": [
        # 캐나다 대표 멸종위기종
        "Ursus maritimus",           # 북극곰 (Polar Bear)
        "Rangifer tarandus",         # 순록 (Caribou/Reindeer)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Ursus arctos",              # 불곰 (Grizzly Bear)
        "Lynx canadensis",           # 캐나다스라소니 (Canada Lynx)
        "Gulo gulo",                 # 울버린 (Wolverine)
        "Puma concolor",             # 퓨마 (Cougar)
        "Alces alces",               # 말코손바닥사슴 (Moose)
        "Balaena mysticetus",        # 북극고래 (Bowhead Whale)
        "Haliaeetus leucocephalus",  # 흰머리수리 (Bald Eagle)
    ],

    "MX": [
        # 멕시코 대표 멸종위기종
        "Panthera onca",             # 재규어 (Jaguar)
        "Tapirus bairdii",           # 중미맥 (Baird's Tapir)
        "Trichechus manatus",        # 매너티 (West Indian Manatee)
        "Alouatta palliata",         # 검은울음원숭이 (Mantled Howler Monkey)
        "Ara militaris",             # 군인금강앵무 (Military Macaw)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Crocodylus acutus",         # 아메리카악어 (American Crocodile)
        "Gopherus flavomarginatus",  # 볼손거북 (Bolson Tortoise)
        "Ambystoma mexicanum",       # 아홀로틀 (Axolotl)
        "Antilocapra americana",     # 프롱혼 (Pronghorn Antelope)
    ],

    "AR": [
        # 아르헨티나 대표 멸종위기종
        "Panthera onca",             # 재규어 (Jaguar)
        "Puma concolor",             # 퓨마 (Cougar)
        "Chrysocyon brachyurus",     # 갈기늑대 (Maned Wolf)
        "Myrmecophaga tridactyla",   # 큰개미핥기 (Giant Anteater)
        "Pteronura brasiliensis",    # 대수달 (Giant Otter)
        "Ara glaucogularis",         # 파란목금강앵무 (Blue-throated Macaw)
        "Hippocamelus bisulcus",     # 칠레사슴 (Chilean Huemul)
        "Chinchilla chinchilla",     # 친칠라 (Chinchilla)
        "Eubalaena australis",       # 남방참고래 (Southern Right Whale)
        "Ctenomys sociabilis",       # 사회적투코투코 (Colonial Tuco-tuco)
    ],

    "GB": [
        # 영국 대표 멸종위기종
        "Lutra lutra",               # 수달 (Eurasian Otter)
        "Mustela putorius",          # 유럽족제비 (European Polecat)
        "Sciurus vulgaris",          # 유럽다람쁘 (Red Squirrel)
        "Halichoerus grypus",        # 회색물범 (Grey Seal)
        "Erinaceus europaeus",       # 유럽고슴도치 (European Hedgehog)
        "Falco peregrinus",          # 매 (Peregrine Falcon)
        "Bubo bubo",                 # 수리부엉이 (Eurasian Eagle-Owl)
        "Salmo salar",               # 대서양연어 (Atlantic Salmon)
        "Phocoena phocoena",         # 쇠돌고래 (Harbor Porpoise)
        "Bufo bufo",                 # 유럽두꺼비 (Common Toad)
    ],

    "FR": [
        # 프랑스 대표 멸종위기종
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lutra lutra",               # 수달 (Eurasian Otter)
        "Vulpes vulpes",             # 붉은여우 (Red Fox)
        "Gypaetus barbatus",         # 수염수리 (Bearded Vulture)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
        "Testudo hermanni",          # 헤르만육지거북 (Hermann's Tortoise)
        "Monachus monachus",         # 지중해몽크물범 (Mediterranean Monk Seal)
        "Phoca vitulina",            # 항구물범 (Harbor Seal)
    ],

    "DE": [
        # 독일 대표 멸종위기종
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lutra lutra",               # 수달 (Eurasian Otter)
        "Castor fiber",              # 유라시아비버 (Eurasian Beaver)
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Mustela lutreola",          # 유럽밍크 (European Mink)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
        "Haliaeetus albicilla",      # 흰꼬리수리 (White-tailed Eagle)
        "Grus grus",                 # 두루미 (Common Crane)
        "Bombina bombina",           # 붉은배두꺼비 (Fire-bellied Toad)
    ],

    "IT": [
        # 이탈리아 대표 멸종위기종
        "Ursus arctos marsicanus",   # 아펜니노곰 (Marsican Brown Bear)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Rupicapra pyrenaica ornata", # 아브루초샤모아 (Abruzzo Chamois)
        "Caretta caretta",           # 붉은바다거북 (Loggerhead Sea Turtle)
        "Monachus monachus",         # 지중해몽크물범 (Mediterranean Monk Seal)
        "Testudo hermanni",          # 헤르만육지거북 (Hermann's Tortoise)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
        "Gypaetus barbatus",         # 수염수리 (Bearded Vulture)
        "Salamandrina perspicillata", # 북부안경도롱뇽 (Northern Spectacled Salamander)
    ],

    "ID": [
        # 인도네시아 대표 멸종위기종
        "Pongo abelii",              # 수마트라오랑우탄 (Sumatran Orangutan)
        "Pongo pygmaeus",            # 보르네오오랑우탄 (Bornean Orangutan)
        "Panthera tigris sumatrae",  # 수마트라호랑이 (Sumatran Tiger)
        "Rhinoceros sondaicus",      # 자바코뿔소 (Javan Rhinoceros)
        "Dicerorhinus sumatrensis",  # 수마트라코뿔소 (Sumatran Rhinoceros)
        "Elephas maximus sumatranus", # 수마트라코끼리 (Sumatran Elephant)
        "Varanus komodoensis",       # 코모도왕도마뱀 (Komodo Dragon)
        "Manis javanica",            # 말레이천산갑 (Sunda Pangolin)
        "Crocodylus porosus",        # 바다악어 (Saltwater Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
    ],

    "KE": [
        # 케냐 대표 멸종위기종
        "Loxodonta africana",        # 아프리카코끼리 (African Elephant)
        "Panthera leo",              # 사자 (Lion)
        "Panthera pardus",           # 표범 (Leopard)
        "Diceros bicornis",          # 검은코뿔소 (Black Rhinoceros)
        "Acinonyx jubatus",          # 치타 (Cheetah)
        "Giraffa camelopardalis",    # 기린 (Giraffe)
        "Hippopotamus amphibius",    # 하마 (Hippopotamus)
        "Equus grevyi",              # 그레비얼룩말 (Grevy's Zebra)
        "Lycaon pictus",             # 아프리카들개 (African Wild Dog)
        "Struthio camelus",          # 타조 (Ostrich)
    ],

    "EG": [
        # 이집트 대표 멸종위기종
        "Panthera pardus",           # 표범 (Leopard)
        "Acinonyx jubatus",          # 치타 (Cheetah)
        "Gazella dorcas",            # 도르카스가젤 (Dorcas Gazelle)
        "Oryx dammah",               # 시미타뿔오릭스 (Scimitar-horned Oryx)
        "Addax nasomaculatus",       # 아닥스 (Addax)
        "Crocodylus niloticus",      # 나일악어 (Nile Crocodile)
        "Caretta caretta",           # 붉은바다거북 (Loggerhead Sea Turtle)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Dugong dugon",              # 듀공 (Dugong)
        "Tursiops truncatus",        # 큰돌고래 (Bottlenose Dolphin)
    ],

    "TH": [
        # 태국 대표 멸종위기종
        "Panthera tigris corbetti",  # 인도차이나호랑이 (Indochinese Tiger)
        "Elephas maximus",           # 아시아코끼리 (Asian Elephant)
        "Panthera pardus",           # 표범 (Leopard)
        "Bos gaurus",                # 가울 (Gaur)
        "Cuon alpinus",              # 붉은개 (Dhole)
        "Prionailurus bengalensis",  # 삵 (Leopard Cat)
        "Crocodylus siamensis",      # 샴악어 (Siamese Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Dermochelys coriacea",      # 장수거북 (Leatherback Turtle)
        "Gavialis gangeticus",       # 인도악어 (Gharial)
    ],

    "MY": [
        # 말레이시아 대표 멸종위기종
        "Panthera tigris jacksoni",  # 말레이호랑이 (Malayan Tiger)
        "Elephas maximus",           # 아시아코끼리 (Asian Elephant)
        "Rhinoceros sondaicus",      # 자바코뿔소 (Javan Rhinoceros)
        "Dicerorhinus sumatrensis",  # 수마트라코뿔소 (Sumatran Rhinoceros)
        "Panthera pardus",           # 표범 (Leopard)
        "Helarctos malayanus",       # 말레이곰 (Sun Bear)
        "Manis javanica",            # 말레이천산갑 (Sunda Pangolin)
        "Pongo pygmaeus",            # 보르네오오랑우탄 (Bornean Orangutan)
        "Nasalis larvatus",          # 긴코원숭이 (Proboscis Monkey)
        "Crocodylus porosus",        # 바다악어 (Saltwater Crocodile)
    ],

    "NZ": [
        # 뉴질랜드 대표 멸종위기종
        "Apteryx haastii",           # 큰키위 (Great Spotted Kiwi)
        "Strigops habroptilus",      # 카카포앵무 (Kakapo)
        "Nestor meridionalis",       # 카카앵무 (Kaka)
        "Megadyptes antipodes",      # 노란눈펭귄 (Yellow-eyed Penguin)
        "Carcharodon carcharias",    # 백상아리 (Great White Shark)
        "Arctocephalus forsteri",    # 뉴질랜드물개 (New Zealand Fur Seal)
        "Sphenodon punctatus",       # 투아타라 (Tuatara)
        "Leiopelma hochstetteri",    # 호흐스테터개구리 (Hochstetter's Frog)
        "Delphinapterus leucas",     # 벨루가 (Beluga Whale)
        "Callorhinus ursinus",       # 북방물개 (Northern Fur Seal)
    ],

    "SE": [
        # 스웨덴 대표 멸종위기종
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Gulo gulo",                 # 울버린 (Wolverine)
        "Rangifer tarandus",         # 순록 (Reindeer)
        "Alces alces",               # 말코손바닥사슴 (Moose)
        "Halichoerus grypus",        # 회색물범 (Grey Seal)
        "Phoca vitulina",            # 항구물범 (Harbor Seal)
        "Haliaeetus albicilla",      # 흰꼬리수리 (White-tailed Eagle)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
    ],

    "NO": [
        # 노르웨이 대표 멸종위기종
        "Ursus maritimus",           # 북극곰 (Polar Bear)
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Gulo gulo",                 # 울버린 (Wolverine)
        "Rangifer tarandus",         # 순록 (Reindeer)
        "Balaenoptera musculus",     # 대왕고래 (Blue Whale)
        "Megaptera novaeangliae",    # 혹등고래 (Humpback Whale)
        "Orcinus orca",              # 범고래 (Orca/Killer Whale)
        "Halichoerus grypus",        # 회색물범 (Grey Seal)
    ],

    "PL": [
        # 폴란드 대표 멸종위기종
        "Bison bonasus",             # 유럽들소 (European Bison)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Castor fiber",              # 유라시아비버 (Eurasian Beaver)
        "Lutra lutra",               # 수달 (Eurasian Otter)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
        "Haliaeetus albicilla",      # 흰꼬리수리 (White-tailed Eagle)
        "Grus grus",                 # 두루미 (Common Crane)
        "Ciconia nigra",             # 검은황새 (Black Stork)
    ],

    "ES": [
        # 스페인 대표 멸종위기종
        "Lynx pardinus",             # 이베리아스라소니 (Iberian Lynx)
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Aquila adalberti",          # 스페인황제독수리 (Spanish Imperial Eagle)
        "Gypaetus barbatus",         # 수염수리 (Bearded Vulture)
        "Monachus monachus",         # 지중해몽크물범 (Mediterranean Monk Seal)
        "Caretta caretta",           # 붉은바다거북 (Loggerhead Sea Turtle)
        "Testudo graeca",            # 그리스육지거북 (Spur-thighed Tortoise)
        "Capra pyrenaica",           # 스페인아이벡스 (Iberian Ibex)
        "Rupicapra pyrenaica",       # 피레네샤모아 (Pyrenean Chamois)
    ],

    "TR": [
        # 터키 대표 멸종위기종
        "Panthera pardus tulliana",  # 아나톨리아표범 (Anatolian Leopard)
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Capra aegagrus",            # 야생염소 (Wild Goat)
        "Gazella subgutturosa",      # 고비가젤 (Goitered Gazelle)
        "Monachus monachus",         # 지중해몽크물범 (Mediterranean Monk Seal)
        "Caretta caretta",           # 붉은바다거북 (Loggerhead Sea Turtle)
        "Testudo graeca",            # 그리스육지거북 (Spur-thighed Tortoise)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
    ],

    "VN": [
        # 베트남 대표 멸종위기종
        "Panthera tigris",           # 호랑이 (Tiger)
        "Elephas maximus",           # 아시아코끼리 (Asian Elephant)
        "Rhinoceros sondaicus",      # 자바코뿔소 (Javan Rhinoceros)
        "Bos sauveli",               # 코프레이소 (Kouprey)
        "Pseudoryx nghetinhensis",   # 사올라 (Saola)
        "Crocodylus siamensis",      # 샴악어 (Siamese Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Dermochelys coriacea",      # 장수거북 (Leatherback Turtle)
        "Manis javanica",            # 말레이천산갑 (Sunda Pangolin)
        "Nomascus gabriellae",       # 황볼긴팔원숭이 (Yellow-cheeked Gibbon)
    ],

    "PE": [
        # 페루 대표 멸종위기종
        "Panthera onca",             # 재규어 (Jaguar)
        "Tremarctos ornatus",        # 안경곰 (Spectacled Bear)
        "Tapirus terrestris",        # 남아메리카맥 (South American Tapir)
        "Pteronura brasiliensis",    # 대수달 (Giant Otter)
        "Ara militaris",             # 군인금강앵무 (Military Macaw)
        "Trichechus manatus",        # 매너티 (West Indian Manatee)
        "Inia geoffrensis",          # 아마존강돌고래 (Amazon River Dolphin)
        "Crocodylus acutus",         # 아메리카악어 (American Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Hippocamelus antisensis",   # 페루사슴 (Taruca)
    ],

    "CL": [
        # 칠레 대표 멸종위기종
        "Puma concolor",             # 퓨마 (Cougar)
        "Hippocamelus bisulcus",     # 칠레사슴 (Chilean Huemul)
        "Lama guanicoe",             # 과나코 (Guanaco)
        "Vicugna vicugna",           # 비쿠냐 (Vicuña)
        "Chinchilla chinchilla",     # 친칠라 (Chinchilla)
        "Lontra felina",             # 해달수달 (Marine Otter)
        "Arctocephalus philippii",   # 후안페르난데스물개 (Juan Fernández Fur Seal)
        "Balaenoptera musculus",     # 대왕고래 (Blue Whale)
        "Eubalaena australis",       # 남방참고래 (Southern Right Whale)
        "Spheniscus humboldti",      # 훔볼트펭귄 (Humboldt Penguin)
    ],

    "CO": [
        # 콜롬비아 대표 멸종위기종
        "Panthera onca",             # 재규어 (Jaguar)
        "Tremarctos ornatus",        # 안경곰 (Spectacled Bear)
        "Tapirus terrestris",        # 남아메리카맥 (South American Tapir)
        "Ateles fusciceps",          # 검은머리거미원숭이 (Brown-headed Spider Monkey)
        "Saguinus oedipus",          # 솜털머리타마린 (Cotton-top Tamarin)
        "Ara militaris",             # 군인금강앵무 (Military Macaw)
        "Crocodylus acutus",         # 아메리카악어 (American Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Trichechus manatus",        # 매너티 (West Indian Manatee)
        "Inia geoffrensis",          # 아마존강돌고래 (Amazon River Dolphin)
    ],

    "NG": [
        # 나이지리아 대표 멸종위기종
        "Gorilla gorilla",           # 서부고릴라 (Western Gorilla)
        "Pan troglodytes",           # 침팬지 (Chimpanzee)
        "Loxodonta africana",        # 아프리카코끼리 (African Elephant)
        "Panthera leo",              # 사자 (Lion)
        "Panthera pardus",           # 표범 (Leopard)
        "Hippopotamus amphibius",    # 하마 (Hippopotamus)
        "Trichechus senegalensis",   # 서아프리카매너티 (West African Manatee)
        "Crocodylus niloticus",      # 나일악어 (Nile Crocodile)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
        "Manis tricuspis",           # 아프리카나무천산갑 (Tree Pangolin)
    ],
}

# 국가 코드와 이름 매핑 (참고용)
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
# CONTINENT_SPECIES_MAP
# ========================================
# 대륙별 대표 멸종위기종 (Regional Fallback Pattern)
# 특정 국가 데이터가 없을 때 대륙 단위로 fallback
# ========================================

CONTINENT_SPECIES_MAP = {
    "AS": [  # Asia
        "Panthera tigris",           # 호랑이 (Tiger)
        "Ailuropoda melanoleuca",    # 자이언트판다 (Giant Panda)
        "Panthera uncia",            # 눈표범 (Snow Leopard)
        "Elephas maximus",           # 아시아코끼리 (Asian Elephant)
        "Pongo abelii",              # 수마트라오랑우탄 (Sumatran Orangutan)
        "Rhinoceros sondaicus",      # 자바코뿔소 (Javan Rhinoceros)
        "Grus japonensis",           # 두루미 (Red-crowned Crane)
        "Ursus thibetanus",          # 반달가슴곰 (Asiatic Black Bear)
        "Naemorhedus caudatus",      # 산양 (Long-tailed Goral)
        "Crocodylus siamensis",      # 샴악어 (Siamese Crocodile)
    ],

    "EU": [  # Europe
        "Ursus arctos",              # 불곰 (Brown Bear)
        "Lynx lynx",                 # 유라시아스라소니 (Eurasian Lynx)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Lynx pardinus",             # 이베리아스라소니 (Iberian Lynx)
        "Bison bonasus",             # 유럽들소 (European Bison)
        "Lutra lutra",               # 수달 (Eurasian Otter)
        "Aquila chrysaetos",         # 금독수리 (Golden Eagle)
        "Gypaetus barbatus",         # 수염수리 (Bearded Vulture)
        "Monachus monachus",         # 지중해몽크물범 (Mediterranean Monk Seal)
        "Castor fiber",              # 유라시아비버 (Eurasian Beaver)
    ],

    "AF": [  # Africa
        "Loxodonta africana",        # 아프리카코끼리 (African Elephant)
        "Panthera leo",              # 사자 (Lion)
        "Diceros bicornis",          # 검은코뿔소 (Black Rhinoceros)
        "Panthera pardus",           # 표범 (Leopard)
        "Acinonyx jubatus",          # 치타 (Cheetah)
        "Giraffa camelopardalis",    # 기린 (Giraffe)
        "Gorilla gorilla",           # 서부고릴라 (Western Gorilla)
        "Hippopotamus amphibius",    # 하마 (Hippopotamus)
        "Lycaon pictus",             # 아프리카들개 (African Wild Dog)
        "Crocodylus niloticus",      # 나일악어 (Nile Crocodile)
    ],

    "NA": [  # North America
        "Haliaeetus leucocephalus",  # 흰머리수리 (Bald Eagle)
        "Ursus arctos horribilis",   # 그리즐리 곰 (Grizzly Bear)
        "Ursus maritimus",           # 북극곰 (Polar Bear)
        "Canis lupus",               # 회색늑대 (Gray Wolf)
        "Puma concolor",             # 퓨마 (Cougar)
        "Lynx canadensis",           # 캐나다스라소니 (Canada Lynx)
        "Grus americana",            # 아메리카두루미 (Whooping Crane)
        "Mustela nigripes",          # 검은발족제비 (Black-footed Ferret)
        "Alligator mississippiensis", # 미시시피악어 (American Alligator)
        "Gymnogyps californianus",   # 캘리포니아콘도르 (California Condor)
    ],

    "SA": [  # South America
        "Panthera onca",             # 재규어 (Jaguar)
        "Tapirus terrestris",        # 남아메리카맥 (South American Tapir)
        "Pteronura brasiliensis",    # 대수달 (Giant Otter)
        "Myrmecophaga tridactyla",   # 큰개미핥기 (Giant Anteater)
        "Tremarctos ornatus",        # 안경곰 (Spectacled Bear)
        "Ara ararauna",              # 파란금강앵무 (Blue-and-yellow Macaw)
        "Leontopithecus rosalia",    # 골든라이언타마린 (Golden Lion Tamarin)
        "Bradypus variegatus",       # 나무늘보 (Brown-throated Sloth)
        "Inia geoffrensis",          # 아마존강돌고래 (Amazon River Dolphin)
        "Trichechus manatus",        # 매너티 (West Indian Manatee)
    ],

    "OC": [  # Oceania
        "Phascolarctos cinereus",    # 코알라 (Koala)
        "Macropus rufus",            # 붉은캥거루 (Red Kangaroo)
        "Ornithorhynchus anatinus",  # 오리너구리 (Platypus)
        "Apteryx haastii",           # 큰키위 (Great Spotted Kiwi)
        "Strigops habroptilus",      # 카카포앵무 (Kakapo)
        "Crocodylus porosus",        # 바다악어 (Saltwater Crocodile)
        "Dugong dugon",              # 듀공 (Dugong)
        "Carcharodon carcharias",    # 백상아리 (Great White Shark)
        "Megadyptes antipodes",      # 노란눈펭귄 (Yellow-eyed Penguin)
        "Chelonia mydas",            # 푸른바다거북 (Green Sea Turtle)
    ],

    "AN": [  # Antarctica
        "Aptenodytes forsteri",      # 황제펭귄 (Emperor Penguin)
        "Aptenodytes patagonicus",   # 킹펭귄 (King Penguin)
        "Pygoscelis adeliae",        # 아델리펭귄 (Adelie Penguin)
        "Balaenoptera musculus",     # 대왕고래 (Blue Whale)
        "Megaptera novaeangliae",    # 혹등고래 (Humpback Whale)
        "Orcinus orca",              # 범고래 (Orca)
        "Hydrurga leptonyx",         # 표범물범 (Leopard Seal)
        "Mirounga leonina",          # 남방코끼리물범 (Southern Elephant Seal)
        "Lobodon carcinophaga",      # 크레이터이터물범 (Crabeater Seal)
        "Diomedea exulans",          # 방랑알바트로스 (Wandering Albatross)
    ],
}

# ========================================
# DEPRECATED: COUNTRY_NAME_TO_CODE
# ========================================
# 이 딕셔너리는 더 이상 사용되지 않습니다.
# iucn_service.py에서 pycountry 라이브러리를 사용하여
# 전 세계 모든 국가명을 자동으로 ISO 코드로 변환합니다.
#
# 하위 호환성을 위해 유지하지만, 새로운 코드에서는 사용하지 마세요.
# ========================================
