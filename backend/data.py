"""The sample flight network: 28 Indian airports and ~85 direct routes."""
from model import Graph

AIRPORTS = [
    ("DEL", "Delhi", 28.5562, 77.1000), ("BOM", "Mumbai", 19.0896, 72.8656),
    ("BLR", "Bengaluru", 13.1986, 77.7066), ("MAA", "Chennai", 12.9900, 80.1693),
    ("CCU", "Kolkata", 22.6547, 88.4467), ("HYD", "Hyderabad", 17.2403, 78.4294),
    ("AMD", "Ahmedabad", 23.0772, 72.6347), ("PNQ", "Pune", 18.5821, 73.9197),
    ("GOI", "Goa", 15.3808, 73.8314), ("COK", "Kochi", 10.1520, 76.4019),
    ("TRV", "Thiruvananthapuram", 8.4821, 76.9200), ("JAI", "Jaipur", 26.8242, 75.8122),
    ("LKO", "Lucknow", 26.7606, 80.8893), ("PAT", "Patna", 25.5913, 85.0880),
    ("GAU", "Guwahati", 26.1061, 91.5859), ("IXC", "Chandigarh", 30.6735, 76.7885),
    ("SXR", "Srinagar", 33.9871, 74.7742), ("BBI", "Bhubaneswar", 20.2444, 85.8178),
    ("NAG", "Nagpur", 21.0922, 79.0472), ("IDR", "Indore", 22.7218, 75.8011),
    ("VNS", "Varanasi", 25.4524, 82.8593), ("ATQ", "Amritsar", 31.7096, 74.7973),
    ("IXL", "Leh", 34.1359, 77.5465), ("VTZ", "Visakhapatnam", 17.7212, 83.2245),
    ("IXB", "Bagdogra", 26.6812, 88.3286), ("RPR", "Raipur", 21.1804, 81.7388),
    ("CJB", "Coimbatore", 11.0300, 77.0434), ("IMF", "Imphal", 24.7600, 93.8967),
]

ROUTES = {
    "DEL": "BOM BLR MAA CCU HYD AMD PNQ JAI LKO PAT GAU IXC SXR VNS ATQ IXL IDR NAG BBI GOI COK",
    "BOM": "BLR MAA CCU HYD AMD GOI COK TRV JAI IDR NAG PNQ LKO",
    "BLR": "MAA HYD COK GOI CCU TRV CJB PNQ VTZ",
    "MAA": "HYD COK CCU TRV CJB VTZ",
    "CCU": "GAU PAT BBI IXB VTZ IMF HYD LKO RPR",
    "HYD": "NAG VTZ PNQ GOI RPR BBI",
    "AMD": "JAI IDR PNQ",
    "GAU": "IMF IXB",
    "COK": "TRV CJB",
    "JAI": "LKO",
    "LKO": "VNS",
    "PAT": "VNS",
    "NAG": "RPR IDR",
    "IXC": "SXR ATQ",
    "SXR": "IXL ATQ",
    "BBI": "VTZ RPR",
}


def build_network():
    g = Graph()
    for code, city, lat, lon in AIRPORTS:
        g.add_airport(code, city, lat, lon)
    for a, targets in ROUTES.items():
        for b in targets.split():
            g.add_route(a, b)
    return g
