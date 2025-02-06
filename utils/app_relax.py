"""Provides functions for setting up and performing structure relaxation using Mattersim."""

import streamlit as st
from mattersim.applications.relax import Relaxer
from ase.units import GPa

# %% Structure relaxation sidebar
def setup_relaxation_sidebar():
    """Configures structure relaxation parameters in the Streamlit sidebar.

    Creates interactive widgets for setting the optimizer, maximum relaxation steps, filtering method,
    symmetry constraint, maximum force (fmax), and pressure.
    Handles pressure unit conversion from GPa to eV/Å³ if necessary.
    Initializes session state variables with default values.

    Returns:
        tuple: A tuple containing the selected
                optimizer (str),
                maximum steps (int),
                filtering method (str or None),
                symmetry constraint (bool),
                maximum force (float),
                pressure (float), and
                pressure unit (str).
    """
    st.sidebar.header("Relaxation parameters")

    # Initialize session state variables before creating widgets if they aren't set
    if "optimizer" not in st.session_state:
        st.session_state.optimizer = "BFGS"
    if "steps" not in st.session_state:
        st.session_state.steps = 500
    if "filtering" not in st.session_state:
        st.session_state.filtering = "FrechetCellFilter"
    if "constrain_symmetry" not in st.session_state:
        st.session_state.constrain_symmetry = True
    if "fmax" not in st.session_state:
        st.session_state.fmax = 0.01
    if "pressure" not in st.session_state:
        st.session_state.pressure= 0.0
    if "unit" not in st.session_state:
        st.session_state.unit = "GPa"

    col1, col2 = st.sidebar.columns(2)
    with col1:
        pressure = st.number_input("Pressure",
                                value = st.session_state.pressure,
                                min_value=0.0)
        """"
        The scalar_pressure used in ExpCellFilter assumes eV/A^3 unit
              and 1 eV/A^3 is already 160 GPa. Please make sure you have
              converted your pressure from GPa to eV/A^3 by dividing by
              160.21766208 (or multiply by GPa from ase.units)."
        """
    with col2:
        unit = st.pills("Unit",
                        ["GPa", "eV/A^3"],
                        default=st.session_state.unit,
                        key="unit")

    if unit == "GPa":
        pressure *=GPa

    optimizer = st.sidebar.pills(
        "Optimizer", 
        ["BFGS", "FIRE"],
        selection_mode="single",
        default=st.session_state.optimizer,
        key="optimizer"
    )
    st.sidebar.caption("""
                       **BFGS**: A quasi-Newton method. Generally a good choice for many systems. Balances speed and accuracy. Approximates the Hessian matrix.\n
                       **FIRE**: Good for systems that are "difficult" to relax. Uses a combination of Newtonian dynamics and friction. Can be slower per step than BFGS.
                       """
    )

    steps = st.sidebar.slider(
        "Maximum Relaxation Steps", 
        value=st.session_state.steps,
        min_value=0,
        max_value=5000,
        step=500,
        key="steps"
    )

    filtering = st.sidebar.pills("Filter",
                                  ["ExpCellFilter", "FrechetCellFilter", "None"],
                                  default=st.session_state.filtering,
                                  key="filtering",

    )
    if filtering == "None":
        filtering = None

    st.sidebar.caption("""
                       Filters are designed to enable simultaneous relaxation of atomic positions and the unit cell shape.
                       *ASE recommends using FrechetCellFilter over ExpCellFilter due to its better convergence properties, especially concerning the cell variables.*
                       """
                       )

    constrain_symmetry = st.sidebar.checkbox("Constrain Symmetry",
                                             value=st.session_state.constrain_symmetry,
                                             key="constrain_symmetry")

    fmax = st.sidebar.number_input("fmax",
                                   value = st.session_state.fmax,
                                   key = "fmax",
                                   min_value=0.01,
                                   step = 0.01,
                                   help = "The maximum force allowed.")

    return optimizer, steps, filtering, constrain_symmetry, fmax, pressure, unit

# %%
def perform_relaxation(basis_positions, structure,
                       optimizer, steps,
                       filtering, constrain_symmetry,
                       fmax, pressure):
    """Performs structure relaxation.

    Args:
        basis_positions (list): A list of basis position lists.
        structure (ase.Atoms): The atomic structure to relax.
        optimizer (str): The optimization algorithm to use
            (e.g., "BFGS", "FIRE").
        steps (int): The maximum number of relaxation steps.
        filtering (str or None): The filtering method to use
            (e.g., "ExpCellFilter", "FrechetCellFilter", None).
        constrain_symmetry (bool): Whether to constrain symmetry during relaxation.
        fmax (float): The maximum force allowed.
        pressure (float): The pressure to apply (in eV/Å³).

    Returns:
        ase.Atoms or None: The relaxed atomic structure. Returns None if relaxation fails.
                            Stops the Streamlit app if an error occurs.
    """

    if basis_positions is None:
        st.warning("Basis positions is None." , icon="⚠️")
        st.stop()

    with st.spinner("Starting relaxation..."):
        # Create relaxer
        try:
            relaxer = Relaxer(
                optimizer=optimizer,
                filter=filtering,
                constrain_symmetry=constrain_symmetry
            )
        except Exception as e:
            st.error(f"Failed to initialize relaxer: {str(e)}", icon="🚨")
            st.stop()

        # Perform relaxation
        try:
            relaxed_structure = relaxer.relax(structure,
                                              steps=steps,
                                              fmax=fmax,
                                              params_filter={"scalar_pressure": pressure})
            # Store the relaxed structure in session_state to persist it across re-runs
            if relaxed_structure:
                st.session_state.relaxed_structure = relaxed_structure
                st.success(f"""
                            **Relaxation completed with:**  \n
                            **Optimizer:** {optimizer}\n
                            **Filter:** {filter}\n
                            **Maximum force:** {fmax}\n
                            **Symmetry constrained:** {constrain_symmetry}\n
                            **Relaxation steps:** {steps}\n
                            **Pressure in eV/Å³:** {pressure:.5f}\n
                            **Pressure in GPa:** {pressure/GPa:.5f}"""
                                                , icon="✅")

                return relaxed_structure
            st.error("Relaxer did not return relaxed structure.", icon="🚨")
            st.stop()

        except Exception as e:
            st.error(f"Relaxation failed: {str(e)}", icon="🚨")
            st.stop()
