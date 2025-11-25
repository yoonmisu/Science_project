import React, { useState } from 'react';
import { X, ChevronRight } from 'lucide-react';
import logoImg from '../assets/logo.png';
import mapImg from '../assets/map.png';

const categoryThemes = {
  식물: {
    bg: 'bg-white',
    border: 'border-green-200',
    button: 'bg-green-100 hover:bg-green-200',
    title: 'text-black',
    icon: '🌿'
  },
  동물: {
    bg: 'bg-white',
    border: 'border-amber-200',
    button: 'bg-amber-100 hover:bg-amber-200',
    title: 'text-black',
    icon: '🦌'
  },
  곤충: {
    bg: 'bg-white',
    border: 'border-yellow-200',
    button: 'bg-yellow-100 hover:bg-yellow-200',
    title: 'text-black',
    icon: '🐝'
  },
  해양생물: {
    bg: 'bg-white',
    border: 'border-blue-200',
    button: 'bg-blue-100 hover:bg-blue-200',
    title: 'text-black',
    icon: '🐠'
  }
};

const countryData = {
  korea: {
    name: '대한민국',
    식물: [
      { id: 1, name: '무궁화', image: '🌺', color: 'purple' },
      { id: 2, name: '코스모스', image: '🌸', color: 'orange' },
      { id: 3, name: '벚꽃', image: '🌸', color: 'pink' },
      { id: 4, name: '진달래', image: '🌷', color: 'red' },
      { id: 5, name: '소나무', image: '🌲', color: 'green' },
      { id: 6, name: '난초', image: '🌱', color: 'white' }
    ],
    동물: [
      { id: 1, name: '호랑이', image: '🐯', color: 'orange' },
      { id: 2, name: '까치', image: '🐦', color: 'black' },
      { id: 3, name: '노루', image: '🦌', color: 'brown' },
      { id: 4, name: '곰', image: '🐻', color: 'brown' },
      { id: 5, name: '토끼', image: '🐇', color: 'white' },
      { id: 6, name: '늑대', image: '🐺', color: 'gray' }
    ],
    곤충: [
      { id: 1, name: '무당벌레', image: '🐞', color: 'red' },
      { id: 2, name: '나비', image: '🦋', color: 'blue' },
      { id: 3, name: '잠자리', image: '🦟', color: 'green' },
      { id: 4, name: '장수풍뎅이', image: '🪲', color: 'black' },
      { id: 5, name: '개미', image: '🐜', color: 'black' },
      { id: 6, name: '벌', image: '🐝', color: 'yellow' }
    ],
    해양생물: [
      { id: 1, name: '명태', image: '🐟', color: 'silver' },
      { id: 2, name: '해파리', image: '🪼', color: 'transparent' },
      { id: 3, name: '문어', image: '🐙', color: 'red' }
    ]
  },
  japan: {
    name: '일본',
    식물: [
      { id: 1, name: '벚꽃', image: '🌸', color: 'pink' },
      { id: 2, name: '국화', image: '🌼', color: 'yellow' },
      { id: 3, name: '매화', image: '🌺', color: 'white' },
      { id: 4, name: '단풍', image: '🍁', color: 'red' }
    ],
    동물: [
      { id: 1, name: '원숭이', image: '🐵', color: 'brown' },
      { id: 2, name: '사슴', image: '🦌', color: 'brown' },
      { id: 3, name: '두루미', image: '🦢', color: 'white' },
      { id: 4, name: '너구리', image: '🦝', color: 'brown' }
    ],
    곤충: [
      { id: 1, name: '사슴벌레', image: '🪲', color: 'black' },
      { id: 2, name: '반딧불이', image: '✨', color: 'yellow' },
      { id: 3, name: '매미', image: '🦗', color: 'green' }
    ],
    해양생물: [
      { id: 1, name: '참치', image: '🐟', color: 'blue' },
      { id: 2, name: '오징어', image: '🦑', color: 'white' },
      { id: 3, name: '고래', image: '🐋', color: 'blue' }
    ]
  },
  usa: {
    name: '미국',
    식물: [
      { id: 1, name: '장미', image: '🌹', color: 'red' },
      { id: 2, name: '선인장', image: '🌵', color: 'green' },
      { id: 3, name: '해바라기', image: '🌻', color: 'yellow' }
    ],
    동물: [
      { id: 1, name: '대머리독수리', image: '🦅', color: 'brown' },
      { id: 2, name: '들소', image: '🦬', color: 'brown' },
      { id: 3, name: '회색곰', image: '🐻', color: 'brown' }
    ],
    곤충: [
      { id: 1, name: '군주나비', image: '🦋', color: 'orange' },
      { id: 2, name: '꿀벌', image: '🐝', color: 'yellow' },
      { id: 3, name: '반딧불이', image: '✨', color: 'yellow' }
    ],
    해양생물: [
      { id: 1, name: '돌고래', image: '🐬', color: 'gray' },
      { id: 2, name: '상어', image: '🦈', color: 'gray' },
      { id: 3, name: '바다거북', image: '🐢', color: 'green' }
    ]
  },
  china: {
    name: '중국',
    식물: [
      { id: 1, name: '대나무', image: '🎋', color: 'green' },
      { id: 2, name: '모란', image: '🏵️', color: 'pink' },
      { id: 3, name: '연꽃', image: '🪷', color: 'white' }
    ],
    동물: [
      { id: 1, name: '판다', image: '🐼', color: 'black/white' },
      { id: 2, name: '호랑이', image: '🐯', color: 'orange' },
      { id: 3, name: '붉은털원숭이', image: '🐒', color: 'brown' }
    ],
    곤충: [
      { id: 1, name: '비단벌레', image: '💎', color: 'green' },
      { id: 2, name: '나방', image: ' moth ', color: 'brown' },
      { id: 3, name: '매미', image: '🦗', color: 'green' }
    ],
    해양생물: [
      { id: 1, name: '민물돌고래', image: '🐬', color: 'white' },
      { id: 2, name: '상어', image: '🦈', color: 'gray' },
      { id: 3, name: '거북이', image: '🐢', color: 'green' }
    ]
  },
  
  russia: {
    name: '러시아',
    식물: [
      { id: 1, name: '자작나무', image: '🌲', color: 'white/black' },
      { id: 2, name: '카모마일', image: '🌼', color: 'white' },
      { id: 3, name: '라일락', image: '🌸', color: 'purple' }
    ],
    동물: [
      { id: 1, name: '시베리아호랑이', image: '🐅', color: 'orange' },
      { id: 2, name: '불곰', image: '🐻', color: 'brown' },
      { id: 3, name: '늑대', image: '🐺', color: 'gray' }
    ],
    곤충: [
      { id: 1, name: '모기', image: '🦟', color: 'black' },
      { id: 2, name: '꿀벌', image: '🐝', color: 'yellow' },
      { id: 3, name: '나비', image: '🦋', color: 'colorful' }
    ],
    해양생물: [
      { id: 1, name: '벨루가', image: '🐳', color: 'white' },
      { id: 2, name: '바다표범', image: '🦭', color: 'gray' },
      { id: 3, name: '연어', image: '🐟', color: 'pink' }
    ]
  }
};

