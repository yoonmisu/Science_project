// 통합 생물다양성 서비스
// IUCN + Wikipedia + Gemini AI를 결합하여 멸종위기종 데이터 제공

import { getEndangeredSpeciesByCountry, getSpeciesDetails, getSpeciesThreats, IUCN_CATEGORIES } from './iucnApi';
import { getWikipediaSummary, getWikipediaFullContent } from './wikipediaApi';
import { summarizeText, generateSpeciesDescription, generateConservationActions } from './geminiApi';

/**
 * 국가별 멸종위기종 데이터 조회 (모든 API 통합)
 * @param {string} countryCode - ISO-2 국가 코드 (예: 'KR', 'US')
 * @param {Object} options - 옵션 { limit: 10, category: 'all' }
 * @returns {Promise<Object>} 통합된 멸종위기종 데이터
 */
export const getEnrichedEndangeredSpecies = async (countryCode, options = {}) => {
  const { limit = 10, category = 'all' } = options;

  try {
    // 1단계: IUCN에서 멸종위기종 목록 가져오기
    console.log(`📊 ${countryCode} 국가의 멸종위기종 데이터 조회 중...`);
    const iucnData = await getEndangeredSpeciesByCountry(countryCode);

    if (iucnData.error || iucnData.species.length === 0) {
      console.warn(`⚠️ IUCN 데이터 없음: ${countryCode}`);
      return {
        countryCode,
        total: 0,
        species: [],
        error: iucnData.error || '데이터를 찾을 수 없습니다.'
      };
    }

    // 카테고리 필터링
    let filteredSpecies = iucnData.species;
    if (category !== 'all') {
      filteredSpecies = filteredSpecies.filter(s => s.category === category);
    }

    // 제한된 수만큼만 처리
    const speciesSubset = filteredSpecies.slice(0, limit);

    console.log(`✅ ${speciesSubset.length}개 종 발견. 상세 정보 수집 중...`);

    // 2단계: 각 종에 대해 Wikipedia + Gemini 데이터 추가
    const enrichedSpecies = await Promise.all(
      speciesSubset.map(async (species) => {
        try {
          // Wikipedia 정보 가져오기
          const wikiData = await getWikipediaSummary(
            species.scientific_name || species.main_common_name
          );

          // Gemini AI로 요약 생성
          let aiSummary = null;
          if (wikiData?.extract) {
            aiSummary = await summarizeText(wikiData.extract, 150);
          }

          // IUCN 위협 요인 가져오기
          const threats = await getSpeciesThreats(species.scientific_name);

          // Gemini AI로 보호 활동 제안 생성
          const conservationActions = await generateConservationActions({
            scientificName: species.scientific_name,
            commonName: species.main_common_name,
            threats: threats.map(t => t.title)
          });

          return {
            // IUCN 기본 정보
            id: species.taxonid,
            scientificName: species.scientific_name,
            commonName: species.main_common_name,
            category: species.category,
            categoryInfo: IUCN_CATEGORIES[species.category],

            // Wikipedia 정보
            wikipedia: wikiData ? {
              summary: wikiData.extract,
              thumbnail: wikiData.thumbnail,
              title: wikiData.title
            } : null,

            // AI 생성 정보
            aiSummary: aiSummary,
            conservationActions: conservationActions,

            // 위협 요인
            threats: threats.map(t => ({
              title: t.title,
              timing: t.timing,
              scope: t.scope
            }))
          };
        } catch (error) {
          console.error(`❌ ${species.scientific_name} 처리 오류:`, error);
          return {
            id: species.taxonid,
            scientificName: species.scientific_name,
            commonName: species.main_common_name,
            category: species.category,
            categoryInfo: IUCN_CATEGORIES[species.category],
            error: '상세 정보를 가져올 수 없습니다.'
          };
        }
      })
    );

    console.log(`🎉 ${countryCode} 데이터 수집 완료!`);

    return {
      countryCode,
      total: filteredSpecies.length,
      showing: enrichedSpecies.length,
      species: enrichedSpecies,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('❌ 통합 데이터 수집 오류:', error);
    return {
      countryCode,
      total: 0,
      species: [],
      error: error.message
    };
  }
};

/**
 * 특정 종의 상세 정보 조회 (모든 API 통합)
 * @param {string} scientificName - 학명
 * @returns {Promise<Object>} 상세 정보
 */
export const getSpeciesFullDetails = async (scientificName) => {
  try {
    console.log(`🔍 ${scientificName} 상세 정보 조회 중...`);

    // 병렬로 모든 정보 수집
    const [iucnDetails, wikiContent, threats] = await Promise.all([
      getSpeciesDetails(scientificName),
      getWikipediaFullContent(scientificName),
      getSpeciesThreats(scientificName)
    ]);

    if (!iucnDetails) {
      throw new Error('IUCN 데이터를 찾을 수 없습니다.');
    }

    // AI 설명 생성
    const aiDescription = await generateSpeciesDescription({
      scientificName: scientificName,
      commonName: iucnDetails.main_common_name,
      category: iucnDetails.category,
      threats: threats.map(t => t.title),
      wikipediaSummary: wikiContent?.extract
    });

    // 보호 활동 제안
    const conservationActions = await generateConservationActions({
      scientificName: scientificName,
      commonName: iucnDetails.main_common_name,
      threats: threats.map(t => t.title)
    });

    return {
      // 기본 정보
      scientificName: iucnDetails.scientific_name,
      commonName: iucnDetails.main_common_name,
      kingdom: iucnDetails.kingdom,
      phylum: iucnDetails.phylum,
      class: iucnDetails.class,
      order: iucnDetails.order,
      family: iucnDetails.family,
      genus: iucnDetails.genus,

      // 멸종위기 정보
      category: iucnDetails.category,
      categoryInfo: IUCN_CATEGORIES[iucnDetails.category],
      populationTrend: iucnDetails.population_trend,

      // Wikipedia 정보
      wikipedia: wikiContent ? {
        content: wikiContent.extract,
        thumbnail: wikiContent.thumbnail,
        url: wikiContent.url
      } : null,

      // AI 생성 정보
      aiDescription: aiDescription,
      conservationActions: conservationActions,

      // 위협 요인
      threats: threats.map(t => ({
        title: t.title,
        timing: t.timing,
        scope: t.scope,
        severity: t.severity
      }))
    };

  } catch (error) {
    console.error('상세 정보 조회 오류:', error);
    throw error;
  }
};

/**
 * 카테고리별 통계 조회
 * @param {string} countryCode - 국가 코드
 * @returns {Promise<Object>} 카테고리별 통계
 */
export const getCategoryStats = async (countryCode) => {
  try {
    const data = await getEndangeredSpeciesByCountry(countryCode);

    if (data.error || data.species.length === 0) {
      return null;
    }

    const stats = {
      CR: 0, // 위급
      EN: 0, // 위기
      VU: 0, // 취약
      total: data.species.length
    };

    data.species.forEach(species => {
      if (stats.hasOwnProperty(species.category)) {
        stats[species.category]++;
      }
    });

    return stats;
  } catch (error) {
    console.error('통계 조회 오류:', error);
    return null;
  }
};

/**
 * 국가 코드 매핑 (지도에서 사용하는 코드 -> IUCN API 코드)
 */
export const COUNTRY_CODE_MAPPING = {
  'korea': 'KR',
  'japan': 'JP',
  'usa': 'US',
  'china': 'CN',
  'russia': 'RU'
};

/**
 * 국가 ID를 IUCN 코드로 변환
 * @param {string} countryId - 국가 ID (예: 'korea')
 * @returns {string} IUCN 국가 코드 (예: 'KR')
 */
export const getIUCNCountryCode = (countryId) => {
  return COUNTRY_CODE_MAPPING[countryId] || countryId.toUpperCase();
};
