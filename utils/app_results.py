"""Provides functions for displaying results and rendering interactive 3D visualizations."""

# %% import necessary libraries
import streamlit as st
import streamlit.components.v1 as components
import time

from utils.visualisation import visualise_structure
from utils.app_setup_structure import calc_energy

def display_results(structure, atoms):
    """Displays the analysis results, including calculated energy and lattice parameters.

    Args:
        structure (ase.Atoms or None): The atomic structure object.
            Can be None if the structure creation failed.
        atoms (list): A list of atomic symbols (strings).

    Returns:
        None
    """
    # Display relaxation results if available
    if structure is not None:
        start = time.time()
        calc_energy(structure, atoms)
        # st.info(f"Energy Change: {relaxed_energy - initial_energy:.4f} GPa")
        st.write(f"Time taken for calculation: {time.time()-start:.5f} s")
        # Display relaxed parameters
        cell_params = structure.cell.cellpar()

        with st.container(border=True):
            st.subheader("Lattice parameters:")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Lattice Constants (Å):")
                st.write(f"a = {cell_params[0]:.4f}")
                st.write(f"b = {cell_params[1]:.4f}")
                st.write(f"c = {cell_params[2]:.4f}")
            with col2:
                st.write("Angles (degrees):")
                st.write(f"α = {cell_params[3]:.4f}")
                st.write(f"β = {cell_params[4]:.4f}")
                st.write(f"γ = {cell_params[5]:.4f}")

# %%
def render_structure(structure, repeat_unit):
    """Renders an interactive 3D visualization of the atomic structure.

    Uses the `visualise_structure` function to generate the HTML for the visualization and embeds
    it in the Streamlit app using `components.html`.

    Args:
        structure (ase.Atoms): The atomic structure object.
        repeat_unit (int): The number of times to repeat the unit cell in each direction.

    Raises:
        Exception: If there's an error during visualization rendering. The Streamlit app execution is stopped.

    """
    st.write(f"Atom positions: {structure.positions}")
    try:
        html_str = visualise_structure(structure, repeat_unit=repeat_unit)
        components.html(html_str, height=500)
    # st.py3Dmol(visualise_structure(structure))
    except Exception as e:
        st.error(f"Unable to render structure: {e}")
        st.stop()
