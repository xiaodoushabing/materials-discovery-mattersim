import streamlit as st
from utils.app_setup_structure import *
from utils.app_relax import *
from utils.app_results import *
from utils.app_sidebar import *
from utils.app_md import *
                   
# %%
def main():
    """Main application function"""
    st.title("Structure Analysis with MatterSim")
    
    # Get model configuration
    model, device = setup_configuration_sidebar()
    st.sidebar.divider()
    optimizer, steps, filter, constrain_symmetry, fmax, pressure, unit = setup_relaxation_sidebar()

    builder = get_builder()
    
    # Get structure inputs
    atoms = get_atomic_input()
    lattice_params = get_lattice_parameters(builder)
    if builder == "Atoms Builder":
        pbc = st.checkbox("Periodic boundary condition",
                          value = True)
    basis_positions = get_basis_positions(atoms, builder)
    if builder == "Crystal Builder":
        spacegroup = get_spacegroup()

    rattle, stdev = get_rattle()

    st.subheader("Lattice Visualisation")
    repeat_unit = st.number_input("Number of cells to display per axis", min_value=1, max_value=10, value=3)

    # Build structure
    st.divider()
    if builder == "Crystal Builder":
        structure = create_crystal(atoms, basis_positions, lattice_params, spacegroup, rattle, stdev)
    else:
        structure = create_atom(atoms, basis_positions, lattice_params, rattle, pbc, stdev)

    setup_calculator(structure, model, device)

    st.header("Initial Structure")
    display_results(structure, atoms)
    render_structure(structure, repeat_unit=repeat_unit)
    
    # Relax structure when requested
    st.divider()
    if st.button("Relax Structure"):
        if unit == "eV/A^3" and pressure >= 1:
            st.warning(f"""
                       Check input pressure: {pressure} {unit}. \n
                       1 eV/A^3 is already 160 GPa.""",
                        icon = "⚠️")
    
        perform_relaxation(basis_positions, structure, optimizer, steps, filter, constrain_symmetry, fmax, pressure)

        # Display results
        st.header("Structure Relaxation Results")
        display_results(structure, atoms)
        render_structure(structure, repeat_unit=repeat_unit)

    # MD simulation
    st.divider()
    st.subheader("Molecular Dynamics (MD) simulation")
    st.caption("""Note: The simulation is performed on the 'latest' structure.
                If relaxation has been done, the MD simulation will run on the relaxed structure; otherwise, it will run on the initial structure.""")

    ensemble, temperature, timestep, taut, n_steps, temp_unit = get_md()
    if st.button("Start MD simulation"):
        if (temp_unit == "K" and temperature <= 0) | (temp_unit == "deg" and temperature <= -273.15):
            st.warning("Temperature cannot be exactly at or below absolute zero.", icon = "⚠️")
            st.stop()
        with st.spinner("Running MD simulation..."):
            md = run_md(structure, ensemble, temperature, timestep, taut, n_steps, temp_unit)
            # Display results
            st.header("MD Simulation Results")
            display_results(md.atoms, atoms)
            render_structure(md.atoms, repeat_unit=repeat_unit)

if __name__ == "__main__":
    main()