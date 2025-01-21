# _*_ coding: utf-8 _*_
# /usr/bin/env python

"""
Author: Thomas Chen
Email: guyanf@gmail.com
Company: Thomas

date: 2025/1/13 10:52
desc:
"""

import os
import base64
import logging
import folium
import pandas as pd
from flask import Flask, render_template
from dash import Dash, dcc, html
from folium import Map, LayerControl, plugins

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='app.log',
    filemode='w'
)

# Create Flask app
server = Flask(__name__)

# Create Dash app
dash_app = Dash(
    __name__,
    server=server,
    url_base_pathname='/dash/',
    external_stylesheets=['https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css']
)


def get_dash():
    # Define Dash layout
    global dash_app
    dash_app.layout = html.Div(
        [
            html.H1('Earthquake In China', className='text-left my-4', style={'marginLeft': '280px'}),
        ]
    )


def prepare_date(df):
    df = df.query("mag >= 6.5 and year >= 1975")

    logging.info(df)
    df["mag_level"] = pd.cut(
        df['mag'],
        # df.loc[df["mag"]>0, 'mag'],
        bins=7,  # split to 7
        labels=[f'{i}' for i in range(4, 11)],  # set label for range
        include_lowest=True  # include minimum value
    ).astype(int)

    df["deepth_level"] = pd.cut(
        df['focaldepth'],
        # df.loc[df["mag"]>0, 'mag'],
        bins=7,  # split to 7
        labels=[f'{i}' for i in range(4, 11)],  # set label for range
        include_lowest=True  # include minimum value
    )

    df['time'] = pd.date_range(start="2024-01-01", periods=len(df), freq="2D").astype(str)

    df["deepth_level"] = 11 - df["deepth_level"].astype(int)

    # df["sec"] = int(df['sec'])

    df["datetime"] = pd.to_datetime(
        df['year'].astype(str) + '-' + df['mo'].astype(str).str.zfill(2) + '-' + df['dy'].astype(str).str.zfill(
            2) + ' ' + df['hr'].astype(int).astype(str).str.zfill(2) + ':' + df['mn'].astype(int).astype(str).str.zfill(
            2) + ':' + df['sec'].astype(int).astype(str).str.zfill(2))

    df['datetime'] = df['datetime'] + pd.to_timedelta('8H')

    df['deathdescription'] = df['deathdescription'].fillna(0)

    logging.info(df[["datetime", "mag", "location"]])

    return df


def get_deepth_circle(row, color="blue"):
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [row['longitude'], row['latitude']],
        },
        "properties": {
            "time": row["time"],
            "icon": "circle",
            "style": {
                "radius": (float(row['mag_level']) + 0.5) * 3.0,
                "color": color,
                "weight": row['deepth_level'] * 0.5,
                "fillColor": "none",
                # "fillOpacity": 1.0,
                "dashArray": "5, 5"
            }
        }
    }

    return feature


def get_death_circle(row):
    """
    prepare death circle, render by different color
    :param row:
    :return:
    """
    # lst_death_color = ["#fcfafa", "#fcc7c7", "#ff8585", "#fc4444", "#fc0303"]
    lst_death_color = ["#fcfafa", "#ffdede", "#fcb3b3", "#fc9090", "#fa7373"]

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [row['longitude'], row['latitude']],
        },
        "properties": {
            "time": row["time"],
            "icon": "circle",
            "style": {
                "radius": float(row['mag_level']) * 3.0,
                "color": lst_death_color[int(row['deathdescription'])],
                "weight": 2,

                "fillColor": lst_death_color[int(row['deathdescription'])],
                "fillOpacity": 1.0,
            }
        }
    }

    return feature

