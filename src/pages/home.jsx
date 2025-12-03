import React, { useState, useEffect } from 'react';
import { X, ChevronRight, Search } from 'lucide-react';
import logoImg from '../assets/logo.png';
import InteractiveDottedMap from '../components/InteractiveDottedMap';
import { categoryThemes, countryNames, endangeredSpeciesCount } from '../data/biodiversityData';
import { fetchSpeciesByCountry, searchSpeciesByName, fetchTrendingSearches, fetchSpeciesDetail } from '../services/api';
import { SpeciesCardSkeletonGrid } from '../components/SpeciesCardSkeleton';
import ErrorMessage from '../components/ErrorMessage';

const HomePage = () => {
  console.log('🏠 HomePage 컴포넌트 초기화 중...');

  const [category, setCategory] = useState('동물');
  const [selectedLocation, setSelectedLocation] = useState(null); // { name, countryCode }
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
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);

  // 실시간 검색어 상태
  const [trendingSearches, setTrendingSearches] = useState([]);

  // 종 상세 정보 모달 상태
  const [selectedSpecies, setSelectedSpecies] = useState(null);
  const [speciesDetail, setSpeciesDetail] = useState(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // API 데이터 사용 (mockData는 제거됨) - 함수 시작 부분으로 이동
  const currentSpeciesData = speciesData || [];

  // 현재 카테고리의 테마
  const theme = categoryThemes[category];

  const categories = ['동물', '식물', '곤충', '해양생물'];
  const categoryIcons = {
    동물: '🦌',
    식물: '🌿',
    곤충: '🐝',
    해양생물: '🐠'
  };

  // 실시간 검색어 로드
  useEffect(() => {
    const loadTrendingSearches = async () => {
      try {
        const result = await fetchTrendingSearches(7, 24);
        setTrendingSearches(result.data || []);
      } catch (error) {
        console.error('❌ 실시간 검색어 로드 실패:', error);
        setTrendingSearches([]);
      }
    };

    loadTrendingSearches();

    // 5분마다 업데이트
    const interval = setInterval(loadTrendingSearches, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 키보드 단축키 (상세 정보 모달에서 ←→ 화살표, ESC)
  useEffect(() => {
    if (!selectedSpecies) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        closeDetailModal();
      } else if (e.key === 'ArrowLeft') {
        goToPreviousSpecies();
      } else if (e.key === 'ArrowRight') {
        goToNextSpecies();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedSpecies, currentSpeciesData]);

  // 위치와 카테고리가 선택되면 API 호출
  useEffect(() => {
    if (!selectedLocation || !isModalOpen || modalView !== 'species') {
      console.log('⏭️ useEffect 스킵:', { selectedLocation, isModalOpen, modalView });
      return;
    }

    const loadSpeciesData = async () => {
      console.log('🔄 loadSpeciesData 시작');
      setIsLoading(true);
      setError(null);

      try {
        // 국가 코드 매핑 없이 직접 전달 (백엔드에서 처리)
        const countryCode = selectedLocation.countryCode;

        if (!countryCode) {
          console.error('⚠️ 국가 코드 없음:', selectedLocation);
          setError('국가 정보를 확인할 수 없습니다.');
          setSpeciesData([]);
          setIsLoading(false);
          return;
        }

        console.log(`📡 API 호출 시작: ${selectedLocation.name} (${countryCode}) - ${category}, 페이지: ${speciesPage + 1}`);

        // ISO 코드 기반 API 호출
        const response = await fetchSpeciesByCountry(
          countryCode,
          category,
          speciesPage + 1,
          3
        );

        console.log('📦 API 응답 받음:', response);
        setSpeciesData(response.data);
        setTotalPages(response.totalPages);
        console.log(`✅ 데이터 로드 성공: ${response.data.length}개 종`);
      } catch (err) {
        console.error('❌ API 호출 실패:', err);
        setError(err.message || '데이터를 불러오는 중 오류가 발생했습니다.');
        setSpeciesData([]);
      } finally {
        setIsLoading(false);
        console.log('🏁 loadSpeciesData 완료');
      }
    };

    loadSpeciesData();
  }, [selectedLocation?.countryCode, category, speciesPage, isModalOpen, modalView]);

  // InteractiveDottedMap 콜백: { name, code } 객체를 받음 (좌표 정보는 제거됨)
  const handleCountryClick = (location) => {
    console.log(`🗺️ 지도 클릭 이벤트 발생!`);
    console.log('받은 location 데이터:', location);
    console.log(`국가: ${location.name}, 코드: ${location.code}`);

    // 국가 정보만 저장하고 모달 열기 (좌표는 실제로 사용하지 않으므로 제거)
    const newLocation = {
      name: location.name,
      countryCode: location.code
    };

    console.log('설정할 selectedLocation:', newLocation);
    setSelectedLocation(newLocation);
    setSpeciesPage(0);
    setModalView('species');
    setIsModalOpen(true);
    console.log('모달 열기 완료');
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

  // 종 카드 클릭 핸들러 - 상세 정보 조회
  const handleSpeciesClick = async (species) => {
    console.log('🔍 종 카드 클릭:', species);
    setSelectedSpecies(species);
    setIsDetailLoading(true);
    setDetailError(null);

    try {
      console.log(`📡 상세 정보 API 호출: ID ${species.id}`);
      const detail = await fetchSpeciesDetail(species.id);
      console.log('✅ 상세 정보 수신:', detail);
      setSpeciesDetail(detail);
    } catch (err) {
      console.error('❌ 상세 정보 조회 실패:', err);
      setDetailError(err.message || '상세 정보를 불러올 수 없습니다.');
    } finally {
      setIsDetailLoading(false);
    }
  };

  // 상세 정보 모달 닫기
  const closeDetailModal = () => {
    setSelectedSpecies(null);
    setSpeciesDetail(null);
    setDetailError(null);
  };

  // 팝업에서 이전 종으로 이동
  const goToPreviousSpecies = () => {
    if (!currentSpeciesData || currentSpeciesData.length === 0) return;

    const currentIndex = currentSpeciesData.findIndex(s => s.id === selectedSpecies.id);
    if (currentIndex > 0) {
      handleSpeciesClick(currentSpeciesData[currentIndex - 1]);
    }
  };

  // 팝업에서 다음 종으로 이동
  const goToNextSpecies = () => {
    if (!currentSpeciesData || currentSpeciesData.length === 0) return;

    const currentIndex = currentSpeciesData.findIndex(s => s.id === selectedSpecies.id);
    if (currentIndex < currentSpeciesData.length - 1) {
      handleSpeciesClick(currentSpeciesData[currentIndex + 1]);
    }
  };

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

  // 실시간 검색어 새로고침 함수
  const refreshTrendingSearches = async () => {
    try {
      const result = await fetchTrendingSearches(7, 24);
      setTrendingSearches(result.data || []);
      console.log('🔄 실시간 검색어 업데이트:', result.data);
    } catch (error) {
      console.error('❌ 실시간 검색어 로드 실패:', error);
    }
  };

  // 검색 처리 함수 (종 이름 기반, 디바운싱 적용)
  const handleSearch = async (query) => {
    console.log('🔍 handleSearch 호출됨:', query);

    if (!query || !query.trim()) {
      console.log('⚠️ 검색어 비어있음');
      // 검색어가 비어있으면 전체 표시
      setFilteredCountries(null);
      return;
    }

    try {
      console.log('📡 API 호출 시작:', query);
      // 백엔드 API를 통해 종 검색 (카테고리 필터 없이 전체 검색)
      const result = await searchSpeciesByName(query, null);
      console.log('✅ API 응답:', result);

      if (result.countries && result.countries.length > 0) {
        console.log(`🎯 ${result.countries.length}개 국가 찾음:`, result.countries);
        setFilteredCountries(result.countries);

        // 매칭된 종의 카테고리로 자동 전환
        if (result.category && result.category !== category) {
          console.log('🔄 카테고리 변경:', category, '->', result.category);
          setCategory(result.category);
        }
      } else {
        console.log('❌ 검색 결과 없음');
        setFilteredCountries([]);
      }

      // 검색 후 즉시 실시간 검색어 새로고침
      await refreshTrendingSearches();
    } catch (error) {
      console.error('❌ 검색 오류:', error);
      setFilteredCountries([]);
    }
  };

  // 디바운스된 검색 (타이핑 후 500ms 대기)
  const handleSearchInput = (value) => {
    setSearchQuery(value);

    // 기존 타이머 취소
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    if (!value.trim()) {
      setFilteredCountries(null);
      return;
    }

    // 새 타이머 설정
    const timer = setTimeout(() => {
      handleSearch(value);
    }, 500);

    setSearchDebounceTimer(timer);
  };

  // Enter 키로 즉시 검색
  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      console.log('⌨️  Enter 키 눌림, 검색 시작:', searchQuery);
      // 디바운스 타이머 취소하고 즉시 검색
      if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
      }
      handleSearch(searchQuery);
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
                onChange={(e) => handleSearchInput(e.target.value)}
                onKeyDown={handleSearchKeyDown}
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
                onClick={() => {
                  console.log('🔎 검색 아이콘 클릭, 검색 시작:', searchQuery);
                  if (searchDebounceTimer) {
                    clearTimeout(searchDebounceTimer);
                  }
                  handleSearch(searchQuery);
                }}
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
                  onClick={() => {
                    setCategory(cat);
                    // 카테고리 변경 시 필터링 초기화
                    setFilteredCountries(null);
                    setSearchQuery('');
                    console.log(`✨ 카테고리 변경: ${cat} (필터링 초기화)`);
                  }}
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
                dotSpacing={5}
                dotRadius={2.0}
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
              {trendingSearches.length > 0 ? (
                trendingSearches.map((item, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '16px 20px',
                      height: `${100 / Math.max(trendingSearches.length, 7)}%`,
                      minHeight: '50px',
                      borderBottom: index !== trendingSearches.length - 1 ? '1px solid #edf3ed' : 'none',
                      fontSize: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      boxSizing: 'border-box'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f8faf8';
                      e.currentTarget.style.transform = 'translateX(4px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                    onClick={async () => {
                      setSearchQuery(item.query);
                      // 검색어 설정 후 약간의 딜레이를 두고 검색 실행
                      setTimeout(async () => {
                        try {
                          const result = await searchSpeciesByName(item.query, null);
                          if (result.countries && result.countries.length > 0) {
                            setFilteredCountries(result.countries);
                            if (result.category && result.category !== category) {
                              setCategory(result.category);
                            }
                          } else {
                            setFilteredCountries([]);
                          }
                          // 클릭 후에도 실시간 검색어 새로고침
                          await refreshTrendingSearches();
                        } catch (error) {
                          console.error('❌ 검색 오류:', error);
                          setFilteredCountries([]);
                        }
                      }, 100);
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <span style={{
                        fontWeight: '700',
                        color: '#4c944a',
                        minWidth: '32px',
                        textAlign: 'center',
                        fontSize: '18px'
                      }}>
                        {String(item.rank).padStart(2, '0')}
                      </span>
                      <span style={{
                        fontWeight: '500',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {item.query}
                      </span>
                    </div>
                    <span style={{
                      fontSize: '13px',
                      color: '#888',
                      fontWeight: '500',
                      minWidth: '50px',
                      textAlign: 'right'
                    }}>
                      {item.count}회
                    </span>
                  </div>
                ))
              ) : (
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '100%',
                  color: '#888',
                  fontSize: '14px'
                }}>
                  검색 기록이 없습니다
                </div>
              )}
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
                        onClick={() => handleSpeciesClick(species)}
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
                                // 이미지 로드 실패 시 동물 이모지 표시
                                e.target.style.display = 'none';
                                e.target.parentElement.style.background = 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)';
                                e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:64px;">🦌</div>`;
                              }}
                            />
                          ) : (
                            <div style={{ fontSize: '64px' }}>🦌</div>
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

      {/* 종 상세 정보 모달 */}
      {selectedSpecies && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 2000,
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '24px',
            maxWidth: '800px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto',
            position: 'relative',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
          }}>
            {/* 닫기 버튼 */}
            <button
              onClick={closeDetailModal}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: 'rgba(255, 255, 255, 0.9)',
                border: 'none',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                zIndex: 10
              }}
            >
              <X size={24} color="#333" />
            </button>

            {/* 로딩 상태 */}
            {isDetailLoading && (
              <div style={{
                padding: '60px 40px',
                textAlign: 'center'
              }}>
                <div style={{
                  display: 'inline-block',
                  width: '60px',
                  height: '60px',
                  border: '4px solid #f3f4f6',
                  borderTopColor: theme.button.includes('green') ? '#bbf7d0' :
                    theme.button.includes('amber') ? '#D8CFBD' :
                      theme.button.includes('yellow') ? '#FFECB2' : '#CCE0F3',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                <p style={{ marginTop: '20px', color: '#6b7280', fontSize: '16px' }}>
                  상세 정보를 불러오는 중...
                </p>
              </div>
            )}

            {/* 에러 상태 */}
            {!isDetailLoading && detailError && (
              <div style={{
                padding: '60px 40px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
                <p style={{ color: '#ef4444', fontSize: '16px', marginBottom: '20px' }}>
                  {detailError}
                </p>
                <button
                  onClick={() => handleSpeciesClick(selectedSpecies)}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '20px',
                    border: 'none',
                    backgroundColor: theme.button.includes('green') ? '#bbf7d0' :
                      theme.button.includes('amber') ? '#D8CFBD' :
                        theme.button.includes('yellow') ? '#FFECB2' : '#CCE0F3',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  다시 시도
                </button>
              </div>
            )}

            {/* 상세 정보 표시 */}
            {!isDetailLoading && !detailError && speciesDetail && (
              <div>
                {/* 이미지 섹션 */}
                <div style={{
                  height: '400px',
                  position: 'relative',
                  overflow: 'hidden',
                  borderRadius: '24px 24px 0 0',
                  background: 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)'
                }}>
                  {speciesDetail.image && speciesDetail.image.startsWith('http') ? (
                    <img
                      src={speciesDetail.image}
                      alt={speciesDetail.name}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover'
                      }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.style.background = 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)';
                        e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:120px;">🦌</div>`;
                      }}
                    />
                  ) : (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: '100%',
                      fontSize: '120px'
                    }}>
                      🦌
                    </div>
                  )}
                </div>

                {/* 내용 섹션 */}
                <div style={{ padding: '32px 40px' }}>
                  {/* 제목 및 기본 정보 */}
                  <div style={{ marginBottom: '24px' }}>
                    <h2 style={{
                      fontSize: '32px',
                      fontWeight: '700',
                      color: '#1f2937',
                      marginBottom: '8px'
                    }}>
                      {speciesDetail.commonName || speciesDetail.name}
                    </h2>
                    <p style={{
                      fontSize: '18px',
                      color: '#6b7280',
                      fontStyle: 'italic',
                      marginBottom: '16px'
                    }}>
                      {speciesDetail.scientificName}
                    </p>

                    {/* 보전 상태 배지 */}
                    {speciesDetail.status && (
                      <div style={{
                        display: 'inline-block',
                        padding: '8px 16px',
                        borderRadius: '12px',
                        backgroundColor:
                          speciesDetail.status === 'CR' ? '#fee2e2' :
                          speciesDetail.status === 'EN' ? '#fed7aa' :
                          speciesDetail.status === 'VU' ? '#fef3c7' :
                          '#dbeafe',
                        color:
                          speciesDetail.status === 'CR' ? '#991b1b' :
                          speciesDetail.status === 'EN' ? '#9a3412' :
                          speciesDetail.status === 'VU' ? '#854d0e' :
                          '#1e40af',
                        fontSize: '14px',
                        fontWeight: '600'
                      }}>
                        {speciesDetail.status === 'CR' ? '심각한 멸종위기 (CR)' :
                         speciesDetail.status === 'EN' ? '멸종위기 (EN)' :
                         speciesDetail.status === 'VU' ? '취약 (VU)' :
                         speciesDetail.status === 'NT' ? '준위협 (NT)' :
                         speciesDetail.status === 'LC' ? '관심대상 (LC)' :
                         speciesDetail.status}
                      </div>
                    )}
                  </div>

                  {/* 설명 */}
                  {speciesDetail.description && (
                    <div style={{ marginBottom: '24px' }}>
                      <h3 style={{
                        fontSize: '20px',
                        fontWeight: '600',
                        color: '#374151',
                        marginBottom: '12px'
                      }}>
                        개요
                      </h3>
                      <p style={{
                        fontSize: '16px',
                        color: '#4b5563',
                        lineHeight: '1.8'
                      }}>
                        {speciesDetail.description}
                      </p>
                    </div>
                  )}

                  {/* 추가 정보 그리드 */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '16px',
                    marginTop: '24px'
                  }}>
                    {speciesDetail.population && (
                      <div style={{
                        padding: '16px',
                        backgroundColor: '#f9fafb',
                        borderRadius: '12px'
                      }}>
                        <div style={{
                          fontSize: '14px',
                          color: '#6b7280',
                          marginBottom: '4px'
                        }}>
                          개체수
                        </div>
                        <div style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#1f2937'
                        }}>
                          {speciesDetail.population}
                        </div>
                      </div>
                    )}

                    {speciesDetail.habitat && (
                      <div style={{
                        padding: '16px',
                        backgroundColor: '#f9fafb',
                        borderRadius: '12px'
                      }}>
                        <div style={{
                          fontSize: '14px',
                          color: '#6b7280',
                          marginBottom: '4px'
                        }}>
                          서식지
                        </div>
                        <div style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#1f2937'
                        }}>
                          {speciesDetail.habitat}
                        </div>
                      </div>
                    )}

                    {speciesDetail.category && (
                      <div style={{
                        padding: '16px',
                        backgroundColor: '#f9fafb',
                        borderRadius: '12px'
                      }}>
                        <div style={{
                          fontSize: '14px',
                          color: '#6b7280',
                          marginBottom: '4px'
                        }}>
                          카테고리
                        </div>
                        <div style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#1f2937'
                        }}>
                          {speciesDetail.category}
                        </div>
                      </div>
                    )}

                    {speciesDetail.country && (
                      <div style={{
                        padding: '16px',
                        backgroundColor: '#f9fafb',
                        borderRadius: '12px'
                      }}>
                        <div style={{
                          fontSize: '14px',
                          color: '#6b7280',
                          marginBottom: '4px'
                        }}>
                          지역
                        </div>
                        <div style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#1f2937'
                        }}>
                          {speciesDetail.country}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 위협 요인 */}
                  {speciesDetail.threats && speciesDetail.threats.length > 0 && (
                    <div style={{ marginTop: '24px' }}>
                      <h3 style={{
                        fontSize: '20px',
                        fontWeight: '600',
                        color: '#374151',
                        marginBottom: '12px'
                      }}>
                        위협 요인
                      </h3>
                      <ul style={{
                        listStyle: 'none',
                        padding: 0,
                        margin: 0
                      }}>
                        {speciesDetail.threats.map((threat, index) => (
                          <li key={index} style={{
                            padding: '12px 16px',
                            backgroundColor: '#fef2f2',
                            borderRadius: '8px',
                            marginBottom: '8px',
                            fontSize: '15px',
                            color: '#991b1b'
                          }}>
                            ⚠️ {threat}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 네비게이션 버튼 */}
                  {currentSpeciesData && currentSpeciesData.length > 1 && (
                    <div style={{
                      marginTop: '32px',
                      paddingTop: '24px',
                      borderTop: '1px solid #e5e7eb',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      {/* 이전 버튼 */}
                      {currentSpeciesData.findIndex(s => s.id === selectedSpecies.id) > 0 ? (
                        <button
                          onClick={goToPreviousSpecies}
                          style={{
                            padding: '12px 24px',
                            borderRadius: '12px',
                            border: '2px solid #e5e7eb',
                            backgroundColor: '#ffffff',
                            cursor: 'pointer',
                            fontSize: '15px',
                            fontWeight: '600',
                            color: '#374151',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = '#f9fafb';
                            e.target.style.borderColor = '#9ca3af';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = '#ffffff';
                            e.target.style.borderColor = '#e5e7eb';
                          }}
                        >
                          <ChevronRight style={{ width: '20px', height: '20px', transform: 'rotate(180deg)' }} />
                          이전 종
                        </button>
                      ) : (
                        <div style={{ width: '120px' }}></div>
                      )}

                      {/* 현재 위치 표시 */}
                      <div style={{
                        fontSize: '14px',
                        color: '#6b7280',
                        fontWeight: '500'
                      }}>
                        {currentSpeciesData.findIndex(s => s.id === selectedSpecies.id) + 1} / {currentSpeciesData.length}
                      </div>

                      {/* 다음 버튼 */}
                      {currentSpeciesData.findIndex(s => s.id === selectedSpecies.id) < currentSpeciesData.length - 1 ? (
                        <button
                          onClick={goToNextSpecies}
                          style={{
                            padding: '12px 24px',
                            borderRadius: '12px',
                            border: '2px solid #e5e7eb',
                            backgroundColor: '#ffffff',
                            cursor: 'pointer',
                            fontSize: '15px',
                            fontWeight: '600',
                            color: '#374151',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = '#f9fafb';
                            e.target.style.borderColor = '#9ca3af';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = '#ffffff';
                            e.target.style.borderColor = '#e5e7eb';
                          }}
                        >
                          다음 종
                          <ChevronRight style={{ width: '20px', height: '20px' }} />
                        </button>
                      ) : (
                        <div style={{ width: '120px' }}></div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;