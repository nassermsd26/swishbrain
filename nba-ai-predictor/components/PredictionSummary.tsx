import React from 'react';
import { PredictionResult } from '../types';
import { TrendingUp, AlertTriangle, ShieldCheck } from 'lucide-react';

interface Props {
  data: PredictionResult;
}

const PredictionSummary: React.FC<Props> = ({ data }) => {
  const winnerTeam = data.winner === data.teamA.abbr ? data.teamA : data.teamB;
  const isConfidenceHigh = data.confidence >= 65;
  const isConfidenceLow = data.confidence < 55;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      {/* Main Winner Card */}
      <div className="lg:col-span-2 bg-gradient-to-br from-[#1D428A] to-[#102652] rounded-xl shadow-xl p-8 text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 opacity-10 transform translate-x-10 -translate-y-10">
          <img src={winnerTeam.logo} alt="logo" className="w-64 h-64 grayscale" />
        </div>
        
        <div className="relative z-10">
          <h2 className="text-gray-300 text-sm font-semibold uppercase tracking-wider mb-2">AI Projected Winner</h2>
          <div className="flex items-center gap-6 mb-8">
            <img src={winnerTeam.logo} alt={winnerTeam.name} className="w-24 h-24 object-contain bg-white rounded-full p-2" />
            <div>
              <h1 className="text-4xl md:text-5xl font-extrabold">{winnerTeam.name}</h1>
              <p className="text-xl text-gray-300 mt-1">Probability: <span className="text-white font-bold">{data.confidence.toFixed(1)}%</span></p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 border-t border-white/20 pt-6">
            <div>
              <p className="text-gray-300 text-sm mb-1">Projected Score</p>
              <div className="text-3xl font-bold font-mono">
                {data.teamA.abbr} <span className={data.winner === data.teamA.abbr ? "text-green-400" : ""}>{data.scoreA}</span>
                <span className="mx-2 text-gray-500">-</span>
                {data.teamB.abbr} <span className={data.winner === data.teamB.abbr ? "text-green-400" : ""}>{data.scoreB}</span>
              </div>
            </div>
            <div>
              <p className="text-gray-300 text-sm mb-1">Total Points</p>
              <div className="text-3xl font-bold font-mono text-yellow-400">
                {data.totalPoints}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Betting Analysis Card */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 flex flex-col justify-center">
        <h3 className="text-[#1D428A] font-bold text-lg mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Betting Matrix
        </h3>

        <div className="space-y-4">
          <div className={`p-4 rounded-lg border-l-4 ${isConfidenceHigh ? 'bg-green-50 border-green-500' : isConfidenceLow ? 'bg-red-50 border-red-500' : 'bg-yellow-50 border-yellow-500'}`}>
            <p className="text-xs font-bold uppercase text-gray-500 mb-1">Risk Level</p>
            <div className="flex items-center gap-2">
              {isConfidenceHigh ? <ShieldCheck className="text-green-600 w-5 h-5" /> : <AlertTriangle className="text-red-600 w-5 h-5" />}
              <span className={`text-lg font-bold ${isConfidenceHigh ? 'text-green-700' : isConfidenceLow ? 'text-red-700' : 'text-yellow-700'}`}>
                {data.bettingAnalysis.riskLevel}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100">
            <p className="text-xs font-bold uppercase text-gray-500 mb-1">Over / Under Prediction</p>
            <p className="text-lg font-bold text-[#1D428A]">
              {data.bettingAnalysis.overUnder}
            </p>
            <p className="text-xs text-gray-400 mt-1">Threshold: 210-225</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionSummary;