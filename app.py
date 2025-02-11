"""Streamlit app for Structure Analysis with MatterSim.

This app provides a user interface for setting up, visualizing, relaxing, and performing
molecular dynamics simulations on atomic structures using MatterSim. It integrates with
Streamlit for interactive input and display.
"""

import streamlit as st
import time

import utils.app_setup_structure as setup
from utils.app_md import get_md, run_md, conv_tri
from utils.app_relax import perform_relaxation, setup_relaxation_sidebar
from utils.app_results import display_results, render_structure
from utils.app_sidebar import setup_configuration_sidebar


# %%
def main():
    """Main application function for the Structure Analysis app.

    This function orchestrates the entire Streamlit application, including:

    - Setting up the model and device configuration via `setup_configuration_sidebar`.
    - Configuring relaxation parameters via `setup_relaxation_sidebar`.
    - Handling structure input and creation using functions from `utils.app_setup_structure`.
    - Visualizing the initial structure.
    - Performing structure relaxation (if requested) and displaying the results.
    - Running molecular dynamics simulations (if requested) and displaying the results.
    """
    st.title("Structure Analysis with MatterSim")


    # Get model configuration
    model, device = setup_configuration_sidebar()
    st.sidebar.divider()
    (optimizer, steps, filtering, constrain_symmetry, fmax, pressure, unit) = (
        setup_relaxation_sidebar()
    )

    builder = setup.get_builder()

    # Get structure inputs
    atoms = setup.get_atomic_input()
    lattice_params = setup.get_lattice_parameters(builder)
    if builder == "Atoms Builder":
        pbc = st.checkbox("Periodic boundary condition", value=True)
    basis_positions = setup.get_basis_positions(atoms, builder)
    if builder == "Crystal Builder":
        spacegroup = setup.get_spacegroup()

    rattle, stdev = setup.get_rattle()

    st.subheader("Lattice Visualisation")
    repeat_unit = st.number_input(
        "Number of cells to display per axis", min_value=1, max_value=10, value=3
    )

    # Build structure
    st.divider()

    if "structure" not in st.session_state or st.session_state.structure is None:
        st.session_state.structure = None
    if builder == "Crystal Builder":
        st.session_state.structure = setup.create_crystal(
            atoms, basis_positions, lattice_params, spacegroup, rattle, stdev
        )
    else:
        st.session_state.structure = setup.create_atom(
            atoms, basis_positions, lattice_params, rattle, pbc, stdev
        )
    if st.session_state.structure is not None:
        setup.setup_calculator(st.session_state.structure, model, device)
        st.header("Initial Structure")
        display_results(st.session_state.structure, atoms)
        render_structure(st.session_state.structure, repeat_unit=repeat_unit)
            
    # Relax structure when requested
    st.divider()
    if st.button("Relax Structure"):
        if unit == "eV/A^3" and pressure >= 1:
            st.warning(
                f"""
                       Check input pressure: {pressure} {unit}. \n
                       1 eV/A^3 is already 160 GPa.""",
                icon="⚠️",
            )
        start = time.time()
        perform_relaxation(
            basis_positions,
            st.session_state.structure,
            optimizer,
            steps,
            filtering,
            constrain_symmetry,
            fmax,
            pressure,
        )
        st.write(f"time taken for relaxation: {time.time()-start} s")
    # Check if a relaxed structure exists in session state
    if "relaxed_structure" in st.session_state:
        st.header("Structure Relaxation Results")
        display_results(st.session_state.relaxed_structure, atoms)
        render_structure(st.session_state.relaxed_structure, repeat_unit=repeat_unit)

    # MD simulation
    st.divider()
    st.subheader("Molecular Dynamics (MD) simulation")
    st.caption("""Note: The simulation is performed on the 'latest' structure.
                If relaxation has been done, the MD simulation will run on the relaxed structure;\
               otherwise, it will run on the initial structure.""")

    ensemble, temperature, timestep, taut, n_steps, temp_unit = get_md()
    absolute_zero = {"K": 0, "deg": -273.15}
    if st.button("Start MD simulation"):
        if temp_unit == "K" and temperature <= absolute_zero[temp_unit]:
            st.warning(
                "Temperature cannot be exactly at or below absolute zero.", icon="⚠️"
            )
            st.stop()

        with st.spinner("Running MD simulation..."):
            start = time.time()
            conv_tri(st.session_state.relaxed_structure)
            md = run_md(
                st.session_state.relaxed_structure, ensemble, temperature, timestep, taut, n_steps, temp_unit
            )
            st.write(f"Time taken for MD simulation: {time.time()-start:.5f} s")
            # Display results
            st.header("MD Simulation Results")
            display_results(md.atoms, atoms)
            render_structure(md.atoms, repeat_unit=repeat_unit)

if __name__ == "__main__":
    main()
