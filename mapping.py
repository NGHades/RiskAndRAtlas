import requests
import folium
from datetime import date, time
import math
import json
import os

# Notes -----------------------
# This should be okay to just add more functions that let you make API calls to get (hopefully) a GeoJson object.
# A GeoJson object is just a JSON file with geometry. 
#
# Depending on the data we want to display, you might have to modify the shape, which can get pretty complicated.
# Please feel free to ask for help.
# - Larry
# ----------------------------

with open('api_keys.json', 'r', encoding='utf-8') as file:
    keys = json.load(file)

#map api link, these keys should be fine to use for the live build too?
map_api_key =  keys["Carto"]
map_tiles_url = "https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key={map_api_key}"

def get_earthquake_info(latitude: float, longitude: float, max_radius: int) -> requests.Response:
    """
        Returns the response object itself.

        Takes in latitude, longitude, and max_radius to send a query to USGS's Earthquake API. 
        Gives us a response of all of the earthquakes recorded in the past month within the provided radius from the coordinates.
    """
    query_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
    params = {
        'format': 'geojson',
        'longitude': longitude,
        'latitude': latitude,
        'maxradiuskm': max_radius
    }

    r = requests.get(query_url, params=params)

    return r

#creates a map object with the tiles url above. returns the map object
def make_map(latitude: float, longitude: float) -> folium.Map:
    """
        Returns a Map object.

        Takes in latitude and longitude to create an empty map.
        Uses the map_tiles_url and the map_api_key provided at the top of the script.
    """

    m = folium.Map(location=[latitude,longitude], zoom_start=12, tiles=None)

    folium.TileLayer(tiles=map_tiles_url, attr='© OpenStreetMap contributors © CARTO', name="CartoDB Voyager").add_to(m)

    return m

#makes a new layer group. layer groups allow the user to turn on and off certain layers.
def create_new_layer_group(layer_group_name: str) -> folium.FeatureGroup:
    """
        Returns a FeatureGroup to be passed into another function.

        Takes in a string for the name of the layer group and creates a FeatureGroup with that name.
        Think of FeatureGroups as layers that you can turn on and off. Use it to separate each type of data we gather and display on the map.
    """
    return folium.FeatureGroup(name=layer_group_name)

#add api geojson to the layer group.
def add_GeoJSON_to_layer_group(layer_group: folium.FeatureGroup, GeoJSON: folium.GeoJson, marker=None, style_function=None, tooltip=None):
    """
        Returns nothing.

        Takes in the layer group
    """

    folium.GeoJson(GeoJSON, marker=marker, style_function=style_function, tooltip=tooltip).add_to(layer_group)

def add_layer_group_to_map(layer_group: folium.FeatureGroup, map_object: folium.Map):
    layer_group.add_to(map_object)

def save_map_to_html(map_object: folium.Map):
    """
        Returns nothing.

        Takes in the Map object and saves it into a usable HTML file.
        Also adds the ability to control the layers.
    """
    folium.LayerControl().add_to(map_object)
    map_object.save("map.html")
    print("Map HTML file created!")

def make_earthquake_map(GeoJSON: folium.GeoJson):
    """
        Returns nothing.

        Takes in the GeoJSON object and adds it to a newly created "Earthquakes" layer. 
        The layer is then added to the map.
    """

    def earthquake_marker_style(feature):
        """
            This function creates the styling for markers. 
            
            It's not meant to actually be called outside of using it in the 'style_function' parameter in folium.GeoJson.
            Make sure not to include parentheses () after the function name when adding it to 'style_function'
        """
        mag = feature["properties"]["mag"]
        radius = 500
        if mag > 0:
            radius_in_km = math.exp((mag / 1.01) - 0.13)
            radius = round(radius_in_km * 1000)

        # color coordinates the magnitude of the earthquakes
        if mag <= 2: fill_color = "green"
        elif mag <= 4.5: fill_color = "orange"
        else: fill_color = "red"
        
        return {"radius": radius, "fillColor": fill_color, "fill": True, "fillOpacity": 0.4, "stroke": False}

    # this part allows me to change from the default pin marker to a circle
    circle_marker = folium.Circle()

    # this shows the magnitude when you mouse over the circles
    earthquake_tooltip = folium.GeoJsonTooltip(
        fields=["mag"],
        aliases=["Magnitude "]
    )

    # create the layer for earthquake info, feed in the data, and change the marker to a circle with a tooltip.
    earthquake_layer = create_new_layer_group("Earthquakes")
    add_GeoJSON_to_layer_group(layer_group=earthquake_layer, GeoJSON=GeoJSON, marker=circle_marker, style_function=earthquake_marker_style, tooltip=earthquake_tooltip)
    add_layer_group_to_map(layer_group=earthquake_layer, map_object=m)

if __name__ == "__main__":
    # dummy info
    # coords for CSUF, plan to have a button that lets you redo a search in the area on the map.
    latitude = 33.881639
    longitude = -117.885245
    max_search_radius_in_km = 100
    
    m = make_map(latitude=latitude, longitude=longitude)

    if not os.path.exists("data_sample.geojson"):
        print("GeoJSON not found! Calling API and writing to file...")
        r = get_earthquake_info(latitude=latitude, longitude=longitude, max_radius=max_search_radius_in_km)
        with open("data_sample.geojson", "w") as f: 
            json.dump(r.json(), f)

        print("GeoJSON file created.")

    make_earthquake_map("data_sample.geojson")

    save_map_to_html(map_object=m)

        