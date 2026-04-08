import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { PredictionResult } from '../types';
import PredictionSummary from './PredictionSummary';
import StatsCharts from './StatsCharts';
import LineupStatus from './LineupStatus';
import { useTheme } from '../contexts/ThemeContext';

interface Props {
  prediction: PredictionResult;
  onBack: () => void;
}

const PredictionPage: React.FC<Props> = ({ prediction, onBack }) => {
  const { theme } = useTheme();

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-950' : 'bg-gray-50'} pb-20`}>
      <div className="max-w-7xl mx-auto px-4 pt-8">
        <button
          onClick={onBack}
          className={`mb-6 flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            theme === 'dark'
              ? 'bg-gray-900/50 text-white hover:bg-gray-800 border border-gray-800'
              : 'bg-white text-gray-800 hover:bg-gray-100 border border-gray-200'
          }`}
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="font-medium">Revenir au menu</span>
        </button>

        <div className="space-y-8">
          <PredictionSummary data={prediction} />
          
          <StatsCharts 
            statsA={prediction.statsA} 
            statsB={prediction.statsB} 
            teamA={prediction.teamA} 
            teamB={prediction.teamB} 
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <LineupStatus 
              team={prediction.teamA} 
              injuries={prediction.injuries.teamA} 
              impactScore={prediction.impactA}
            />
            <LineupStatus 
              team={prediction.teamB} 
              injuries={prediction.injuries.teamB} 
              impactScore={prediction.impactB}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionPage;

