import { Team, PredictionResult, MatchStats, Player, GameSchedule } from '../types';
import { TEAMS } from '../constants';

// ---------------------------------------------------------------------------
// CONFIGURATION DU BACKEND (BACKEND CONFIGURATION)
// ---------------------------------------------------------------------------
// Mettez cette variable à 'true' pour connecter votre vrai projet Python.
// Set this to 'true' to connect your real Python project.
export const USE_REAL_BACKEND = true;

// L'URL de votre API (ex: Flask, FastAPI, Django)
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
const BACKEND_URL = `${BASE_URL}/predict`;
const SCHEDULE_URL = `${BASE_URL}/schedule`;

// ---------------------------------------------------------------------------

// Helper to generate random stats (Fallback/Simulation Logic)
const generateStats = (): MatchStats => ({
  pts: Math.floor(Math.random() * (125 - 100) + 100),
  reb: Math.floor(Math.random() * (55 - 35) + 35),
  ast: Math.floor(Math.random() * (35 - 20) + 20),
  fg_pct: Math.random() * (55 - 42) + 42,
  fg3_pct: Math.random() * (45 - 30) + 30,
  plus_minus: Math.floor(Math.random() * 20 - 10),
});

const generateInjuries = (teamAbbr: string): Player[] => {
  if (Math.random() > 0.6) return [];
  return [
    {
      id: Math.floor(Math.random() * 1000),
      name: `Star Player (${teamAbbr})`,
      status: Math.random() > 0.5 ? 'OUT' : 'GTD',
      pts_avg: Math.floor(Math.random() * 15 + 10)
    }
  ];
};

export const simulatePrediction = async (teamA_abbr: string, teamB_abbr: string, token?: string | null): Promise<PredictionResult> => {
  // 1. REAL BACKEND CONNECTION ATTEMPT
  if (USE_REAL_BACKEND) {
    try {
      console.log(`Calling backend at ${BACKEND_URL}...`);
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Ajouter le token JWT si l'utilisateur est connecté
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          teamA: teamA_abbr,
          teamB: teamB_abbr
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `Server error: ${response.statusText}`);
      }

      const realData = await response.json();

      // Le backend retourne déjà le bon format, on peut l'utiliser directement
      return realData as PredictionResult;

    } catch (error) {
      console.error("Backend Connection Failed:", error);
      console.warn("Falling back to simulation mode.");
      // Afficher une erreur claire à l'utilisateur
      throw new Error(`Impossible de se connecter au backend: ${error instanceof Error ? error.message : 'Erreur inconnue'}. Vérifiez que le serveur Flask est lancé sur le port 5002.`);
    }
  }

  // 2. MOCK SIMULATION (Fallback)
  await new Promise(resolve => setTimeout(resolve, 1500));

  const teamA = TEAMS.find(t => t.abbr === teamA_abbr) || TEAMS[0];
  const teamB = TEAMS.find(t => t.abbr === teamB_abbr) || TEAMS[1];

  const scoreA = Math.floor(Math.random() * 30 + 95);
  const scoreB = Math.floor(Math.random() * 30 + 95);
  const winner = scoreA > scoreB ? teamA_abbr : teamB_abbr;

  const confidence = Math.random() * (90 - 51) + 51;
  const total = scoreA + scoreB;

  let risk: 'Secure' | 'Risky' | 'Very Risky' = 'Secure';
  if (confidence < 65) risk = 'Risky';
  if (confidence < 55) risk = 'Very Risky';

  let overUnder: 'Lean OVER' | 'Lean UNDER' | 'Neutral' = 'Neutral';
  if (total > 225) overUnder = 'Lean OVER';
  if (total < 210) overUnder = 'Lean UNDER';

  return {
    matchId: `${teamA_abbr}-${teamB_abbr}-${Date.now()}`,
    teamA,
    teamB,
    winner,
    confidence,
    scoreA,
    scoreB,
    totalPoints: total,
    bettingAnalysis: {
      riskLevel: risk,
      overUnder: overUnder,
    },
    statsA: generateStats(),
    statsB: generateStats(),
    injuries: {
      teamA: generateInjuries(teamA.abbr),
      teamB: generateInjuries(teamB.abbr)
    },
    impactA: Math.random() * 5,
    impactB: Math.random() * 5
  };
};

// Fonction pour récupérer les matchs réels depuis l'API
export const getRealSchedule = async (): Promise<GameSchedule[]> => {
  if (USE_REAL_BACKEND) {
    try {
      const response = await fetch(SCHEDULE_URL);
      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }
      const data = await response.json();
      return data.games || [];
    } catch (error) {
      console.error("Failed to fetch schedule:", error);
      return [];
    }
  }
  return [];
};

// Fonction pour récupérer les actualités NBA depuis l'API
export const getRealNews = async (): Promise<any[]> => {
  if (USE_REAL_BACKEND) {
    try {
      const response = await fetch(`${BASE_URL}/news`);
      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }
      const data = await response.json();
      return data.news || [];
    } catch (error) {
      console.error("Failed to fetch news:", error);
      return [];
    }
  }
  return [];
};