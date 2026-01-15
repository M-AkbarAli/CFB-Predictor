/**
 * Team logo placeholder component.
 * Displays team abbreviation/initials in a circular badge.
 */

interface TeamLogoProps {
  team: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function TeamLogo({
  team,
  size = 'md',
  className = '',
}: TeamLogoProps) {
  // Extract abbreviation from team name
  // Try to get initials or common abbreviation
  const getAbbreviation = (teamName: string): string => {
    // Common team abbreviations
    const abbreviations: Record<string, string> = {
      'Alabama': 'ALA',
      'Ohio State': 'OSU',
      'Georgia': 'UGA',
      'Michigan': 'MICH',
      'Texas': 'TEX',
      'Oregon': 'ORE',
      'Notre Dame': 'ND',
      'Penn State': 'PSU',
      'Florida State': 'FSU',
      'LSU': 'LSU',
      'Oklahoma': 'OU',
      'Clemson': 'CLEM',
      'USC': 'USC',
      'Tennessee': 'TENN',
      'Washington': 'WASH',
      'Utah': 'UTAH',
      'Ole Miss': 'MISS',
      'Texas A&M': 'TAMU',
      'Miami': 'MIA',
      'Indiana': 'IU',
      'Texas Tech': 'TT',
      'James Madison': 'JMU',
      'Tulane': 'TUL',
      'BYU': 'BYU',
      'Vanderbilt': 'VAN',
    };

    if (abbreviations[teamName]) {
      return abbreviations[teamName];
    }

    // Fallback: use first letters of words
    const words = teamName.split(' ');
    if (words.length > 1) {
      return words
        .map((w) => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 3);
    }

    // Single word: use first 3 letters
    return teamName.slice(0, 3).toUpperCase();
  };

  const abbreviation = getAbbreviation(team);
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-xs',
    lg: 'w-16 h-16 text-base',
  };

  return (
    <div
      className={`${sizeClasses[size]} ${className} rounded-full bg-gradient-to-br from-blue-600 to-blue-800 text-white font-bold flex items-center justify-center shadow-md border-2 border-white`}
      title={team}
    >
      {abbreviation}
    </div>
  );
}
