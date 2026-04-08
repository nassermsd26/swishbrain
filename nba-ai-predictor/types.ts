export interface Team {
  id: string;
  name: string;
  abbr: string;
  logo: string;
  color: string;
}

export interface Player {
  id: number;
  name: string;
  position?: string;
  status: 'ACTIVE' | 'OUT' | 'GTD'; // Game Time Decision
  pts_avg: number;
}

export interface MatchStats {
  pts: number;
  reb: number;
  ast: number;
  fg_pct: number;
  fg3_pct: number;
  plus_minus: number;
}

export interface PredictionResult {
  matchId: string;
  teamA: Team;
  teamB: Team;
  winner: string; // Abbr of winner
  confidence: number;
  scoreA: number;
  scoreB: number;
  totalPoints: number;
  bettingAnalysis: {
    riskLevel: 'Secure' | 'Risky' | 'Very Risky';
    overUnder: 'Lean OVER' | 'Lean UNDER' | 'Neutral';
  };
  statsA: MatchStats;
  statsB: MatchStats;
  injuries: {
    teamA: Player[];
    teamB: Player[];
  };
  impactA: number; // Points lost due to injury
  impactB: number;
  tokens_remaining?: number;
}

export interface GameSchedule {
  id: string;
  home: string;
  away: string;
  time: string;
  isToday: boolean;
}