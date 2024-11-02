# main.py - Main script to run end-to-end pipeline

from src.data_processing.downloader import download_topography_data
from src.data_processing.gridder import process_topography_to_grid
from src.data_processing.converter import convert_grid_to_polygons
from src.model_generation.model_creator import create_stl_model
from src.model_generation.scale_manager import scale_model
from src.utils.map_selector import select_map_area

def main():
    # Step 1: Get user-selected bounding box
    bbox = select_map_area()

    # Step 2: Download data for selected area
    data_path = download_topography_data(bbox)

    # Step 3: Process data into grid or contour format
    grid_data = process_topography_to_grid(data_path)

    # Step 4: Convert grid data to 3D model polygons
    mesh_data = convert_grid_to_polygons(grid_data)

    # Step 5: Scale the model to fit specified dimensions and vertical exaggeration
    scaled_mesh = scale_model(mesh_data, width=5, height=7, vertical_exaggeration=2)

    # Step 6: Export the scaled mesh to an STL file
    create_stl_model(scaled_mesh, output_path="output/model.stl")

if __name__ == "__main__":
    main()
