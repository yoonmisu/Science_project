import React from 'react';
import styled, { css } from 'styled-components';
import { Link } from 'react-router-dom'; 
import Landing from '../assets/Landing.png';
import misu from '../assets/misu.png';
import jaejun from '../assets/jaejun.png';
import logo from '../assets/logo.png';
import github from '../assets/github.png';

const VARS = {
  verdeDark: '#A8B78E',
  verdeLight: '#FBFFF4',
  textDark: '#333',
  textLight: '#fff',
  backgroundLight: '#f5f5f5',
};

const Header = styled.header`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 15px 0;
  z-index: 10;
  text-align: center;

  nav p {
    color: ${VARS.textLight};
    text-decoration: none;
    margin: 0 15px;
    font-size: 16px;
    opacity: 0.8;
    transition: opacity 0.3s;
    &:hover {
      opacity: 1;
    }
  }
`;

const CtaButton = styled.button`
  padding: 12px 28px;
  border: none;
  border-radius: 10px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
  text-decoration: none;
  display: inline-block;

  background-color: ${VARS.verdeLight};
  color: ${VARS.textDark};
  &:hover {
    background-color: #747F60;
  }

  ${props =>
    props.$secondary &&
    css`
      background-color: ${VARS.textLight};
      color: ${VARS.verdeDark};
      &:hover {
        background-color: #ddd;
      }
    `}
`;

const HeroSection = styled.section`
  height: 700px;
  background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.6)), url(${Landing}) no-repeat center center/cover;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: ${VARS.textLight};

  h1 {
    font-size: 40px;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 50px;
  }
  .brand-name {
    color: ${VARS.verdeDark};
  }
`;

const FeaturesSection = styled.section`
  padding: 80px 5%;
  background-color: ${VARS.backgroundLight};
  text-align: center;

  h2 {
    font-size: 14px;
    color: #888;
    margin-bottom: 50px;
  }

  .feature-grid {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 60px;
  }
  
  .feature-item {
    width: 250px;
  }

  .icon-circle {
    font-size: 30px;
    width: 60px;
    height: 60px;
    line-height: 60px;
    border-radius: 50%;
    margin: 0 auto 20px;
    border: 2px solid transparent;
  }

  .testimonial-row {
    display: flex;
    justify-content: center;
    gap: 80px;
    margin-top: 40px;
    flex-wrap: wrap;
  }

  .testimonial-item {
    display: flex;
    align-items: center;
    text-align: left;
  }
  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
    margin-right: 15px;
  }
  .quote {
    font-style: italic;
    font-size: 14px;
    color: #555;
  }
`;

const Footer = styled.footer`
  background-color: ${VARS.verdeLight};
  color: ${VARS.textLight};
  padding: 60px 5%;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 28px;

  .footer-left {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;

    .verde-logo {
      height: 40px;
      width: auto;
      filter: drop-shadow(2px 2px 2px rgba(0, 0, 0, 0.4));
    }

    p {
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: #67728A;
    }
  }

  .footer-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 20px;

    .github-link {
      display: block;
    }

    .github-icon {
      height: 30px;
      width: auto;
      opacity: 0.7;
      transition: opacity 0.3s;
      &:hover {
        opacity: 1;
      }
    }

    .copyright {
      color : #67728A
      font-size: 12px;
      opacity: 0.6;
      margin-top: 20px;
    }
  }
`;


const LandingPage = () => {
  return (
    <div className="verde-landing">
      <Header>
        <nav>
          <p>== Welcome this is landing page! ==</p>
        </nav>
      </Header>

      <HeroSection>
        <div className="hero-content">
          <h1>
            우리가 사는 지구, <br /> 그 안의 모든 생명에 대해 <span className="brand-name">Verde</span>
          </h1>
          <CtaButton as={Link} to="/home">
            Verde 시작하기
          </CtaButton>
        </div>
      </HeroSection>

      <FeaturesSection>
        <h2>== 주요 기능 ==</h2>
        <div className="feature-grid">
          <div className="feature-item">
            <div className="icon-circle">🍃</div>
            <h3>멸종 위기 동물</h3>
            <p>멸종 위기 동물을 확인해요</p>
          </div>
          <div className="feature-item">
            <div className="icon-circle">⚙️</div>
            <h3>생물 다양성 확인</h3>
            <p>지도 위에서 전 세계의 생물들을 확인해요</p>
          </div>
          <div className="feature-item">
            <div className="icon-circle">🌱</div>
            <h3>생물 수업시간</h3>
            <p>생명과학 수업시간에 사용해요</p>
          </div>
        </div>

        <div className="testimonial-row">
        <div className="testimonial-item">
            <img src={misu} alt="미수 윤" className="avatar" />
        <div>
        <span className="name">Yoonmisu</span>
        <p className="quote">"Verde 덕분에 전 세계의 멸종 위기 동물을 알게 되어서 좋았어요"</p>
        </div>
        </div>
        <div className="testimonial-item">
        <img src={jaejun} alt="재준 윤" className="avatar" />
        <div>
        <span className="name">Yoonjaejun</span>
        <p className="quote">"생물 수업 시간에 이렇게 시각화 된 웹을 보면서 더 이해가 잘 됐어요"</p>
        </div>
        </div>
        </div>
      </FeaturesSection>
      <Footer>
        <div className="footer-left">
          <img src={logo} alt="Verde Logo" className="verde-logo" />
          <p>UX/UI, Frontend : 25_42@bssm.hs.kr</p>
          <p>AI, Backend : 25_43@bssm.hs.kr</p>
        </div>
        <div className="footer-right">
          <a href="https://github.com/yoonmisu/Science_project" target="_blank" rel="noopener noreferrer" className="github-link"> 
            <img src={github} alt="GitHub" className="github-icon" />
          </a>
          <p className="copyright">© 2025 Verde</p>
        </div>
      </Footer>
    </div>
  );
};

export default LandingPage;