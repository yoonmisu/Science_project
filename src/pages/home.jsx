import React, { useState, useEffect } from 'react';
import { X, ChevronRight, Search } from 'lucide-react';
import logoImg from '../assets/logo.png';
import InteractiveDottedMap from '../components/InteractiveDottedMap';
import { categoryThemes, countryNames, updateSpeciesCount, resetColorStats } from '../data/biodiversityData';
import { fetchSpeciesByCountry, searchSpeciesByName, fetchTrendingSearches, fetchSpeciesDetail, fetchAllCountriesSpeciesCount, fetchDailyRandomSpecies, fetchWeeklyTopSpecies } from '../services/api';
import { SpeciesCardSkeletonGrid } from '../components/SpeciesCardSkeleton';
import ErrorMessage from '../components/ErrorMessage';

const getBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage || 'en';
  const langCode = browserLang.split('-')[0].toLowerCase();
  const supportedLanguages = ['ko', 'en', 'ja', 'zh', 'es', 'fr', 'de', 'pt', 'ru', 'it', 'vi', 'th', 'id'];
  return supportedLanguages.includes(langCode) ? langCode : 'en';
};

const HomePage = () => {

  const [category, setCategory] = useState('동물');
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalView, setModalView] = useState('species');
  const [speciesPage, setSpeciesPage] = useState(0);

  const [speciesData, setSpeciesData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [totalPages, setTotalPages] = useState(0);

  const [searchQuery, setSearchQuery] = useState('');
  const [filteredCountries, setFilteredCountries] = useState(null);
  const [searchedSpeciesName, setSearchedSpeciesName] = useState(null);
  const [trendingSearches, setTrendingSearches] = useState([]);

  const [selectedSpecies, setSelectedSpecies] = useState(null);
  const [speciesDetail, setSpeciesDetail] = useState(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  const [endangeredData, setEndangeredData] = useState(null);
  const [isEndangeredLoading, setIsEndangeredLoading] = useState(false);
  const [endangeredError, setEndangeredError] = useState(null);
  const [endangeredFilter, setEndangeredFilter] = useState(null);

  const [mapDataVersion, setMapDataVersion] = useState(0);
  const [isMapDataLoaded, setIsMapDataLoaded] = useState(false);

  const [dailyRandomSpecies, setDailyRandomSpecies] = useState(null);
  const [weeklyTopSpecies, setWeeklyTopSpecies] = useState(null);

  const currentSpeciesData = speciesData || [];
  const theme = categoryThemes[category];

  const categories = ['동물', '식물', '곤충', '해양생물'];
  const categoryIcons = {
    동물: '🦌',
    식물: '🌿',
    곤충: '🐝',
    해양생물: '🐠'
  };

  useEffect(() => {
    const loadTrendingSearches = async () => {
      try {
        const result = await fetchTrendingSearches(7, 24);
        setTrendingSearches(result.data || []);
      } catch (error) {
        setTrendingSearches([]);
      }
    };

    loadTrendingSearches();
    const interval = setInterval(loadTrendingSearches, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const loadDailyAndWeeklySpecies = async () => {
      try {
        const [dailyResult, weeklyResult] = await Promise.all([
          fetchDailyRandomSpecies(),
          fetchWeeklyTopSpecies()
        ]);
        if (dailyResult) setDailyRandomSpecies(dailyResult);
        if (weeklyResult) setWeeklyTopSpecies(weeklyResult);
      } catch (error) {}
    };
    loadDailyAndWeeklySpecies();
  }, []);

  useEffect(() => {
    const loadAllCountriesSpeciesCount = async () => {
      try {
        setIsMapDataLoaded(false);
        const countryCounts = await fetchAllCountriesSpeciesCount(category);
        updateSpeciesCount(countryCounts, category);
        setIsMapDataLoaded(true);
        setMapDataVersion(v => v + 1);
      } catch (error) {
        setIsMapDataLoaded(true);
      }
    };
    resetColorStats();
    loadAllCountriesSpeciesCount();
  }, [category]);

  useEffect(() => {
    if (!selectedSpecies) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') closeDetailModal();
      else if (e.key === 'ArrowLeft') goToPreviousSpecies();
      else if (e.key === 'ArrowRight') goToNextSpecies();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedSpecies, currentSpeciesData]);

  useEffect(() => {
    if (!selectedLocation || !isModalOpen || modalView !== 'species') return;

    const loadSpeciesData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const countryCode = selectedLocation.countryCode;
        if (!countryCode) {
          setError('국가 정보를 확인할 수 없습니다.');
          setSpeciesData([]);
          setIsLoading(false);
          return;
        }
        const response = await fetchSpeciesByCountry(countryCode, category, speciesPage + 1, 3, searchedSpeciesName);
        setSpeciesData(response.data);
        setTotalPages(response.totalPages);
      } catch (err) {
        setError(err.message || '데이터를 불러오는 중 오류가 발생했습니다.');
        setSpeciesData([]);
      } finally {
        setIsLoading(false);
      }
    };
    loadSpeciesData();
  }, [selectedLocation?.countryCode, category, speciesPage, isModalOpen, modalView, searchedSpeciesName]);

  const handleCountryClick = (location) => {
    setSelectedLocation({ name: location.name, countryCode: location.code?.toUpperCase() });
    setSpeciesPage(0);
    setModalView('species');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedLocation(null);
  };

  const goToEndangeredView = async () => {
    setModalView('endangered');
    setIsEndangeredLoading(true);
    setEndangeredError(null);
    setEndangeredData(null);
    setEndangeredFilter(null);

    const categories = ['동물', '식물', '곤충', '해양생물'];
    const categoryIcons = { '동물': '🦌', '식물': '🌿', '곤충': '🐝', '해양생물': '🐠' };

    try {
      const results = await Promise.all(
        categories.map(async (cat) => {
          try {
            const response = await fetchSpeciesByCountry(selectedLocation.countryCode, cat, 1, 30);
            return { category: cat, icon: categoryIcons[cat], species: response.data || [], total: response.total || 0 };
          } catch (err) {
            return { category: cat, icon: categoryIcons[cat], species: [], total: 0 };
          }
        })
      );
      setEndangeredData(results);
    } catch (err) {
      setEndangeredError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsEndangeredLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    setSpeciesPage(0);
  };

  const handleSpeciesClick = async (species) => {
    setSelectedSpecies(species);
    setIsDetailLoading(true);
    setDetailError(null);
    setSpeciesDetail(null);

    try {
      const userLang = getBrowserLanguage();
      const scientificName = species.scientificName || species.scientific_name || null;
      const detail = await fetchSpeciesDetail(species.id, userLang, scientificName);
      setSpeciesDetail(detail);
      try {
        const updatedWeekly = await fetchWeeklyTopSpecies();
        if (updatedWeekly && updatedWeekly.taxonId) setWeeklyTopSpecies(updatedWeekly);
      } catch (weeklyErr) {}
    } catch (err) {
      setDetailError(err.message || '상세 정보를 불러올 수 없습니다.');
    } finally {
      setIsDetailLoading(false);
    }
  };

  const closeDetailModal = () => {
    setSelectedSpecies(null);
    setSpeciesDetail(null);
    setDetailError(null);
  };

  const goToPreviousSpecies = () => {
    if (!currentSpeciesData || currentSpeciesData.length === 0) return;
    const currentIndex = currentSpeciesData.findIndex(s => s.id === selectedSpecies.id);
    if (currentIndex > 0) handleSpeciesClick(currentSpeciesData[currentIndex - 1]);
  };

  const goToNextSpecies = () => {
    if (!currentSpeciesData || currentSpeciesData.length === 0) return;
    const currentIndex = currentSpeciesData.findIndex(s => s.id === selectedSpecies.id);
    if (currentIndex < currentSpeciesData.length - 1) handleSpeciesClick(currentSpeciesData[currentIndex + 1]);
  };

  const handleNextPage = () => {
    if (speciesPage < totalPages - 1) setSpeciesPage((prev) => prev + 1);
  };

  const handlePrevPage = () => {
    if (speciesPage > 0) setSpeciesPage((prev) => prev - 1);
  };

  const refreshTrendingSearches = async () => {
    try {
      const result = await fetchTrendingSearches(7, 24);
      setTrendingSearches(result.data || []);
    } catch (error) {}
  };

  const handleSearch = async (query) => {
    if (!query || !query.trim()) {
      setFilteredCountries(null);
      setSearchedSpeciesName(null);
      try {
        const countryCounts = await fetchAllCountriesSpeciesCount(category);
        updateSpeciesCount(countryCounts, category);
        setMapDataVersion(v => v + 1);
      } catch (error) {}
      return;
    }

    try {
      const result = await searchSpeciesByName(query, null);
      if (result.countries && result.countries.length > 0) {
        const targetCategory = result.category || category;
        if (result.category && result.category !== category) setCategory(result.category);
        setFilteredCountries(result.countries);
        setSearchedSpeciesName(result.matchedScientificName || result.matchedSpecies);
        const searchResultCounts = {};
        result.countries.forEach(countryCode => { searchResultCounts[countryCode] = 1; });
        updateSpeciesCount(searchResultCounts, targetCategory);
        setMapDataVersion(v => v + 1);
      } else {
        setFilteredCountries([]);
        setSearchedSpeciesName(null);
      }
      await refreshTrendingSearches();
    } catch (error) {
      setFilteredCountries([]);
      setSearchedSpeciesName(null);
    }
  };

  const handleSearchInput = (value) => {
    setSearchQuery(value);
    if (!value.trim()) {
      setFilteredCountries(null);
      setSearchedSpeciesName(null);
    }
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch(searchQuery);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setFilteredCountries(null);
    setSearchedSpeciesName(null);
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
                onClick={() => handleSearch(searchQuery)}
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
                    setFilteredCountries(null);
                    setSearchQuery('');
                    setSearchedSpeciesName(null);
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
              marginBottom: '30px'
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
                key={`map-${category}`}
                width={800}
                height={460}
                dotSpacing={5}
                dotRadius={2.0}
                dotColor="#728C87"
                highlightColor="#4D625E"
                category={category}
                filteredCountries={filteredCountries}
                dataVersion={mapDataVersion}
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
            borderRadius: '25px',
            boxShadow: '0 2px 8px rgba(150, 180, 150, 0.15)',
            padding: '16px 20px',
            cursor: 'pointer',
            transition: 'box-shadow 0.3s',
          }}
            onClick={() => {
              if (dailyRandomSpecies?.taxonId) {
                // taxon_id가 있으면 상세 팝업으로 바로 연결
                handleSpeciesClick({
                  id: dailyRandomSpecies.taxonId,
                  name: dailyRandomSpecies.koreanName || dailyRandomSpecies.commonName || dailyRandomSpecies.scientificName,
                  scientific_name: dailyRandomSpecies.scientificName,
                  category: dailyRandomSpecies.category
                });
              } else if (dailyRandomSpecies?.scientificName) {
                // taxon_id가 없으면 검색 (fallback)
                handleSearch(dailyRandomSpecies.scientificName);
              }
            }}
            onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(150, 180, 150, 0.25)'}
            onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(150, 180, 150, 0.15)'}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>🎲</span>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>오늘의 생물</p>
                {dailyRandomSpecies ? (
                  <p style={{ fontSize: '16px', fontWeight: '600', color: '#2f6b2d' }}>
                    {dailyRandomSpecies.koreanName || dailyRandomSpecies.commonName || dailyRandomSpecies.scientificName}
                  </p>
                ) : (
                  <p style={{ fontSize: '14px', color: '#aaa' }}>로딩 중...</p>
                )}
              </div>
              <ChevronRight size={20} color="#888" />
            </div>
          </div>

          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '25px',
            boxShadow: '0 2px 8px rgba(150, 180, 150, 0.15)',
            padding: '16px 20px',
            cursor: 'pointer',
            transition: 'box-shadow 0.3s',
          }}
            onClick={() => {
              if (weeklyTopSpecies?.taxonId) {
                // taxon_id가 있으면 상세 팝업으로 바로 연결
                handleSpeciesClick({
                  id: weeklyTopSpecies.taxonId,
                  name: weeklyTopSpecies.speciesName,
                  scientific_name: weeklyTopSpecies.scientificName,
                  category: weeklyTopSpecies.category
                });
              } else if (weeklyTopSpecies?.speciesName) {
                // taxon_id가 없으면 검색 (fallback)
                handleSearch(weeklyTopSpecies.speciesName);
              }
            }}
            onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(150, 180, 150, 0.25)'}
            onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(150, 180, 150, 0.15)'}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '24px' }}>🔥</span>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>주간 인기 생물</p>
                {weeklyTopSpecies ? (
                  <div>
                    <p style={{ fontSize: '16px', fontWeight: '600', color: '#2f6b2d' }}>
                      {weeklyTopSpecies.speciesName}
                    </p>
                  </div>
                ) : (
                  <p style={{ fontSize: '14px', color: '#aaa' }}>로딩 중...</p>
                )}
              </div>
              <ChevronRight size={20} color="#888" />
            </div>
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
                            // 검색된 종의 카테고리 결정
                            const targetCategory = result.category || category;

                            if (result.category && result.category !== category) {
                              setCategory(result.category);
                            }

                            // 필터링된 국가들 설정
                            setFilteredCountries(result.countries);

                            // 검색된 종의 학명 저장 (국가 클릭 시 해당 종만 표시하기 위해)
                            setSearchedSpeciesName(result.matchedScientificName || result.matchedSpecies);

                            // 필터링된 국가들의 실제 종 개수 업데이트 (새 카테고리에 맞게)
                            const searchResultCounts = {};
                            result.countries.forEach(countryCode => {
                              searchResultCounts[countryCode] = 1;
                            });
                            updateSpeciesCount(searchResultCounts, targetCategory);

                            // 지도 재렌더링 트리거
                            setMapDataVersion(v => v + 1);
                          } else {
                            setFilteredCountries([]);
                            setSearchedSpeciesName(null);
                          }
                          await refreshTrendingSearches();
                        } catch (error) {
                          setFilteredCountries([]);
                          setSearchedSpeciesName(null);
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
                {selectedLocation.name}의 {searchedSpeciesName ? `"${searchQuery}" 검색 결과` : `생물 다양성 - ${category}`}
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
                {isLoading && <SpeciesCardSkeletonGrid count={3} />}

                {!isLoading && error && (
                  <ErrorMessage message={error} onRetry={handleRetry} />
                )}

                {!isLoading && !error && currentSpeciesData.length === 0 && (
                  <div style={{
                    textAlign: 'center',
                    padding: '60px 20px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '16px',
                    marginBottom: '24px'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
                    <p style={{ fontSize: '18px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
                      해당 카테고리의 데이터가 없습니다
                    </p>
                    <p style={{ fontSize: '14px', color: '#6b7280' }}>
                      다른 카테고리를 선택하거나 다른 국가를 선택해보세요
                    </p>
                  </div>
                )}

                {!isLoading && !error && currentSpeciesData.length > 0 && (
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
                                // 이미지 로드 실패 시 동물 이모지 표시 + 안내 메시지
                                e.target.style.display = 'none';
                                e.target.parentElement.style.background = 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)';
                                e.target.parentElement.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;"><div style="font-size:48px;">🦌</div><span style="font-size:11px;color:#9ca3af;margin-top:4px;">이미지 없음</span></div>`;
                              }}
                            />
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                              <div style={{ fontSize: '48px' }}>🦌</div>
                              <span style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>이미지 없음</span>
                            </div>
                          )}
                        </div>
                        <div style={{ padding: '12px', textAlign: 'center' }}>
                          <p style={{ fontWeight: '500', color: '#1f2937' }}>{species.name}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
                minHeight: '300px',
                backgroundColor: '#fefcfa',
                borderRadius: '15px',
                padding: '20px'
              }}>
                {/* 헤더 */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '20px'
                }}>
                  <h3 style={{
                    color: '#374151',
                    fontSize: '18px',
                    fontWeight: '600',
                    margin: 0
                  }}>
                    {selectedLocation.name}의 멸종위기종 카테고리별 현황
                  </h3>
                  <button
                    onClick={() => setModalView('species')}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '20px',
                      border: '1px solid #d1d5db',
                      backgroundColor: '#fff',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '500',
                      transition: 'background 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = '#fff'}
                  >
                    목록으로 돌아가기
                  </button>
                </div>

                {/* 로딩 상태 */}
                {isEndangeredLoading && (
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '60px 20px'
                  }}>
                    <div style={{
                      width: '40px',
                      height: '40px',
                      border: '3px solid #e5e7eb',
                      borderTop: '3px solid #10b981',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                    <p style={{ marginTop: '16px', color: '#6b7280' }}>카테고리별 데이터 로딩 중...</p>
                    <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                  </div>
                )}

                {/* 에러 상태 */}
                {endangeredError && (
                  <div style={{
                    textAlign: 'center',
                    padding: '40px 20px',
                    color: '#ef4444'
                  }}>
                    <p>{endangeredError}</p>
                    <button
                      onClick={goToEndangeredView}
                      style={{
                        marginTop: '12px',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        backgroundColor: '#ef4444',
                        color: '#fff',
                        cursor: 'pointer'
                      }}
                    >
                      다시 시도
                    </button>
                  </div>
                )}

                {/* 카테고리별 그룹화된 리스트 - 테이블 형식 */}
                {!isEndangeredLoading && !endangeredError && endangeredData && (
                  <>
                    {/* 전체 통계 요약 - 상단 (클릭하여 필터링) - 스크롤 영역 밖 */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: '12px',
                      marginBottom: '16px',
                      padding: '4px'
                    }}>
                      {endangeredData.map((categoryData) => (
                        <div
                          key={categoryData.category}
                          onClick={() => setEndangeredFilter(
                            endangeredFilter === categoryData.category ? null : categoryData.category
                          )}
                          style={{
                            padding: '16px',
                            borderRadius: '12px',
                            textAlign: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            border: endangeredFilter === categoryData.category ? '2px solid #3b82f6' : '2px solid transparent',
                            backgroundColor: categoryData.category === '동물' ? '#dcfce7' :
                              categoryData.category === '식물' ? '#d1fae5' :
                                categoryData.category === '곤충' ? '#fef3c7' : '#dbeafe',
                            transform: endangeredFilter === categoryData.category ? 'scale(1.02)' : 'scale(1)',
                            boxShadow: endangeredFilter === categoryData.category ? '0 4px 12px rgba(59, 130, 246, 0.3)' : 'none'
                          }}
                        >
                          <div style={{ fontSize: '28px', marginBottom: '4px' }}>{categoryData.icon}</div>
                          <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '2px' }}>{categoryData.category}</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#374151' }}>{categoryData.species.length}종</div>
                          {endangeredFilter === categoryData.category && (
                            <div style={{ fontSize: '10px', color: '#3b82f6', marginTop: '4px' }}>필터 적용중</div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* 테이블 영역 - 스크롤 가능 */}
                    <div style={{
                      maxHeight: '280px',
                      overflowY: 'auto'
                    }}>
                    {/* 테이블 헤더 */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '80px 2fr 1fr 80px 60px',
                      gap: '8px',
                      padding: '12px 16px',
                      backgroundColor: '#f3f4f6',
                      borderRadius: '8px 8px 0 0',
                      fontWeight: '600',
                      fontSize: '13px',
                      color: '#6b7280'
                    }}>
                      <div>카테고리</div>
                      <div>종 이름</div>
                      <div>학명</div>
                      <div style={{ textAlign: 'center' }}>위험등급</div>
                      <div></div>
                    </div>

                    {/* 테이블 바디 */}
                    <div style={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderTop: 'none',
                      borderRadius: '0 0 8px 8px'
                    }}>
                      {endangeredData
                        .filter((categoryData) => !endangeredFilter || categoryData.category === endangeredFilter)
                        .flatMap((categoryData) =>
                        categoryData.species.map((species, idx) => (
                          <div
                            key={`${categoryData.category}-${species.id || idx}`}
                            onClick={() => handleSpeciesClick(species)}
                            style={{
                              display: 'grid',
                              gridTemplateColumns: '80px 2fr 1fr 80px 60px',
                              gap: '8px',
                              padding: '12px 16px',
                              alignItems: 'center',
                              cursor: 'pointer',
                              borderBottom: '1px solid #f3f4f6',
                              transition: 'background 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                          >
                            {/* 카테고리 */}
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <span style={{ fontSize: '16px' }}>{categoryData.icon}</span>
                              <span style={{
                                fontSize: '11px',
                                color: '#6b7280',
                                display: 'none'
                              }}>
                                {categoryData.category}
                              </span>
                            </div>

                            {/* 종 이름 + 이미지 */}
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '10px'
                            }}>
                              <div style={{
                                width: '36px',
                                height: '36px',
                                borderRadius: '6px',
                                overflow: 'hidden',
                                flexShrink: 0,
                                backgroundColor: '#f3f4f6',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
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
                                      e.target.style.display = 'none';
                                      e.target.parentElement.innerHTML = '<span style="font-size: 14px;">🌱</span>';
                                    }}
                                  />
                                ) : (
                                  <span style={{ fontSize: '14px' }}>{species.image || '🌱'}</span>
                                )}
                              </div>
                              <span style={{
                                fontSize: '14px',
                                fontWeight: '500',
                                color: '#1f2937',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis'
                              }}>
                                {species.name}
                              </span>
                            </div>

                            {/* 학명 */}
                            <div style={{
                              fontSize: '13px',
                              color: '#9ca3af',
                              fontStyle: 'italic',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}>
                              {species.scientificName}
                            </div>

                            {/* 위험등급 */}
                            <div style={{ textAlign: 'center' }}>
                              {species.riskLevel ? (
                                <span style={{
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  padding: '4px 10px',
                                  borderRadius: '4px',
                                  backgroundColor:
                                    species.riskLevel === 'CR' ? '#fecaca' :
                                      species.riskLevel === 'EN' ? '#fed7aa' :
                                        species.riskLevel === 'VU' ? '#fef08a' :
                                          species.riskLevel === 'NT' ? '#bbf7d0' : '#e5e7eb',
                                  color:
                                    species.riskLevel === 'CR' ? '#991b1b' :
                                      species.riskLevel === 'EN' ? '#9a3412' :
                                        species.riskLevel === 'VU' ? '#854d0e' :
                                          species.riskLevel === 'NT' ? '#166534' : '#374151'
                                }}>
                                  {species.riskLevel}
                                </span>
                              ) : (
                                <span style={{ color: '#d1d5db' }}>-</span>
                              )}
                            </div>

                            {/* 화살표 */}
                            <div style={{ textAlign: 'center' }}>
                              <ChevronRight style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                            </div>
                          </div>
                        ))
                      )}

                      {/* 데이터 없음 */}
                      {endangeredData.every(cat => cat.species.length === 0) && (
                        <div style={{
                          padding: '40px',
                          textAlign: 'center',
                          color: '#9ca3af'
                        }}>
                          등록된 멸종위기종 데이터가 없습니다
                        </div>
                      )}
                    </div>
                    </div>

                    {/* 총계 */}
                    <div style={{
                      marginTop: '16px',
                      padding: '14px',
                      backgroundColor: '#f9fafb',
                      borderRadius: '8px',
                      textAlign: 'center'
                    }}>
                      <span style={{ color: '#6b7280', fontSize: '14px' }}>
                        총 <strong style={{ color: '#374151', fontSize: '16px' }}>
                          {endangeredData.reduce((sum, cat) => sum + cat.species.length, 0)}
                        </strong>종의 멸종위기종이 표시됩니다
                      </span>
                    </div>
                  </>
                )}
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
                        e.target.parentElement.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;"><div style="font-size:80px;">🦌</div><span style="font-size:14px;color:#9ca3af;margin-top:8px;">이미지를 불러오지 못했습니다</span></div>`;
                      }}
                    />
                  ) : (
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: '100%'
                    }}>
                      <div style={{ fontSize: '80px' }}>🦌</div>
                      <span style={{ fontSize: '14px', color: '#9ca3af', marginTop: '8px' }}>이미지를 불러오지 못했습니다</span>
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