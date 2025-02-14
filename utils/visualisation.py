"""
This module provides functions for visualizing atomic structures and plotting energy distributions.

It includes functions for:

- Rendering interactive 3D visualizations of atomic structures using py3Dmol.
- Plotting the distribution of energies before and after structure relaxation.
- Plotting the distribution of total energy, forces, and stresses from MD predictions.
"""

# %% import necessary libraries
import sys
import os
import seaborn as sns
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import py3Dmol
from ase.io import write
from ase import io
import numpy as np

# %% Define function to visualise data distribution from Potential inference
def plot_potential(predictions, title = None):
    """Plots the distribution of total energy, forces, and stresses from MD predictions.

    Args:
        predictions (tuple): A tuple containing three lists:
            - predictions[0]: A list of total energies.
            - predictions[1]: A list of forces (each element is a list of 3 force components).
            - predictions[2]: A list of stresses (each element is a list of 3 stress components).
        title (str, optional): The title for the entire plot. Defaults to None.
    """

    fig = plt.figure(figsize=(15, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig, height_ratios=[1, 1, 1], hspace=0.4, wspace=0.3)

    # Plot energy
    ax1 = fig.add_subplot(gs[0, :])
    sns.histplot(predictions[0], kde=True, ax=ax1, color="blue")
    ax1.set_title("Total energy")

    rows = [1, 1, 1, 2, 2, 2]
    cols = [0, 1, 2, 0, 1, 2]

    for r, c in zip(rows, cols):
        ax = fig.add_subplot(gs[r, c])
        if r == 1:   #plot forces
            if c == 0:
                # forces[0] for atom 1
                sns.histplot([forces[0][0] for forces in predictions[1]],
                            ax=ax,
                            kde=True,
                            color="blue")
                ax.set_xlabel("(x)")
            if c == 1:
                sns.histplot([forces[0][1] for forces in predictions[1]],
                            ax=ax,
                            kde=True,
                            color="green")
                ax.set_xlabel("(y)")
            if c == 2:
                sns.histplot([forces[0][2] for forces in predictions[1]],
                            ax=ax,
                            kde=True,
                            color="red")
                ax.set_xlabel("(z)")
            ax.set_title("Forces for Atom 1 (eV/A)")
        else:
            if c == 0:
                sns.histplot([stresses[0][0] for stresses in predictions[2]],
                            ax=ax,
                            kde=True,
                            color='blue')
                ax.set_xlabel("(x-x)")
                for axs in ax.get_xticklabels():
                    axs.set_rotation(45)
            if c == 1:
                sns.histplot([stresses[0][1] for stresses in predictions[2]],
                            ax=ax,
                            kde=True,
                            color='green')
                ax.set_xlabel("(x-y)")
            if c == 2:
                sns.histplot([stresses[0][2] for stresses in predictions[2]],
                            ax=ax,
                            kde=True,
                            color='red')
                ax.set_xlabel("(x-z)")
            ax.set_title("Stress (GPa)")

    if title:
        fig.suptitle(title, fontsize=16)
    plt.show()

## %% Define function to visualise relaxation
def visualise_structure(structure, input_file=None, preview=True, repeat_unit=3, store_xyz=True, width=800, height=600):
    """Renders an interactive 3D visualization of an atomic structure using py3Dmol.

    Args:
        structure (ase.Atoms): The atomic structure to visualize. Must be an ASE Atoms object.
        preview (bool, optional): If True, prints the atomic positions to the console.
            Defaults to True.
        repeat_unit (int, optional): The number of times to repeat the unit cell in each direction 
            to create a supercell. Defaults to 3.
        store_xyz (bool, optional): If True, keeps the temporary XYZ file.
                                    If False (default), deletes it.
        width (int, optional): The width of the viewer in pixels. Defaults to 800.
        height (int, optional): The height of the viewer in pixels. Defaults to 600.

    Returns:
        str or None: If running in Streamlit environment, returns HTML representation of the viewer.
                     Otherwise, returns None.

    Raises:
        TypeError: If `structure` is not an ase.Atoms object.
        ValueError: If `repeat_unit` is not a positive integer.

    """
    if structure is None and input_file:
        structure = io.read(input_file)
    ## Extract unit cell vectors e.g., Cell([3.85, 3.85, 3.72])
    unit_cell = structure.get_cell()

    if preview:
        print(f"Structure positions: {structure.positions}")

    # Define the corners of a single unit cell
    corners = [
        [0, 0, 0],  # Origin
        unit_cell[0],    # a [3.85, 0.  , 0.  ]
        unit_cell[1],    # b
        unit_cell[2],    # c
        unit_cell[0] + unit_cell[1],  # a + b
        unit_cell[0] + unit_cell[2],  # a + c
        unit_cell[1] + unit_cell[2],  # b + c
        unit_cell[0] + unit_cell[1] + unit_cell[2]  # a + b + c
    ]

    # Define the edges of the bounding box as pairs of corners
    edges = [
        (0, 1), (0, 2), (0, 3),  # Edges from the origin
        (1, 4), (1, 5),          # Edges from a
        (2, 4), (2, 6),          # Edges from b
        (3, 5), (3, 6),          # Edges from c
        (4, 7), (5, 7), (6, 7)   # Edges from a+b, a+c, b+c
    ]

    ## Create a supercell (repeat the unit cell along each axis)
    supercell = structure.repeat((repeat_unit, repeat_unit, repeat_unit))

    write("./supercell.xyz", supercell)

    # Read the XYZ file for atom positions
    with open("./supercell.xyz", "r") as f:
        xyz = f.read()

    ## Initialize Py3Dmol viewer
    viewer = py3Dmol.view(width=width, height=height)

    # Add the atoms from the XYZ file
    viewer.addModel(xyz, "xyz")

    if not store_xyz:
        os.remove("./supercell.xyz")

    # Get the atomic masses for scaling
    atomic_masses = supercell.get_masses()
    max_mass = max(atomic_masses)

    # Extract unique elements and assign colors
    unique_elements = sorted(set(supercell.get_chemical_symbols()))
    cmap = plt.cm.get_cmap("tab10", len(unique_elements))
    element_colors = {
        element: "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))  # Convert RGB to HEX
        for element, (r, g, b, _) in zip(unique_elements, cmap(np.linspace(0, 1, len(unique_elements))))
    }

    # Apply Colors to Each Atom and size scaling based on atomic mass
    for atom_index, atom in enumerate(supercell):
        max_scale = 0.5
        min_scale = 0.2
        sphere_scale = (atomic_masses[atom_index] / max_mass)**(1/3) * max_scale
        sphere_scale = max(sphere_scale, min_scale)
        color = element_colors[atom.symbol]  # Ensure consistent coloring by element symbol
        viewer.setStyle({"serial": atom_index}, {"sphere": {"scale": sphere_scale,
                                                            "color": color,
                                                              }})

    for edge in edges:
        start = corners[edge[0]]
        end = corners[edge[1]]
        viewer.addLine({
            "start": {"x": start[0], "y": start[1], "z": start[2]},
            "end": {"x": end[0], "y": end[1], "z": end[2]},
            "color": "black"
        })

    # Add bounding boxes for the supercell by translating the unit cell edges
    for nx in range(repeat_unit):  # Adjust repetitions as per the supercell size
        for ny in range(repeat_unit):
            for nz in range(repeat_unit):
                translation = nx * unit_cell[0] + ny * unit_cell[1] + nz * unit_cell[2]
                for edge in edges:
                    start = corners[edge[0]] + translation
                    end = corners[edge[1]] + translation
                    viewer.addLine({
                        "start": {"x": start[0], "y": start[1], "z": start[2]},
                        "end": {"x": end[0], "y": end[1], "z": end[2]},
                        "color": 'grey'
                    })

    # Coordinate Axes
    origin=[-7,0,0]
    axes = [
        {"start": origin, "end": unit_cell[0]+origin, "color": "red", "label": "a"},
        {"start": origin, "end": unit_cell[1]+origin, "color": "green", "label": "b"},
        {"start": origin, "end": unit_cell[2]+origin, "color": "blue", "label": "c"}
    ]

    for axis in axes:
        # Arrowhead slightly outside the unit cell
        arrow_start = axis["start"]
        arrow_end = axis["end"]
        viewer.addArrow({"start": {"x": arrow_start[0], "y": arrow_start[1], "z": arrow_start[2]},
                         "end": {"x": arrow_end[0], "y": arrow_end[1], "z": arrow_end[2]},
                         "color": axis["color"], "radius": 0.1})

        # Move labels even further outside
        text_pos = axis["end"] * 1.01  # Move text beyond arrow tip
        viewer.addLabel(axis["label"],
                        {"position":
                            {"x": text_pos[0], "y": text_pos[1], "z": text_pos[2]},
                        "fontSize": 17,
                        "backgroundColor": "white",
                        "fontColor": axis["color"]
                        })

    # Define legend starting position and offsets
    legend_start = np.array([-15, -5, 0])  # Start position for the legend
    legend_offset = np.array([0, 5, 0])   # Offset for spacing out labels

    # Dynamically scale font size based on the number of elements
    font_size = max(12, 18 - len(unique_elements))  

    for i, (element, color) in enumerate(element_colors.items()):
        legend_pos = (legend_start + i * legend_offset).tolist()

        # Determine sphere size based on atomic mass
        sphere_scale = (supercell[supercell.get_chemical_symbols().index(element)].mass / max_mass) * 0.5

        # Add sphere representing the element
        viewer.addSphere({
            "center": {"x": legend_pos[0] - 1, "y": legend_pos[1], "z": legend_pos[2]},  # Offset to the left of the label
            "radius": 1,
            "color": color
        })

        # Add legend label
        viewer.addLabel(
            element,
            {
                "position": {"x": legend_pos[0], "y": legend_pos[1], "z": legend_pos[2]},
                "fontSize": font_size,
                "backgroundColor": "white",
                "fontColor": color
            }
        )


    # Zoom to the structure and display
    viewer.zoomTo()
    viewer.show()

    if "streamlit" in sys.modules:
        return viewer._make_html()
    return None
