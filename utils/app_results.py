# %% import necessary libraries
import streamlit as st
import streamlit.components.v1 as components

from utils.visualisation import visualise_structure
from utils.app_setup_structure import calc_energy

def display_results(structure, atoms):
    """Display analysis results"""
    # Display relaxation results if available
    if structure is not None:
        calc_energy(structure, atoms)
        # st.info(f"Energy Change: {relaxed_energy - initial_energy:.4f} GPa")
        
        # Display relaxed parameters
        cell_params = structure.cell.cellpar()
        
        with st.container(border=True):
            st.subheader(f"Lattice parameters:")
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
    st.write(f"Atom positions: {structure.positions}")
    try:
        html_str = visualise_structure(structure, repeat_unit=repeat_unit)
        components.html(html_str, height=500)
    # st.py3Dmol(visualise_structure(structure))
    except Exception as e:
        st.error(f"Unable to render structure: {e}")
        st.stop()