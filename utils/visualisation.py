# %% import necessary libraries
import seaborn as sns
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import os
import py3Dmol
from ase.io import write
import sys
import streamlit as st

# %% Define function to visualise data distribution from Potential inference
def plot_potential(predictions, title = None):
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
def plot_relaxation(relaxation_trajectories, split = False):

     # # Extract the relaxed structures and corresponding energies
     relaxed_energies = [traj[-1].info['total_energy'] for traj in relaxation_trajectories.values()]
     # relaxed_structures = [traj[-1] for traj in relaxation_trajectories.values()]
     # relaxed_energies = [structure.info['total_energy'] for structure in relaxed_structures]

     # # Do the same with the initial structures and energies
     initial_energies = [traj[0].info['total_energy'] for traj in relaxation_trajectories.values()]     
     # initial_structures = [traj[0] for traj in relaxation_trajectories.values()]
     # initial_energies = [structure.info['total_energy'] for structure in initial_structures]

     # verify by inspection that total energy has decreased in all instances
     # for initial_energy, relaxed_energy in zip(initial_energies, relaxed_energies):
     #     print(f"Initial energy: {initial_energy} eV, relaxed energy: {relaxed_energy} eV")
     if split:
          fig, axs = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
          sns.histplot(initial_energies, kde=True, ax=axs[0], color="red", edgecolor = None, label = "Initial Energy", bins = 50)
          axs[0].set_title("Initial Energies")
          axs[0].set_xlabel("Energy (eV)")
          axs[0].legend()
          
          sns.histplot(relaxed_energies, kde = True, ax = axs[1], color = "darkgreen", edgecolor = None, label = 'Relaxed Energy', bins =50)
          axs[1].set_title("Relaxed Energies")
          axs[1].set_xlabel("Energy (eV)")
          axs[1].legend()
          
          fig.suptitle("Comparison of Energies Before and After Relaxation", fontsize=16)
          plt.tight_layout()
          plt.show()
     else:
          fig, ax = plt.subplots(figsize = (10,5))
          sns.histplot(initial_energies, kde=True, ax=ax, color="red", edgecolor = None, label = "Initial Energy", bins = 50)
          sns.histplot(relaxed_energies, kde = True, ax = ax, color = "darkgreen", edgecolor = 'darkgreen', fill=True, label = 'Relaxed Energy', bins =50)
          ax.set_title("Comparison of energies before and after relaxation")
          ax.set_xlabel("Energy (eV)")
          ax.legend()
          plt.tight_layout()
          plt.show()

# %% visualise structure
def visualise_structure(structure, preview = True, repeat_unit =3, store_xyz=False, width=800, height=600):

    ## Extract the unit cell vectors e.g., Cell([3.85, 3.85, 3.72])
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
    xyz = open("./supercell.xyz", "r").read()

    ## Initialize Py3Dmol viewer
    viewer = py3Dmol.view(width=width, height=height)

    # Add the atoms from the XYZ file
    viewer.addModel(xyz, "xyz")

    if not store_xyz:
        os.remove("./supercell.xyz")

    # Get the atomic masses for scaling
    atomic_masses = structure.get_masses()
    max_mass = max(atomic_masses)

    # Apply individual sphere size scaling for each atom based on atomic mass
    for atom_index, mass in enumerate(atomic_masses):
        sphere_scale = (mass / max_mass) * 0.5
        viewer.setStyle({"model": atom_index, "sphere": {"scale": sphere_scale}})

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
        viewer.addLabel(axis["label"], {"position": {"x": text_pos[0], "y": text_pos[1], "z": text_pos[2]},
                                        "fontSize": 17, "backgroundColor": "white",
                                        "fontColor": axis["color"]})
        
    # Zoom to the structure and display
    viewer.zoomTo()
    viewer.show()

    if "streamlit" in sys.modules:
        return viewer._make_html()
