import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key
api_key = os.getenv("GOOGLE_MAPS_API_KEY")

import googlemaps
from itertools import permutations

# Replace 'YOUR_API_KEY' with your actual Google Maps API key
gmaps = googlemaps.Client(key=api_key)

# Define the list of locations
locations = [
    "New York, NY",
    "Los Angeles, CA",
    "Chicago, IL",
    "Houston, TX",
    "Phoenix, AZ",
]


# Get the distance matrix
def get_distance_matrix(locations):
    distance_matrix = []
    for location1 in locations:
        row = []
        for location2 in locations:
            if location1 == location2:
                row.append(0)
            else:
                result = gmaps.distance_matrix(location1, location2, mode="driving")
                distance = result["rows"][0]["elements"][0]["distance"]["value"]
                row.append(distance)
        distance_matrix.append(row)
    return distance_matrix


# Calculate the total distance of a path
def calculate_total_distance(path, distance_matrix):
    total_distance = 0
    for i in range(len(path) - 1):
        total_distance += distance_matrix[path[i]][path[i + 1]]
    total_distance += distance_matrix[path[-1]][path[0]]  # Return to the starting point
    return total_distance


# Find the shortest path using brute force
def tsp_bruteforce(locations):
    distance_matrix = get_distance_matrix(locations)
    num_locations = len(locations)
    shortest_path = None
    min_distance = float("inf")

    for path in permutations(range(num_locations)):
        distance = calculate_total_distance(path, distance_matrix)
        if distance < min_distance:
            min_distance = distance
            shortest_path = path

    return shortest_path, min_distance


# Solve the TSP
shortest_path, min_distance = tsp_bruteforce(locations)

# Print the result
print(f"Shortest path: {locations[shortest_path[0]]}", end=" -> ")
for i in range(1, len(shortest_path)):
    print(f"{locations[shortest_path[i]]}", end=" -> ")
print(f"{locations[shortest_path[0]]}")
print(f"Total distance: {min_distance} meters")
