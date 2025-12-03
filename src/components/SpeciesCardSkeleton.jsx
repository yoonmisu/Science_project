import React from 'react';

/**
 * 생물 카드 스켈레톤 UI
 * 데이터 로딩 중에 카드 레이아웃을 미리 보여줍니다
 */
const SpeciesCardSkeleton = () => {
  return (
    <div style={{
      backgroundColor: '#f9fafb',
      borderRadius: '16px',
      overflow: 'hidden',
      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      animation: 'pulse 1.5s ease-in-out infinite'
    }}>
      {/* 이미지 영역 스켈레톤 */}
      <div style={{
        height: '140px',
        background: 'linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite'
      }} />

      {/* 텍스트 영역 스켈레톤 */}
      <div style={{ padding: '12px', textAlign: 'center' }}>
        <div style={{
          height: '16px',
          backgroundColor: '#e5e7eb',
          borderRadius: '4px',
          width: '70%',
          margin: '0 auto',
          background: 'linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 1.5s infinite'
        }} />
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }

        @keyframes shimmer {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>
    </div>
  );
};

/**
 * 여러 개의 스켈레톤 카드를 그리드로 표시
 */
export const SpeciesCardSkeletonGrid = ({ count = 3 }) => {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '16px',
      marginBottom: '24px'
    }}>
      {Array.from({ length: count }).map((_, index) => (
        <SpeciesCardSkeleton key={index} />
      ))}
    </div>
  );
};

export default SpeciesCardSkeleton;
