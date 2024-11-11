import requests
import pandas as pd
from geopy.distance import geodesic # type: ignore

class HouseRanking:
    def __init__(self, search_location, radius_km):
        self.search_location = self.get_coordinates(search_location)  # Use get_coordinates to fetch lat/lon
        self.radius_km = radius_km
        self.houses = []

    def get_coordinates(self, location):  # New function for geocoding
        # Use OpenStreetMap Nominatim API to get the latitude and longitude
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location,
            'format': 'json',
            'addressdetails': 1,
            'limit': 1
        }
        response = requests.get(url, params=params)
        response_data = response.json()

        if response_data:
            lat = float(response_data[0]["lat"])
            lon = float(response_data[0]["lon"])
            print(f"Found coordinates for '{location}': Latitude = {lat}, Longitude = {lon}")
            return {"latitude": lat, "longitude": lon}
        else:
            raise ValueError("Location not found. Please enter a valid address or city name.")
        
        
    def fetch_data(self):
        # Placeholder: This function would fetch data from Realtor.ca
        # Example: Use an API or scraping tool to collect house data.
        # Let's simulate this with sample data for now.
        sample_data = [
            {"address": "123 Maple St", "price": 500000, "size": 2000, "walk_score": 80, "transit_score": 70, "latitude": 45.4215, "longitude": -75.6972},
            {"address": "456 Oak St", "price": 450000, "size": 1800, "walk_score": 60, "transit_score": 50, "latitude": 45.4245, "longitude": -75.6950},
            {"address": "789 Pine St", "price": 550000, "size": 2200, "walk_score": 85, "transit_score": 75, "latitude": 45.4230, "longitude": -75.6985}
        ]
        self.houses = sample_data

    def calculate_distance(self, house):
        search_coords = (self.search_location['latitude'], self.search_location['longitude'])
        house_coords = (house['latitude'], house['longitude'])
        return geodesic(search_coords, house_coords).km

    def filter_houses_within_radius(self):
        # Filter houses based on the radius
        filtered_houses = []
        for house in self.houses:
            distance = self.calculate_distance(house)
            if distance <= self.radius_km:
                house["distance"] = distance
                filtered_houses.append(house)
        self.houses = filtered_houses

    def rank_houses(self):
        # Ranking houses based on chosen KPIs
        for house in self.houses:
            # Simple scoring formula combining KPIs
            house['score'] = (
                (1000000 / house['price']) +         # Higher score for lower price
                (house['size'] / 100) +              # Higher score for larger size
                (house['walk_score'] * 0.3) +        # Walk score weighted
                (house['transit_score'] * 0.2)       # Transit score weighted
            )

        # Sort houses based on the computed score in descending order
        self.houses.sort(key=lambda x: x['score'], reverse=True)

    def display_ranked_houses(self):
        # Display ranked houses
        df = pd.DataFrame(self.houses)
        df = df[['address', 'price', 'size', 'walk_score', 'transit_score', 'distance', 'score']]
        df.columns = ['Address', 'Price ($)', 'Size (sqft)', 'Walk Score', 'Transit Score', 'Distance (km)', 'Score']
        print(df)

    def run(self):
        self.fetch_data()
        self.filter_houses_within_radius()
        self.rank_houses()
        self.display_ranked_houses()

# Example Usage
if __name__ == "__main__":
    # Define search location and radius
    search_location = {"latitude": 45.4215, "longitude": -75.6972}  # Replace with actual lat/lon or use geocoding for address input
    radius_km = 10

    house_ranker = HouseRanking(search_location, radius_km)
    house_ranker.run()