def get_mag_circle(row):
    """
    prepare mag circle, different size have the different mag
    :param row:
    :return:
    """
    lst_colors = [
        "#000000", "#1C1C1C", "#383838", "#545454", "#707070",
        "#8C8C8C", "#A8A8A8", "#C4C4C4", "#D0D0D0", "#DCDCDC"
    ]

    lst_width = [
        3.7, 3.4, 3.1, 2.8, 2.5, 2.2, 1.9, 1.6, 1.3, 1.0
    ]

    lst_radius = [
        0.2, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5
    ]

    lst_opacity = [
        1.0, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45
    ]

    lst_feature = []

    mag = int(row["mag_level"])

    cur_lst_radius = lst_radius[:mag]
    cur_lst_colors = lst_colors[:mag]
    cur_lst_width = lst_width[:mag]
    cur_lst_opacity = lst_opacity[::-1][:mag]
    logging.info(cur_lst_radius)
    for prop in range(mag):
    #     logging.info(prop)

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row['longitude'], row['latitude']],
            },
            "properties": {
                "time": row["time"],
                "icon": "circle",
                "style": {
                    "radius": cur_lst_radius[prop] * 6.0,
                    "color": cur_lst_colors[prop],
                    "weight": cur_lst_width[prop],
                    "opacity": cur_lst_opacity[prop]
                }
            }
        }
        lst_feature.append(feature)

    return lst_feature


def get_date_popup(row):
    """
    popup
    :param row:
    :return:
    """
    popup_html = '''
        <div style="
            background-color: lightblue; 
            padding: 2px; 
            border-radius: 50%/20%;; 
            border: 2px solid blue;">
            <p style="font-size: 14px; color: black; ">震级：{0}<br>深度：{1}km<br>位置：{2}<br>时刻：{3}</p>
        </div>
    '''

    # logging.info(datetime.strptime( row["time"], "%Y-%m-%d") + timedelta(hours=1))
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            # "coordinates": [104, 45],
            "coordinates": [row['longitude'], row['latitude']+2.0],
        },
        "properties": {
            "time": row["time"],
            # "time": datetime.strptime( row["time"], "%Y-%m-%d") + timedelta(hours=1),
            "icon": "circle",
            "style": {
                "radius": 0.0001,
                "color": "gray",
                "opacity": 0.01,
            },
            "popup": popup_html.format(row["mag"], row["focaldepth"], row["location"], row["datetime"]),
            "autopopup": True,
            "popuptime": 2000,  # microseconds
        }
    }

    return feature


def get_chart():
    df = pd.read_csv('data/quake.csv')
    df = prepare_date(df)

    logging.info(f"\n{df}")

    lst_features = []
    for _, row in df.iterrows():
        feature_death = get_death_circle(row)
        lst_features.append(feature_death)

        lst_feature_mag = get_mag_circle(row)
        lst_features.extend(lst_feature_mag)

        feature_deepth = get_deepth_circle(row)
        lst_features.append(feature_deepth)

        feature_date_popup = get_date_popup(row)
        lst_features.append(feature_date_popup)

    return lst_features


def add_legend(m):

    left_bottom = [16, 72.5]

    h, w = 7, 23.5
    polygon_coords = [
        [left_bottom[0], left_bottom[1]],  # Point 1
        [left_bottom[0], left_bottom[1] + w],  # Point 2
        [left_bottom[0] + h, left_bottom[1] + w],  # Point 3
        [left_bottom[0] + h, left_bottom[1]],  # Point 4
    ]

    # Create the polygon
    folium.Polygon(
        locations=polygon_coords,  # Set the polygon coordinates
        color='navy',  # Border color
        width=0.6,
        dash_array='5, 5',  # Dash pattern for the border
        fill=True,  # Whether to fill the polygon
        fill_color='lightblue',  # Fill color
        fill_opacity=1.0  # Opacity of the fill color
    ).add_to(m)

    # image_path = os.path.abspath('/python-tools/ai_study/earthquake/static/images/legend.png')
    # folium.raster_layers.ImageOverlay(
    #     image_path,
    #     bounds=[[14, 72], [24, 95]],
    #     opacity=1.0,
    #     interactive=False
    # ).add_to(m)

    lst_h = [2.5, 5.8]
    lst_w = [3.4, 11.2, 19]

    lst_label = [
        "震级 大",
        "震级 小",
        "深度 浅",
        "深度 深",
        "伤亡 大",
        "伤亡 小"
    ]

    lst_legend = [
        [[left_bottom[0] + lst_h[0], left_bottom[1] + lst_w[0]], lst_label[0]],
        [[left_bottom[0] + lst_h[1], left_bottom[1] + lst_w[0]], lst_label[1]],
        [[left_bottom[0] + lst_h[0], left_bottom[1] + lst_w[1]], lst_label[2]],
        [[left_bottom[0] + lst_h[1], left_bottom[1] + lst_w[1]], lst_label[3]],
        [[left_bottom[0] + lst_h[0], left_bottom[1] + lst_w[2]], lst_label[4]],
        [[left_bottom[0] + lst_h[1], left_bottom[1] + lst_w[2]], lst_label[5]]
    ]

    img_path = "./static/images/"
    lst_name = ["01.png", "02.png", "03.png", "04.png", "05.png", "06.png"]
    lst_images = []
    for image in lst_name:
        with open(os.path.join(img_path, image), "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode()
        lst_images.append(base64_image)

    font_color = "black"
    font_size = 12

    i = 0
    for (lat, lon), name in lst_legend:
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                icon_size=(46, 30),  # Size of the label box
                icon_anchor=(0, 0),  # Anchor for positioning
                html=f"""
                <div style="font-size: {font_size}px; color: {font_color}; text-align: center; background-color: rgba(255, 255, 255, 1.0); border-radius: 5px;">
                    {name}
                </div>
                """
            ),
        ).add_to(m)

        folium.Marker(
            location=[lat, lon-2.5],
            icon=folium.DivIcon(
                html=f"""
                <div style="text-align: left;">
                    <img src="data:image/png;base64,{lst_images[i]}" style="width:30px; height:30px; opacity:1.0;" />
                </div>
                """
            ),
        ).add_to(m)
        i += 1

    return m

