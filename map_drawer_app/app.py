from flask import Flask, request, jsonify
import requests # Import the requests library
import json # Import the json library
from playwright.sync_api import sync_playwright

app = Flask(__name__, static_folder='.', static_url_path='')

# Basic point-in-polygon check using the ray casting algorithm
def is_point_in_polygon(point, polygon):
    x, y = point
    num_vertices = len(polygon)
    is_inside = False

    p1x, p1y = polygon[0]
    for i in range(num_vertices + 1):
        p2x, p2y = polygon[i % num_vertices]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        is_inside = not is_inside
        p1x, p1y = p2x, p2y

    return is_inside

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/process_polygon', methods=['POST'])
def process_polygon():
    data = request.get_json()
    polygon_coords = data.get('polygon', [])

    # Implement polygon to rectangles logic here
    print(f"Received polygon: {polygon_coords}")

    rectangles = []
    if polygon_coords:
        # Calculate bounding box
        min_lat = min(p[0] for p in polygon_coords)
        max_lat = max(p[0] for p in polygon_coords)
        min_lon = min(p[1] for p in polygon_coords)
        max_lon = max(p[1] for p in polygon_coords)

        # Define grid resolution (adjust as needed for precision)
        lat_step = (max_lat - min_lat) / 50  # Example: 50 divisions in latitude
        lon_step = (max_lon - min_lon) / 50  # Example: 50 divisions in longitude

        # Iterate over grid cells
        lat = min_lat
        while lat < max_lat:
            lon = min_lon
            while lon < max_lon:
                # Check if the center of the grid cell is inside the polygon
                # Using a simple point-in-polygon check (ray casting algorithm)
                # This is a basic implementation and can be improved for complex polygons or performance
                point = (lat + lat_step / 2, lon + lon_step / 2)
                if is_point_in_polygon(point, polygon_coords):
                    rectangles.append({
                        'lat_min': lat,
                        'lon_min': lon,
                        'lat_max': lat + lat_step,
                        'lon_max': lon + lon_step
                    })
                lon += lon_step
            lat += lat_step

    return jsonify({"rectangles": rectangles})

@app.route('/send_multiple_rectangles', methods=['POST'])
def send_multiple_rectangles():
    data = request.get_json()
    shapes_data = data.get('shapes', [])
    
    response_results = []

    if not shapes_data:
        return jsonify({"message": "No shapes data received.", "results": []}), 400

    for shape in shapes_data:
        shape_id = shape.get('id')
        shape_name = shape.get('name', 'Unknown Shape')
        rectangles = shape.get('rectangles', [])

        print(f"\nReceived Riemann Rectangles for Shape ID '{shape_id}' (Name: '{shape_name}'):")
        if rectangles:
            for i, rect in enumerate(rectangles):
                print(f"  Rectangle {i+1}: Lat: {rect['lat_min']}-{rect['lat_max']}, Lon: {rect['lon_min']}-{rect['lon_max']}")
            response_results.append({
                "shapeId": shape_id,
                "status": "success",
                "message": f"Rectangles for '{shape_name}' received successfully."
            })
        else:
            print("  No rectangles received for this shape.")
            response_results.append({
                "shapeId": shape_id,
                "status": "error",
                "message": f"No rectangles received for '{shape_name}'."
            })
            
    return jsonify({"message": "Processed all toggled shapes.", "results": response_results})


if __name__ == '__main__':
    app.run(debug=True)
