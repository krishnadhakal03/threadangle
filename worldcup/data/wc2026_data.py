"""
Hardcoded, accurate World Cup 2026 data.

Replaces fragile Wikipedia/regex parsing. All historical figures are verified.
Group assignments are from the official FIFA draw held 2025-12-05 in Miami.

Sources: FIFA.com, Wikipedia, Transfermarkt (as of 2025).
"""
from __future__ import annotations

# ── Team history ───────────────────────────────────────────────────────────────
# Keys: titles, appearances, best_finish, famous_players, titles_years

TEAM_HISTORY: dict[str, dict] = {
    "brazil": {
        "titles": 5,
        "titles_years": [1958, 1962, 1970, 1994, 2002],
        "appearances": 23,   # every tournament 1930-2022, plus WC 2026
        "best_finish": "Champions",
        "famous_players": ["Pelé", "Ronaldo", "Ronaldinho", "Zico", "Cafu", "Roberto Carlos"],
    },
    "germany": {
        "titles": 4,
        "titles_years": [1954, 1974, 1990, 2014],
        "appearances": 20,
        "best_finish": "Champions",
        "famous_players": ["Franz Beckenbauer", "Gerd Müller", "Lothar Matthäus", "Miroslav Klose", "Oliver Kahn"],
    },
    "italy": {
        "titles": 4,
        "titles_years": [1934, 1938, 1982, 2006],
        "appearances": 18,
        "best_finish": "Champions",
        "famous_players": ["Paolo Maldini", "Roberto Baggio", "Gianluigi Buffon", "Alessandro Del Piero", "Franco Baresi"],
    },
    "argentina": {
        "titles": 3,
        "titles_years": [1978, 1986, 2022],
        "appearances": 18,
        "best_finish": "Champions",
        "famous_players": ["Diego Maradona", "Lionel Messi", "Gabriel Batistuta", "Osvaldo Ardiles", "Mario Kempes"],
    },
    "france": {
        "titles": 2,
        "titles_years": [1998, 2018],
        "appearances": 16,
        "best_finish": "Champions",
        "famous_players": ["Zinedine Zidane", "Michel Platini", "Thierry Henry", "Didier Deschamps", "Kylian Mbappe"],
    },
    "uruguay": {
        "titles": 2,
        "titles_years": [1930, 1950],
        "appearances": 14,
        "best_finish": "Champions",
        "famous_players": ["Luis Suarez", "Diego Forlan", "Enzo Francescoli", "Alvaro Recoba"],
    },
    "england": {
        "titles": 1,
        "titles_years": [1966],
        "appearances": 16,
        "best_finish": "Champions (1966)",
        "famous_players": ["Bobby Moore", "Bobby Charlton", "Gary Lineker", "David Beckham", "Wayne Rooney", "Harry Kane"],
    },
    "spain": {
        "titles": 1,
        "titles_years": [2010],
        "appearances": 15,
        "best_finish": "Champions (2010)",
        "famous_players": ["Xavi", "Iniesta", "Raul", "Fernando Torres", "Iker Casillas", "David Villa"],
    },
    "netherlands": {
        "titles": 0,
        "titles_years": [],
        "appearances": 11,
        "best_finish": "Runner-up (1974, 1978, 2010)",
        "famous_players": ["Johan Cruyff", "Ruud Gullit", "Marco van Basten", "Arjen Robben", "Virgil van Dijk"],
    },
    "portugal": {
        "titles": 0,
        "titles_years": [],
        "appearances": 9,
        "best_finish": "3rd Place (1966)",
        "famous_players": ["Eusebio", "Luis Figo", "Rui Costa", "Cristiano Ronaldo"],
    },
    "croatia": {
        "titles": 0,
        "titles_years": [],
        "appearances": 7,
        "best_finish": "Runner-up (2018)",
        "famous_players": ["Luka Modric", "Davor Suker", "Robert Prosinecki", "Ivan Rakitic"],
    },
    "belgium": {
        "titles": 0,
        "titles_years": [],
        "appearances": 14,
        "best_finish": "3rd Place (2018)",
        "famous_players": ["Eden Hazard", "Kevin De Bruyne", "Romelu Lukaku", "Jan Vertonghen", "Thibaut Courtois"],
    },
    "morocco": {
        "titles": 0,
        "titles_years": [],
        "appearances": 6,
        "best_finish": "Semi-final (2022)",
        "famous_players": ["Hakim Ziyech", "Achraf Hakimi", "Yassine Bounou", "Sofiane Boufal"],
    },
    "japan": {
        "titles": 0,
        "titles_years": [],
        "appearances": 7,
        "best_finish": "Round of 16",
        "famous_players": ["Hidetoshi Nakata", "Shunsuke Nakamura", "Shinji Kagawa", "Takumi Minamino"],
    },
    "usa": {
        "titles": 0,
        "titles_years": [],
        "appearances": 11,
        "best_finish": "Semi-final (1930)",
        "famous_players": ["Landon Donovan", "Clint Dempsey", "Tim Howard", "Christian Pulisic", "Gio Reyna"],
    },
    "mexico": {
        "titles": 0,
        "titles_years": [],
        "appearances": 17,
        "best_finish": "Quarter-final (1970, 1986)",
        "famous_players": ["Hugo Sanchez", "Cuauhtemoc Blanco", "Rafael Marquez", "Chicharito", "Memo Ochoa"],
    },
    "colombia": {
        "titles": 0,
        "titles_years": [],
        "appearances": 6,
        "best_finish": "Quarter-final (2014)",
        "famous_players": ["Carlos Valderrama", "Tino Asprilla", "Rene Higuita", "Radamel Falcao", "James Rodriguez"],
    },
    "canada": {
        "titles": 0,
        "titles_years": [],
        "appearances": 2,
        "best_finish": "Group Stage",
        "famous_players": ["Alphonso Davies", "Jonathan David", "Cyle Larin", "Milan Borjan"],
    },
    "ecuador": {
        "titles": 0,
        "titles_years": [],
        "appearances": 4,
        "best_finish": "Round of 16",
        "famous_players": ["Agustin Delgado", "Ivan Hurtado", "Enner Valencia"],
    },
    "senegal": {
        "titles": 0,
        "titles_years": [],
        "appearances": 3,
        "best_finish": "Quarter-final (2002)",
        "famous_players": ["El-Hadji Diouf", "Khalilou Fadiga", "Sadio Mane", "Kalidou Koulibaly"],
    },
    "south korea": {
        "titles": 0,
        "titles_years": [],
        "appearances": 11,
        "best_finish": "4th Place (2002)",
        "famous_players": ["Park Ji-sung", "Hong Myung-bo", "Son Heung-min", "Lee Kang-in"],
    },
    "australia": {
        "titles": 0,
        "titles_years": [],
        "appearances": 6,
        "best_finish": "Round of 16 (2006, 2022)",
        "famous_players": ["Tim Cahill", "Harry Kewell", "Mark Schwarzer", "Mathew Leckie"],
    },
    "switzerland": {
        "titles": 0,
        "titles_years": [],
        "appearances": 12,
        "best_finish": "Quarter-final (1934, 1938, 1954)",
        "famous_players": ["Xherdan Shaqiri", "Granit Xhaka", "Stephan Lichtsteiner"],
    },
    "serbia": {
        "titles": 0,
        "titles_years": [],
        "appearances": 13,
        "best_finish": "Runner-up as Yugoslavia (1954)",
        "famous_players": ["Dragan Dzajic", "Nemanja Vidic", "Dusan Tadic", "Aleksandar Mitrovic"],
    },
    "ghana": {
        "titles": 0,
        "titles_years": [],
        "appearances": 4,
        "best_finish": "Quarter-final (2010)",
        "famous_players": ["Abedi Pele", "Michael Essien", "Asamoah Gyan", "Thomas Partey"],
    },
    "chile": {
        "titles": 0,
        "titles_years": [],
        "appearances": 9,
        "best_finish": "3rd Place (1962)",
        "famous_players": ["Marcelo Salas", "Ivan Zamorano", "Arturo Vidal", "Alexis Sanchez"],
    },
    "iran": {
        "titles": 0,
        "titles_years": [],
        "appearances": 6,
        "best_finish": "Group Stage",
        "famous_players": ["Ali Daei", "Mehdi Mahdavikia", "Sardar Azmoun", "Mehdi Taremi"],
    },
    "scotland": {
        "titles": 0,
        "titles_years": [],
        "appearances": 8,
        "best_finish": "Group Stage",
        "famous_players": ["Denis Law", "Kenny Dalglish", "Graeme Souness", "Andy Robertson"],
    },
    "haiti": {
        "titles": 0,
        "titles_years": [],
        "appearances": 1,
        "best_finish": "Group Stage (1974)",
        "famous_players": ["Emmanuel Sanon", "Duckens Nazon", "Frantzdy Pierrot"],
    },
    "paraguay": {
        "titles": 0,
        "titles_years": [],
        "appearances": 8,
        "best_finish": "Quarter-final (2010)",
        "famous_players": ["Jose Luis Chilavert", "Roque Santa Cruz", "Salvador Cabanas"],
    },
    "turkey": {
        "titles": 0,
        "titles_years": [],
        "appearances": 2,
        "best_finish": "3rd Place (2002)",
        "famous_players": ["Hakan Sukur", "Tugay Kerimoglu", "Arda Turan", "Hakan Calhanoglu"],
    },
    "ivory coast": {
        "titles": 0,
        "titles_years": [],
        "appearances": 3,
        "best_finish": "Group Stage",
        "famous_players": ["Didier Drogba", "Yaya Toure", "Kolo Toure", "Franck Kessie"],
    },
    "sweden": {
        "titles": 0,
        "titles_years": [],
        "appearances": 12,
        "best_finish": "Runner-up (1958)",
        "famous_players": ["Gunnar Nordahl", "Nils Liedholm", "Henke Larsson", "Zlatan Ibrahimovic"],
    },
    "tunisia": {
        "titles": 0,
        "titles_years": [],
        "appearances": 6,
        "best_finish": "Group Stage",
        "famous_players": ["Hatem Trabelsi", "Sami Trabelsi", "Wahbi Khazri", "Youssef Msakni"],
    },
    "egypt": {
        "titles": 0,
        "titles_years": [],
        "appearances": 3,
        "best_finish": "Group Stage",
        "famous_players": ["Hossam Hassan", "Ahmed Hassan", "Mohamed Salah"],
    },
    "new zealand": {
        "titles": 0,
        "titles_years": [],
        "appearances": 2,
        "best_finish": "Group Stage",
        "famous_players": ["Vaughan Coveny", "Ryan Nelsen", "Chris Wood"],
    },
    "cape verde": {
        "titles": 0,
        "titles_years": [],
        "appearances": 0,
        "best_finish": "First appearance",
        "famous_players": ["Ryan Mendes", "Garry Rodrigues", "Julio Tavares"],
    },
    "saudi arabia": {
        "titles": 0,
        "titles_years": [],
        "appearances": 6,
        "best_finish": "Round of 16 (1994)",
        "famous_players": ["Sami Al-Jaber", "Yasser Al-Qahtani", "Salem Al-Dawsari"],
    },
    "iraq": {
        "titles": 0,
        "titles_years": [],
        "appearances": 1,
        "best_finish": "Group Stage (1986)",
        "famous_players": ["Ahmed Radhi", "Emad Mohammed", "Mohanad Ali"],
    },
    "norway": {
        "titles": 0,
        "titles_years": [],
        "appearances": 3,
        "best_finish": "Round of 16 (1938)",
        "famous_players": ["Jahn Ivar Jakobsen", "Ole Gunnar Solskjaer", "Erling Haaland"],
    },
    "algeria": {
        "titles": 0,
        "titles_years": [],
        "appearances": 4,
        "best_finish": "Round of 16 (2014)",
        "famous_players": ["Lakhdar Belloumi", "Rabah Madjer", "Riyad Mahrez", "Islam Slimani"],
    },
    "austria": {
        "titles": 0,
        "titles_years": [],
        "appearances": 7,
        "best_finish": "3rd Place (1954)",
        "famous_players": ["Ernst Ocwirk", "Hans Krankl", "David Alaba", "Marcel Sabitzer"],
    },
    "jordan": {
        "titles": 0,
        "titles_years": [],
        "appearances": 0,
        "best_finish": "First appearance",
        "famous_players": ["Ahmad Hayel", "Baha Faisal", "Yazan Al-Naimat"],
    },
    "dr congo": {
        "titles": 0,
        "titles_years": [],
        "appearances": 1,
        "best_finish": "Group Stage (1974 as Zaire)",
        "famous_players": ["Ndaye Mulamba", "Cedric Bakambu", "Chancel Mbemba"],
    },
    "uzbekistan": {
        "titles": 0,
        "titles_years": [],
        "appearances": 0,
        "best_finish": "First appearance",
        "famous_players": ["Odil Ahmedov", "Eldor Shomurodov", "Abbosbek Fayzullaev"],
    },
    "panama": {
        "titles": 0,
        "titles_years": [],
        "appearances": 1,
        "best_finish": "Group Stage (2018)",
        "famous_players": ["Roman Torres", "Blas Perez", "Alfredo Tejada", "Frederico Baloy"],
    },
    "south africa": {
        "titles": 0,
        "titles_years": [],
        "appearances": 3,
        "best_finish": "Group Stage",
        "famous_players": ["Benni McCarthy", "Lucas Radebe", "Siyanda Xulu", "Bafana Bafana"],
    },
    "czech republic": {
        "titles": 0,
        "titles_years": [],
        "appearances": 9,   # including Czechoslovakia
        "best_finish": "Runner-up (1934, 1962 as Czechoslovakia)",
        "famous_players": ["Pavel Nedved", "Tomas Rosicky", "Petr Cech", "Patrik Schick"],
    },
    "bosnia and herzegovina": {
        "titles": 0,
        "titles_years": [],
        "appearances": 1,
        "best_finish": "Group Stage (2014)",
        "famous_players": ["Edin Dzeko", "Miralem Pjanic", "Asmir Begovic", "Vedad Ibisevic"],
    },
    "qatar": {
        "titles": 0,
        "titles_years": [],
        "appearances": 1,
        "best_finish": "Group Stage (2022)",
        "famous_players": ["Hassan Al-Haydos", "Almoez Ali", "Akram Afif"],
    },
    "curacao": {
        "titles": 0,
        "titles_years": [],
        "appearances": 0,
        "best_finish": "First appearance",
        "famous_players": ["Leandro Bacuna", "Cuco Martina", "Jurien Gaari"],
    },
}


