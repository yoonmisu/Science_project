import React from 'react';

/**
 * 에러 메시지 컴포넌트
 * API 호출 실패 시 표시됩니다
 */
const ErrorMessage = ({
  message = '데이터를 불러오는 중 오류가 발생했습니다.',
  onRetry = null
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      minHeight: '200px',
      backgroundColor: '#fef2f2',
      borderRadius: '12px',
      border: '1px solid #fecaca'
    }}>
      {/* 에러 아이콘 */}
      <div style={{
        fontSize: '48px',
        marginBottom: '16px'
      }}>
        ⚠️
      </div>

      {/* 에러 메시지 */}
      <p style={{
        fontSize: '16px',
        color: '#991b1b',
        textAlign: 'center',
        margin: '0 0 20px 0',
        fontWeight: '500'
      }}>
        {message}
      </p>

      {/* 재시도 버튼 */}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '10px 24px',
            backgroundColor: '#dc2626',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.backgroundColor = '#b91c1c'}
          onMouseLeave={(e) => e.target.style.backgroundColor = '#dc2626'}
        >
          다시 시도
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
