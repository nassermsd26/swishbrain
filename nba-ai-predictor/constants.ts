import { Team, GameSchedule } from './types';

export const NBA_BLUE = '#1D428A';
export const NBA_RED = '#C8102E';

// Mapping des IDs NBA vers les logos officiels
const NBA_LOGO_BASE = 'https://cdn.nba.com/logos/nba';
const NBA_TEAM_IDS: Record<string, string> = {
  'ATL': '1610612737', 'BOS': '1610612738', 'BKN': '1610612751', 'CHA': '1610612766',
  'CHI': '1610612741', 'CLE': '1610612739', 'DAL': '1610612742', 'DEN': '1610612743',
  'DET': '1610612765', 'GSW': '1610612744', 'HOU': '1610612745', 'IND': '1610612754',
  'LAC': '1610612746', 'LAL': '1610612747', 'MEM': '1610612763', 'MIA': '1610612748',
  'MIL': '1610612749', 'MIN': '1610612750', 'NOP': '1610612740', 'NYK': '1610612752',
  'OKC': '1610612760', 'ORL': '1610612753', 'PHI': '1610612755', 'PHX': '1610612756',
  'POR': '1610612757', 'SAC': '1610612758', 'SAS': '1610612759', 'TOR': '1610612761',
  'UTA': '1610612762', 'WAS': '1610612764'
};

const getNBALogo = (abbr: string) => {
  const teamId = NBA_TEAM_IDS[abbr];
  return teamId ? `${NBA_LOGO_BASE}/${teamId}/primary/L/logo.svg` : '';
};

export const TEAMS: Team[] = [
  { id: '1', name: 'Atlanta Hawks', abbr: 'ATL', color: '#E03A3E', logo: getNBALogo('ATL') },
  { id: '2', name: 'Boston Celtics', abbr: 'BOS', color: '#007A33', logo: getNBALogo('BOS') },
  { id: '3', name: 'Brooklyn Nets', abbr: 'BKN', color: '#000000', logo: getNBALogo('BKN') },
  { id: '4', name: 'Charlotte Hornets', abbr: 'CHA', color: '#1D1160', logo: getNBALogo('CHA') },
  { id: '5', name: 'Chicago Bulls', abbr: 'CHI', color: '#CE1141', logo: getNBALogo('CHI') },
  { id: '6', name: 'Cleveland Cavaliers', abbr: 'CLE', color: '#860038', logo: getNBALogo('CLE') },
  { id: '7', name: 'Dallas Mavericks', abbr: 'DAL', color: '#00538C', logo: getNBALogo('DAL') },
  { id: '8', name: 'Denver Nuggets', abbr: 'DEN', color: '#0E2240', logo: getNBALogo('DEN') },
  { id: '9', name: 'Detroit Pistons', abbr: 'DET', color: '#C8102E', logo: getNBALogo('DET') },
  { id: '10', name: 'Golden State Warriors', abbr: 'GSW', color: '#1D428A', logo: getNBALogo('GSW') },
  { id: '11', name: 'Houston Rockets', abbr: 'HOU', color: '#CE1141', logo: getNBALogo('HOU') },
  { id: '12', name: 'Indiana Pacers', abbr: 'IND', color: '#002D62', logo: getNBALogo('IND') },
  { id: '13', name: 'LA Clippers', abbr: 'LAC', color: '#C8102E', logo: getNBALogo('LAC') },
  { id: '14', name: 'Los Angeles Lakers', abbr: 'LAL', color: '#552583', logo: getNBALogo('LAL') },
  { id: '15', name: 'Memphis Grizzlies', abbr: 'MEM', color: '#5D76A9', logo: getNBALogo('MEM') },
  { id: '16', name: 'Miami Heat', abbr: 'MIA', color: '#98002E', logo: getNBALogo('MIA') },
  { id: '17', name: 'Milwaukee Bucks', abbr: 'MIL', color: '#00471B', logo: getNBALogo('MIL') },
  { id: '18', name: 'Minnesota Timberwolves', abbr: 'MIN', color: '#0C2340', logo: getNBALogo('MIN') },
  { id: '19', name: 'New Orleans Pelicans', abbr: 'NOP', color: '#0C2340', logo: getNBALogo('NOP') },
  { id: '20', name: 'New York Knicks', abbr: 'NYK', color: '#006BB6', logo: getNBALogo('NYK') },
  { id: '21', name: 'Oklahoma City Thunder', abbr: 'OKC', color: '#007AC1', logo: getNBALogo('OKC') },
  { id: '22', name: 'Orlando Magic', abbr: 'ORL', color: '#0077C0', logo: getNBALogo('ORL') },
  { id: '23', name: 'Philadelphia 76ers', abbr: 'PHI', color: '#006BB6', logo: getNBALogo('PHI') },
  { id: '24', name: 'Phoenix Suns', abbr: 'PHX', color: '#1D1160', logo: getNBALogo('PHX') },
  { id: '25', name: 'Portland Trail Blazers', abbr: 'POR', color: '#E03A3E', logo: getNBALogo('POR') },
  { id: '26', name: 'Sacramento Kings', abbr: 'SAC', color: '#5A2D81', logo: getNBALogo('SAC') },
  { id: '27', name: 'San Antonio Spurs', abbr: 'SAS', color: '#C4CED4', logo: getNBALogo('SAS') },
  { id: '28', name: 'Toronto Raptors', abbr: 'TOR', color: '#CE1141', logo: getNBALogo('TOR') },
  { id: '29', name: 'Utah Jazz', abbr: 'UTA', color: '#002B5C', logo: getNBALogo('UTA') },
  { id: '30', name: 'Washington Wizards', abbr: 'WAS', color: '#002B5C', logo: getNBALogo('WAS') },
];

export const MOCK_SCHEDULE: GameSchedule[] = [
  { id: '101', home: 'LAL', away: 'GSW', time: '19:30', isToday: true },
  { id: '102', home: 'BOS', away: 'MIA', time: '20:00', isToday: true },
  { id: '103', home: 'DEN', away: 'PHX', time: '21:00', isToday: true },
  { id: '104', home: 'MIL', away: 'PHI', time: '19:00', isToday: false },
  { id: '105', home: 'DAL', away: 'HOU', time: '20:30', isToday: false },
];