# ── Key players per team (WC 2026 squad focus) ────────────────────────────────
# Accurate as of mid-2025; clubs may have changed.

KEY_PLAYERS: dict[str, list[dict]] = {
    "brazil": [
        {"name": "Vinicius Jr",     "position": "FW", "club": "Real Madrid",   "country_goals": 24,
         "caps": 83,  "club_goals": 24, "market_value": "180M EUR",
         "hype_quote": "He runs the world."},
        {"name": "Rodrygo",         "position": "FW", "club": "Real Madrid",   "country_goals": 12,
         "caps": 55,  "club_goals": 15, "market_value": "100M EUR",
         "hype_quote": "Silently deadly."},
        {"name": "Endrick",         "position": "FW", "club": "Real Madrid",   "country_goals": 8,
         "caps": 22,  "club_goals": 12, "market_value": "60M EUR",
         "hype_quote": "The next legend starts here."},
        {"name": "Bruno Guimaraes", "position": "MF", "club": "Newcastle Utd", "country_goals": 5,
         "caps": 40,  "club_goals": 11, "market_value": "80M EUR",
         "hype_quote": "The engine of Brazil."},
        {"name": "Alisson Becker",  "position": "GK", "club": "Liverpool",     "country_goals": 0,
         "caps": 75,  "club_goals": 0,  "market_value": "40M EUR",
         "hype_quote": "The last line of defence."},
    ],
    "france": [
        {"name": "Kylian Mbappe",    "position": "FW", "club": "Real Madrid",    "country_goals": 47,
         "caps": 88,  "club_goals": 31, "market_value": "200M EUR",
         "hype_quote": "Born to win the biggest stage."},
        {"name": "Antoine Griezmann","position": "FW", "club": "Atletico Madrid","country_goals": 44,
         "caps": 134, "club_goals": 26, "market_value": "35M EUR",
         "hype_quote": "Always delivers when it matters."},
        {"name": "Ousmane Dembele",  "position": "FW", "club": "Paris SG",       "country_goals": 15,
         "caps": 62,  "club_goals": 24, "market_value": "60M EUR",
         "hype_quote": "Unstoppable on the wing."},
        {"name": "Eduardo Camavinga","position": "MF", "club": "Real Madrid",    "country_goals": 3,
         "caps": 28,  "club_goals": 5,  "market_value": "90M EUR",
         "hype_quote": "The future is now."},
        {"name": "Mike Maignan",     "position": "GK", "club": "AC Milan",       "country_goals": 0,
         "caps": 30,  "club_goals": 0,  "market_value": "45M EUR",
         "hype_quote": "A wall between the posts."},
    ],
    "england": [
        {"name": "Harry Kane",      "position": "FW", "club": "Bayern Munich", "country_goals": 68,
         "caps": 97,  "club_goals": 36, "market_value": "80M EUR",
         "hype_quote": "England's greatest ever striker."},
        {"name": "Jude Bellingham", "position": "MF", "club": "Real Madrid",   "country_goals": 14,
         "caps": 37,  "club_goals": 19, "market_value": "180M EUR",
         "hype_quote": "A generational talent."},
        # Phil Foden removed per issue #119
        {"name": "Bukayo Saka",     "position": "FW", "club": "Arsenal",       "country_goals": 17,
         "caps": 52,  "club_goals": 20, "market_value": "150M EUR",
         "hype_quote": "Arsenal's brightest star."},
        {"name": "Jordan Pickford", "position": "GK", "club": "Everton",       "country_goals": 0,
         "caps": 65,  "club_goals": 0,  "market_value": "25M EUR",
         "hype_quote": "A keeper of big moments."},
    ],
    "argentina": [
        {"name": "Lionel Messi",    "position": "FW", "club": "Inter Miami",    "country_goals": 109,
         "caps": 188, "club_goals": 11, "market_value": "30M EUR",
         "hype_quote": "The greatest to ever do it."},
        {"name": "Julian Alvarez",  "position": "FW", "club": "Atletico Madrid","country_goals": 24,
         "caps": 48,  "club_goals": 22, "market_value": "90M EUR",
         "hype_quote": "A champion in every sense."},
        {"name": "Rodrigo De Paul", "position": "MF", "club": "Atletico Madrid","country_goals": 15,
         "caps": 74,  "club_goals": 8,  "market_value": "30M EUR",
         "hype_quote": "The heartbeat of Argentina."},
        {"name": "Enzo Fernandez",  "position": "MF", "club": "Chelsea",        "country_goals": 7,
         "caps": 38,  "club_goals": 7,  "market_value": "80M EUR",
         "hype_quote": "World Cup winner at 21."},
        {"name": "Emiliano Martinez","position": "GK","club": "Aston Villa",    "country_goals": 0,
         "caps": 47,  "club_goals": 0,  "market_value": "30M EUR",
         "hype_quote": "The penalty king."},
    ],
    "spain": [
        {"name": "Lamine Yamal",    "position": "FW", "club": "Barcelona",     "country_goals": 10,
         "caps": 24,  "club_goals": 18, "market_value": "250M EUR",
         "hype_quote": "The 17-year-old superstar."},
        {"name": "Nico Williams",   "position": "FW", "club": "Athletic Club", "country_goals": 9,
         "caps": 26,  "club_goals": 14, "market_value": "100M EUR",
         "hype_quote": "Speed and skill combined."},
        {"name": "Pedri",           "position": "MF", "club": "Barcelona",     "country_goals": 8,
         "caps": 40,  "club_goals": 10, "market_value": "120M EUR",
         "hype_quote": "The Spanish maestro."},
        {"name": "Rodri",           "position": "MF", "club": "Man City",      "country_goals": 14,
         "caps": 60,  "club_goals": 9,  "market_value": "120M EUR",
         "hype_quote": "The Ballon d'Or brain."},
        {"name": "Unai Simon",      "position": "GK", "club": "Athletic Club", "country_goals": 0,
         "caps": 40,  "club_goals": 0,  "market_value": "30M EUR",
         "hype_quote": "Spain's safe hands."},
    ],
    "germany": [
        {"name": "Florian Wirtz",   "position": "MF", "club": "Bayer Leverkusen","country_goals": 14,
         "caps": 38,  "club_goals": 22, "market_value": "150M EUR",
         "hype_quote": "Germany's creative genius."},
        {"name": "Jamal Musiala",   "position": "MF", "club": "Bayern Munich",  "country_goals": 12,
         "caps": 48,  "club_goals": 20, "market_value": "150M EUR",
         "hype_quote": "Grace and power in one."},
        {"name": "Kai Havertz",     "position": "FW", "club": "Arsenal",        "country_goals": 26,
         "caps": 55,  "club_goals": 18, "market_value": "65M EUR",
         "hype_quote": "Goals at every level."},
        {"name": "Joshua Kimmich",  "position": "MF", "club": "Bayern Munich",  "country_goals": 10,
         "caps": 88,  "club_goals": 7,  "market_value": "55M EUR",
         "hype_quote": "Germany's leader on the pitch."},
        {"name": "Manuel Neuer",    "position": "GK", "club": "Bayern Munich",  "country_goals": 0,
         "caps": 124, "club_goals": 0,  "market_value": "10M EUR",
         "hype_quote": "A legend in goal."},
    ],
    "portugal": [
        {"name": "Cristiano Ronaldo","position": "FW", "club": "Al Nassr",     "country_goals": 134,
         "caps": 218, "club_goals": 35, "market_value": "15M EUR",
         "hype_quote": "The greatest goalscorer of all time."},
        {"name": "Bruno Fernandes", "position": "MF", "club": "Man United",    "country_goals": 23,
         "caps": 72,  "club_goals": 18, "market_value": "60M EUR",
         "hype_quote": "Portugal's creative force."},
        {"name": "Rafael Leao",     "position": "FW", "club": "AC Milan",      "country_goals": 10,
         "caps": 42,  "club_goals": 16, "market_value": "80M EUR",
         "hype_quote": "Lightning on the left wing."},
        {"name": "Bernardo Silva",  "position": "MF", "club": "Man City",      "country_goals": 22,
         "caps": 88,  "club_goals": 14, "market_value": "70M EUR",
         "hype_quote": "Consistent brilliance."},
        {"name": "Rui Patricio",    "position": "GK", "club": "Roma",          "country_goals": 0,
         "caps": 114, "club_goals": 0,  "market_value": "8M EUR",
         "hype_quote": "Experience when it counts."},
    ],
    "netherlands": [
        {"name": "Virgil van Dijk",  "position": "DF", "club": "Liverpool",    "country_goals": 9},
        {"name": "Cody Gakpo",       "position": "FW", "club": "Liverpool",    "country_goals": 17},
        {"name": "Xavi Simons",      "position": "MF", "club": "Paris SG",     "country_goals": 9},
        {"name": "Frenkie de Jong",  "position": "MF", "club": "Barcelona",    "country_goals": 9},
        {"name": "Bart Verbruggen",  "position": "GK", "club": "Brighton",     "country_goals": 0},
    ],
    "morocco": [
        {"name": "Achraf Hakimi",    "position": "DF", "club": "Paris SG",    "country_goals": 14},
        {"name": "Hakim Ziyech",     "position": "MF", "club": "Galatasaray", "country_goals": 24},
        {"name": "Youssef En-Nesyri","position": "FW", "club": "Fenerbahce",  "country_goals": 18},
        {"name": "Azzedine Ounahi",  "position": "MF", "club": "OM",          "country_goals": 7},
        {"name": "Yassine Bounou",   "position": "GK", "club": "Al-Hilal",    "country_goals": 0},
    ],
    "usa": [
        {"name": "Christian Pulisic","position": "FW", "club": "AC Milan",    "country_goals": 32},
        {"name": "Gio Reyna",        "position": "MF", "club": "Nottm Forest","country_goals": 8},
        {"name": "Weston McKennie",  "position": "MF", "club": "Juventus",    "country_goals": 16},
        {"name": "Tyler Adams",      "position": "MF", "club": "Bournemouth", "country_goals": 5},
        {"name": "Matt Turner",      "position": "GK", "club": "Crystal Palace","country_goals": 0},
    ],
    "mexico": [
        {"name": "Hirving Lozano",  "position": "FW", "club": "PSV",         "country_goals": 30},
        {"name": "Alexis Vega",     "position": "FW", "club": "Toluca",      "country_goals": 11},
        {"name": "Santiago Gimenez","position": "FW", "club": "Feyenoord",   "country_goals": 17},
        {"name": "Edson Alvarez",   "position": "MF", "club": "West Ham",    "country_goals": 5},
        {"name": "Guillermo Ochoa", "position": "GK", "club": "Salernitana", "country_goals": 0},
    ],
    "canada": [
        {"name": "Alphonso Davies", "position": "DF", "club": "Bayern Munich","country_goals": 16},
        {"name": "Jonathan David",  "position": "FW", "club": "Lille",        "country_goals": 30},
        {"name": "Cyle Larin",      "position": "FW", "club": "Club Brugge",  "country_goals": 27},
        {"name": "Tajon Buchanan",  "position": "FW", "club": "Inter Milan",  "country_goals": 11},
        {"name": "Milan Borjan",    "position": "GK", "club": "Red Star",     "country_goals": 0},
    ],
    "japan": [
        {"name": "Takumi Minamino", "position": "FW", "club": "AS Monaco",   "country_goals": 28},
        {"name": "Kaoru Mitoma",    "position": "FW", "club": "Brighton",    "country_goals": 15},
        {"name": "Ritsu Doan",      "position": "FW", "club": "Freiburg",    "country_goals": 12},
        {"name": "Wataru Endo",     "position": "MF", "club": "Liverpool",   "country_goals": 5},
        {"name": "Shuichi Gonda",   "position": "GK", "club": "Shimizu",     "country_goals": 0},
    ],
    "croatia": [
        {"name": "Luka Modric",     "position": "MF", "club": "Real Madrid",  "country_goals": 24},
        {"name": "Ivan Perisic",    "position": "MF", "club": "Hajduk Split", "country_goals": 34},
        {"name": "Andrej Kramaric", "position": "FW", "club": "Hoffenheim",   "country_goals": 21},
        {"name": "Mateo Kovacic",   "position": "MF", "club": "Man City",     "country_goals": 8},
        {"name": "Dominik Livakovic","position": "GK","club": "Fenerbahce",   "country_goals": 0},
    ],
    "belgium": [
        {"name": "Kevin De Bruyne", "position": "MF", "club": "Man City",    "country_goals": 27},
        {"name": "Romelu Lukaku",   "position": "FW", "club": "Roma",        "country_goals": 84},
        {"name": "Thibaut Courtois","position": "GK", "club": "Real Madrid", "country_goals": 0},
        {"name": "Leandro Trossard","position": "FW", "club": "Arsenal",     "country_goals": 10},
        {"name": "Yannick Carrasco","position": "FW", "club": "Al-Qadsiah",  "country_goals": 12},
    ],
    "uruguay": [
        {"name": "Federico Valverde","position": "MF", "club": "Real Madrid", "country_goals": 14},
        {"name": "Darwin Nunez",    "position": "FW", "club": "Liverpool",    "country_goals": 25},
        {"name": "Ronald Araujo",   "position": "DF", "club": "Barcelona",    "country_goals": 7},
        {"name": "Sergio Rochet",   "position": "GK", "club": "Internacional","country_goals": 0},
    ],
    "colombia": [
        {"name": "James Rodriguez", "position": "MF", "club": "Rayo Vallecano","country_goals": 30},
        {"name": "Luis Diaz",       "position": "FW", "club": "Liverpool",    "country_goals": 22},
        {"name": "Juan Cuadrado",   "position": "FW", "club": "Juventus",     "country_goals": 17},
        {"name": "Camilo Vargas",   "position": "GK", "club": "Atlas",        "country_goals": 0},
    ],
    "south korea": [
        {"name": "Son Heung-min",   "position": "FW", "club": "Tottenham",    "country_goals": 42},
        {"name": "Lee Kang-in",     "position": "MF", "club": "Paris SG",     "country_goals": 15},
        {"name": "Kim Min-jae",     "position": "DF", "club": "Bayern Munich","country_goals": 5},
        {"name": "Hwang Hee-chan",  "position": "FW", "club": "Wolves",       "country_goals": 17},
        {"name": "Kim Seung-gyu",   "position": "GK", "club": "Al-Shabab",    "country_goals": 0},
    ],
    "senegal": [
        {"name": "Sadio Mane",      "position": "FW", "club": "Al-Nassr",     "country_goals": 38},
        {"name": "Ismaila Sarr",    "position": "FW", "club": "Crystal Palace","country_goals": 15},
        {"name": "Kalidou Koulibaly","position": "DF", "club": "Al-Hilal",    "country_goals": 6},
        {"name": "Edouard Mendy",   "position": "GK", "club": "Al-Ahli",      "country_goals": 0},
    ],
    "ghana": [
        {"name": "Thomas Partey",   "position": "MF", "club": "Arsenal",      "country_goals": 15},
        {"name": "Jordan Ayew",     "position": "FW", "club": "Leicester",    "country_goals": 25},
        {"name": "Inaki Williams",  "position": "FW", "club": "Athletic Club","country_goals": 2},
        {"name": "Mohammed Salisu", "position": "DF", "club": "Monaco",       "country_goals": 2},
        {"name": "Lawrence Ati-Zigi","position": "GK","club": "St. Gallen",   "country_goals": 0},
    ],
    "scotland": [
        {"name": "Andrew Robertson","position": "DF", "club": "Liverpool",   "country_goals": 3},
        {"name": "Scott McTominay", "position": "MF", "club": "Napoli",      "country_goals": 14},
        {"name": "Che Adams",       "position": "FW", "club": "Southampton",  "country_goals": 8},
        {"name": "John McGinn",     "position": "MF", "club": "Aston Villa",  "country_goals": 9},
        {"name": "Angus Gunn",      "position": "GK", "club": "Norwich",      "country_goals": 0},
    ],
    "norway": [
        {"name": "Erling Haaland",  "position": "FW", "club": "Man City",     "country_goals": 31},
        {"name": "Martin Odegaard", "position": "MF", "club": "Arsenal",      "country_goals": 10},
        {"name": "Alexander Sorloth","position": "FW","club": "Atletico Madrid","country_goals": 20},
        {"name": "Orjan Nyland",    "position": "GK", "club": "Lazio",        "country_goals": 0},
    ],
    "algeria": [
        {"name": "Riyad Mahrez",    "position": "FW", "club": "Al-Ahli",      "country_goals": 30},
        {"name": "Islam Slimani",   "position": "FW", "club": "Retired",      "country_goals": 43},
        {"name": "Youcef Atal",     "position": "DF", "club": "Nice",         "country_goals": 7},
        {"name": "Rais M'Bolhi",    "position": "GK", "club": "Al-Qadsiah",   "country_goals": 0},
    ],
}


