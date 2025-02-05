import torch
import streamlit as st
from ase.units import GPa

# %%
def setup_configuration_sidebar():
    """Configure model and device selection in sidebar"""
    st.sidebar.header("Model and device configuration")
    model = st.sidebar.pills(
        "Select MatterSim Model",
        ["1M", "5M"],
        default = "1M"
    )
    # Check CUDA availability
    if torch.cuda.is_available():
        device = st.sidebar.radio(
            "Select Device", 
            ["cuda", "cpu"]
            )
        if device == "cuda":
            st.sidebar.info(f"Using GPU: {torch.cuda.get_device_name(0)}", icon="ℹ️")
            # st.info('This is a purely informational message', icon="ℹ️")
        else:
            st.sidebar.warning("Cuda is available but using CPU instead.", icon="⚠️")
    else:
        device = "cpu"
        st.sidebar.warning("Cuda unavailable. Using CPU.", icon="⚠️")
    
    return model[0], device

# %% Structure relaxation sidebar
def setup_relaxation_sidebar():
    """ Configure structure relaxation parameters in the sidebar """
    st.sidebar.header("Relaxation parameters")
    
    # Initialize session state variables before creating widgets if they aren't set
    if "optimizer" not in st.session_state:
        st.session_state.optimizer = "BFGS"
    if "steps" not in st.session_state:
        st.session_state.steps = 500
    if "filter" not in st.session_state:
        st.session_state.filter = "FrechetCellFilter"
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
        """"The scalar_pressure used in ExpCellFilter assumes eV/A^3 unit and 1 eV/A^3 is already 160 GPa. 
            Please make sure you have converted your pressure from GPa to eV/A^3 by dividing by 160.21766208
            (or multiply by GPa from ase.units)."
            
            elif filter is None and pressure_in_GPa is not None:
                filter = "ExpCellFilter"
                params_filter["scalar_pressure"] = (
                    pressure_in_GPa * GPa
                )  # GPa = 1 / 160.21766208
            elif filter is not None and pressure_in_GPa is None:
                params_filter["scalar_pressure"] = 0.0
            else:
                params_filter["scalar_pressure"] = (
                    pressure_in_GPa * GPa
                )
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
    
    filter = st.sidebar.pills("Filter",
                                  ["ExpCellFilter", "FrechetCellFilter", "None"],
                                  default=st.session_state.filter,
                                  key="filter",
                                  
    )
    if filter == "None":
        filter = None

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

    return optimizer, steps, filter, constrain_symmetry, fmax, pressure, unit