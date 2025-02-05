# %% import necessary libraries
import torch
import streamlit as st
import streamlit.components.v1 as components
from ase import Atoms
from ase.spacegroup import crystal
from mattersim.forcefield.potential import MatterSimCalculator
from mattersim.applications.relax import Relaxer
from mattersim.applications.moldyn import MolecularDynamics

from utils.visualisation import visualise_structure

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

    return optimizer, steps, filter, constrain_symmetry, fmax

# %%
def get_atomic_input():
    """Get atomic structure input from user"""
    st.subheader("Define Atoms")
    st.write("Enter atoms")
    # Atoms input
    atoms_input = st.text_input(
        "Enter atoms",
        value="Fe, Pt",
        placeholder="Example: Fe, Pt, C",
        label_visibility="collapsed"
    )

    if not atoms_input:  # Handle empty input
        st.warning("Please enter at least one atom.", icon="⚠️")
        st.stop()

    atoms_input = atoms_input.strip()  # Remove leading/trailing whitespace
    atoms = [atom.strip() for atom in atoms_input.split(',')]

    if not all(atoms):
        st.warning("Atoms must be comma-separated and cannot be empty strings.", icon="⚠️")
        st.stop()

    # Check for spaces within atom names
    for atom in atoms:
        if ' ' in atom and not atom.startswith('"') and not atom.endswith('"'): # check for space and not quoted
            st.warning(f"Atom '{atom}' contains spaces. Please separate atoms with commas only.", icon="⚠️")
            st.stop()

    return atoms

# %%
def get_basis_positions(atoms, builder):
    """Get basis positions input from user"""
    st.subheader("Basis Positions")
    st.info(f"You have entered {len(atoms)} atoms above.")
    num_atoms = st.number_input("Number of Atoms", min_value=len(atoms), value=len(atoms), step=1,
                                help="The number you enter should match the total number of coordinate sets you will provide.")

    basis_positions = []
    if builder == "Crystal Builder":
        st.write("**Fractional** Coordinates")
        for i in range(num_atoms):
            
            col1, col2, col3 = st.columns(3)  # Three columns for x, y, z

            with col1:
                x = st.number_input(f"Atom {i+1} (x)", value=0.0, key=f"x_{i}", step=0.001, min_value=-1.0, max_value=1.0)
            with col2:
                y = st.number_input(f"Atom {i+1} (y)", value=0.0, key=f"y_{i}", step=0.001, min_value=-1.0, max_value=1.0)
            with col3:
                z = st.number_input(f"Atom {i+1} (z)", value=0.0, key=f"z_{i}", step=0.001, min_value=-1.0, max_value=1.0)

            basis_positions.append([float(x), float(y), float(z)])
    else:
        st.write("**Cartesian** Coordinates")
        for i in range(num_atoms):
            
            col1, col2, col3 = st.columns(3)  # Three columns for x, y, z

            with col1:
                x = st.number_input(f"Atom {i+1} (x)", value=0.0, key=f"x_{i}", step=0.001)
            with col2:
                y = st.number_input(f"Atom {i+1} (y)", value=0.0, key=f"y_{i}", step=0.001)
            with col3:
                z = st.number_input(f"Atom {i+1} (z)", value=0.0, key=f"z_{i}", step=0.001)

            basis_positions.append([float(x), float(y), float(z)])
            
    return basis_positions

# %%
def get_lattice_parameters(builder):
    """Get lattice parameters input from user"""
    st.subheader("Lattice Parameters")
    
    # Lattice constants
    st.text("Lattice Constants")
    col1, col2, col3 = st.columns(3)
    with col1:
        a = st.number_input("a (Å)", value=3.85, step=0.01)
    with col2:
        b = st.number_input("b (Å)", value=3.85, step=0.01)
    with col3:
        c = st.number_input("c (Å)", value=3.72, step=0.01)
    
    if builder == "Crystal Builder":
    # Angles
        st.text("Angles")
        col1, col2, col3 = st.columns(3)
        with col1:
            alpha = st.number_input("α (degrees)", value=90.0, max_value=360.0, step=0.1)
        with col2:
            beta = st.number_input("β (degrees)", value=90.0, max_value=360.0, step=0.1)
        with col3:
            gamma = st.number_input("γ (degrees)", value=90.0, max_value=360.0, step=0.1)
    
        return [a, b, c, alpha, beta, gamma]
    return [a, b, c]

# %%
def get_spacegroup():
    """Get lattice space group input from user"""
    st.subheader("Space group")
    st.link_button("The Materials Project ", "https://next-gen.materialsproject.org/")
    spacegroup = st.number_input("Space group number", value=123, step=1, min_value=1, max_value=230,
                                 help="Example: 123 for P4/mmm")

    return spacegroup

# %%
def get_builder():
    builder = st.pills("Choose structure builder",
                       default = "Crystal Builder",
                       options=["Crystal Builder", "Atoms Builder"],
                       help=(
        "🔹 **Crystal Builder**: Requires space group and lattice angles, ensuring symmetry. \n"
        "🔹 **Atoms Builder**: Allows manual atom perturbation using the `.rattle()` method."
    )
)
    return builder
