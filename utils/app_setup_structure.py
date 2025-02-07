"""
Provides functions for setting up atomic structures, defining calculation parameters,
and performing energy calculations using MatterSim.
"""
# %% import necessary libraries
import torch
import streamlit as st
from ase import Atoms
from ase.spacegroup import crystal
from mattersim.forcefield.potential import MatterSimCalculator

# %%
def get_atomic_input():
    """Gets the list of atom symbols from user input.

    Prompts the user to enter a comma-separated list of atom symbols (e.g., "Fe, Pt, C").
    Handles empty input and input containing spaces within atom names.

    Returns:
        list: A list of atom symbols (strings). Returns an empty list if no valid input is provided.
              Stops the Streamlit app execution if invalid input is detected.
    """
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
         # check for space and not quoted
        if ' ' in atom and not atom.startswith('"') and not atom.endswith('"'):
            st.warning(f"Atom '{atom}' contains spaces. \
                       Please separate atoms with commas only."
                       , icon="⚠️")
            st.stop()

    return atoms

# %%
def get_basis_positions(atoms, builder):
    """Gets the basis positions from user input.

    Prompts the user to enter the atomic coordinates. Supports both fractional (Crystal Builder)
    and Cartesian coordinates (Atoms Builder). The number of input coordinate sets must match
    the number of atoms defined previously.

    Args:
        atoms (list): A list of atom symbols (strings).
        builder (str): The selected structure builder ("Crystal Builder" or "Atoms Builder").

    Returns:
        list: A list of basis position lists. Each sub-list contains the (x, y, z) coordinates
              for an atom.
              Stops the Streamlit app execution if the number of coordinates
              does not match the number of atoms.
    """
    st.subheader("Basis Positions")
    st.info(f"You have entered {len(atoms)} atoms above.")

    basis_positions = []
    if builder == "Crystal Builder":
        st.write("**Fractional** Coordinates")
        for i in range(len(atoms)):

            col1, col2, col3 = st.columns(3)  # Three columns for x, y, z

            with col1:
                x = st.number_input(f"Atom {i+1} (x)",
                                    value=0.0,
                                    key=f"x_{i}",
                                    step=0.001,
                                    min_value=-1.0,
                                    max_value=1.0)

            with col2:
                y = st.number_input(f"Atom {i+1} (y)",
                                    value=0.0,
                                    key=f"y_{i}",
                                    step=0.001,
                                    min_value=-1.0,
                                    max_value=1.0)

            with col3:
                z = st.number_input(f"Atom {i+1} (z)",
                                    value=0.0,
                                    key=f"z_{i}",
                                    step=0.001,
                                    min_value=-1.0,
                                    max_value=1.0)

            basis_positions.append([float(x), float(y), float(z)])
    else:
        st.write("**Cartesian** Coordinates")
        for i in range(len(atoms)):

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
    """Gets the lattice parameters from user input.

    Prompts the user to enter the lattice constants (a, b, c).
    If Crystal Builder is selected, it also prompts for lattice angles(alpha, beta, gamma).

    Args:
        builder (str): The selected structure builder ("Crystal Builder" or "Atoms Builder").

    Returns:
        list: A list of lattice parameters.
                For Crystal Builder, it contains [a, b, c, alpha, beta, gamma].
                For Atoms Builder, it contains [a, b, c].
    """
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
    """Gets the space group number from user input.

    Prompts the user to enter the space group number.

    Returns:
        int: The space group number.
    """
    st.subheader("Space group")
    st.link_button("The Materials Project ", "https://next-gen.materialsproject.org/")
    spacegroup = st.number_input("Space group number",
                                 value=123,
                                 step=1,
                                 min_value=1,
                                 max_value=230,
                                 help="Example: 123 for P4/mmm")

    return spacegroup

# %%
def get_builder():
    """Gets the structure builder choice from the user.

    Presents the user with a choice between "Crystal Builder" and "Atoms Builder".

    Returns:
        str: The selected builder ("Crystal Builder" or "Atoms Builder").
    """
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
    """Creates a crystal structure.

    Args:
        atoms (list): A list of atomic symbols (strings).
        basis_positions (list): A list of basis position lists
            (each sublist contains x, y, z coordinates).
        lattice_params (list): A list of lattice parameters
            (a, b, c, alpha, beta, gamma).
        spacegroup (int): The space group number.
        rattle (bool): Whether to apply random displacements to the atomic positions.
        stdev (float): The standard deviation for the random displacements
            (if `rattle` is True).

    Returns:
        ase.Atoms: The created crystal structure. Returns None and stops the Streamlit app
                   if an error occurs during structure creation.
    """
    st.session_state.structure = None
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
        return None

# %%
def create_atom(atoms, basis_positions, lattice_params, rattle, pbc, stdev):

    """Creates an atomic structure.

    Args:
        atoms (list): A list of atomic symbols (strings).
        basis_positions (list): A list of basis position lists
            (each sublist contains x, y, z coordinates).
        lattice_params (list): A list of lattice constants
            (a, b, c).
        rattle (bool): Whether to apply random displacements to the atomic positions.
        pbc (list or bool): Periodic boundary conditions.
        stdev (float): The standard deviation for the random displacements
            (if `rattle` is True).

    Returns:
        ase.Atoms: The created atomic structure. Returns None and stops the Streamlit app
                   if an error occurs during structure creation.
    """
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
    """Gets rattle parameters from the user.

    Prompts the user to enable/disable rattling of atoms and,
    if enabled, to provide the standard deviation for the displacements.

    Returns:
        tuple: A tuple containing a boolean indicating whether rattling
            is enabled and the standard deviation for the 
            displacements (float). Returns (False, 0)
            if rattling is not enabled.
    """
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
    """Attaches a MatterSim calculator to the atomic structure.

    Args:
        structure (ase.Atoms): The atomic structure to which
            the calculator will be attached.
        model (str): The MatterSim model size ("1M" or "5M").
        device (str): The device to use for calculations ("cuda" or "cpu").

    Raises:
        Exception: If there's an error attaching the calculator.
            The Streamlit app execution is stopped.
    """
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
    """Calculates and displays the potential energy of the atomic structure.

    Args:
        structure (ase.Atoms): The atomic structure.
        atoms (list): List of atomic symbols. Used to calculate energy per atom.

    Raises:
        ValueError: if structure is None. The Streamlit app execution is stopped.
    """
    if structure:
        with st.container(border=True):
            st.subheader("Calculated energy:")
            energy = structure.get_potential_energy()
            st.write(f"Energy:      {energy:.2f} eV")
            st.write(f"Energy/atom: {energy/len(atoms):.2f} eV/atom")
    else:
        st.error("Structure is None." , icon="🚨")
        st.stop()
