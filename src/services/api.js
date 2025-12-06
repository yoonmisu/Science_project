const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const COUNTRY_MAPPING = {
  'korea': 'korea',
  'japan': 'japan',
  'china': 'china',
  'india': 'india',
  'usa': 'usa',
  'canada': 'canada',
  'mexico': 'mexico',
  'russia': 'russia',
  'uk': 'uk',
  'germany': 'germany',
  'france': 'france',
  'brazil': 'brazil',
  'argentina': 'argentina',
  'southafrica': 'southafrica',
  'kenya': 'kenya',
  'australia': 'australia',
  'newzealand': 'newzealand'
};

const apiRequest = async (endpoint, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }

  const fullUrl = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const fetchSpeciesByCountry = async (countryCode, category, page = 1, limit = 3, speciesName = null) => {
  try {
    const params = new URLSearchParams({
      country: countryCode,
      category: category,
      page: page.toString(),
      limit: limit.toString(),
    });

    if (speciesName) {
      params.append('species_name', speciesName);
    }

    const response = await apiRequest(`/api/v1/species?${params}`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.common_name || species.scientific_name,
        image: species.image_url || species.image || '🌱',
        color: species.color || 'green',
        scientificName: species.scientific_name,
        description: species.description,
        riskLevel: species.risk_level,
        country: species.country,
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
    };
  } catch (error) {
    throw error;
  }
};

export const fetchSpeciesByLocation = async (lat, lng, category, page = 1, limit = 3) => {
  try {

    const params = new URLSearchParams({
      lat: lat.toString(),
      lng: lng.toString(),
      category: category,
      page: page.toString(),
      limit: limit.toString(),
    });

    const response = await apiRequest(`/api/v1/species/by-location?${params}`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        image: species.image || '🌱',
        color: species.color || 'green',
        scientificName: species.scientific_name,
        description: species.description,
        country: species.country,
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
    };
  } catch (error) {
    throw error;
  }
};

export const fetchSpeciesDetail = async (speciesId, lang = 'en', scientificName = null) => {
  try {
    const params = new URLSearchParams({ lang });
    if (scientificName) {
      params.append('scientific_name', scientificName);
    }
    const response = await apiRequest(`/api/v1/species/${speciesId}?${params}`);

    return {
      id: response.id,
      name: response.name,
      scientificName: response.scientific_name,
      commonName: response.common_name,
      category: response.category,
      country: response.country,
      image: response.image || '',
      color: response.color || 'green',
      description: response.description || '',
      status: response.status,
      population: response.population,
      habitat: response.habitat,
      threats: response.threats || [],
      error: response.error || false,
      errorMessage: response.error_message || null,
    };
  } catch (error) {
    throw error;
  }
};

export const fetchEndangeredSpecies = async (countryCode, category = null, page = 1, limit = 20) => {
  try {

    const mappedCountry = COUNTRY_MAPPING[countryCode] || countryCode;

    const params = new URLSearchParams({
      country: mappedCountry,
      page: page.toString(),
      limit: limit.toString(),
    });

    if (category) {
      params.append('category', category);
    }

    const response = await apiRequest(`/api/v1/species/endangered?${params}`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        image: species.image || '🌱',
        status: species.status,
        population: species.population,
        threats: species.threats || [],
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
    };
  } catch (error) {
    throw error;
  }
};

export const fetchDailyRandomSpecies = async () => {
  try {
    const response = await apiRequest('/api/v1/species/random-daily');

    return {
      scientificName: response.scientific_name,
      commonName: response.common_name,
      koreanName: response.korean_name,
      taxonId: response.taxon_id,
      image: response.image,
      category: response.category,
      date: response.date,
      message: response.message,
    };
  } catch (error) {
    return null;
  }
};

export const fetchWeeklyTopSpecies = async () => {
  try {
    const response = await apiRequest('/api/v1/species/weekly-top');

    return {
      speciesName: response.species_name,
      scientificName: response.scientific_name,
      taxonId: response.taxon_id,
      category: response.category,
      viewCount: response.view_count,
      periodDays: response.period_days,
      message: response.message,
    };
  } catch (error) {
    return null;
  }
};

export const fetchPopularEndangered = async (limit = 10) => {
  try {
    const response = await apiRequest(`/api/v1/species/popular-endangered?limit=${limit}`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        country: species.country,
        category: species.category,
        mentions: species.mentions || 0,
        status: species.status,
      })),
    };
  } catch (error) {
    throw error;
  }
};

export const searchSpecies = async (query, country = null, category = null, page = 1, limit = 20) => {
  try {

    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      limit: limit.toString(),
    });

    if (country) {
      params.append('country', COUNTRY_MAPPING[country] || country);
    }

    if (category) {
      params.append('category', category);
    }

    const response = await apiRequest(`/api/v1/species/search?${params}`);

    return {
      data: response.data.map(species => ({
        id: species.id,
        name: species.name,
        image: species.image || '🌱',
        category: species.category,
        country: species.country,
      })),
      total: response.total,
      page: response.page,
      totalPages: response.totalPages,
      query: response.query,
    };
  } catch (error) {
    throw error;
  }
};

export const searchSpeciesByName = async (query, category = null) => {
  try {
    const params = new URLSearchParams({
      query: query,
    });

    if (category) {
      params.append('category', category);
    }

    const response = await apiRequest(`/api/v1/species/search?${params}`);

    return {
      query: response.query,
      countries: response.countries,
      total: response.total,
      category: response.category,
      matchedSpecies: response.matched_species,
      matchedScientificName: response.matched_scientific_name,
    };
  } catch (error) {
    throw error;
  }
};

export const fetchTrendingSearches = async (limit = 7, hours = 24) => {
  try {

    const params = new URLSearchParams({
      limit: limit.toString(),
      hours: hours.toString(),
    });

    const response = await apiRequest(`/api/v1/species/trending?${params}`);

    return {
      data: response.data,
      periodHours: response.period_hours,
      total: response.total,
    };
  } catch (error) {
    return {
      data: [],
      periodHours: hours,
      total: 0,
    };
  }
};

export const fetchAllCountriesSpeciesCount = async (category = '동물') => {
  try {
    const params = new URLSearchParams({
      category: category,
    });

    const response = await apiRequest(`/api/v1/species/stats/countries?${params}`);

    return response;
  } catch (error) {
    return {};
  }
};

export const checkApiHealth = async () => {
  try {
    const response = await apiRequest('/');
    return response && response.message;
  } catch (error) {
    return false;
  }
};