# %%
def create_crystal(atoms, basis_positions, lattice_params, spacegroup, rattle, stdev):
    """Create crystal structure from input parameters"""
    try:
        structure = crystal(
            symbols=atoms,
            basis=basis_positions,
            spacegroup=spacegroup,
            cellpar=lattice_params
        )
        if rattle:
            structure.rattle(stdev=stdev)
        st.success("Structure created successfully.", icon="✅")
        return structure
    except Exception as e:
        st.error(f"Error creating structure: {str(e)}", icon="🚨")
        st.stop()

# %%
def create_atom(atoms, basis_positions, lattice_params, rattle, pbc, stdev):
    """Create atom structure from input parameters"""
    try:
        a, b, c = lattice_params
        structure = Atoms(symbols="".join(atoms),
                        positions=basis_positions,
                        cell=[(a, 0, 0), (0, b, 0), (0, 0, c)],
                        pbc=pbc)  # Periodic boundary conditions
        if rattle:
            structure.rattle(stdev=stdev)
        st.success("Structure created successfully.", icon="✅")
        return structure
    except Exception as e:
        st.error(f"Error creating structure: {str(e)}", icon="🚨")
        st.stop()

# %%
def get_rattle():
    st.subheader("Structure perturbation")
    rattle = st.toggle("Rattle",
                            value = False)
    if rattle:
        stdev = st.number_input("Standard deviation for rattle",
                        value = 0.01,
                        step = 0.01)
        return rattle, stdev
    return rattle, 0
  
# %%
def setup_calculator(structure, model, device): 
    try:
        if device == "cuda" and torch.cuda.is_available():
            map_location = None  # Let PyTorch handle CUDA if available
        else:
            map_location = torch.device('cpu') # Map to CPU

        structure.calc = MatterSimCalculator(
            load_path=f"MatterSim-v1.0.0-{model}M.pth", 
            device=device, 
            map_location=map_location # Map location for the model
        )
    except Exception as e:
        st.error(f"Failed to attach calculator to structure: {str(e)}", icon="🚨")
        st.stop()

# %%
def calc_energy(structure, atoms):
    if structure:
        with st.container(border=True):
            st.subheader(f"Calculated energy:")
            energy = structure.get_potential_energy()
            st.write(f"Energy:      {energy:.2f} eV")
            st.write(f"Energy/atom: {energy/len(atoms):.2f} eV/atom")
    else:
        st.error("Structure is None." , icon="🚨")

# %%
def perform_relaxation(basis_positions, structure, optimizer, steps, filter, constrain_symmetry, fmax):

    """Perform structure relaxation"""
    with st.spinner("Starting relaxation..."):
        if basis_positions is None:
            st.warning("Basis positions is None." , icon="⚠️")
            return
            
    # Create relaxer
    try:
        relaxer = Relaxer(
            optimizer=optimizer,
            filter=filter,
            constrain_symmetry=constrain_symmetry
        )
    except Exception as e:
        st.error(f"Failed to initialize relaxer: {str(e)}", icon="🚨")
    
    # Perform relaxation
    try:
        relaxed_structure = relaxer.relax(structure, steps=steps, fmax=fmax)
        # Store the relaxed structure in session_state to persist it across re-runs
        if relaxed_structure:
            st.session_state.relaxed_structure = relaxed_structure
            st.success(f"""
        Relaxation completed with:\n\n
        Optimizer: {optimizer} \n
        Relaxation steps: {steps}\n 
        Filter: {filter}\n
        Maximum force: {fmax}\n
        Symmetry constrained: {constrain_symmetry}
        """
                    , icon="✅")
            return relaxed_structure
    
    except Exception as e:
        st.error(f"Relaxation failed: {str(e)}", icon="🚨")
        st.stop()


# %%
def get_md():
    # Initialize session state variables if not present
    if "ensemble" not in st.session_state:
        st.session_state.ensemble = "NVT_NOSE_HOOVER"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 300.0
    if "timestep" not in st.session_state:
        st.session_state.timestep = 1.0
    if "taut" not in st.session_state:
        st.session_state.taut = None
    if "n_steps" not in st.session_state:
        st.session_state.n_steps = 1000

    # Assign updated values and store them in session state
    st.session_state.ensemble = st.pills(
        "Simulation Ensemble",
        ["NVT_NOSE_HOOVER", "NVT_BERENDSEN"],
        default=st.session_state.ensemble,
        help="Simulation ensemble chosen"
    )

    st.session_state.temperature = st.number_input(
        "Temperature in K",
        min_value=0.0,
        value=st.session_state.temperature,
        help="Simulation temperature, in Kelvin"
    )

    st.session_state.timestep = st.number_input(
        "Time step",
        min_value=0.0,
        value=st.session_state.timestep,
        help="The simulation time step, in fs"
    )

    st.session_state.taut = st.number_input(
        "Timescale of thermostat",
        value=st.session_state.taut if st.session_state.taut is not None else 1000 * st.session_state.timestep,
        placeholder="If left empty, taut will be automatically set to 1000 * timestep.",
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
    )

# %%
def run_md(structure, ensemble, temperature, timestep, taut, n_steps):
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
        MD simulation completed with:\n\n
        Ensemble: {ensemble} \n
        Temperature: {temperature} K\n 
        Time step: {timestep}\n
        Taut: {taut}\n
        """
        , icon="✅")
            
        return md
    
    except Exception as e:
        st.error(f"Relaxation failed: {str(e)}", icon="🚨")
        st.stop()

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