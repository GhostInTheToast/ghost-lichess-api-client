import React, { useState, useEffect } from 'react';
import { ApiService, handleApiError } from '../services/api';
import { TierListItem } from '../types/types';
import './HomePage.css';

const HomePage: React.FC = () => {
  const [openings, setOpenings] = useState<TierListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadOpenings();
  }, []);

  const loadOpenings = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await ApiService.getTierList();
      setOpenings(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  // Sort openings by win rate for White (higher is better for White)
  const topOpeningsForWhite = [...openings]
    .sort((a, b) => b.statistics.win_rate_white - a.statistics.win_rate_white)
    .slice(0, 10);

  // Sort openings by win rate for Black (higher black win rate is better for Black)
  const topOpeningsForBlack = [...openings]
    .sort((a, b) => b.statistics.win_rate_black - a.statistics.win_rate_black)
    .slice(0, 10);

  if (loading) {
    return (
      <div className="home-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading chess openings data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="home-page">
        <div className="error-container">
          <h3>Error loading data</h3>
          <p>{error}</p>
          <button onClick={loadOpenings} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <div className="home-page">
      <header className="page-header">
        <h1>🏆 Chess Openings Analysis</h1>
        <p className="subtitle">
          Discover the most successful chess openings based on real game data
        </p>
        <div className="stats-summary">
          <span>{openings.length} openings analyzed</span>
          <span>•</span>
          <span>Updated daily from Lichess</span>
        </div>
      </header>

      <div className="tables-container">
        {/* Top Openings for White */}
        <div className="table-section">
          <div className="table-header">
            <h2>⚪ Best Openings for White</h2>
            <p className="table-description">
              Openings with the highest win rate for White pieces
            </p>
          </div>
          
          <div className="table-container">
            <table className="openings-table">
              <thead>
                <tr>
                  <th className="rank-col">#</th>
                  <th className="eco-col">ECO</th>
                  <th className="name-col">Opening Name</th>
                  <th className="moves-col">Key Moves</th>
                  <th className="win-rate-col">White Win Rate</th>
                  <th className="games-col">Games</th>
                  <th className="score-col">Score</th>
                </tr>
              </thead>
              <tbody>
                {topOpeningsForWhite.map((item, index) => (
                  <tr key={item.opening.id} className={index < 3 ? 'top-three' : ''}>
                    <td className="rank-col">
                      <span className={`rank rank-${index + 1}`}>
                        {index + 1}
                      </span>
                    </td>
                    <td className="eco-col">
                      <span className="eco-code">
                        {item.opening.eco_code || '---'}
                      </span>
                    </td>
                    <td className="name-col">
                      <div className="opening-name">
                        {item.opening.name || 'Unknown Opening'}
                      </div>
                    </td>
                    <td className="moves-col">
                      <div className="moves-text">
                        {item.opening.moves_sequence.slice(0, 4).join(' ')}
                        {item.opening.moves_sequence.length > 4 && '...'}
                      </div>
                    </td>
                    <td className="win-rate-col">
                      <div className="win-rate white-rate">
                        {formatPercentage(item.statistics.win_rate_white)}
                      </div>
                    </td>
                    <td className="games-col">
                      {item.statistics.total_games.toLocaleString()}
                    </td>
                    <td className="score-col">
                      <div className="performance-score">
                        {item.statistics.performance_score.toFixed(1)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Openings for Black */}
        <div className="table-section">
          <div className="table-header">
            <h2>⚫ Best Openings for Black</h2>
            <p className="table-description">
              Openings with the highest win rate for Black pieces
            </p>
          </div>
          
          <div className="table-container">
            <table className="openings-table">
              <thead>
                <tr>
                  <th className="rank-col">#</th>
                  <th className="eco-col">ECO</th>
                  <th className="name-col">Opening Name</th>
                  <th className="moves-col">Key Moves</th>
                  <th className="win-rate-col">Black Win Rate</th>
                  <th className="games-col">Games</th>
                  <th className="score-col">Score</th>
                </tr>
              </thead>
              <tbody>
                {topOpeningsForBlack.map((item, index) => (
                  <tr key={item.opening.id} className={index < 3 ? 'top-three' : ''}>
                    <td className="rank-col">
                      <span className={`rank rank-${index + 1}`}>
                        {index + 1}
                      </span>
                    </td>
                    <td className="eco-col">
                      <span className="eco-code">
                        {item.opening.eco_code || '---'}
                      </span>
                    </td>
                    <td className="name-col">
                      <div className="opening-name">
                        {item.opening.name || 'Unknown Opening'}
                      </div>
                    </td>
                    <td className="moves-col">
                      <div className="moves-text">
                        {item.opening.moves_sequence.slice(0, 4).join(' ')}
                        {item.opening.moves_sequence.length > 4 && '...'}
                      </div>
                    </td>
                    <td className="win-rate-col">
                      <div className="win-rate black-rate">
                        {formatPercentage(item.statistics.win_rate_black)}
                      </div>
                    </td>
                    <td className="games-col">
                      {item.statistics.total_games.toLocaleString()}
                    </td>
                    <td className="score-col">
                      <div className="performance-score">
                        {item.statistics.performance_score.toFixed(1)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <footer className="page-footer">
        <p>
          Data sourced from Lichess games • Updated regularly • 
          <a href="https://lichess.org" target="_blank" rel="noopener noreferrer">
            Visit Lichess
          </a>
        </p>
      </footer>
    </div>
  );
};

export default HomePage;