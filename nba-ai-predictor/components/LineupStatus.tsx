import React from 'react';
import { Player, Team } from '../types';
import { UserMinus, Activity } from 'lucide-react';

interface Props {
  team: Team;
  injuries: Player[];
  impactScore: number;
}

const LineupStatus: React.FC<Props> = ({ team, injuries, impactScore }) => {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
        <h3 className="font-bold text-gray-800 flex items-center gap-2">
          <img src={team.logo} className="w-6 h-6 object-contain" alt="" />
          {team.abbr} Injury Report
        </h3>
        <span className="text-xs font-mono text-gray-500">
          Impact: -{impactScore.toFixed(1)} pts
        </span>
      </div>
      
      <div className="p-4">
        {injuries.length === 0 ? (
          <div className="flex items-center gap-2 text-green-600 text-sm py-2">
            <Activity className="w-4 h-4" />
            <span>Clean bill of health. Full lineup available.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {injuries.map((player) => (
              <div key={player.id} className="flex items-center justify-between p-2 bg-red-50 rounded-lg border border-red-100">
                <div className="flex items-center gap-3">
                  <div className="bg-white p-1 rounded-full">
                    <UserMinus className="w-4 h-4 text-red-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-800">{player.name}</p>
                    <p className="text-xs text-gray-500">Avg: {player.pts_avg} PPG</p>
                  </div>
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded ${
                  player.status === 'OUT' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'
                }`}>
                  {player.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LineupStatus;