def get_map():
    m = Map(
        location=[29, 106],  # Center the map (latitude, longitude)
        zoom_start=4,  # Initial zoom level
        width='965px',  # Set width to 80% of the parent container
        height='96%',
        control_scale=False,  # Optional: show scale bar
        zoom_control=False,
        name="AMAP",
        tiles=f"https://webst03.is.autonavi.com/appmaptile?style=6&x={{x}}&y={{y}}&z={{z}}",
        # tiles=f"https://webrd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}",
        attr="AMAP"
    )

    folium.TileLayer(
        name='country',
        tiles=f"https://wprd01.is.autonavi.com/appmaptile?x={{x}}&y={{y}}&z={{z}}&lang=zh_cn&size=1&scl=1&style=8&ltype=11",
        attr="AMAP"
    ).add_to(m)

    # # set the iframe width and height
    # m.get_root().width = "100%"
    m.get_root().height = "800px"
    #
    lst_features = get_chart()

    m = add_legend(m)

    # LayerControl().add_to(m)

    logging.info(f"\n{lst_features}")

    plugins.TimestampedGeoJson(
        {"type": "FeatureCollection", "features": lst_features},
        period="PT48H",
        add_last_point=True,
        auto_play=True,
        loop=True,
        max_speed=5,
        loop_button=True,
        date_options="YYYY-MM-DD",
        time_slider_drag_update=True,
        duration="P55D",
        transition_time=1000,
    ).add_to(m)

    m.get_root().html.add_child(folium.Element("""
        <script>
            // Append custom text to the Leaflet copyright bar
            document.addEventListener("DOMContentLoaded", function() {
                let attributionControl = document.querySelector(".leaflet-control-attribution");
                if (attributionControl) {
                    attributionControl.innerHTML += ' | cite: DOI:10.7289/V5TD9V7K';
                }
            });
        </script>
        <style>
            .leaflet-control-attribution {
                position: fixed;
                bottom: 105px;
                left: 630px;
                background: white;
                padding: 1px;
                font-size: 10px;
            }
        </style>

        """))

    return m
    # map_html = m._repr_html_()
    # return render_template_string(map_html)


# Define a Flask route
@server.route('/')
def index():
    get_dash()
    cur_map = get_map()

    # map_html = render_template(
    #     'index.html',
    #     dash_layout=dash_app.index(),
    #     map=cur_map.get_root()._repr_html_()
    # )
    #
    # with open("./temp/temp_view.html", 'w') as f:
    #     f.write(map_html)

    return render_template(
        'index.html',
        dash_layout=dash_app.index(),
        map=cur_map._repr_html_(),
        title="Earthquake Map"
        # map=cur_map.get_root()._repr_html_()
    )


if __name__ == '__main__':
    get_dash()
    server.run(host="0.0.0.0", port=5000, debug=True)