# ── Flag CDN codes (flagcdn.com ISO 3166-1 alpha-2) ───────────────────────────

FLAG_CODES: dict[str, str] = {
    "brazil":               "br",
    "germany":              "de",
    "italy":                "it",
    "argentina":            "ar",
    "france":               "fr",
    "uruguay":              "uy",
    "england":              "gb-eng",
    "spain":                "es",
    "netherlands":          "nl",
    "portugal":             "pt",
    "croatia":              "hr",
    "belgium":              "be",
    "morocco":              "ma",
    "japan":                "jp",
    "usa":                  "us",
    "mexico":               "mx",
    "colombia":             "co",
    "canada":               "ca",
    "ecuador":              "ec",
    "senegal":              "sn",
    "south korea":          "kr",
    "australia":            "au",
    "switzerland":          "ch",
    "serbia":               "rs",
    "ghana":                "gh",
    "chile":                "cl",
    "iran":                 "ir",
    "scotland":             "gb-sct",
    "haiti":                "ht",
    "paraguay":             "py",
    "turkey":               "tr",
    "ivory coast":          "ci",
    "sweden":               "se",
    "tunisia":              "tn",
    "egypt":                "eg",
    "new zealand":          "nz",
    "cape verde":           "cv",
    "saudi arabia":         "sa",
    "iraq":                 "iq",
    "norway":               "no",
    "algeria":              "dz",
    "austria":              "at",
    "jordan":               "jo",
    "dr congo":             "cd",
    "uzbekistan":           "uz",
    "panama":               "pa",
    "south africa":         "za",
    "czech republic":       "cz",
    "bosnia and herzegovina": "ba",
    "qatar":                "qa",
    "curacao":              "cw",
}


