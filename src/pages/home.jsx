import React, { useState, useEffect } from 'react';
import { X, ChevronRight, Search } from 'lucide-react';
import logoImg from '../assets/logo.png';
import InteractiveDottedMap from '../components/InteractiveDottedMap';
import { categoryThemes, countryNames, endangeredSpeciesCount } from '../data/biodiversityData';
import { fetchSpeciesByCountry, searchSpeciesByName } from '../services/api';
import { SpeciesCardSkeletonGrid } from '../components/SpeciesCardSkeleton';
import ErrorMessage from '../components/ErrorMessage';

const HomePage = () => {
  const [category, setCategory] = useState('동물');
  const [selectedLocation, setSelectedLocation] = useState(null); // { lat, lng, name, countryCode }
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [modalView, setModalView] = useState('species');
  const [speciesPage, setSpeciesPage] = useState(0);

  // API 상태 관리
  const [speciesData, setSpeciesData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(0);

  // 검색 기능 상태
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredCountries, setFilteredCountries] = useState(null); // null = 전체 표시, array = 필터링된 국가들

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

  // 위치와 카테고리가 선택되면 API 호출
  useEffect(() => {
    if (!selectedLocation || !isModalOpen || modalView !== 'species') {
      return;
    }

    const loadSpeciesData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // 국가 코드 매핑 없이 직접 전달 (백엔드에서 처리)
        const countryCode = selectedLocation.countryCode;

        if (!countryCode) {
          setError('국가 정보를 확인할 수 없습니다.');
          setSpeciesData([]);
          setIsLoading(false);
          return;
        }

        console.log(`📡 API 호출: ${selectedLocation.name} (${countryCode}) - ${category}`);

        // ISO 코드 기반 API 호출
        const response = await fetchSpeciesByCountry(
          countryCode,
          category,
          speciesPage + 1,
          3
        );

        setSpeciesData(response.data);
        setTotalPages(response.totalPages);
        console.log(`✅ 데이터 로드 성공: ${response.data.length}개`);
      } catch (err) {
        console.error('❌ API 호출 실패:', err);
        setError(err.message || '데이터를 불러오는 중 오류가 발생했습니다.');
        setSpeciesData([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadSpeciesData();
  }, [selectedLocation, category, speciesPage, isModalOpen, modalView]);

  // InteractiveDottedMap 콜백: { name, code, lat, lng } 객체를 받음
  const handleCountryClick = (location) => {
    console.log(`🗺️ 지도 클릭: ${location.name} (${location.lat.toFixed(2)}, ${location.lng.toFixed(2)})`);

    // 위치 정보 + 국가 코드를 저장하고 모달 열기
    setSelectedLocation({
      lat: location.lat,
      lng: location.lng,
      name: location.name,
      countryCode: location.code // 빠른 조회를 위한 국가 코드
    });
    setSpeciesPage(0);
    setModalView('species');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedLocation(null);
  };

  const goToEndangeredView = () => {
    setModalView('endangered');
  };

  // 에러 재시도 핸들러
  const handleRetry = () => {
    setError(null);
    setSpeciesPage(0); // 페이지 리셋하면 useEffect가 자동으로 재실행됨
  };

  const theme = categoryThemes[category];

  // API 데이터 사용 (mockData는 제거됨)
  const currentSpeciesData = speciesData || [];

  const handleNextPage = () => {
    if (speciesPage < totalPages - 1) {
      setSpeciesPage((prev) => prev + 1);
    }
  };

  const handlePrevPage = () => {
    if (speciesPage > 0) {
      setSpeciesPage((prev) => prev - 1);
    }
  };

  // 검색 처리 함수 (종 이름 기반)
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // 검색어가 비어있으면 전체 표시
      setFilteredCountries(null);
      return;
    }

    try {
      // 백엔드 API를 통해 종 검색
      const result = await searchSpeciesByName(searchQuery, category);

      if (result.countries && result.countries.length > 0) {
        setFilteredCountries(result.countries);
        console.log(`🔍 "${searchQuery}" 검색 결과:`, result.countries);
      } else {
        setFilteredCountries([]);
        console.log(`🔍 "${searchQuery}" 검색 결과: 없음`);
      }
    } catch (error) {
      console.error('❌ 검색 오류:', error);
      setFilteredCountries([]);
    }
  };

  // Enter 키로 검색
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 검색 초기화
  const clearSearch = () => {
    setSearchQuery('');
    setFilteredCountries(null);
  };

  return (
    <div style={{
      backgroundColor: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Pretendard, sans-serif',
      color: '#2e3d2f',
      padding: '0 30px'
    }}>
      <div style={{ padding: '20px 0' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <img src={logoImg} alt="Verde 로고" style={{ height: '60px' }} />
          <div style={{
            position: 'relative',
            width: '420px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end'
          }}>
            <div style={{ position: 'relative', width: '320px' }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleSearchKeyPress}
                placeholder="종 이름을 입력하세요 (예: 판다, 호랑이, panda, tiger)"
                style={{
                  width: '100%',
                  backgroundColor: '#ffffff',
                  padding: '12px 40px 12px 20px',
                  border: '1px solid #d0d0d0',
                  borderRadius: '25px',
                  fontSize: '14px',
                  outline: 'none',
                  color: '#333',
                  boxSizing: 'border-box'
                }}
              />
              <Search
                size={18}
                style={{
                  position: 'absolute',
                  right: '15px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  cursor: 'pointer',
                  color: '#666'
                }}
                onClick={handleSearch}
              />
            </div>
            {filteredCountries !== null && (
              <button
                onClick={clearSearch}
                style={{
                  position: 'absolute',
                  left: '0',
                  padding: '8px 16px',
                  backgroundColor: '#f0f0f0',
                  border: '1px solid #d0d0d0',
                  borderRadius: '20px',
                  fontSize: '13px',
                  cursor: 'pointer',
                  color: '#666',
                  whiteSpace: 'nowrap'
                }}
              >
                초기화 ✕
              </button>
            )}
          </div>
        </div>
      </div>

      <div style={{
        backgroundColor: '#f5faf5',
        borderRadius: '40px',
        padding: '20px 40px 45px',
        minHeight: '85vh',
        display: 'flex',
        gap: '30px'
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
            <div style={{ display: 'flex', gap: '20px' }}>
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
              padding: '20px',
              overflow: 'hidden',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              <InteractiveDottedMap
                width={800}
                height={460}
                dotSpacing={4}
                dotRadius={1.8}
                dotColor="#728C87"
                highlightColor="#4D625E"
                category={category}
                filteredCountries={filteredCountries}
                onCountryClick={handleCountryClick}
              />
            </div>
          </div>
        </div>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          minWidth: '360px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            height: '60px',
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

            onClick={() => {/* 모달 열기 로직 추가 필요 */ }}
            onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(150, 180, 150, 0.25)'}
            onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(150, 180, 150, 0.15)'}
          >
            <p style={{ fontSize: '18px', fontWeight: '600'}}>
              👀
              아직 정보가 없어요!
            </p>
          </div>

          <div style={{
            backgroundColor: '#ffffff',
            height: '60px',
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
            onClick={() => {/* 모달 열기 로직 추가 필요 */ }}
            onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(150, 180, 150, 0.25)'}
            onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(150, 180, 150, 0.15)'}
          >
            <p style={{ fontSize: '18px', fontWeight: '600'}}>
              👀
              아직 정보가 없어요!
            </p>
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

      {isModalOpen && selectedLocation && (
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
                {selectedLocation.name}의 생물 다양성 - {category}
              </h2>
              <p style={{ fontSize: '13px', color: '#7f8d7b', marginBottom: '8px' }}>
                📍 위치: {selectedLocation.lat.toFixed(2)}°, {selectedLocation.lng.toFixed(2)}°
              </p>
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
                {/* 로딩 상태 */}
                {isLoading && <SpeciesCardSkeletonGrid count={3} />}

                {/* 에러 상태 */}
                {!isLoading && error && (
                  <ErrorMessage message={error} onRetry={handleRetry} />
                )}

                {/* 데이터 표시 */}
                {!isLoading && !error && (
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
                          height: '180px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          overflow: 'hidden',
                          background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)'
                        }}>
                          {species.image && species.image.startsWith('http') ? (
                            <img
                              src={species.image}
                              alt={species.name}
                              style={{
                                width: '100%',
                                height: '100%',
                                objectFit: 'cover'
                              }}
                              onError={(e) => {
                                // 이미지 로드 실패 시 회색 배경 표시
                                e.target.style.display = 'none';
                                e.target.parentElement.style.background = '#e5e7eb';
                                e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:48px;color:#9ca3af;">📷</div>`;
                              }}
                            />
                          ) : (
                            <div style={{ fontSize: '64px' }}>{species.image}</div>
                          )}
                        </div>
                        <div style={{ padding: '12px', textAlign: 'center' }}>
                          <p style={{ fontWeight: '500', color: '#1f2937' }}>{species.name}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {/* 페이지네이션 버튼 - 로딩 중이거나 에러일 때는 숨김 */}
                {!isLoading && !error && (
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
                    {speciesPage < totalPages - 1 ? (
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
                )}
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
                  {selectedLocation.name}의 멸종 위기종 목록
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

            {/* 페이지 인디케이터 - 데이터가 있을 때만 표시 */}
            {!isLoading && !error && totalPages > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '8px',
                marginTop: '16px'
              }}>
                {Array.from({ length: totalPages }).map((_, index) => (
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
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;