const HomePage = () => {
  const [category, setCategory] = useState('동물');
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState(null); 
  
  const [modalView, setModalView] = useState('species'); 
  const [speciesPage, setSpeciesPage] = useState(0); 

  const categories = ['동물', '식물', '곤충', '해양생물'];
  const categoryIcons = {
    동물: '🦌',
    식물: '🌿',
    곤충: '🐝',
    해양생물: '🐠'
  };

  const searches = [
    '영국 식물 멸종위기 종류',
    '미국 곤충 생물 다양성',
    '대한민국 해양 생물 다양성',
    '일본 식물 멸종위기 종류',
    '대한민국 곤충 멸종위기 종류',
    '중국 동물 생물 다양성',
    '호주 멸종 위기종!!!!'
  ];

  const handleCountryClick = (countryId) => {
    setSelectedCountry(countryId);
    setSpeciesPage(0);
    setModalView('species');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedCountry(null);
  };
  
  const goToEndangeredView = () => {
    setModalView('endangered');
  };
  
  const theme = categoryThemes[category];
  const currentData = selectedCountry ? countryData[selectedCountry] : null;
  const itemsPerPage = 3;
  const totalSpeciesItems = currentData ? currentData[category]?.length || 0 : 0;
  const totalSpeciesPages = Math.ceil(totalSpeciesItems / itemsPerPage);
  
  const currentSpeciesData = currentData 
    ? currentData[category]?.slice(speciesPage * itemsPerPage, speciesPage * itemsPerPage + itemsPerPage)
    : [];
  const handleNextPage = () => {
    if (speciesPage < totalSpeciesPages - 1) {
      setSpeciesPage((prev) => prev + 1);
    } 
  };

  const handlePrevPage = () => {
    if (speciesPage > 0) {
      setSpeciesPage((prev) => prev - 1);
    } 
  };

  return (
    <div style={{
      backgroundColor: '#ffffff', 
      minHeight: '100vh', 
      fontFamily: 'Pretendard, sans-serif',
      color: '#2e3d2f',
      padding: '0 50px'
    }}>
      <div style={{ padding: '20px 0' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <img src={logoImg} alt="Verde 로고" style={{ height: '60px' }}/>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              placeholder="나라이름과 카테고리명을 꼭 넣어서 검색해요..."
              style={{
                width: '320px',
                padding: '12px 40px 12px 20px',
                border: '1px solid #d0d0d0',
                borderRadius: '25px',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            <span style={{ 
              position: 'absolute', 
              right: '15px', 
              top: '50%', 
              transform: 'translateY(-50%)',
              cursor: 'pointer'
            }}>
              🔍
            </span>
          </div>
        </div>
      </div>

      <div style={{
        backgroundColor: '#f5faf5',
        borderRadius: '40px',
        padding: '20px 90px 45px',
        minHeight: '85vh',
        display: 'flex',
        gap: '68px'
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ 
              color: '#2f6b2d', 
              fontSize: '18px', 
              marginBottom: '16px' 
            }}>
              # 카테고리 선택
            </h2>
            <div style={{ display: 'flex', gap: '12px' }}>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '25px',
                    border: 'none',
                    fontSize: '15px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    backgroundColor: category === cat ? '#c8e6c9' : '#ffffff',
                    color: category === cat ? '#2f6b2d' : '#5a5a5a',
                    boxShadow: category === cat 
                      ? '0 3px 8px rgb(255, 255, 255)' 
                      : '0 2px 4px rgb(255, 255, 255)',
                    transition: 'all 0.3s'
                  }}
                >
                  <span style={{ marginRight: '6px' }}>{categoryIcons[cat]}</span>
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 style={{ 
              color: '#2f6b2d', 
              fontSize: '18px', 
              marginBottom: '16px' 
            }}>
              # 세계 지도
            </h2>
            <p style={{ 
              fontSize: '13px', 
              color: '#7f8d7b', 
              marginBottom: '8px' 
            }}>
              ** 지역을 선택하면 {category} 카테고리에 맞는 생물들이 카드로 나타나요!
            </p>
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '25px',
              boxShadow: '0 3px 6px rgba(150, 180, 150, 0.2)',
              padding: '40px',
              position: 'relative',
              height: '450px'
            }}>
              <img src={mapImg} alt="세계지도" style={{ width: '800px', height: '460px' }}/>
                <button
                  onClick={() => handleCountryClick('korea')}
                  onMouseEnter={() => setHoveredCountry('korea')}
                  onMouseLeave={() => setHoveredCountry(null)}
                  style={{
                    position: 'absolute', top: '45%', right: '28%', width: '50px', height: '50px', borderRadius: '50%', border: 'none', backgroundColor: 'transparent', color: 'white', fontSize: '24px', cursor: 'pointer', boxShadow: '0 4px 8px rgba(0,0,0,0.2)', transition: 'opacity 0.3s', opacity: hoveredCountry === 'korea' ? 1 : 0, display: 'flex', alignItems: 'center', justifyContent: 'center'      
                  }}
                  title="대한민국"
                >
                🇰🇷
                </button>

                <button
                  onClick={() => handleCountryClick('japan')}
                  onMouseEnter={() => setHoveredCountry('japan')}
                  onMouseLeave={() => setHoveredCountry(null)}
                  style={{
                    position: 'absolute', top: '45%', right: '25%', width: '45px', height: '45px', borderRadius: '50%', border: 'none', backgroundColor: 'transparent', color: 'white', fontSize: '22px', cursor: 'pointer', boxShadow: '0 4px 8px rgba(0,0,0,0.2)', transition: 'opacity 0.3s', opacity: hoveredCountry === 'japan' ? 1 : 0, display: 'flex', alignItems: 'center', justifyContent: 'center'      
                  }}
                  title="일본"
                >
                  🇯🇵
                </button>

                <button
                  onClick={() => handleCountryClick('usa')}
                  onMouseEnter={() => setHoveredCountry('usa')}
                  onMouseLeave={() => setHoveredCountry(null)}
                  style={{
                    position: 'absolute', top: '40%', left: '20%', width: '60px', height: '60px', borderRadius: '50%', border: 'none', backgroundColor: 'transparent', color: 'white', fontSize: '28px', cursor: 'pointer', boxShadow: '0 4px 8px rgba(0,0,0,0.2)', transition: 'opacity 0.3s', opacity: hoveredCountry === 'usa' ? 1 : 0, display: 'flex', alignItems: 'center', justifyContent: 'center'      
                  }}
                  title="미국"
                >
                  🇺🇸
                </button>

                <button
                  onClick={() => handleCountryClick('china')}
                  onMouseEnter={() => setHoveredCountry('china')}
                  onMouseLeave={() => setHoveredCountry(null)}
                  style={{
                    position: 'absolute', top: '43%', right: '35%', width: '50px', height: '50px', borderRadius: '50%', border: 'none', backgroundColor: 'transparent', color: 'white', fontSize: '24px', cursor: 'pointer', boxShadow: '0 4px 8px rgba(0,0,0,0.2)', transition: 'opacity 0.3s', opacity: hoveredCountry === 'china' ? 1 : 0, display: 'flex', alignItems: 'center', justifyContent: 'center'      
                  }}
                  title="중국"
                >
                  🇨🇳
                </button>

                <button
                  onClick={() => handleCountryClick('russia')}
                  onMouseEnter={() => setHoveredCountry('russia')}
                  onMouseLeave={() => setHoveredCountry(null)}
                  style={{
                    position: 'absolute', top: '30%', left: '60%', width: '60px', height: '60px', borderRadius: '50%', border: 'none', backgroundColor: 'transparent', color: 'white', fontSize: '28px', cursor: 'pointer', boxShadow: '0 4px 8px rgba(0,0,0,0.2)', transition: 'opacity 0.3s', opacity: hoveredCountry === 'russia' ? 1 : 0, display: 'flex', alignItems: 'center', justifyContent: 'center'      
                  }}
                  title="러시아"
                >
                🇷🇺
                </button>

                <div style={{
                  color: '#a0a0a0',
                  fontSize: '14px',
                  textAlign: 'center'
                }}>
                </div>
            </div>
          </div>
        </div>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          minWidth: '400px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            height: '80px',
            borderRadius: '25px',
            boxShadow: '0 2px 8px rgba(150, 180, 150, 0.15)',
            padding: '20px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'box-shadow 0.3s',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center'
          }}
          
          onClick={() => {/* 모달 열기 로직 추가 필요 */}}
          onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(150, 180, 150, 0.25)'}
          onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(150, 180, 150, 0.15)'}
          >
            <p style={{ fontSize: '18px', fontWeight: '600', marginBottom: '5px' }}>
              오늘의 랜덤 생물 소개!
            </p>
            <p style={{ fontSize: '12px', color: '#808d7c' }}>자세히 보기</p>
          </div>

          <div style={{
            backgroundColor: '#ffffff',
            height: '80px',
            borderRadius: '25px',
            boxShadow: '0 2px 8px rgba(150, 180, 150, 0.15)',
            padding: '20px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'box-shadow 0.3s'
          }}
          onClick={() => {/* 모달 열기 로직 추가 필요 */}}
          onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(150, 180, 150, 0.25)'}
          onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(150, 180, 150, 0.15)'}
          >
            <p style={{ fontSize: '18px', fontWeight: '600', marginBottom: '5px' }}>
              가장 많이 언급되는 멸종 위기종?
            </p>
            <p style={{ fontSize: '12px', color: '#808d7c' }}>자세히 보기</p>
          </div>

          <div>
            <h2 style={{ 
              color: '#2f6b2d', 
              fontSize: '18px', 
              marginBottom: '16px' 
            }}>
              # Verde 실시간 검색어
            </h2>
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '25px',
              boxShadow: '0 2px 8px rgba(150, 180, 150, 0.15)',
              height: '400px',
              overflow: 'hidden'
            }}>
              {searches.map((item, index) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '8px 16px',
                    borderBottom: index !== searches.length - 1 ? '1px solid #edf3ed' : 'none',
                    fontSize: '16px'
                  }}
                >
                  <span style={{
                    fontWeight: '700',
                    color: '#4c944a',
                    minWidth: '28px',
                    padding: '8px'
                  }}>
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {isModalOpen && currentData && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.55)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className={`${theme.bg} ${theme.border}`} style={{
            position: 'relative',
            border: '8px solid',
            borderRadius: '30px',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            maxWidth: '700px',
            width: '100%',
            padding: '40px',
            backgroundColor: '#ffffff',
            borderColor: theme.border === 'border-green-200' ? '#bbf7d0' :
                        theme.border === 'border-amber-200' ? '#D8CFBD' :
                        theme.border === 'border-yellow-200' ? '#FFECB2' : '#CCE0F3'
          }}>
            <button
              onClick={closeModal}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                padding: '8px',
                background: 'rgba(255,255,255,0.5)',
                border: 'none',
                borderRadius: '50%',
                cursor: 'pointer',
                transition: 'background 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => e.target.style.background = 'rgba(0,0,0,0.1)'}
              onMouseLeave={(e) => e.target.style.background = 'rgba(255,255,255,0.5)'}
            >
              <X style={{ width: '24px', height: '24px' }} />
            </button>

            <div style={{ marginBottom: '24px' }}>
              <h2 className={theme.title} style={{
              fontSize: '24px',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
              color: '#1d1d1d'
              }}>
              <span style={{ fontSize: '32px' }}>{theme.icon}</span>
              {currentData.name}의 생물 다양성 - {category}
              </h2>
              <button 
                className={theme.button}
                onClick={goToEndangeredView}
                style={{
                  padding: '10px 20px',
                  borderRadius: '20px',
                  border: 'none',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  backgroundColor: theme.button.includes('green') ? '#bbf7d0' :
                                  theme.button.includes('amber') ? '#D8CFBD' :
                                  theme.button.includes('yellow') ? '#FFECB2' : '#CCE0F3',
                  transition: 'background 0.2s'
                }}>
                멸종위기 종류 보기
              </button>
            </div>
            {modalView === 'species' && (
              <>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '16px',
                  marginBottom: '24px'
                }}>
                  {currentSpeciesData.map((species) => (
                    <div
                      key={species.id}
                      style={{
                        backgroundColor: '#ffffff',
                        borderRadius: '16px',
                        overflow: 'hidden',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        cursor: 'pointer',
                        transition: 'all 0.3s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                        e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(87, 87, 87, 0.1)';
                      }}
                    >
                      <div style={{
                        height: '140px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '64px',
                        background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)'
                      }}>
                        {species.image}
                      </div>
                      <div style={{ padding: '12px', textAlign: 'center' }}>
                        <p style={{ fontWeight: '500', color: '#1f2937' }}>{species.name}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}> 
                  {speciesPage > 0 ? (
                    <button 
                      className={theme.button} 
                      onClick={handlePrevPage}
                      style={{
                        padding: '10px 24px',
                        borderRadius: '20px',
                        border: 'none',
                        fontSize: '16px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        backgroundColor: 'transparent',
                        transition: 'background 0.2s',
                        color: '#555' 
                      }}>
                      <ChevronRight style={{ width: '16px', height: '16px', transform: 'rotate(180deg)' }} />
                      이전으로
                    </button>
                  ) : (
                    <div style={{ minWidth: '100px', height: '16px' }}></div> 
                  )}
                  {speciesPage < totalSpeciesPages - 1 ? (
                    <button 
                      className={theme.button} 
                      onClick={handleNextPage}
                      style={{
                        padding: '10px 24px',
                        borderRadius: '20px',
                        border: 'none',
                        fontSize: '16px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        backgroundColor: 'transparent',
                        transition: 'background 0.2s'
                      }}>
                      다음으로
                      <ChevronRight style={{ width: '16px', height: '16px' }} />
                    </button>
                  ) : (
                    <div style={{ minWidth: '100px', height: '16px' }}></div>
                  )}

                </div>
              </>
            )}
            {modalView === 'endangered' && (
              <div style={{ 
                padding: '40px', 
                textAlign: 'center', 
                minHeight: '300px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#fefcfa',
                borderRadius: '15px'
              }}>
                <h3 style={{
                  color: '#747F60', 
                  fontSize: '20px', 
                  marginBottom: '15px'
                }}>
                  {currentData.name}의 멸종 위기종 목록
                </h3>
                <p style={{ color: '#666', marginBottom: '25px' }}>
                  이 섹션에서는 해당 국가의 멸종 위기종에 대한 상세 정보를 제공할 예정입니다.
                </p>
                <button
                  onClick={() => setModalView('species')}
                  style={{
                    padding: '10px 20px',
                    borderRadius: '20px',
                    border: '1px solid #ccc',
                    backgroundColor: '#fff',
                    cursor: 'pointer',
                    fontSize: '15px',
                    fontWeight: '500',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = '#fff'}
                >
                  생물 다양성 목록으로 돌아가기
                </button>
              </div>
            )}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '16px'
            }}>
              {Array.from({ length: totalSpeciesPages }).map((_, index) => (
                <div 
                  key={index}
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: speciesPage === index ? 
                                    (theme.button.includes('green') ? '#bbf7d0' :
                                    theme.button.includes('amber') ? '#D8CFBD' :
                                    theme.button.includes('yellow') ? '#FFECB2' : '#CCE0F3')
                                    : '#d1d5db'
                  }}
                ></div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;