def get_flag_url(team_name: str, width: int = 80) -> str:
    """
    Return a flagcdn.com URL for *team_name*.

    Example: get_flag_url("brazil") -> "https://flagcdn.com/w80/br.png"
    Returns "" for unknown teams.
    """
    code = FLAG_CODES.get(team_name.lower().strip(), "")
    if not code:
        return ""
    return f"https://flagcdn.com/w{width}/{code}.png"


# ── WC 2026 Groups (official draw, 2025-12-05, Miami) ─────────────────────────
# 48 teams · 12 groups of 4 · Top 2 from each + 8 best 3rd-place teams advance.
# Host nations: Mexico (A), Canada (B), USA (D).

GROUPS: dict[str, dict] = {
    "A": {"teams": ["Mexico",   "South Africa",          "South Korea",   "Czech Republic"],      "host": "Mexico"},
    "B": {"teams": ["Canada",   "Bosnia and Herzegovina","Qatar",          "Switzerland"],         "host": "Canada"},
    "C": {"teams": ["Brazil",   "Morocco",               "Haiti",          "Scotland"],            "host": None},
    "D": {"teams": ["USA",      "Paraguay",              "Australia",      "Turkey"],              "host": "USA"},
    "E": {"teams": ["Germany",  "Curacao",               "Ivory Coast",    "Ecuador"],             "host": None},
    "F": {"teams": ["Netherlands","Japan",               "Sweden",         "Tunisia"],             "host": None},
    "G": {"teams": ["Belgium",  "Egypt",                 "Iran",           "New Zealand"],         "host": None},
    "H": {"teams": ["Spain",    "Cape Verde",            "Saudi Arabia",   "Uruguay"],             "host": None},
    "I": {"teams": ["France",   "Senegal",               "Iraq",           "Norway"],              "host": None},
    "J": {"teams": ["Argentina","Algeria",               "Austria",        "Jordan"],              "host": None},
    "K": {"teams": ["Portugal", "DR Congo",              "Uzbekistan",     "Colombia"],            "host": None},
    "L": {"teams": ["England",  "Croatia",               "Ghana",          "Panama"],              "host": None},
}

