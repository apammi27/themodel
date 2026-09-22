"""
Canonical Team Resolver for 8rain Station EV Engine
Maps official team short-codes, city names, and mascots to canonical alias lists.
"""

TEAM_DICTIONARY = {
    # MLB
    'AZ': {'name': 'Arizona Diamondbacks', 'city': 'Arizona', 'mascot': 'Diamondbacks', 'aliases': ['AZ', 'DIAMONDBACKS', 'D-BACKS', 'ARIZONA']},
    'ATH': {'name': 'Athletics', 'city': 'Oakland', 'mascot': 'Athletics', 'aliases': ['ATH', 'ATHLETICS', 'A\'S', 'OAKLAND']},
    'ATL': {'name': 'Atlanta Braves', 'city': 'Atlanta', 'mascot': 'Braves', 'aliases': ['ATL', 'BRAVES', 'ATLANTA']},
    'BAL': {'name': 'Baltimore Orioles', 'city': 'Baltimore', 'mascot': 'Orioles', 'aliases': ['BAL', 'ORIOLES', 'BALTIMORE']},
    'BOS': {'name': 'Boston Red Sox', 'city': 'Boston', 'mascot': 'Red Sox', 'aliases': ['BOS', 'RED SOX', 'BOSTON', 'BRUINS', 'CELTICS']},
    'CHC': {'name': 'Chicago Cubs', 'city': 'Chicago', 'mascot': 'Cubs', 'aliases': ['CHC', 'CUBS', 'CHICAGO']},
    'CWS': {'name': 'Chicago White Sox', 'city': 'Chicago', 'mascot': 'White Sox', 'aliases': ['CWS', 'WHITE SOX']},
    'CIN': {'name': 'Cincinnati Reds', 'city': 'Cincinnati', 'mascot': 'Reds', 'aliases': ['CIN', 'REDS', 'CINCINNATI', 'BENGALS']},
    'CLE': {'name': 'Cleveland Guardians', 'city': 'Cleveland', 'mascot': 'Guardians', 'aliases': ['CLE', 'GUARDIANS', 'CLEVELAND', 'BROWNS', 'CAVALIERS']},
    'COL': {'name': 'Colorado Rockies', 'city': 'Colorado', 'mascot': 'Rockies', 'aliases': ['COL', 'ROCKIES', 'COLORADO', 'AVALANCHE']},
    'DET': {'name': 'Detroit Tigers', 'city': 'Detroit', 'mascot': 'Tigers', 'aliases': ['DET', 'TIGERS', 'DETROIT', 'LIONS', 'PISTONS', 'RED WINGS']},
    'HOU': {'name': 'Houston Astros', 'city': 'Houston', 'mascot': 'Astros', 'aliases': ['HOU', 'ASTROS', 'HOUSTON', 'TEXANS', 'ROCKETS']},
    'KC': {'name': 'Kansas City Royals', 'city': 'Kansas City', 'mascot': 'Royals', 'aliases': ['KC', 'ROYALS', 'KANSAS CITY', 'CHIEFS']},
    'LAA': {'name': 'Los Angeles Angels', 'city': 'Los Angeles', 'mascot': 'Angels', 'aliases': ['LAA', 'ANGELS']},
    'LAD': {'name': 'Los Angeles Dodgers', 'city': 'Los Angeles', 'mascot': 'Dodgers', 'aliases': ['LAD', 'DODGERS']},
    'MIA': {'name': 'Miami Marlins', 'city': 'Miami', 'mascot': 'Marlins', 'aliases': ['MIA', 'MARLINS', 'MIAMI', 'DOLPHINS', 'HEAT']},
    'MIL': {'name': 'Milwaukee Brewers', 'city': 'Milwaukee', 'mascot': 'Brewers', 'aliases': ['MIL', 'BREWERS', 'MILWAUKEE', 'BUCKS']},
    'MIN': {'name': 'Minnesota Twins', 'city': 'Minnesota', 'mascot': 'Twins', 'aliases': ['MIN', 'TWINS', 'MINNESOTA', 'VIKINGS', 'WILD', 'TIMBERWOLVES', 'LYNX']},
    'NYM': {'name': 'New York Mets', 'city': 'New York', 'mascot': 'Mets', 'aliases': ['NYM', 'METS']},
    'NYY': {'name': 'New York Yankees', 'city': 'New York', 'mascot': 'Yankees', 'aliases': ['NYY', 'YANKEES']},
    'PHI': {'name': 'Philadelphia Phillies', 'city': 'Philadelphia', 'mascot': 'Phillies', 'aliases': ['PHI', 'PHILLIES', 'PHILADELPHIA', 'EAGLES', '76ERS', 'FLYERS']},
    'PIT': {'name': 'Pittsburgh Pirates', 'city': 'Pittsburgh', 'mascot': 'Pirates', 'aliases': ['PIT', 'PIRATES', 'PITTSBURGH', 'STEELERS', 'PENGUINS']},
    'SD': {'name': 'San Diego Padres', 'city': 'San Diego', 'mascot': 'Padres', 'aliases': ['SD', 'PADRES', 'SAN DIEGO']},
    'SF': {'name': 'San Francisco Giants', 'city': 'San Francisco', 'mascot': 'Giants', 'aliases': ['SF', 'GIANTS', 'SAN FRANCISCO', '49ERS', 'NINERS']},
    'SEA': {'name': 'Seattle Mariners', 'city': 'Seattle', 'mascot': 'Mariners', 'aliases': ['SEA', 'MARINERS', 'SEATTLE', 'SEAHAWKS', 'KRAKEN', 'STORM']},
    'STL': {'name': 'St. Louis Cardinals', 'city': 'St. Louis', 'mascot': 'Cardinals', 'aliases': ['STL', 'CARDINALS', 'ST. LOUIS', 'BLUES']},
    'TB': {'name': 'Tampa Bay Rays', 'city': 'Tampa Bay', 'mascot': 'Rays', 'aliases': ['TB', 'RAYS', 'TAMPA BAY', 'BUCCANEERS', 'LIGHTNING']},
    'TEX': {'name': 'Texas Rangers', 'city': 'Texas', 'mascot': 'Rangers', 'aliases': ['TEX', 'RANGERS', 'TEXAS']},
    'TOR': {'name': 'Toronto Blue Jays', 'city': 'Toronto', 'mascot': 'Blue Jays', 'aliases': ['TOR', 'BLUE JAYS', 'TORONTO', 'RAPTORS', 'MAPLE LEAFS']},
    'WSH': {'name': 'Washington Nationals', 'city': 'Washington', 'mascot': 'Nationals', 'aliases': ['WSH', 'NATIONALS', 'WASHINGTON', 'CAPITALS']},

    # NHL (additional)
    'ANA': {'name': 'Anaheim Ducks', 'city': 'Anaheim', 'mascot': 'Ducks', 'aliases': ['ANA', 'DUCKS']},
    'BUF': {'name': 'Buffalo Sabres', 'city': 'Buffalo', 'mascot': 'Sabres', 'aliases': ['BUF', 'SABRES', 'BUFFALO', 'BILLS']},
    'CGY': {'name': 'Calgary Flames', 'city': 'Calgary', 'mascot': 'Flames', 'aliases': ['CGY', 'FLAMES', 'CALGARY']},
    'CAR': {'name': 'Carolina Hurricanes', 'city': 'Carolina', 'mascot': 'Hurricanes', 'aliases': ['CAR', 'HURRICANES', 'CANES', 'PANTHERS']},
    'CHI': {'name': 'Chicago Blackhawks', 'city': 'Chicago', 'mascot': 'Blackhawks', 'aliases': ['CHI', 'BLACKHAWKS', 'HAWKS', 'BEARS', 'BULLS']},
    'CBJ': {'name': 'Columbus Blue Jackets', 'city': 'Columbus', 'mascot': 'Blue Jackets', 'aliases': ['CBJ', 'BLUE JACKETS']},
    'DAL': {'name': 'Dallas Stars', 'city': 'Dallas', 'mascot': 'Stars', 'aliases': ['DAL', 'STARS', 'DALLAS', 'COWBOYS', 'MAVERICKS', 'WINGS']},
    'EDM': {'name': 'Edmonton Oilers', 'city': 'Edmonton', 'mascot': 'Oilers', 'aliases': ['EDM', 'OILERS', 'EDMONTON']},
    'FLA': {'name': 'Florida Panthers', 'city': 'Florida', 'mascot': 'Panthers', 'aliases': ['FLA', 'PANTHERS', 'FLORIDA']},
    'LAK': {'name': 'Los Angeles Kings', 'city': 'Los Angeles', 'mascot': 'Kings', 'aliases': ['LAK', 'KINGS']},
    'MTL': {'name': 'Montreal Canadiens', 'city': 'Montreal', 'mascot': 'Canadiens', 'aliases': ['MTL', 'CANADIENS', 'HABS']},
    'NSH': {'name': 'Nashville Predators', 'city': 'Nashville', 'mascot': 'Predators', 'aliases': ['NSH', 'PREDATORS', 'PREDS']},
    'NJD': {'name': 'New Jersey Devils', 'city': 'New Jersey', 'mascot': 'Devils', 'aliases': ['NJD', 'DEVILS']},
    'NYI': {'name': 'New York Islanders', 'city': 'New York', 'mascot': 'Islanders', 'aliases': ['NYI', 'ISLANDERS']},
    'NYR': {'name': 'New York Rangers', 'city': 'New York', 'mascot': 'Rangers', 'aliases': ['NYR', 'RANGERS']},
    'OTT': {'name': 'Ottawa Senators', 'city': 'Ottawa', 'mascot': 'Senators', 'aliases': ['OTT', 'SENATORS', 'SENS']},
    'SJS': {'name': 'San Jose Sharks', 'city': 'San Jose', 'mascot': 'Sharks', 'aliases': ['SJS', 'SHARKS']},
    'TBL': {'name': 'Tampa Bay Lightning', 'city': 'Tampa Bay', 'mascot': 'Lightning', 'aliases': ['TBL', 'LIGHTNING']},
    'UTA': {'name': 'Utah Mammoth', 'city': 'Utah', 'mascot': 'Mammoth', 'aliases': ['UTA', 'UTAH', 'JAZZ']},
    'VAN': {'name': 'Vancouver Canucks', 'city': 'Vancouver', 'mascot': 'Canucks', 'aliases': ['VAN', 'CANUCKS']},
    'VGK': {'name': 'Vegas Golden Knights', 'city': 'Vegas', 'mascot': 'Golden Knights', 'aliases': ['VGK', 'KNIGHTS', 'VEGAS']},
    'WPG': {'name': 'Winnipeg Jets', 'city': 'Winnipeg', 'mascot': 'Jets', 'aliases': ['WPG', 'JETS']},

    # NBA (additional)
    'BKN': {'name': 'Brooklyn Nets', 'city': 'Brooklyn', 'mascot': 'Nets', 'aliases': ['BKN', 'NETS', 'BROOKLYN']},
    'CHA': {'name': 'Charlotte Hornets', 'city': 'Charlotte', 'mascot': 'Hornets', 'aliases': ['CHA', 'HORNETS', 'CHARLOTTE']},
    'DEN': {'name': 'Denver Nuggets', 'city': 'Denver', 'mascot': 'Nuggets', 'aliases': ['DEN', 'NUGGETS', 'DENVER', 'BRONCOS']},
    'GSW': {'name': 'Golden State Warriors', 'city': 'Golden State', 'mascot': 'Warriors', 'aliases': ['GSW', 'WARRIORS']},
    'IND': {'name': 'Indiana Pacers', 'city': 'Indiana', 'mascot': 'Pacers', 'aliases': ['IND', 'PACERS', 'INDIANA', 'COLTS']},
    'LAC': {'name': 'Los Angeles Clippers / Chargers', 'city': 'Los Angeles', 'mascot': 'Chargers', 'aliases': ['LAC', 'CHARGERS', 'LA CHARGERS', 'CLIPPERS']},
    'LAL': {'name': 'Los Angeles Lakers', 'city': 'Los Angeles', 'mascot': 'Lakers', 'aliases': ['LAL', 'LAKERS']},
    'MEM': {'name': 'Memphis Grizzlies', 'city': 'Memphis', 'mascot': 'Grizzlies', 'aliases': ['MEM', 'GRIZZLIES', 'MEMPHIS']},
    'NOP': {'name': 'New Orleans Pelicans', 'city': 'New Orleans', 'mascot': 'Pelicans', 'aliases': ['NOP', 'PELICANS', 'SAINTS']},
    'NYK': {'name': 'New York Knicks', 'city': 'New York', 'mascot': 'Knicks', 'aliases': ['NYK', 'KNICKS']},
    'OKC': {'name': 'Oklahoma City Thunder', 'city': 'Oklahoma City', 'mascot': 'Thunder', 'aliases': ['OKC', 'THUNDER']},
    'ORL': {'name': 'Orlando Magic', 'city': 'Orlando', 'mascot': 'Magic', 'aliases': ['ORL', 'MAGIC', 'ORLANDO']},
    'PHO': {'name': 'Phoenix Suns', 'city': 'Phoenix', 'mascot': 'Suns', 'aliases': ['PHO', 'PHX', 'SUNS', 'PHOENIX']},
    'POR': {'name': 'Portland Trail Blazers', 'city': 'Portland', 'mascot': 'Trail Blazers', 'aliases': ['POR', 'BLAZERS', 'TRAIL BLAZERS']},
    'SAC': {'name': 'Sacramento Kings', 'city': 'Sacramento', 'mascot': 'Kings', 'aliases': ['SAC', 'KINGS', 'SACRAMENTO']},
    'SAS': {'name': 'San Antonio Spurs', 'city': 'San Antonio', 'mascot': 'Spurs', 'aliases': ['SAS', 'SPURS', 'SAN ANTONIO']},

    # NFL (additional)
    'ARI': {'name': 'Arizona Cardinals', 'city': 'Arizona', 'mascot': 'Cardinals', 'aliases': ['ARI', 'CARDINALS', 'ARIZONA']},
    'BAL': {'name': 'Baltimore Ravens', 'city': 'Baltimore', 'mascot': 'Ravens', 'aliases': ['BAL', 'RAVENS', 'BALTIMORE']},
    'GB': {'name': 'Green Bay Packers', 'city': 'Green Bay', 'mascot': 'Packers', 'aliases': ['GB', 'PACKERS', 'GREEN BAY']},
    'JAX': {'name': 'Jacksonville Jaguars', 'city': 'Jacksonville', 'mascot': 'Jaguars', 'aliases': ['JAX', 'JAGUARS', 'JACKSONVILLE']},
    'LV': {'name': 'Las Vegas Raiders', 'city': 'Las Vegas', 'mascot': 'Raiders', 'aliases': ['LV', 'RAIDERS', 'VEGAS']},
    'LAR': {'name': 'Los Angeles Rams', 'city': 'Los Angeles', 'mascot': 'Rams', 'aliases': ['LAR', 'RAMS']},
    'NE': {'name': 'New England Patriots', 'city': 'New England', 'mascot': 'Patriots', 'aliases': ['NE', 'PATRIOTS', 'PATS']},
    'NO': {'name': 'New Orleans Saints', 'city': 'New Orleans', 'mascot': 'Saints', 'aliases': ['NO', 'SAINTS']},
    'NYG': {'name': 'New York Giants', 'city': 'New York', 'mascot': 'Giants', 'aliases': ['NYG', 'GIANTS']},
    'NYJ': {'name': 'New York Jets', 'city': 'New York', 'mascot': 'Jets', 'aliases': ['NYJ', 'JETS']},
    'TEN': {'name': 'Tennessee Titans', 'city': 'Tennessee', 'mascot': 'Titans', 'aliases': ['TEN', 'TITANS']},

    # EPL
    'ARS': {'name': 'Arsenal', 'city': 'London', 'mascot': 'Arsenal', 'aliases': ['ARS', 'ARSENAL']},
    'AVL': {'name': 'Aston Villa', 'city': 'Birmingham', 'mascot': 'Aston Villa', 'aliases': ['AVL', 'ASTON VILLA', 'VILLA']},
    'BHA': {'name': 'Brighton & Hove Albion', 'city': 'Brighton', 'mascot': 'Brighton', 'aliases': ['BHA', 'BRIGHTON']},
    'BRE': {'name': 'Brentford', 'city': 'London', 'mascot': 'Brentford', 'aliases': ['BRE', 'BRENTFORD']},
    'BRN': {'name': 'Burnley', 'city': 'Burnley', 'mascot': 'Burnley', 'aliases': ['BRN', 'BURNLEY']},
    'CHE': {'name': 'Chelsea', 'city': 'London', 'mascot': 'Chelsea', 'aliases': ['CHE', 'CHELSEA']},
    'CRY': {'name': 'Crystal Palace', 'city': 'London', 'mascot': 'Crystal Palace', 'aliases': ['CRY', 'CRYSTAL PALACE', 'PALACE']},
    'EVE': {'name': 'Everton', 'city': 'Liverpool', 'mascot': 'Everton', 'aliases': ['EVE', 'EVERTON']},
    'FUL': {'name': 'Fulham', 'city': 'London', 'mascot': 'Fulham', 'aliases': ['FUL', 'FULHAM']},
    'LEE': {'name': 'Leeds United', 'city': 'Leeds', 'mascot': 'Leeds', 'aliases': ['LEE', 'LEEDS']},
    'LIV': {'name': 'Liverpool', 'city': 'Liverpool', 'mascot': 'Liverpool', 'aliases': ['LIV', 'LIVERPOOL']},
    'MCI': {'name': 'Manchester City', 'city': 'Manchester', 'mascot': 'Man City', 'aliases': ['MCI', 'MAN CITY', 'MANCHESTER CITY']},
    'MUN': {'name': 'Manchester United', 'city': 'Manchester', 'mascot': 'Man Utd', 'aliases': ['MUN', 'MAN UTD', 'MANCHESTER UNITED']},
    'NEW': {'name': 'Newcastle United', 'city': 'Newcastle', 'mascot': 'Newcastle', 'aliases': ['NEW', 'NEWCASTLE']},
    'NFO': {'name': 'Nottingham Forest', 'city': 'Nottingham', 'mascot': 'Forest', 'aliases': ['NFO', 'FOREST', 'NOTTINGHAM']},
    'SUN': {'name': 'Sunderland', 'city': 'Sunderland', 'mascot': 'Sunderland', 'aliases': ['SUN', 'SUNDERLAND']},
    'TOT': {'name': 'Tottenham Hotspur', 'city': 'London', 'mascot': 'Spurs', 'aliases': ['TOT', 'SPURS', 'TOTTENHAM']},
    'WHU': {'name': 'West Ham United', 'city': 'London', 'mascot': 'West Ham', 'aliases': ['WHU', 'WEST HAM']},
    'WOL': {'name': 'Wolverhampton', 'city': 'Wolverhampton', 'mascot': 'Wolves', 'aliases': ['WOL', 'WOLVES', 'WOLVERHAMPTON']},

    # WNBA
    'CON': {'name': 'Connecticut Sun', 'city': 'Connecticut', 'mascot': 'Sun', 'aliases': ['CON', 'SUN', 'CONNECTICUT']},
    'GSV': {'name': 'Golden State Valkyries', 'city': 'Golden State', 'mascot': 'Valkyries', 'aliases': ['GSV', 'VALKYRIES']},
    'LVA': {'name': 'Las Vegas Aces', 'city': 'Las Vegas', 'mascot': 'Aces', 'aliases': ['LVA', 'ACES']},
    'LAS': {'name': 'Los Angeles Sparks', 'city': 'Los Angeles', 'mascot': 'Sparks', 'aliases': ['LAS', 'SPARKS']},
    'NYL': {'name': 'New York Liberty', 'city': 'New York', 'mascot': 'Liberty', 'aliases': ['NYL', 'LIBERTY']},
}

def resolve_team(code_or_name):
    if not code_or_name:
        return None
    key = str(code_or_name).strip().upper()
    if key in TEAM_DICTIONARY:
        return TEAM_DICTIONARY[key]
    
    # Search by alias
    for info in TEAM_DICTIONARY.values():
        if any(alias == key or alias in key for alias in info['aliases']):
            return info

    return {'name': key, 'city': key, 'mascot': key, 'aliases': [key]}
