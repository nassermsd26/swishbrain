import React from 'react';
import { MatchStats, Team } from '../types';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis 
} from 'recharts';

interface Props {
  statsA: MatchStats;
  statsB: MatchStats;
  teamA: Team;
  teamB: Team;
}

const StatsCharts: React.FC<Props> = ({ statsA, statsB, teamA, teamB }) => {
  const barData = [
    { name: 'PTS', [teamA.abbr]: statsA.pts, [teamB.abbr]: statsB.pts },
    { name: 'REB', [teamA.abbr]: statsA.reb, [teamB.abbr]: statsB.reb },
    { name: 'AST', [teamA.abbr]: statsA.ast, [teamB.abbr]: statsB.ast },
  ];

  const radarData = [
    { subject: 'FG%', A: statsA.fg_pct, B: statsB.fg_pct, fullMark: 100 },
    { subject: '3PT%', A: statsA.fg3_pct, B: statsB.fg3_pct, fullMark: 100 },
    { subject: 'AST', A: statsA.ast, B: statsB.ast, fullMark: 40 },
    { subject: 'REB', A: statsA.reb, B: statsB.reb, fullMark: 60 },
    { subject: 'DIFF', A: statsA.plus_minus + 20, B: statsB.plus_minus + 20, fullMark: 40 }, // Offset for visualization
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
      {/* Bar Chart */}
      <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
        <h3 className="text-gray-800 font-bold mb-4">Stat Comparison</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={barData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip 
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
              />
              <Legend />
              <Bar dataKey={teamA.abbr} fill="#1D428A" radius={[4, 4, 0, 0]} />
              <Bar dataKey={teamB.abbr} fill="#C8102E" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
        <h3 className="text-gray-800 font-bold mb-4">Performance Radar</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} hide />
              <Radar
                name={teamA.abbr}
                dataKey="A"
                stroke="#1D428A"
                fill="#1D428A"
                fillOpacity={0.3}
              />
              <Radar
                name={teamB.abbr}
                dataKey="B"
                stroke="#C8102E"
                fill="#C8102E"
                fillOpacity={0.3}
              />
              <Legend />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default StatsCharts;