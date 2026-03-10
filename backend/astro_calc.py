import swisseph as swe
import datetime
import math
from timezonefinder import TimezoneFinder
import pytz

# ─── Constants ────────────────────────────────────────────────────────────────

RASIS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Nakshatra lords in Vimshottari order
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
    "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
}

# ─── Planetary Dignity Tables ─────────────────────────────────────────────────
# Sign index: 0=Aries, 1=Taurus, ..., 11=Pisces

# Exaltation signs and exact degrees
EXALTATION = {
    "Sun":     {"sign": 0, "degree": 10},     # Aries 10°
    "Moon":    {"sign": 1, "degree": 3},      # Taurus 3°
    "Mars":    {"sign": 9, "degree": 28},     # Capricorn 28°
    "Mercury": {"sign": 5, "degree": 15},     # Virgo 15°
    "Jupiter": {"sign": 3, "degree": 5},      # Cancer 5°
    "Venus":   {"sign": 11, "degree": 27},    # Pisces 27°
    "Saturn":  {"sign": 6, "degree": 20},     # Libra 20°
}

# Debilitation (exactly opposite exaltation)
DEBILITATION = {
    "Sun":     {"sign": 6, "degree": 10},     # Libra 10°
    "Moon":    {"sign": 7, "degree": 3},      # Scorpio 3°
    "Mars":    {"sign": 3, "degree": 28},     # Cancer 28°
    "Mercury": {"sign": 11, "degree": 15},    # Pisces 15°
    "Jupiter": {"sign": 9, "degree": 5},      # Capricorn 5°
    "Venus":   {"sign": 5, "degree": 27},     # Virgo 27°
    "Saturn":  {"sign": 0, "degree": 20},     # Aries 20°
}

# Own signs (planets rule these signs)
OWN_SIGNS = {
    "Sun":     [4],           # Leo
    "Moon":    [3],           # Cancer
    "Mars":    [0, 7],        # Aries, Scorpio
    "Mercury": [2, 5],        # Gemini, Virgo
    "Jupiter": [8, 11],       # Sagittarius, Pisces
    "Venus":   [1, 6],        # Taurus, Libra
    "Saturn":  [9, 10],       # Capricorn, Aquarius
    "Rahu":    [10],          # Aquarius (per BPHS)
    "Ketu":    [7],           # Scorpio (per BPHS)
}

# Moolatrikona signs and degree ranges
MOOLATRIKONA = {
    "Sun":     {"sign": 4, "start": 0, "end": 20},      # Leo 0-20°
    "Moon":    {"sign": 1, "start": 4, "end": 30},       # Taurus 4-30°
    "Mars":    {"sign": 0, "start": 0, "end": 12},       # Aries 0-12°
    "Mercury": {"sign": 5, "start": 16, "end": 20},      # Virgo 16-20°
    "Jupiter": {"sign": 8, "start": 0, "end": 10},       # Sagittarius 0-10°
    "Venus":   {"sign": 6, "start": 0, "end": 15},       # Libra 0-15°
    "Saturn":  {"sign": 10, "start": 0, "end": 20},      # Aquarius 0-20°
}

# Ascendant lord map
LORD_MAP = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
}

# Directional Strength (Dig Bala) — planets are strongest in these houses
DIG_BALA = {
    "Sun": 10,      # 10th house
    "Moon": 4,      # 4th house
    "Mars": 10,     # 10th house
    "Mercury": 1,   # 1st house
    "Jupiter": 1,   # 1st house
    "Venus": 4,     # 4th house
    "Saturn": 7,    # 7th house
    "Rahu": 10,     # 10th house (approximate)
    "Ketu": 4,      # 4th house (approximate)
}