# Team → group lookup (lowercase keys)
TEAM_GROUP: dict[str, str] = {}
for _gid, _gdata in GROUPS.items():
    for _team in _gdata["teams"]:
        TEAM_GROUP[_team.lower()] = _gid


# ── Tournament info ────────────────────────────────────────────────────────────

TOURNAMENT = {
    "name": "FIFA World Cup 2026",
    "dates": "June 11 - July 19, 2026",
    "hosts": ["United States", "Canada", "Mexico"],
    "teams": 48,
    "format": "12 groups of 4 · Top 2 + 8 best 3rd advance",
    "final_venue": "MetLife Stadium, New York/New Jersey",
}


# ── Helper functions ───────────────────────────────────────────────────────────

def get_team_history(team_name: str) -> dict | None:
    """Return hardcoded history for *team_name*, or None if unknown."""
    return TEAM_HISTORY.get(team_name.lower().strip())


def get_key_players(team_name: str) -> list[dict]:
    """Return list of key player dicts for *team_name*."""
    return KEY_PLAYERS.get(team_name.lower().strip(), [])


def get_group_info(team_name: str) -> dict:
    """
    Return group info for *team_name*.

    Returns:
        {"group": "C", "teams": [...], "host": None}
        or {"group": "TBD", "teams": [team_name], "host": None}
    """
    key = team_name.lower().strip()
    gid = TEAM_GROUP.get(key)
    if gid:
        return {"group": gid, **GROUPS[gid]}
    return {"group": "TBD", "teams": [team_name], "host": None}


def get_full_team_data(team_name: str) -> dict:
    """
    Convenience: merge history + players + group into one dict.
    Falls back gracefully for unknown teams.
    """
    history = get_team_history(team_name) or {
        "titles": 0, "titles_years": [], "appearances": 0,
        "best_finish": "Unknown", "famous_players": [],
    }
    return {
        "team_name": team_name,
        **history,
        "key_players": get_key_players(team_name),
        "group_info":  get_group_info(team_name),
        "flag_url":    get_flag_url(team_name),
        "tournament":  TOURNAMENT,
    }
