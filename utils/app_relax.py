import streamlit as st
from mattersim.applications.relax import Relaxer
from ase.units import GPa

# %%
def perform_relaxation(basis_positions, structure, optimizer, steps, filter, constrain_symmetry, fmax, pressure):

    if basis_positions is None:
        st.warning("Basis positions is None." , icon="⚠️")
        return
    
    """Perform structure relaxation"""
    with st.spinner("Starting relaxation..."):
        # Create relaxer
        try:
            relaxer = Relaxer(
                optimizer=optimizer,
                filter=filter,
                constrain_symmetry=constrain_symmetry
            )
        except Exception as e:
            st.error(f"Failed to initialize relaxer: {str(e)}", icon="🚨")
            st.stop()
        
        # Perform relaxation
        try:
            relaxed_structure = relaxer.relax(structure, steps=steps, fmax=fmax, params_filter={"scalar_pressure": pressure})
            # Store the relaxed structure in session_state to persist it across re-runs
            if relaxed_structure:
                st.session_state.relaxed_structure = relaxed_structure
                st.success(f"""
                            **Relaxation completed with:**  \n
                            **Optimizer:** {optimizer}  
                            **Filter:** {filter}  
                            **Maximum force:** {fmax}  
                            **Symmetry constrained:** {constrain_symmetry}  
                            **Relaxation steps:** {steps}  
                            **Pressure in eV/Å³:** {pressure:.5f}  
                            **Pressure in GPa:** {pressure/GPa:.5f}"""
                                                , icon="✅")
                
                return relaxed_structure
    
        except Exception as e:
            st.error(f"Relaxation failed: {str(e)}", icon="🚨")
            st.stop()
