import svgwrite
import os
from drawscape_factorio.import_json import parseJSON
from drawscape_factorio.themes.circles_theme import CirclesTheme
from drawscape_factorio.themes.default_theme import DefaultTheme
from drawscape_factorio.optimize_svg import optimize_svg


# The create function is responsible for generating an SVG drawing of a Factorio blueprint
# based on the provided JSON file. It handles the following tasks:
#   1. Parsing the JSON file to extract entity data (Coming from Factorio MOD export)
#   2. Determining the appropriate theme (default or circles)
#   3. Calculating the bounds and scale of the drawing
#   4. Creating an SVG drawing object with the correct dimensions and viewBox
#   5. Drawing each entity using the selected theme
#   6. Optionally optimizing the SVG output
#   7. Saving the final SVG file
#
# Parameters:
#   json_file_path (str): Path to the JSON file containing the Factorio blueprint data
#   optimize (bool): Whether to optimize the SVG output (default: False)
#   template (str): The theme to use for drawing entities (default: 'default')
#   output_file_name (str): Name of the output SVG file (default: 'output.svg')
#
# Returns:
#   str: Path to the created (and optionally optimized) SVG file


def create(json_file_path, optimize=False, template='default', output_file_name='output.svg'):
    
    # Initialize the theme based on the template parameter
    if template == 'circles':
        theme = CirclesTheme()
    else:  # default theme
        theme = DefaultTheme(resolution='LOW')

    # Use parseJSON function to load and process the JSON file
    data = parseJSON(json_file_path)
    
    # Calculate canvas size and viewBox
    svg_width_mm, svg_height_mm, viewbox_x, viewbox_y, viewbox_width, viewbox_height = calculate_canvas_and_viewbox(data, 'landscape')
    
    # Create the SVG drawing object with forced A4 size and centered content
    dwg = svgwrite.Drawing(
        filename=output_file_name,
        profile='full',
        size=(f'{svg_width_mm}mm', f'{svg_height_mm}mm'),
        viewBox=f"{viewbox_x} {viewbox_y} {viewbox_width} {viewbox_height}"
    )

    # Add the grid to the drawing
    create_grid(dwg, viewbox_x, viewbox_y, viewbox_width, viewbox_height)

    # Define entity types and that will be rendered
    entity_types = {
        'belts': theme.render_belt,
        'walls': theme.render_wall,
        'splitters': theme.render_splitter,
        'asset': theme.render_asset,
        'spaceship': theme.render_spaceship,
        'rails': theme.render_rail,
        # 'electrical': theme.render_electrical

    }

    # Create and populate groups for each entity type
    for entity_type, render_method in entity_types.items():
        group = dwg.g(id=entity_type)
        entities = data.get(entity_type, [])
        for entity in entities:
            group.add(render_method(dwg, entity))
        if entities:  # Check if there are any entities for this type
            dwg.add(group)

    # Save the SVG file
    dwg.save()

    # Print information about the SVG drawing
    print(f"Created SVG drawing:")
    print(f"  Output file: {output_file_name}")
    print(f"  Size: {svg_width_mm}mm x {svg_height_mm}mm (A4)")
    print(f"  ViewBox: {viewbox_x} {viewbox_y} {viewbox_width} {viewbox_height}")
    print(f"  Template: {template}")
    print(f"  Theme resolution: {theme.resolution}")

    if optimize:
        # Optimize the SVG file
        optimized_svg = optimize_svg(output_file_name)
        
        if optimized_svg:
            # Remove the original unoptimized SVG file
            os.remove(output_file_name)
            print(f"Original SVG file {output_file_name} has been deleted.")
        else:
            print("SVG optimization failed. Original file retained.")
    else:
        print(f"SVG file saved as {output_file_name}")


def calculate_canvas_and_viewbox(data, orientation='portrait'):
    
    # Define A4 paper size in mm with 10mm padding
    if orientation == 'landscape':
        svg_width_mm = 297
        svg_height_mm = 210
    else:  # default to portrait
        svg_width_mm = 210
        svg_height_mm = 297
    
    padding_mm = 10
    content_width_mm = svg_width_mm - 2 * padding_mm
    content_height_mm = svg_height_mm - 2 * padding_mm
    
    # Calculate the bounds of all entities in the data
    bounds = get_entity_bounds(data)
    
    # Calculate the dimensions and scale
    width = bounds['max_x'] - bounds['min_x']
    height = bounds['max_y'] - bounds['min_y']
    scale = min(content_width_mm / width, content_height_mm / height)
    
    # Calculate the scaled dimensions
    scaled_width = width * scale
    scaled_height = height * scale
    
    # Calculate offsets to center the drawing horizontally and vertically with padding
    x_offset = (svg_width_mm - scaled_width) / 2
    y_offset = (svg_height_mm - scaled_height) / 2

    # Calculate the viewBox parameters to center the content both horizontally and vertically
    viewbox_width = svg_width_mm / scale
    viewbox_height = svg_height_mm / scale
    viewbox_x = bounds['min_x'] - (x_offset - padding_mm) / scale
    viewbox_y = bounds['min_y'] - (y_offset - padding_mm) / scale
    
    return svg_width_mm, svg_height_mm, viewbox_x, viewbox_y, viewbox_width, viewbox_height


# Function to calculate the bounds of all entities in the data
def get_entity_bounds(data):
    # Flatten all entities into a single list
    all_entities = [entity for category in data.values() for entity in category]
    
    # If there are no entities, return None
    if not all_entities:
        return None
    
    # Calculate the minimum and maximum x and y coordinates
    min_x = min(entity['x'] for entity in all_entities)
    max_x = max(entity['x'] for entity in all_entities)
    min_y = min(entity['y'] for entity in all_entities)
    max_y = max(entity['y'] for entity in all_entities)
    
    # Return a dictionary with the calculated bounds
    return {
        'min_x': min_x,
        'max_x': max_x,
        'min_y': min_y,
        'max_y': max_y
    }

def create_grid(dwg, viewbox_x, viewbox_y, viewbox_width, viewbox_height):
    # Create a light gray grid for the whole drawing
    # really just for debugging theme layouts.

    grid_color = svgwrite.rgb(200, 200, 200)  # Light gray color
    grid_stroke_width = 0.05
        
    # Create a group for the grid
    grid_group = dwg.g(id="grid")
    
    # Vertical lines
    for x in range(int(viewbox_x), int(viewbox_x + viewbox_width) + 1):
        grid_group.add(dwg.line(
            start=(x, viewbox_y),
            end=(x, viewbox_y + viewbox_height),
            stroke=grid_color,
            stroke_width=grid_stroke_width
        ))
    
    # Horizontal lines
    for y in range(int(viewbox_y), int(viewbox_y + viewbox_height) + 1):
        grid_group.add(dwg.line(
            start=(viewbox_x, y),
            end=(viewbox_x + viewbox_width, y),
            stroke=grid_color,
            stroke_width=grid_stroke_width
        ))
    
    # Add the grid group to the drawing
    dwg.add(grid_group)