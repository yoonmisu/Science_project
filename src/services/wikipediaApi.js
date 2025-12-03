// Wikipedia API
// API 문서: https://www.mediawiki.org/wiki/API:Main_page

const WIKIPEDIA_BASE_URL = 'https://en.wikipedia.org/w/api.php';

/**
 * 종에 대한 Wikipedia 요약 정보 조회
 * @param {string} searchTerm - 검색어 (학명 또는 일반명)
 * @returns {Promise<Object>} Wikipedia 요약 정보
 */
export const getWikipediaSummary = async (searchTerm) => {
  try {
    // Wikipedia API는 CORS를 지원하므로 직접 호출 가능
    const params = new URLSearchParams({
      action: 'query',
      format: 'json',
      prop: 'extracts|pageimages',
      exintro: true,
      explaintext: true,
      exsentences: 3,
      piprop: 'thumbnail',
      pithumbsize: 500,
      titles: searchTerm,
      origin: '*' // CORS 허용
    });

    const response = await fetch(`${WIKIPEDIA_BASE_URL}?${params}`);

    if (!response.ok) {
      throw new Error(`Wikipedia API error: ${response.status}`);
    }

    const data = await response.json();
    const pages = data.query?.pages;

    if (!pages) {
      return null;
    }

    const page = Object.values(pages)[0];

    if (page.missing) {
      return null;
    }

    return {
      title: page.title,
      extract: page.extract || '정보를 찾을 수 없습니다.',
      thumbnail: page.thumbnail?.source || null,
      pageId: page.pageid
    };
  } catch (error) {
    console.error('Wikipedia API 오류:', error);
    return null;
  }
};

/**
 * 종에 대한 상세 정보 조회 (전체 내용)
 * @param {string} searchTerm - 검색어
 * @returns {Promise<Object>} 상세 정보
 */
export const getWikipediaFullContent = async (searchTerm) => {
  try {
    const params = new URLSearchParams({
      action: 'query',
      format: 'json',
      prop: 'extracts|pageimages|info',
      exlimit: 1,
      explaintext: true,
      piprop: 'thumbnail',
      pithumbsize: 500,
      inprop: 'url',
      titles: searchTerm,
      origin: '*'
    });

    const response = await fetch(`${WIKIPEDIA_BASE_URL}?${params}`);

    if (!response.ok) {
      throw new Error(`Wikipedia API error: ${response.status}`);
    }

    const data = await response.json();
    const pages = data.query?.pages;

    if (!pages) {
      return null;
    }

    const page = Object.values(pages)[0];

    if (page.missing) {
      return null;
    }

    return {
      title: page.title,
      extract: page.extract || '정보를 찾을 수 없습니다.',
      thumbnail: page.thumbnail?.source || null,
      url: page.fullurl,
      pageId: page.pageid
    };
  } catch (error) {
    console.error('Wikipedia API 상세 정보 오류:', error);
    return null;
  }
};

/**
 * Wikipedia 검색 (학명 또는 일반명으로)
 * @param {string} query - 검색어
 * @param {number} limit - 결과 개수 (기본값: 5)
 * @returns {Promise<Array>} 검색 결과
 */
export const searchWikipedia = async (query, limit = 5) => {
  try {
    const params = new URLSearchParams({
      action: 'opensearch',
      format: 'json',
      search: query,
      limit: limit,
      origin: '*'
    });

    const response = await fetch(`${WIKIPEDIA_BASE_URL}?${params}`);

    if (!response.ok) {
      throw new Error(`Wikipedia API error: ${response.status}`);
    }

    const data = await response.json();

    // OpenSearch 결과 형식: [query, [titles], [descriptions], [urls]]
    if (data.length >= 4) {
      const titles = data[1];
      const descriptions = data[2];
      const urls = data[3];

      return titles.map((title, index) => ({
        title: title,
        description: descriptions[index],
        url: urls[index]
      }));
    }

    return [];
  } catch (error) {
    console.error('Wikipedia 검색 오류:', error);
    return [];
  }
};
