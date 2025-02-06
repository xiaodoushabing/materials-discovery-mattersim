"""Provides functions for setting up and running molecular dynamics simulations using Mattersim."""

import streamlit as st
from mattersim.applications.moldyn import MolecularDynamics

# %%
def get_md():
    """Gets molecular dynamics simulation parameters from the user using Streamlit widgets.

    This function initializes and updates the simulation parameters stored in `st.session_state`.
    It uses Streamlit widgets to allow the user to set the ensemble, temperature, time step,
    thermostat timescale (taut), number of steps, and temperature unit.

    Returns:
        tuple: A tuple containing the following simulation parameters:
            - ensemble (str): The simulation ensemble.
            - temperature (float): The simulation temperature.
            - timestep (float): The simulation time step (fs).
            - taut (float): The timescale of the thermostat (fs).
            - n_steps (int): The number of simulation steps.
            - temp_unit (str): The temperature unit ("K" or "deg").
    """
    # Initialize session state variables if not present
    if "ensemble" not in st.session_state:
        st.session_state.ensemble = "NVT_NOSE_HOOVER"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 300
    if "timestep" not in st.session_state:
        st.session_state.timestep = 1.0
    if "taut" not in st.session_state:
        st.session_state.taut = None
    if "n_steps" not in st.session_state:
        st.session_state.n_steps = 1000
    if "temp_unit" not in st.session_state:
        st.session_state.temp_unit = "K"

    # Assign updated values and store them in session state
    st.session_state.ensemble = st.pills(
        "Simulation Ensemble",
        ["NVT_NOSE_HOOVER", "NVT_BERENDSEN"],
        default=st.session_state.ensemble,
        help="Simulation ensemble chosen"
    )
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.temperature = st.number_input(
            "Temperature",
            value=st.session_state.temperature,
            help="Simulation temperature"
        )

    with col2:
        st.session_state.temp_unit = st.pills("Unit",
                                          ["K", "deg"],
                                          default = st.session_state.temp_unit)

    st.session_state.timestep = st.number_input(
        "Time step (fs)",
        min_value=0.0,
        value=st.session_state.timestep,
        help="The simulation time step, in fs"
    )

    st.session_state.taut = st.number_input(
        "Timescale of thermostat (fs)",
        value=st.session_state.taut if st.session_state.taut is not None else 1000 * st.session_state.timestep,
        placeholder="If left empty, taut will be automatically set to 1000*timestep.",
        help="Characteristic timescale of the thermostat, in fs."
    )

    st.session_state.n_steps = st.number_input(
        "Number of simulation steps",
        value=st.session_state.n_steps,
        min_value=0,
        step=1
    )

    return (
        st.session_state.ensemble,
        st.session_state.temperature,
        st.session_state.timestep,
        st.session_state.taut,
        st.session_state.n_steps,
        st.session_state.temp_unit
    )

# %%
def run_md(structure, ensemble, temperature, timestep, taut, n_steps, temp_unit):
    """Runs a molecular dynamics simulation using the specified parameters.

    Args:
        structure (ase.Atoms): The atomic structure to simulate.
        ensemble (str): The simulation ensemble.
        temperature (float): The simulation temperature.
        timestep (float): The simulation time step (fs).
        taut (float): The timescale of the thermostat (fs).
        n_steps (int): The number of simulation steps.
        temp_unit (str): The temperature unit ("K" or "deg").

    Returns:
        mattersim.applications.moldyn.MolecularDynamics or 
        None: The MolecularDynamics object if the simulation completes
                successfully, otherwise None. The Streamlit app is stopped
                if an exception occurs.
    """
    if temp_unit == "deg":
        temperature += 273.15
    try:
        md = MolecularDynamics(
        atoms=structure,
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        taut=taut
        )
        md.run(n_steps=n_steps)
        st.success(f"""
        **MD simulation completed with:**\n\n
        **Ensemble:** {ensemble} \n
        **Temperature (K):** {temperature:.5f} \n
        **Temperature (deg):** {temperature-273.15:.5f}\n
        **Time step:** {timestep}\n
        **Taut:** {taut}
        """
        , icon="✅")

        return md

    except Exception as e:
        st.error(f"Relaxation failed: {str(e)}", icon="🚨")
        st.stop()
