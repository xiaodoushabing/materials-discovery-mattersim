<div style="text-align: center">
<h1 style="text-align: center;">MatterSim</h1>

*[MatterSim](https://github.com/microsoft/mattersim/tree/main?tab=readme-ov-file#----) is a deep learning atomistic model across elements, temperatures and pressures.*
</div>

## 1. Using MatterSim
To run MatterSim, either create a clean conda environment as recommended, or
1. Create a docker container using NVIDIA's pytorch docker image: nvcr.io/nvidia/pytorch:24.12-py3
2. Clone the repository:

   ```bash
   git clone git@seagit.okla.seagate.com:adapt-ml/materials-discovery.git
   cd materials-discovery/matter/
   ```
3.  Install MatterSim:
    ```bash
    pip install mattersim
    ```
4. Install other dependencies as necessary. Run:
   ```bash
   pip install -r requirements.txt
   ```
   or install dependencies manually.
   
## 2. Streamlit app (Structure Analysis with MatterSim)

This Streamlit application provides a user-friendly interface for analyzing atomic and crystal structures using the MatterSim force field.  It allows users to define structures, perform structural relaxations, and run molecular dynamics (MD) simulations.

#### Features

* **Model and Device Selection:** Choose between different MatterSim models (1M, 5M) and select the device for computation (CUDA if available, or CPU).
* **Structure Building:** Create atomic structures using either:
    * **Crystal Builder:** Defines structures based on space group and lattice parameters, ensuring crystallographic symmetry.
    * **Atoms Builder:** Defines structures by specifying atomic symbols and Cartesian coordinates. Working with Atoms builder also allow you to run MD simulations.
* **Structure Perturbation:** Introduce random displacements ("rattle") to atom positions.
* **Structural Relaxation:** Optimize structures using BFGS or FIRE algorithms with optional filters (ExpCellFilter, FrechetCellFilter) and symmetry constraints.
* **Energy Calculation:** Calculate the potential energy of the structure.
* **Molecular Dynamics (MD) Simulations:** Run MD simulations with different ensembles (NVT_NOSE_HOOVER, NVT_BERENDSEN).

* **Parameter Control:**  Fine-grained control over relaxation and MD simulation parameters.
* **Result Display:** Display calculated energies, lattice parameters, and other relevant information.
* **Visualisation:** Interactive 3D visualization of the structures.

#### Running the app

In your terminal, run:
   ```bash
   streamlit run app.py
   ```
This will open the app in your web browser.

#### Usage
**Model and Device Configuration:** In the sidebar, select the desired MatterSim model and computational device.

**Structure Definition:** Choose either "Crystal Builder" or "Atoms Builder" and provide the necessary input (atomic symbols, basis positions, lattice parameters, space group if applicable).

> 🚨 Crystal Builder takes in **fractional** coordinates, while Atoms Builder takes in **cartesean** coordinates.

**Structure Perturbation (Optional):** Toggle the "Rattle" option to introduce small random displacements to the atom positions.

**Lattice Visualisation:** Adjust the "Number of cells to display per axis" to control the size of the visualized structure.

**Initial Structure:** The initial structure will be displayed, including energy and lattice parameters.

**Relax Structure:** Click the "Relax Structure" button to perform structural relaxation. The relaxed structure and results will be displayed.

**Molecular Dynamics (MD) Simulation (Atoms Builder only):** If you used the "Atoms Builder," you can perform MD simulations by configuring the MD parameters and checking the "Start MD simulation" when you are ready.

#### Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 3. Notebooks
Define the variable `model` accordingly to run the 1M or 5M model. e.g., `model = 1` for the 1M model
1. **Structure optimization**
   1. Predicted energy, forces & stresses of a single Si or C lattice
   2. Perturbed the structure
   3. Relaxed the structure
   4. Predicted energy, forces & stresses of the relaxed lattice
2. **Batch structure optimization**
   1. Predicted energy, forces & stresses of 1000 Si lattices
   2. Perturbed the structures using .rattle method
   3. Relaxed the structures
   4. Predicted energy, forces & stresses of the 1000 relaxed lattices
   5. For all structures above, use `plot_potential` and `plot_relaxation` to visualise the energy distribution.
3. **Playground**
   1. To try running the relaxation and predictions with FePt L1<sub>o</sub> lattice
   2. Use `visualise_structure` to visualise a lattice structure.

#### Utility functions
1. **Plot potential**: Plot distribution of energy, forces and stresses
2. **Plot relaxation**: Plot energies before and after relaxation
3. **Visualise structure**: Visualise a lattice structure

#### Key observations

##### 1. Reproducibility of predictions

For 1000 identical Si diamond structures (generated using `si = bulk("Si", "diamond", a=5.43)`), force and stress predictions exhibit a normal distribution. Energy predictions are generally consistent, although a left-skewed tail is observed.

![Prediction distribution](./plots/image.png)

##### 2. Energy minimization through relaxation
As expected, structural relaxation consistently lowers the energy of the 1000 identical Si diamond structures.

![Energy minimization](./plots/image-1.png)
![Energy minimization (split)](./plots/image-2.png)

##### 3. Impact of atomic displacement on predictions
The 1000 identical Si diamond structures were perturbed using `si.rattle(stdev=np.random.random())`. Introducing random atomic displacements results in significantly increased variation in predicted energies, forces, and stresses.  This reflects the sensitivity of these properties to structural changes.

![alt text](./plots/image-3.png)

##### 4. Energy convergence after relaxation
Despite the initial variation in predicted energies due to the random perturbations, subsequent structural relaxation brings the energies of the 1000 structures into a narrower, more consistent range.  This indicates that relaxation effectively minimizes the energy of the perturbed structures, leading to a more homogeneous energetic state.
![alt text](./plots/image-5.png)
![alt text](./plots/image-4.png)