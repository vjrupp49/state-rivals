"""Static reference: state FIPS <-> USPS abbreviation <-> name.

Standard Census Bureau state FIPS codes (50 states + DC). This table is
official/static reference data, not a research finding, so it is
hand-maintained here rather than re-derived per script.
"""

STATE_FIPS_TO_USPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}

# All 50 contest states (D-001). DC is retained in the network (docs/PROTOCOL.md
# section 5) but is not a contestant.
CONTEST_STATES = {usps for fips, usps in STATE_FIPS_TO_USPS.items() if usps != "DC"}

CENSUS_REGION_NAMES = {
    "1": "Northeast",
    "2": "Midwest",
    "3": "South",
    "4": "West",
}

CENSUS_DIVISION_NAMES = {
    "1": "New England",
    "2": "Middle Atlantic",
    "3": "East North Central",
    "4": "West North Central",
    "5": "South Atlantic",
    "6": "East South Central",
    "7": "West South Central",
    "8": "Mountain",
    "9": "Pacific",
}
