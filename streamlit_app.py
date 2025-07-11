import streamlit as st
import os
import tempfile
from osgeo import gdal, ogr
import folium
from streamlit_folium import st_folium
import rasterio
import fiona
import shutil

def visualize_vector(filepath):
    with fiona.open(filepath, 'r') as src:
        first = next(iter(src))
        lon, lat = None, None
        # Try to get centroid
        if 'geometry' in first and first['geometry'] and 'coordinates' in first['geometry']:
            coords = first['geometry']['coordinates']
            if isinstance(coords[0], (float, int)):
                lon, lat = coords[0], coords[1]
            elif isinstance(coords[0][0], (float, int)):
                lon, lat = coords[0][0], coords[0][1]
            else:
                lon, lat = coords[0][0][0], coords[0][0][1]
        # Center map
        if lon is not None and lat is not None:
            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.GeoJson(filepath, name="geojson").add_to(m)
            st_folium(m, width=700)
        else:
            st.warning("Could not get coordinates to center the map.")

def visualize_raster(filepath):
    with rasterio.open(filepath) as src:
        bounds = src.bounds
        m = folium.Map(location=[(bounds.top + bounds.bottom) / 2, (bounds.left + bounds.right) / 2], zoom_start=12)
        folium.raster_layers.ImageOverlay(
            image=src.read(1),  # Only first band
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            opacity=0.6
        ).add_to(m)
        st_folium(m, width=700)

def convert_vector(infile, outformat):
    formats = {
        "GeoJSON": ".geojson",
        "ESRI Shapefile": ".shp",
        "GPKG": ".gpkg"
    }
    ext = formats[outformat]
    tmp_dir = tempfile.mkdtemp()
    outfile = os.path.join(tmp_dir, "converted" + ext)
    driver = ogr.GetDriverByName(outformat)
    dataSource = driver.CopyDataSource(ogr.Open(infile), outfile)
    dataSource = None
    return outfile

def convert_raster(infile, outformat):
    formats = {
        "GTiff": ".tif",
        "JPEG": ".jpg",
        "PNG": ".png"
    }
    ext = formats[outformat]
    tmp_dir = tempfile.mkdtemp()
    outfile = os.path.join(tmp_dir, "converted" + ext)
    gdal.Translate(outfile, infile, format=outformat)
    return outfile

st.title("Vector and Raster File Visualizer & Converter")

uploaded = st.file_uploader("Upload a vector (.shp, .geojson, .gpkg) or raster (.tif, .jpg, .png) file", type=['shp', 'geojson', 'gpkg', 'tif', 'tiff', 'jpg', 'jpeg', 'png'])

if uploaded:
    # Save to temp file
    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmpfile:
        tmpfile.write(uploaded.getbuffer())
        input_path = tmpfile.name

    st.success(f"File uploaded: {uploaded.name}")

    # Determine type
    vector_types = [".shp", ".geojson", ".gpkg"]
    raster_types = [".tif", ".tiff", ".jpg", ".jpeg", ".png"]
    if suffix.lower() in vector_types:
        st.subheader("Vector Data Visualization")
        visualize_vector(input_path)
        st.subheader("Convert Vector Format")
        vector_outformat = st.selectbox("Convert to:", ["GeoJSON", "ESRI Shapefile", "GPKG"])
        if st.button("Convert Vector"):
            out_path = convert_vector(input_path, vector_outformat)
            with open(out_path, "rb") as f:
                st.download_button("Download Converted File", f, file_name=f"converted{os.path.splitext(out_path)[1]}")
    elif suffix.lower() in raster_types:
        st.subheader("Raster Data Visualization")
        visualize_raster(input_path)
        st.subheader("Convert Raster Format")
        raster_outformat = st.selectbox("Convert to:", ["GTiff", "JPEG", "PNG"])
        if st.button("Convert Raster"):
            out_path = convert_raster(input_path, raster_outformat)
            with open(out_path, "rb") as f:
                st.download_button("Download Converted File", f, file_name=f"converted{os.path.splitext(out_path)[1]}")
    else:
        st.error("Unsupported file type.")