# Friendly/Enemy relationships (simplified essential dignities)
FRIENDSHIPS = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutral": ["Mercury"]},
    "Moon":    {"friends": ["Sun", "Mercury"], "enemies": [], "neutral": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutral": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutral": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutral": ["Saturn"]},
    "Venus":   {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutral": ["Mars", "Jupiter"]},
    "Saturn":  {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]},
    "Rahu":    {"friends": ["Venus", "Saturn"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Mercury", "Jupiter"]},
    "Ketu":    {"friends": ["Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutral": ["Sun", "Moon", "Mercury"]},
}

# Combustion orbs
COMBUST_ORBS = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}

# Timezone finder (singleton)
_tf = TimezoneFinder()

# Souv's hardcoded data (kept for backward compat)
NATAL_PLANETS_SOUV = {
    "Ascendant": 20.65, "Sun": 250.00, "Moon": 245.81, "Mars": 187.16,
    "Mercury": 249.73, "Jupiter": 38.93, "Venus": 295.68, "Saturn": 31.05,
    "Rahu": 82.18, "Ketu": 262.18
}

SAV_SCORES_SOUV = {
    "Aries": 29, "Taurus": 34, "Gemini": 33, "Cancer": 26,
    "Leo": 27, "Virgo": 26, "Libra": 30, "Scorpio": 27,
    "Sagittarius": 30, "Capricorn": 24, "Aquarius": 32, "Pisces": 19
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def lon_to_sign(lon):
    return RASIS[int(lon // 30)]

def lon_to_sign_idx(lon):
    return int(lon // 30)

def lon_to_dms(lon):
    deg_in_sign = lon % 30
    d = int(deg_in_sign)
    m = int((deg_in_sign - d) * 60)
    return d, m

def lon_to_nakshatra(lon):
    nak_index = int(lon / (360 / 27))
    nak_deg = lon % (360 / 27)
    pada = int(nak_deg / (360 / 108)) % 4 + 1
    balance = 1.0 - (nak_deg / (360 / 27))
    return nak_index, pada, balance

def get_planetary_state(speed, name):
    if name in ["Sun", "Moon", "Rahu", "Ketu"]:
        return ""
    if speed < -0.01:
        return "(R)"
    elif abs(speed) <= 0.01:
        return "(S)"
    return ""

def local_to_utc(dob_str, tob_str, lat, lon):
    """Convert local birth time to UTC using timezone lookup from coordinates."""
    year, month, day = map(int, dob_str.split('-'))
    parts = tob_str.split(':')
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0

    tz_name = _tf.timezone_at(lat=lat, lng=lon)
    if tz_name:
        tz = pytz.timezone(tz_name)
        local_dt = datetime.datetime(year, month, day, hour, minute, second)
        try:
            local_aware = tz.localize(local_dt)
        except Exception:
            local_aware = tz.localize(local_dt, is_dst=False)
        utc_dt = local_aware.astimezone(pytz.utc)
        utc_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        # Handle date change across UTC boundary
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_hour, tz_name
    else:
        # Fallback: approximate from longitude
        offset_hours = lon / 15.0
        utc_hour = hour - offset_hours + minute / 60.0 + second / 3600.0
        return year, month, day, utc_hour, f"UTC+{offset_hours:.1f}"


# ─── Dignity Analysis ────────────────────────────────────────────────────────

def get_dignity(name, lon):
    """Determine the dignity status of a planet at a given longitude."""
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30

    # Moolatrikona (check first — it's the strongest own-sign variant)
    if name in MOOLATRIKONA:
        mt = MOOLATRIKONA[name]
        if sign_idx == mt["sign"] and mt["start"] <= deg_in_sign < mt["end"]:
            return "Moolatrikona"

    # Exaltation
    if name in EXALTATION:
        ex = EXALTATION[name]
        if sign_idx == ex["sign"]:
            return "Exalted"

    # Debilitation
    if name in DEBILITATION:
        db = DEBILITATION[name]
        if sign_idx == db["sign"]:
            return "Debilitated"

    # Own Sign
    if name in OWN_SIGNS and sign_idx in OWN_SIGNS[name]:
        return "Own Sign"

    # Friend/Enemy of sign lord
    sign_lord = LORD_MAP[sign_idx]
    if name in FRIENDSHIPS and name != sign_lord:
        rel = FRIENDSHIPS[name]
        if sign_lord in rel["friends"]:
            return "Friendly"
        elif sign_lord in rel["enemies"]:
            return "Enemy"
        else:
            return "Neutral"

    return "Neutral"


# ─── Gandanta ─────────────────────────────────────────────────────────────────

def check_gandanta(lon):
    deg_in_sign = lon % 30
    sign_idx = int(lon // 30)
    if sign_idx in [3, 7, 11] and deg_in_sign >= (30 - 3.333):
        return True
    if sign_idx in [0, 4, 8] and deg_in_sign <= 3.333:
        return True
    return False


# ─── Arudha Lagna ─────────────────────────────────────────────────────────────

def calculate_arudha_lagna(asc_sign_idx, asc_lord_sign_idx):
    distance = (asc_lord_sign_idx - asc_sign_idx) % 12
    if distance == 0:
        al_idx = (asc_sign_idx + 9) % 12
    elif distance == 6:
        al_idx = (asc_sign_idx + 3) % 12
    else:
        al_idx = (asc_lord_sign_idx + distance) % 12
    return RASIS[al_idx]


# ─── Vedic Aspects ────────────────────────────────────────────────────────────

def get_vedic_aspects_for_planet(name, sign_idx):
    """Return list of sign indices aspected by a planet from its sign."""
    aspected = []
    # All planets have 7th aspect (opposition)
    aspected.append((sign_idx + 6) % 12)

    if name == "Mars":
        aspected.append((sign_idx + 3) % 12)   # 4th aspect
        aspected.append((sign_idx + 7) % 12)   # 8th aspect
    elif name in ["Jupiter", "Rahu", "Ketu"]:
        aspected.append((sign_idx + 4) % 12)   # 5th aspect
        aspected.append((sign_idx + 8) % 12)   # 9th aspect
    elif name == "Saturn":
        aspected.append((sign_idx + 2) % 12)   # 3rd aspect
        aspected.append((sign_idx + 9) % 12)   # 10th aspect

    return aspected


def compute_natal_aspects(planets, house_positions):
    """Compute all Vedic aspects between natal planets."""
    aspects = []
    planet_signs = {}
    for name, pdata in planets.items():
        planet_signs[name] = int(pdata["longitude"] // 30)

    for p1_name, p1_sign in planet_signs.items():
        aspected_signs = get_vedic_aspects_for_planet(p1_name, p1_sign)
        for p2_name, p2_sign in planet_signs.items():
            if p1_name == p2_name:
                continue
            if p2_sign in aspected_signs:
                aspects.append({
                    "from": p1_name,
                    "to": p2_name,
                    "type": "aspect",
                })

    # Conjunctions (same sign)
    names = list(planet_signs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if planet_signs[names[i]] == planet_signs[names[j]]:
                # Check within orb (8° for conjunction)
                diff = abs(planets[names[i]]["longitude"] - planets[names[j]]["longitude"])
                if diff > 180:
                    diff = 360 - diff
                if diff <= 8:
                    aspects.append({
                        "from": names[i],
                        "to": names[j],
                        "type": "conjunction",
                        "orb": round(diff, 2),
                    })

    return aspects


# ─── Strength Scoring (Simplified Shadbala) ──────────────────────────────────

def compute_planet_strength(name, pdata, house, combustion_data):
    """
    Compute a 0-100 strength score for a planet.
    Based on: dignity, directional strength, retrogression, combustion.
    """
    score = 50  # Base neutral

    # 1. Dignity (+/- up to 25)
    dignity = pdata.get("dignity", "Neutral")
    dignity_scores = {
        "Exalted": 25, "Moolatrikona": 20, "Own Sign": 15,
        "Friendly": 5, "Neutral": 0, "Enemy": -10, "Debilitated": -25
    }
    score += dignity_scores.get(dignity, 0)

    # 2. Directional Strength (Dig Bala) (+/- up to 15)
    best_house = DIG_BALA.get(name, 1)
    if house == best_house:
        score += 15
    elif house == ((best_house + 5) % 12 + 1):  # Opposite house
        score -= 10

    # 3. Retrogression (+8 — retrograde planets are stronger in Vedic)
    if pdata.get("state") == "(R)":
        score += 8

    # 4. Combustion penalty (-15 to -25)
    if name in combustion_data:
        orb = combustion_data[name]
        if orb < 1:
            score -= 25  # Astangata
        elif orb < 3:
            score -= 20
        else:
            score -= 12

    # 5. Gandanta penalty (-15)
    if pdata.get("is_gandanta"):
        score -= 15

    # 6. Kendra/Trikona bonus
    if house in [1, 4, 7, 10]:  # Kendra
        score += 8
    elif house in [5, 9]:       # Trikona
        score += 6
    elif house in [6, 8, 12]:   # Dusthana
        score -= 8

    return max(0, min(100, score))


# ─── Yoga Detection ──────────────────────────────────────────────────────────

def detect_yogas(planets, house_positions, asc_sign_idx):
    """Detect major Vedic yogas from chart data."""
    yogas = []

    moon_house = house_positions.get("Moon")
    jupiter_house = house_positions.get("Jupiter")
    sun_house = house_positions.get("Sun")
    mercury_house = house_positions.get("Mercury")
    mars_house = house_positions.get("Mars")
    venus_house = house_positions.get("Venus")
    saturn_house = house_positions.get("Saturn")

    moon_sign = lon_to_sign_idx(planets["Moon"]["longitude"]) if "Moon" in planets else None
    jupiter_sign = lon_to_sign_idx(planets["Jupiter"]["longitude"]) if "Jupiter" in planets else None

    # ─── Gajakesari Yoga (Jupiter in Kendra from Moon) ───
    if moon_house and jupiter_house:
        diff = abs(moon_house - jupiter_house)
        if diff in [0, 3, 6, 9]:
            yogas.append({
                "name": "Gajakesari Yoga",
                "planets": "Moon + Jupiter",
                "meaning": "Wisdom, fame, lasting reputation; the native leaves a mark on the world",
                "strength": "Strong" if planets["Jupiter"].get("dignity") in ["Exalted", "Own Sign", "Moolatrikona"] else "Moderate"
            })

    # ─── Budhaditya Yoga (Sun + Mercury in same sign) ───
    if sun_house and mercury_house and sun_house == mercury_house:
        sun_sign_idx = lon_to_sign_idx(planets["Sun"]["longitude"])
        merc_sign_idx = lon_to_sign_idx(planets["Mercury"]["longitude"])
        if sun_sign_idx == merc_sign_idx:
            # Not valid if Mercury is combust (too close to Sun)
            merc_combust = abs(planets["Sun"]["longitude"] - planets["Mercury"]["longitude"])
            if merc_combust > 180:
                merc_combust = 360 - merc_combust
            if merc_combust > 5:  # Functional yoga only if Mercury has some separation
                yogas.append({
                    "name": "Budhaditya Yoga",
                    "planets": "Sun + Mercury",
                    "meaning": "Sharp intellect, articulation, analytical brilliance, command over words",
                    "strength": "Strong" if merc_combust > 10 else "Moderate"
                })

    # ─── Pancha Mahapurusha Yogas (in Kendra + own/exalted sign) ───
    pmy_planets = {
        "Mars": ("Ruchaka", "Fearless warrior energy, physical courage, leadership through action"),
        "Mercury": ("Bhadra", "Supreme intellect, wit, communication mastery, merchant mind"),
        "Jupiter": ("Hamsa", "Spiritual depth, wisdom, ethical leadership, divine protection"),
        "Venus": ("Malavya", "Artistic genius, sensual refinement, beauty, luxury magnetism"),
        "Saturn": ("Sasa", "Iron discipline, authority through endurance, structural power"),
    }
    for pname, (yoga_name, meaning) in pmy_planets.items():
        if pname in planets and pname in house_positions:
            h = house_positions[pname]
            dignity = planets[pname].get("dignity", "")
            if h in [1, 4, 7, 10] and dignity in ["Exalted", "Own Sign", "Moolatrikona"]:
                yogas.append({
                    "name": f"{yoga_name} Yoga (Pancha Mahapurusha)",
                    "planets": pname,
                    "meaning": meaning,
                    "strength": "Strong"
                })

    # ─── Kemadruma Yoga (Moon isolation — no planets in 2nd/12th from Moon) ───
    if moon_house:
        moon_sign_idx = lon_to_sign_idx(planets["Moon"]["longitude"])
        adjacent_signs = [(moon_sign_idx - 1) % 12, (moon_sign_idx + 1) % 12]
        has_adjacent = False
        for pname, pdata in planets.items():
            if pname in ["Moon", "Rahu", "Ketu"]:
                continue
            p_sign = lon_to_sign_idx(pdata["longitude"])
            if p_sign in adjacent_signs:
                has_adjacent = True
                break
        if not has_adjacent:
            # Check if cancelled by Kendra from Lagna
            if moon_house not in [1, 4, 7, 10]:
                yogas.append({
                    "name": "Kemadruma Yoga",
                    "planets": "Moon (isolated)",
                    "meaning": "Emotional isolation, poverty of inner peace, feeling fundamentally alone even in company",
                    "strength": "Active" if planets["Moon"].get("dignity") == "Debilitated" else "Moderate"
                })

    # ─── Vipareeta Raja Yoga (lords of 6/8/12 in 6/8/12) ───
    dusthana_houses = [6, 8, 12]
    dusthana_lords = {}
    for h in dusthana_houses:
        lord_sign_idx = (asc_sign_idx + h - 1) % 12
        lord_name = LORD_MAP[lord_sign_idx]
        dusthana_lords[h] = lord_name

    for h, lord_name in dusthana_lords.items():
        if lord_name in house_positions:
            lord_house = house_positions[lord_name]
            if lord_house in dusthana_houses and lord_house != h:
                yogas.append({
                    "name": "Vipareeta Raja Yoga",
                    "planets": f"{lord_name} (lord of {h}th in {lord_house}th)",
                    "meaning": "Power through crisis, unexpected reversals into fortune, triumph born from suffering",
                    "strength": "Strong"
                })
                break  # One VRY is enough

    # ─── Neechabhanga Raja Yoga (cancelled debilitation) ───
    for pname, pdata in planets.items():
        if pdata.get("dignity") == "Debilitated" and pname in DEBILITATION:
            deb_sign = DEBILITATION[pname]["sign"]
            sign_lord = LORD_MAP[deb_sign]
            # Check if sign lord is in a Kendra from Lagna or Moon
            if sign_lord in house_positions:
                lord_house = house_positions[sign_lord]
                if lord_house in [1, 4, 7, 10]:
                    yogas.append({
                        "name": "Neechabhanga Raja Yoga",
                        "planets": f"{pname} (debilitated, cancelled by {sign_lord})",
                        "meaning": "The deepest weakness transforms into unexpected greatness; the wound becomes the gift",
                        "strength": "Strong"
                    })

    return yogas


# ─── Navamsha (D9) Positions ──────────────────────────────────────────────────

def compute_navamsha(lon):
    """
    Compute the Navamsha (D9) sign for a given longitude.
    Each sign is divided into 9 parts of 3°20' each.
    The Navamsha sign for Aries starts from Aries, Taurus from Capricorn,
    Gemini from Libra, Cancer from Cancer, etc. (follows the element cycle).
    """
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    navamsha_part = int(deg_in_sign / (30 / 9))  # 0-8
    
    # Starting sign for navamsha depends on the element of the rasi
    # Fire signs (0,4,8) start from Aries(0)
    # Earth signs (1,5,9) start from Capricorn(9)
    # Air signs (2,6,10) start from Libra(6)
    # Water signs (3,7,11) start from Cancer(3)
    start_map = {0: 0, 1: 9, 2: 6, 3: 3, 4: 0, 5: 9, 6: 6, 7: 3, 8: 0, 9: 9, 10: 6, 11: 3}
    navamsha_sign_idx = (start_map[sign_idx] + navamsha_part) % 12
    return RASIS[navamsha_sign_idx]


def compute_navamsha_chart(planets, asc_lon):
    """Compute Navamsha (D9) positions for all planets and Ascendant."""
    d9 = {}
    d9["Ascendant"] = compute_navamsha(asc_lon)
    for name, pdata in planets.items():
        d9[name] = compute_navamsha(pdata["longitude"])
    return d9


# ─── Atmakaraka (Soul Planet) ─────────────────────────────────────────────────

def find_atmakaraka(planets):
    """
    Atmakaraka = planet with highest degree in its sign (excluding Rahu/Ketu).
    This planet represents the soul's deepest desire and karmic purpose.
    """
    max_deg = -1
    ak_name = None
    for name, pdata in planets.items():
        if name in ["Rahu", "Ketu"]:
            continue
        deg_in_sign = pdata["longitude"] % 30
        if deg_in_sign > max_deg:
            max_deg = deg_in_sign
            ak_name = name
    return ak_name, round(max_deg, 2)


# ─── Graha Yuddha (Planetary War) ─────────────────────────────────────────────

def detect_graha_yuddha(planets):
    """
    Planetary war occurs when two planets (Mars, Mercury, Jupiter, Venus, Saturn)
    are within 1° of each other. The planet with higher longitude wins.
    """
    wars = []
    war_planets = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for i in range(len(war_planets)):
        for j in range(i + 1, len(war_planets)):
            p1, p2 = war_planets[i], war_planets[j]
            if p1 in planets and p2 in planets:
                diff = abs(planets[p1]["longitude"] - planets[p2]["longitude"])
                if diff > 180:
                    diff = 360 - diff
                if diff <= 1.0:
                    # Planet with higher degree in sign wins
                    d1 = planets[p1]["longitude"] % 30
                    d2 = planets[p2]["longitude"] % 30
                    winner = p1 if d1 > d2 else p2
                    loser = p2 if winner == p1 else p1
                    wars.append({
                        "planets": f"{p1} vs {p2}",
                        "orb": round(diff, 3),
                        "winner": winner,
                        "loser": loser,
                    })
    return wars


# ─── Sade Sati Detection ──────────────────────────────────────────────────────

def detect_sade_sati(natal_moon_lon):
    """
    Detect if Saturn is currently transiting within 1 sign of natal Moon.
    Sade Sati = Saturn in 12th, 1st, or 2nd from natal Moon sign.
    This is the most psychologically intense transit in Vedic astrology (7.5 years).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                    now_utc.hour + now_utc.minute / 60.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    pos, _ = swe.calc_ut(jd, swe.SATURN, flags)
    saturn_lon = pos[0]
    saturn_sign = int(saturn_lon // 30)
    moon_sign = int(natal_moon_lon // 30)
    
    diff = (saturn_sign - moon_sign) % 12
    
    if diff == 11:  # 12th from Moon (rising phase)
        return {"active": True, "phase": "rising", "meaning": "the weight is arriving. something heavy is building beneath the surface. the pressure hasn't peaked yet."}
    elif diff == 0:  # Over Moon (peak phase)
        return {"active": True, "phase": "peak", "meaning": "the heaviest passage. emotional bedrock is being demolished and rebuilt. this transforms everything."}
    elif diff == 1:  # 2nd from Moon (setting phase)
        return {"active": True, "phase": "setting", "meaning": "the weight is lifting but the scars remain. financial and emotional reconstruction. the lesson is almost learned."}
    
    return {"active": False, "phase": None, "meaning": None}


# ─── Dasamsa (D10) Career Chart ──────────────────────────────────────────────

def compute_dasamsa(lon):
    """
    Compute the Dasamsa (D10) sign for career/profession analysis.
    Each sign is divided into 10 parts of 3° each.
    For odd signs: counting starts from the sign itself.
    For even signs: counting starts from the 9th sign from it.
    """
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    dasamsa_part = int(deg_in_sign / 3)  # 0-9

    if sign_idx % 2 == 0:  # Odd signs (0=Aries, 2=Gemini, etc.)
        d10_sign = (sign_idx + dasamsa_part) % 12
    else:  # Even signs
        d10_sign = (sign_idx + 8 + dasamsa_part) % 12  # 9th from sign + offset
    return RASIS[d10_sign]


def compute_dasamsa_chart(planets, asc_lon):
    """Compute Dasamsa (D10) positions for career analysis."""
    d10 = {}
    d10["Ascendant"] = compute_dasamsa(asc_lon)
    for name, pdata in planets.items():
        d10[name] = compute_dasamsa(pdata["longitude"])
    return d10


# ─── Bhava Lords (House Lord Placements) ─────────────────────────────────────

def compute_bhava_lords(asc_sign_idx, planets):
    """
    Compute the lord of each house and where it sits.
    This is one of the most important analytical tools in Vedic astrology.
    """
    bhava_lords = {}
    for house_num in range(1, 13):
        house_sign_idx = (asc_sign_idx + house_num - 1) % 12
        lord_name = LORD_MAP[house_sign_idx]

        # Find where the lord sits (its house position)
        lord_lon = planets[lord_name]["longitude"] if lord_name in planets else None
        lord_sign_idx = int(lord_lon // 30) if lord_lon else None
        lord_house = ((lord_sign_idx - asc_sign_idx) % 12) + 1 if lord_sign_idx is not None else None
        lord_dignity = planets[lord_name].get("dignity", "Neutral") if lord_name in planets else "Unknown"

        bhava_lords[house_num] = {
            "sign": RASIS[house_sign_idx],
            "lord": lord_name,
            "lord_in_house": lord_house,
            "lord_dignity": lord_dignity,
        }
    return bhava_lords


# ─── Panchada (5-fold) Planetary Friendships ─────────────────────────────────

# Natural friendships (Naisargika Maitri) — fixed relationships
NATURAL_FRIENDS = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutrals": ["Mercury"]},
    "Moon":    {"friends": ["Sun", "Mercury"], "enemies": [], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutrals": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutrals": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutrals": ["Saturn"]},
    "Venus":   {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutrals": ["Mars", "Jupiter"]},
    "Saturn":  {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutrals": ["Jupiter"]},
}


def compute_temporal_friendship(planet_name, planet_lon, other_name, other_lon):
    """
    Temporal (Tatkalika) friendship: planets in 2nd, 3rd, 4th, 10th, 11th,
    or 12th from each other are temporal friends; else temporal enemies.
    """
    p_sign = int(planet_lon // 30)
    o_sign = int(other_lon // 30)
    diff = (o_sign - p_sign) % 12
    # Houses 2,3,4,10,11,12 from planet = friend positions
    if diff in [1, 2, 3, 9, 10, 11]:
        return "friend"
    return "enemy"


def compute_panchada_friendships(planets):
    """
    Compute 5-fold (Panchada) friendship for each planet pair.
    Natural friend + Temporal friend = Intimate friend (Adhi Mitra)
    Natural friend + Temporal enemy = Neutral
    Natural neutral + Temporal friend = Friend
    Natural neutral + Temporal enemy = Enemy
    Natural enemy + Temporal friend = Neutral
    Natural enemy + Temporal enemy = Bitter enemy (Adhi Shatru)
    """
    friendships = {}
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if pname not in planets:
            continue
        friendships[pname] = {}
        for oname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            if oname == pname or oname not in planets:
                continue

            natural = NATURAL_FRIENDS.get(pname, {})
            if oname in natural.get("friends", []):
                nat = "friend"
            elif oname in natural.get("enemies", []):
                nat = "enemy"
            else:
                nat = "neutral"

            temp = compute_temporal_friendship(pname, planets[pname]["longitude"],
                                               oname, planets[oname]["longitude"])

            # Panchada combination
            if nat == "friend" and temp == "friend":
                result = "intimate friend"
            elif nat == "friend" and temp == "enemy":
                result = "neutral"
            elif nat == "neutral" and temp == "friend":
                result = "friend"
            elif nat == "neutral" and temp == "enemy":
                result = "enemy"
            elif nat == "enemy" and temp == "friend":
                result = "neutral"
            elif nat == "enemy" and temp == "enemy":
                result = "bitter enemy"
            else:
                result = "neutral"

            friendships[pname][oname] = result
    return friendships


# ─── Simplified Ashtakavarga ──────────────────────────────────────────────────

def compute_sarva_ashtakavarga(planets, asc_sign_idx):
    """
    Compute a simplified Sarva Ashtakavarga (SAV) — total benefic points per sign.
    SAV ranges from 0-56 per sign. Signs with 25+ points are favorable for transits.
    Signs with <25 points are unfavorable.
    This is a simplified version using classical bindhu (point) contribution rules.
    """
    # Initialize 12 signs with base points
    sav = [0] * 12

    # Classical contribution: each planet contributes points to signs
    # based on its position relative to itself, Sun, Moon, etc.
    # Simplified: use the planet's position to distribute points
    contributing_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

    for pname in contributing_planets:
        if pname not in planets:
            continue
        p_sign = int(planets[pname]["longitude"] // 30)

        # Each planet gives benefic points to certain houses from itself
        # Different planets have different contribution patterns
        # Using averaged classical patterns
        if pname == "Sun":
            benefic_houses = [1, 2, 4, 7, 8, 9, 10, 11]
        elif pname == "Moon":
            benefic_houses = [1, 3, 6, 7, 10, 11]
        elif pname == "Mars":
            benefic_houses = [1, 2, 4, 7, 8, 10, 11]
        elif pname == "Mercury":
            benefic_houses = [1, 2, 4, 6, 8, 10, 11]
        elif pname == "Jupiter":
            benefic_houses = [1, 2, 3, 4, 7, 8, 10, 11]
        elif pname == "Venus":
            benefic_houses = [1, 2, 3, 4, 5, 8, 9, 11]
        elif pname == "Saturn":
            benefic_houses = [1, 2, 4, 7, 8, 10, 11]
        else:
            benefic_houses = [1, 2, 4, 7, 10, 11]

        for h in benefic_houses:
            target_sign = (p_sign + h - 1) % 12
            sav[target_sign] += 1

    # Also add Lagna (Ascendant) contribution
    asc_benefic = [1, 3, 6, 10, 11]
    for h in asc_benefic:
        target_sign = (asc_sign_idx + h - 1) % 12
        sav[target_sign] += 1

    return {RASIS[i]: sav[i] for i in range(12)}


# ─── Dynamic Natal Chart Calculation ─────────────────────────────────────────

def compute_natal_chart(dob_str, tob_str, lat, lon):
    """
    Compute a full Vedic natal chart for any birth data.
    Now timezone-aware, with dignity, aspects, yogas, and strength scoring.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Timezone-aware UTC conversion
    utc_year, utc_month, utc_day, utc_hour, tz_name = local_to_utc(dob_str, tob_str, lat, lon)
    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour)

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    # Calculate Ascendant
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P', flags)
    asc_lon = ascmc[0]

    # Calculate planets
    planets = {}
    for name, pid in PLANET_IDS.items():
        pos, ret = swe.calc_ut(jd, pid, flags)
        plan_lon = pos[0]
        speed = pos[3]

        sign = lon_to_sign(plan_lon)
        deg, min_arc = lon_to_dms(plan_lon)
        nak_idx, pada, balance = lon_to_nakshatra(plan_lon)
        state = get_planetary_state(speed, name)
        dignity = get_dignity(name, plan_lon)

        planets[name] = {
            "longitude": plan_lon,
            "sign": sign,
            "degree": deg,
            "minute": min_arc,
            "nakshatra": NAKSHATRAS[nak_idx],
            "pada": pada,
            "state": state,
            "speed": speed,
            "is_gandanta": check_gandanta(plan_lon),
            "dignity": dignity,
        }

    # Add Ketu (180° from Rahu)
    rahu_lon = planets["Rahu"]["longitude"]
    ketu_lon = (rahu_lon + 180) % 360
    nak_idx, pada, balance = lon_to_nakshatra(ketu_lon)
    planets["Ketu"] = {
        "longitude": ketu_lon,
        "sign": lon_to_sign(ketu_lon),
        "degree": lon_to_dms(ketu_lon)[0],
        "minute": lon_to_dms(ketu_lon)[1],
        "nakshatra": NAKSHATRAS[nak_idx],
        "pada": pada,
        "state": "",
        "speed": 0,
        "is_gandanta": check_gandanta(ketu_lon),
        "dignity": get_dignity("Ketu", ketu_lon),
    }

    # Ascendant data
    asc_sign = lon_to_sign(asc_lon)
    asc_deg, asc_min = lon_to_dms(asc_lon)
    asc_nak_idx, asc_pada, _ = lon_to_nakshatra(asc_lon)
    asc_sign_idx = int(asc_lon // 30)

    # House positions
    house_positions = {}
    for name, pdata in planets.items():
        plan_sign_idx = int(pdata["longitude"] // 30)
        house = ((plan_sign_idx - asc_sign_idx) % 12) + 1
        house_positions[name] = house

    # Arudha Lagna
    asc_lord_name = LORD_MAP[asc_sign_idx]
    asc_lord_sign_idx = int(planets[asc_lord_name]["longitude"] // 30)
    arudha_lagna_sign = calculate_arudha_lagna(asc_sign_idx, asc_lord_sign_idx)

    # Combustion
    sun_lon = planets["Sun"]["longitude"]
    combustion = {}
    for name, orb in COMBUST_ORBS.items():
        if name in planets:
            diff = abs(planets[name]["longitude"] - sun_lon)
            if diff > 180:
                diff = 360 - diff
            if diff <= orb:
                combustion[name] = round(diff, 2)

    # Natal Aspects
    natal_aspects = compute_natal_aspects(planets, house_positions)

    # Strength Scores
    strength_scores = {}
    for name, pdata in planets.items():
        house = house_positions.get(name, 1)
        strength_scores[name] = compute_planet_strength(name, pdata, house, combustion)

    # Yoga Detection
    yogas = detect_yogas(planets, house_positions, asc_sign_idx)

    # Navamsha (D9) chart
    navamsha = compute_navamsha_chart(planets, asc_lon)

    # Atmakaraka (soul planet)
    ak_name, ak_degree = find_atmakaraka(planets)

    # Graha Yuddha (planetary war)
    graha_yuddha = detect_graha_yuddha(planets)

    # Sade Sati
    moon_lon = planets["Moon"]["longitude"]
    sade_sati = detect_sade_sati(moon_lon)

    # Dasamsa (D10) career chart
    dasamsa = compute_dasamsa_chart(planets, asc_lon)

    # Bhava lords
    bhava_lords = compute_bhava_lords(asc_sign_idx, planets)
    
    # Inject Atmakaraka and House into individual planet dictionaries
    for name, pdata in planets.items():
        pdata["house"] = house_positions.get(name)
        pdata["is_atmakaraka"] = (name == ak_name)

    # Panchada friendships
    friendships = compute_panchada_friendships(planets)

    # Sarva Ashtakavarga
    sarva_ashtakavarga = compute_sarva_ashtakavarga(planets, asc_sign_idx)

    # Vimshottari Dasha
    moon_nak_idx, moon_pada, moon_nak_balance = lon_to_nakshatra(moon_lon)
    dasha_data = compute_vimshottari_dasha(moon_nak_idx, moon_nak_balance, dob_str)

    return {
        "ascendant": {
            "sign": asc_sign,
            "degree": asc_deg,
            "minute": asc_min,
            "nakshatra": NAKSHATRAS[asc_nak_idx],
            "pada": asc_pada,
            "is_gandanta": check_gandanta(asc_lon),
        },
        "arudha_lagna": arudha_lagna_sign,
        "planets": planets,
        "houses": house_positions,
        "combustion": combustion,
        "natal_aspects": natal_aspects,
        "strength_scores": strength_scores,
        "yogas": yogas,
        "navamsha": navamsha,
        "dasamsa": dasamsa,
        "special_lagnas": {
            "atmakaraka": ak_name,
            "atmakaraka_degree": ak_degree
        },
        "graha_yuddha": graha_yuddha,
        "sade_sati": sade_sati,
        "bhava_lords": bhava_lords,
        "friendships": friendships,
        "sarva_ashtakavarga": sarva_ashtakavarga,
        "moon_nakshatra": NAKSHATRAS[moon_nak_idx],
        "dasha": dasha_data,
        "timezone": tz_name,
    }


def compute_vimshottari_dasha(moon_nak_idx, moon_nak_balance, dob_str):
    year, month, day = map(int, dob_str.split('-'))
    dob = datetime.datetime(year, month, day)
    now = datetime.datetime.now()

    start_lord = NAKSHATRA_LORDS[moon_nak_idx]
    start_idx = DASHA_SEQUENCE.index(start_lord)

    remaining_years = DASHA_YEARS[start_lord] * moon_nak_balance
    remaining_days = remaining_years * 365.24219

    mahadashas = []
    cursor = dob

    end = cursor + datetime.timedelta(days=remaining_days)
    mahadashas.append({
        "lord": start_lord,
        "start": cursor.strftime("%Y-%m-%d"),
        "end": end.strftime("%Y-%m-%d"),
        "years": round(remaining_years, 2),
        "current": cursor <= now < end,
    })
    cursor = end

    for i in range(1, 9):
        idx = (start_idx + i) % 9
        lord = DASHA_SEQUENCE[idx]
        years = DASHA_YEARS[lord]
        end = cursor + datetime.timedelta(days=years * 365.24219)
        mahadashas.append({
            "lord": lord,
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "years": years,
            "current": cursor <= now < end,
        })
        cursor = end

    current_md = None
    for md in mahadashas:
        if md["current"]:
            current_md = md
            break

    current_ad = None
    current_pd = None

    if current_md:
        md_lord = current_md["lord"]
        md_start = datetime.datetime.strptime(current_md["start"], "%Y-%m-%d")
        md_years = current_md["years"]
        md_idx = DASHA_SEQUENCE.index(md_lord)

        ad_sequence = DASHA_SEQUENCE[md_idx:] + DASHA_SEQUENCE[:md_idx]
        ad_cursor = md_start

        for ad_lord in ad_sequence:
            ad_days = (md_years * DASHA_YEARS[ad_lord] * 365.25) / 120
            ad_end = ad_cursor + datetime.timedelta(days=ad_days)

            if ad_cursor <= now < ad_end:
                current_ad = ad_lord

                pd_idx = DASHA_SEQUENCE.index(ad_lord)
                pd_sequence = DASHA_SEQUENCE[pd_idx:] + DASHA_SEQUENCE[:pd_idx]
                pd_cursor = ad_cursor

                for pd_lord in pd_sequence:
                    pd_days = (md_years * DASHA_YEARS[ad_lord] * DASHA_YEARS[pd_lord] * 365.25) / (120 * 120)
                    pd_end = pd_cursor + datetime.timedelta(days=pd_days)

                    if pd_cursor <= now < pd_end:
                        current_pd = pd_lord
                        break
                    pd_cursor = pd_end
                break
            ad_cursor = ad_end

    return {
        "mahadashas": mahadashas,
        "current_md": current_md["lord"] if current_md else None,
        "current_ad": current_ad,
        "current_pd": current_pd,
    }


# ─── Enhanced Chart Context Formatter ─────────────────────────────────────────

def format_chart_as_context(chart_data, name="User"):
    """Format computed chart data into an ultra-detailed system prompt context block."""
    c = chart_data
    asc = c["ascendant"]

    ctx = f"{'='*60}\n{name.upper()}'S COMPLETE VEDIC BIRTH CHART ANALYSIS\n{'='*60}\n\n"

    # Timezone
    ctx += f"TIMEZONE USED: {c.get('timezone', 'Unknown')}\n\n"

    # Ascendant
    ctx += f"ASCENDANT: {asc['sign']} ({asc['degree']}°{asc['minute']}') | {asc['nakshatra']} Pada {asc['pada']}"
    if asc.get("is_gandanta"):
        ctx += " [GANDANTA — Deep karmic knot at the very foundation of self-identity]"
    ctx += "\n"
    ctx += f"ASCENDANT LORD: {LORD_MAP.get(RASIS.index(asc['sign']), '?')}\n"

    ctx += f"\nARUDHA LAGNA (Public Mask / Worldly Perception): {c.get('arudha_lagna', 'Unknown')}\n"
    ctx += "→ Arudha Lagna = how the outside world sees this person vs. who they actually are (Ascendant). The gap between these two is the source of their deepest exhaustion.\n\n"

    # Planetary Positions with Dignity and Strength
    ctx += "PLANETARY POSITIONS (Sidereal/Lahiri Ayanamsha):\n"
    ctx += f"{'Planet':<10} {'Sign':<14} {'Deg':>4} {'Nak':<20} {'House':>5} {'Dignity':<14} {'Str':>4} {'Notes'}\n"
    ctx += "─" * 95 + "\n"

    for name_p, p in c["planets"].items():
        house = c["houses"].get(name_p, "?")
        state_str = f" {p['state']}" if p['state'] else ""
        dignity = p.get("dignity", "")
        strength = c["strength_scores"].get(name_p, 50)

        notes = []
        if p.get("is_gandanta"):
            notes.append("GANDANTA")
        if name_p in c["combustion"]:
            orb = c["combustion"][name_p]
            if orb < 1:
                notes.append(f"ASTANGATA(combust {orb}°)")
            else:
                notes.append(f"COMBUST({orb}°)")
        if p['state'] == "(R)":
            notes.append("RETROGRADE")
        notes_str = " | ".join(notes) if notes else ""

        ctx += f"  {name_p:<10} {p['sign']:<14} {p['degree']:>2}°{p['minute']:>02}'{state_str:<4} {p['nakshatra']:<20} H{house:>2}    {dignity:<14} {strength:>3}/100 {notes_str}\n"

    # Natal Aspects
    if c.get("natal_aspects"):
        ctx += "\nNATAL ASPECT GRID:\n"
        conjunctions = [a for a in c["natal_aspects"] if a["type"] == "conjunction"]
        aspects = [a for a in c["natal_aspects"] if a["type"] == "aspect"]

        if conjunctions:
            ctx += "  CONJUNCTIONS:\n"
            for a in conjunctions:
                ctx += f"    {a['from']} ☌ {a['to']} (orb: {a.get('orb', '?')}°)\n"

        if aspects:
            ctx += "  VEDIC ASPECTS:\n"
            for a in aspects:
                ctx += f"    {a['from']} aspects {a['to']}\n"

    # Yogas
    if c.get("yogas"):
        ctx += f"\nACTIVE YOGAS ({len(c['yogas'])} detected):\n"
        for y in c["yogas"]:
            ctx += f"  ★ {y['name']} [{y['strength']}]\n"
            ctx += f"    Planets: {y['planets']}\n"
            ctx += f"    Psychological Impact: {y['meaning']}\n"

    # Combustion detail
    if c["combustion"]:
        ctx += "\nCOMBUSTION ANALYSIS:\n"
        for pname, orb in c["combustion"].items():
            ctx += f"  {pname}: {orb}° from Sun"
            if orb < 1:
                ctx += " → ASTANGATA: planet's significations are completely swallowed, creating deep hidden wounds"
            elif orb < 3:
                ctx += " → SEVERE: the planet's energy is drastically suppressed"
            elif orb < 6:
                ctx += " → MODERATE: planet struggles to express its nature freely"
            else:
                ctx += " → MILD: subtle suppression"
            ctx += "\n"

    # Dasha
    dasha = c["dasha"]
    if dasha["current_md"]:
        ctx += f"\nCURRENT VIMSHOTTARI DASHA (Timing System):\n"
        ctx += f"  Mahadasha:   {dasha['current_md']} (dominant life theme RIGHT NOW)\n"
        ctx += f"  Antardasha:  {dasha['current_ad']} (sub-theme coloring the current period)\n"
        ctx += f"  Pratyantar:  {dasha['current_pd']} (micro-theme of this exact moment)\n"
        ctx += f"  → The combination {dasha['current_md']}-{dasha['current_ad']}-{dasha['current_pd']} creates a SPECIFIC psychological atmosphere. Synthesize what these three planetary energies combined mean for the native's CURRENT lived experience.\n"

    ctx += "\nMAHADASHA TIMELINE:\n"
    for md in dasha["mahadashas"]:
        marker = " ◄ CURRENT" if md["current"] else ""
        ctx += f"  {md['lord']}: {md['start']} → {md['end']} ({md['years']} yr){marker}\n"

    # Navamsha (D9) — the chart of dharma, marriage, and inner self
    if c.get("navamsha"):
        ctx += "\nNAVAMSHA (D9) — DHARMA & RELATIONSHIP CHART:\n"
        ctx += "→ Navamsha reveals the INNER self, dharmic purpose, and the reality of relationships.\n"
        ctx += "→ A planet in the same sign in both Rasi and Navamsha = VARGOTTAMA (extremely strong and pure).\n"
        for name_p, d9_sign in c["navamsha"].items():
            rasi_sign = ""
            if name_p == "Ascendant":
                rasi_sign = c["ascendant"]["sign"]
            elif name_p in c["planets"]:
                rasi_sign = c["planets"][name_p]["sign"]
            vargottama = " [VARGOTTAMA — exceptionally pure and strong]" if d9_sign == rasi_sign else ""
            ctx += f"  {name_p:<10} D9: {d9_sign}{vargottama}\n"

    # Atmakaraka (soul planet)
    ak = c.get("atmakaraka", {})
    if ak.get("planet"):
        ak_meanings = {
            "Sun": "soul craves recognition, authority, and self-mastery. the life lesson is learning to lead without ego.",
            "Moon": "soul craves emotional security and nurturing. the lesson is learning that peace comes from within, not from others.",
            "Mars": "soul craves courage and conquest. the lesson is learning to fight without destroying.",
            "Mercury": "soul craves knowledge and communication. the lesson is learning that understanding is not the same as wisdom.",
            "Jupiter": "soul craves wisdom, teaching, and expansion. the lesson is learning humility in the face of knowledge.",
            "Venus": "soul craves beauty, love, and pleasure. the lesson is learning that real love requires sacrifice.",
            "Saturn": "soul craves discipline and structure. the lesson is learning that control is an illusion.",
        }
        meaning = ak_meanings.get(ak["planet"], "soul purpose defined by this planet's themes.")
        ctx += f"\nATMAKARAKA (Soul Planet): {ak['planet']} at {ak['degree']}° in sign\n"
        ctx += f"→ The Atmakaraka is the KING of the chart. Whatever this planet signifies is the native's deepest karmic purpose.\n"
        ctx += f"→ {meaning}\n"

    # Graha Yuddha (planetary war)
    if c.get("graha_yuddha"):
        ctx += "\nGRAHA YUDDHA (PLANETARY WAR):\n"
        ctx += "→ When two planets are within 1° of each other, they are at war. The loser's significations are suppressed.\n"
        for war in c["graha_yuddha"]:
            ctx += f"  ⚔ {war['planets']} (orb: {war['orb']}°) → WINNER: {war['winner']}, LOSER: {war['loser']}\n"
            ctx += f"    The loser ({war['loser']}) has its themes crushed and dominated by {war['winner']}. This creates intense internal conflict.\n"

    # Sade Sati
    sade_sati = c.get("sade_sati", {})
    if sade_sati.get("active"):
        ctx += f"\n⚠ SADE SATI — ACTIVE ({sade_sati['phase'].upper()} PHASE)\n"
        ctx += f"→ Saturn is transiting over the natal Moon. This is the most psychologically crushing transit in Vedic astrology (7.5 years).\n"
        ctx += f"→ {sade_sati['meaning']}\n"
        ctx += "→ THIS MUST heavily influence your reading of 'today at a glance', 'emotions', and 'pressure' sections. The native is in a period of deep transformation.\n"

    # Dasamsa (D10) — Career chart
    if c.get("dasamsa"):
        ctx += "\nDASAMSA (D10) — CAREER & SOCIAL STATUS CHART:\n"
        ctx += "→ D10 reveals the native's professional destiny and public achievement.\n"
        for name_p, d10_sign in c["dasamsa"].items():
            ctx += f"  {name_p:<10} D10: {d10_sign}\n"

    # Bhava Lords — lord of each house and where it sits
    if c.get("bhava_lords"):
        ctx += "\nBHAVA LORDS (Lord of Each House → Where It Sits):\n"
        ctx += "→ The lord's placement tells the STORY of that house. E.g., lord of 7th (marriage) in 12th (loss) = relationships that dissolve.\n"
        house_meanings = {
            1: "Self/Body", 2: "Wealth/Speech", 3: "Courage/Siblings", 4: "Home/Mother",
            5: "Children/Creativity", 6: "Enemies/Illness", 7: "Marriage/Partners", 8: "Death/Secrets",
            9: "Fortune/Father", 10: "Career/Fame", 11: "Gains/Wishes", 12: "Loss/Liberation"
        }
        for h, data in c["bhava_lords"].items():
            meaning = house_meanings.get(h, "")
            ctx += f"  H{h:>2} ({meaning:<18}) {data['sign']:<14} Lord: {data['lord']:<10} → sits in H{data['lord_in_house']} ({data['lord_dignity']})\n"

    # Panchada Friendships — only show significant ones (intimate/bitter)
    if c.get("friendships"):
        ctx += "\nKEY PLANETARY RELATIONSHIPS (Panchada — 5-fold friendships):\n"
        ctx += "→ Intimate friends amplify each other. Bitter enemies create crushing internal conflict.\n"
        for pname, relations in c["friendships"].items():
            intimates = [o for o, r in relations.items() if r == "intimate friend"]
            bitters = [o for o, r in relations.items() if r == "bitter enemy"]
            if intimates:
                ctx += f"  {pname} ♡ {', '.join(intimates)} (intimate allies — these themes support each other deeply)\n"
            if bitters:
                ctx += f"  {pname} ⚔ {', '.join(bitters)} (bitter enemies — these themes are at war inside the native)\n"

    # Sarva Ashtakavarga — transit strength per sign
    if c.get("sarva_ashtakavarga"):
        ctx += "\nSARVA ASHTAKAVARGA (Transit Strength by Sign):\n"
        ctx += "→ When planets transit signs with high SAV points (25+), the transit is FAVORABLE. Low points (<25) = DIFFICULT transit.\n"
        sav = c["sarva_ashtakavarga"]
        for sign_name, points in sorted(sav.items(), key=lambda x: x[1], reverse=True):
            bar = "●" * points + "○" * (max(0, 8 - points))
            label = "STRONG" if points >= 5 else "MODERATE" if points >= 3 else "WEAK"
            ctx += f"  {sign_name:<14} {bar} {points} pts ({label})\n"

    # Strength Summary
    ctx += "\nPLANETARY STRENGTH SUMMARY (0=powerless, 100=dominant):\n"
    sorted_strengths = sorted(c["strength_scores"].items(), key=lambda x: x[1], reverse=True)
    for name_p, score in sorted_strengths:
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        label = "DOMINANT" if score >= 75 else "STRONG" if score >= 60 else "MODERATE" if score >= 40 else "WEAK" if score >= 25 else "AFFLICTED"
        ctx += f"  {name_p:<10} [{bar}] {score}/100 ({label})\n"

    ctx += f"\n{'='*60}\nEND CHART DATA\n{'='*60}\n"
    return ctx


# ─── Legacy Transit Functions ─────────────────────────────────────────────────

def calculate_aspects(transit_lon, transit_name, natal_planets):
    aspects = []
    ORB = 5.0
    for natal_name, natal_lon in natal_planets.items():
        distance = (natal_lon - transit_lon) % 360
        if distance < ORB or distance > (360 - ORB):
            aspects.append(f"CONJUNCT Natal {natal_name}")
        if abs(distance - 180) <= ORB:
            aspects.append(f"7TH ASPECT to Natal {natal_name}")
        if transit_name == "Mars":
            if abs(distance - 90) <= ORB:
                aspects.append(f"4TH ASPECT to Natal {natal_name}")
            elif abs(distance - 210) <= ORB:
                aspects.append(f"8TH ASPECT to Natal {natal_name}")
        elif transit_name in ["Jupiter", "Rahu", "Ketu"]:
            if abs(distance - 120) <= ORB:
                aspects.append(f"5TH ASPECT to Natal {natal_name}")
            elif abs(distance - 240) <= ORB:
                aspects.append(f"9TH ASPECT to Natal {natal_name}")
        elif transit_name == "Saturn":
            if abs(distance - 60) <= ORB:
                aspects.append(f"3RD ASPECT to Natal {natal_name}")
            elif abs(distance - 270) <= ORB:
                aspects.append(f"10TH ASPECT to Natal {natal_name}")
    return aspects


def get_live_astro_context(natal_planets=None, sav_scores=None):
    """Live transits — optionally against custom natal positions."""
    if natal_planets is None:
        natal_planets = NATAL_PLANETS_SOUV
    if sav_scores is None:
        sav_scores = SAV_SCORES_SOUV

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                    now_utc.hour + now_utc.minute/60.0 + now_utc.second/3600.0)

    live_transits = []
    live_aspects = []
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    for name, p_id in PLANET_IDS.items():
        try:
            pos, ret = swe.calc_ut(jd, p_id, flags)
            plan_lon = pos[0]
            speed = pos[3]

            sign_name = lon_to_sign(plan_lon)
            deg, min_arc = lon_to_dms(plan_lon)
            state = get_planetary_state(speed, name)
            sav_score = sav_scores.get(sign_name, 28)
            sav_eval = "FAVORABLE" if sav_score >= 28 else "UNFAVORABLE"

            transit_str = f"{name}: {sign_name} ({deg}°{min_arc}') {state} -> SAV: {sav_score}/56 ({sav_eval})"
            live_transits.append(transit_str)

            aspect_hits = calculate_aspects(plan_lon, name, natal_planets)
            for hit in aspect_hits:
                live_aspects.append(f"Transit {name}: {hit}")

            if name == "Rahu":
                ketu_lon = (plan_lon + 180) % 360
                k_sign = lon_to_sign(ketu_lon)
                k_deg, k_min = lon_to_dms(ketu_lon)
                k_sav = sav_scores.get(k_sign, 28)
                k_eval = "FAVORABLE" if k_sav >= 28 else "UNFAVORABLE"
                live_transits.append(f"Ketu: {k_sign} ({k_deg}°{k_min}') -> SAV: {k_sav}/56 ({k_eval})")
                for hit in calculate_aspects(ketu_lon, "Ketu", natal_planets):
                    live_aspects.append(f"Transit Ketu: {hit}")

        except Exception as e:
            print(f"Error calculating {name}: {e}")

    context = "=== LIVE TRANSITS (Current Sky) ===\n"
    context += f"Time: {now_utc.strftime('%Y-%m-%d %H:%M')} UTC\n"
    for t in live_transits:
        context += f"- {t}\n"
    if live_aspects:
        context += "\nACTIVE TRANSIT ASPECTS TO NATAL CHART:\n"
        for a in live_aspects:
            context += f"!! {a}\n"
    context += "=== END TRANSITS ==="
    return context


def get_current_dasha(date_to_calc=None):
    """Souv's hardcoded dasha (backward compat)."""
    if date_to_calc is None:
        date_to_calc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    mahadashas = [
        ("Ketu", datetime.datetime(1997, 12, 5), datetime.datetime(2004, 12, 5), 7),
        ("Venus", datetime.datetime(2004, 12, 5), datetime.datetime(2024, 12, 5), 20),
        ("Sun", datetime.datetime(2024, 12, 5), datetime.datetime(2030, 12, 5), 6),
        ("Moon", datetime.datetime(2030, 12, 5), datetime.datetime(2040, 12, 5), 10),
        ("Mars", datetime.datetime(2040, 12, 5), datetime.datetime(2047, 12, 6), 7),
        ("Rahu", datetime.datetime(2047, 12, 6), datetime.datetime(2065, 12, 5), 18),
        ("Jupiter", datetime.datetime(2065, 12, 5), datetime.datetime(2081, 12, 5), 16),
        ("Saturn", datetime.datetime(2081, 12, 5), datetime.datetime(2100, 12, 6), 19),
        ("Mercury", datetime.datetime(2100, 12, 6), datetime.datetime(2117, 12, 5), 17)
    ]

    dasha_sequence_tuples = [(name, DASHA_YEARS[name]) for name in DASHA_SEQUENCE]

    current_md = None
    md_start = None
    md_total_years = 0

    for md_name, start_date, end_date, total_years in mahadashas:
        if start_date <= date_to_calc < end_date:
            current_md = md_name
            md_start = start_date
            md_total_years = total_years
            break

    if not current_md:
        return "Dasha calculation out of bounds."

    start_idx = next(i for i, v in enumerate(dasha_sequence_tuples) if v[0] == current_md)
    ad_sequence_ordered = dasha_sequence_tuples[start_idx:] + dasha_sequence_tuples[:start_idx]

    current_ad = None
    ad_start = md_start
    ad_years = 0

    for ad_name, ad_lord_years in ad_sequence_ordered:
        ad_days = (md_total_years * ad_lord_years * 365.24219) / 120
        ad_end = ad_start + datetime.timedelta(days=ad_days)
        if ad_start <= date_to_calc < ad_end:
            current_ad = ad_name
            ad_years = ad_lord_years
            break
        ad_start = ad_end

    start_pd_idx = next(i for i, v in enumerate(dasha_sequence_tuples) if v[0] == current_ad)
    pd_sequence_ordered = dasha_sequence_tuples[start_pd_idx:] + dasha_sequence_tuples[:start_pd_idx]

    current_pd = None
    pd_start = ad_start

    for pd_name, pd_lord_years in pd_sequence_ordered:
        pd_days = (ad_years * pd_lord_years * md_total_years * 365.24219) / (120 * 120)
        pd_end = pd_start + datetime.timedelta(days=pd_days)
        if pd_start <= date_to_calc < pd_end:
            current_pd = pd_name
            break
        pd_start = pd_end

    dasha_context = f"\n=== LIVE VIMSHOTTARI DASHA ===\n"
    dasha_context += f"- Mahadasha: {current_md}\n"
    dasha_context += f"- Antardasha: {current_ad}\n"
    dasha_context += f"- Pratyantar: {current_pd}\n"
    dasha_context += "=== END DASHA ==="
    return dasha_context


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Timezone-Aware Chart Computation")
    print("=" * 60)

    # Test: Souv's data (Bankura, India)
    chart = compute_natal_chart("2000-12-25", "13:44:39", 23.25, 87.07)
    print(format_chart_as_context(chart, "Souv"))

    # Print Yogas separately
    if chart["yogas"]:
        print(f"\n🔮 Detected {len(chart['yogas'])} Yogas:")
        for y in chart["yogas"]:
            print(f"   ★ {y['name']} ({y['strength']})")
    print()

    # Test legacy
    print("=== Live Transits ===")
    print(get_live_astro_context())
    print(get_current_dasha())
