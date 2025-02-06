"""Provides functions for configuring MatterSim model and device selection within a Streamlit application."""

import torch
import streamlit as st

# %%
def setup_configuration_sidebar():
    """Configures the MatterSim model and device selection in the Streamlit sidebar.

    This function creates interactive widgets in the sidebar to allow the user to choose
    the MatterSim model size (1M or 5M) and the device (GPU or CPU). It automatically
    detects CUDA availability and adjusts the device selection options accordingly.

    Returns:
        tuple: A tuple containing the selected model size (str) and device (str).
               The model size will be either "1M" or "5M". The device will be
               either "cuda" or "cpu".
    """
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
