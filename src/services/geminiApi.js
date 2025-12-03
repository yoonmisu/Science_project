// Google Gemini API (무료)
// API 문서: https://ai.google.dev/docs

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY || 'YOUR_API_KEY';
const GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';

/**
 * Gemini를 사용한 텍스트 요약
 * @param {string} text - 요약할 텍스트
 * @param {number} maxLength - 최대 길이 (기본값: 200자)
 * @returns {Promise<string>} 요약된 텍스트
 */
export const summarizeText = async (text, maxLength = 200) => {
  try {
    const prompt = `다음 텍스트를 ${maxLength}자 이내로 한국어로 요약해주세요. 핵심 내용만 간결하게 정리해주세요:\n\n${text}`;

    const response = await fetch(`${GEMINI_BASE_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.4,
          maxOutputTokens: 500,
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`);
    }

    const data = await response.json();
    const summary = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!summary) {
      throw new Error('요약 생성 실패');
    }

    return summary.trim();
  } catch (error) {
    console.error('Gemini API 요약 오류:', error);
    // 오류 시 원본 텍스트의 첫 부분 반환
    return text.substring(0, maxLength) + '...';
  }
};

/**
 * 멸종위기종에 대한 상세 설명 생성
 * @param {Object} speciesData - 종 데이터 (IUCN + Wikipedia)
 * @returns {Promise<string>} 생성된 설명
 */
export const generateSpeciesDescription = async (speciesData) => {
  try {
    const { scientificName, commonName, category, threats, wikipediaSummary } = speciesData;

    const prompt = `
다음 멸종위기종에 대한 간단하고 이해하기 쉬운 설명을 200자 이내로 한국어로 작성해주세요:

학명: ${scientificName}
일반명: ${commonName || '정보 없음'}
멸종위기 등급: ${category}
주요 위협: ${threats?.join(', ') || '정보 없음'}
Wikipedia 요약: ${wikipediaSummary || '정보 없음'}

설명은 다음을 포함해야 합니다:
1. 이 종의 특징
2. 왜 멸종위기에 처했는지
3. 보호가 필요한 이유

어린이도 이해할 수 있도록 쉽고 친근하게 작성해주세요.
`;

    const response = await fetch(`${GEMINI_BASE_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.7,
          maxOutputTokens: 500,
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`);
    }

    const data = await response.json();
    const description = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!description) {
      throw new Error('설명 생성 실패');
    }

    return description.trim();
  } catch (error) {
    console.error('Gemini API 설명 생성 오류:', error);
    return `${speciesData.commonName || speciesData.scientificName}은(는) ${speciesData.category} 등급의 멸종위기종입니다.`;
  }
};

/**
 * 여러 종에 대한 일괄 요약
 * @param {Array<string>} texts - 요약할 텍스트 배열
 * @param {number} maxLength - 각 요약의 최대 길이
 * @returns {Promise<Array<string>>} 요약된 텍스트 배열
 */
export const batchSummarize = async (texts, maxLength = 150) => {
  try {
    const promises = texts.map(text => summarizeText(text, maxLength));
    return await Promise.all(promises);
  } catch (error) {
    console.error('일괄 요약 오류:', error);
    return texts.map(text => text.substring(0, maxLength) + '...');
  }
};

/**
 * 보호 활동 제안 생성
 * @param {Object} speciesData - 종 데이터
 * @returns {Promise<Array<string>>} 보호 활동 제안 목록
 */
export const generateConservationActions = async (speciesData) => {
  try {
    const { scientificName, commonName, threats } = speciesData;

    const prompt = `
${commonName || scientificName}의 멸종을 막기 위한 구체적인 보호 활동 3가지를 제안해주세요.
주요 위협 요인: ${threats?.join(', ') || '서식지 파괴'}

각 제안은 다음 형식으로 작성해주세요:
- 간결한 한 문장 (30자 이내)
- 실천 가능한 구체적인 행동

3가지 제안만 작성하고, 번호나 불필요한 설명은 제외해주세요.
`;

    const response = await fetch(`${GEMINI_BASE_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.6,
          maxOutputTokens: 300,
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`);
    }

    const data = await response.json();
    const actionsText = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!actionsText) {
      throw new Error('보호 활동 생성 실패');
    }

    // 텍스트를 배열로 변환
    const actions = actionsText
      .split('\n')
      .filter(line => line.trim().length > 0)
      .map(line => line.replace(/^[-•*]\s*/, '').trim())
      .slice(0, 3);

    return actions.length > 0 ? actions : [
      '서식지 보호 및 복원 활동 참여',
      '환경 보호 단체 후원',
      '멸종위기종 보호 인식 확산'
    ];
  } catch (error) {
    console.error('보호 활동 생성 오류:', error);
    return [
      '서식지 보호 및 복원 활동 참여',
      '환경 보호 단체 후원',
      '멸종위기종 보호 인식 확산'
    ];
  }
};
