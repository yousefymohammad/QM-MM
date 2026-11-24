# How chalcone synthase controls cyclization

Tetraketide cyclization is a branch point in chalcone biosynthesis. Intramolecular **Claisen condensation** produces naringenin chalcone, the desired product. Competing **lactonization** produces p-coumaroyltriacetic acid lactone (CTAL). This study asks cyclization occur when the tetraketide intermediate bound to the CoA (LIG) or bound to the catalytical amino acid Cys167. 

 Classical MD and conformational clustering provided representative structures for QM/MM molecular dynamics (QM/MM-MD) umbrella sampling of both reaction pathways. The study then examined capped CYL in explicit water without the enzyme to isolate the contribution of the active site. Finally, gas-phase DFT scans of capped CYL probed the intrinsic energetics of the two cyclizations in the absence of both protein and solvent.


## Study workflow

| Stage | What was calculated | Repository contents |
| --- | --- | --- |
| Classical MD and clustering | AMBER22 simulations of solvated TaCHS, followed by CPPTRAJ processing and TTClust clustering. Representative snapshots seeded the QM/MM calculations. | [Classical MD topology](classical_md/) and the selected QM/MM starting snapshots. The classical production trajectories and full preparation and clustering inputs are outside the tracked repository. |
| Cyclization in TaCHS | DFTB3/AMBER ff14SB umbrella sampling of both pathways for representative CYL and LIG conformations. | [Enzyme QM/MM inputs](enzyme_qm_mm_md/) for two CYL and four LIG clusters. |
| Cyclization in water | QM/MM-MD umbrella sampling of two comparable CYL conformations in explicit water. The extracted intermediate was capped with acetyl (ACE) and N-methylamide (NME) groups. | [Solution QM/MM inputs](solution_qm_mm_md/). |
| Gas-phase cyclization | Gaussian 16 relaxed potential-energy scans of capped CYL along the forming C1–C6 bond for Claisen condensation and the forming O5–C1 bond for lactonization. Chapter 3 reports B3LYP/6-31G(d) calculations. | [Archived Gaussian inputs and logs](gas_phase_dft/), with the limitations below. |

## Run the QM/MM umbrella sampling

Use Python 3 and AMBER22. Put `sander` on your `PATH`. The solution runs also require `cpptraj` to reimage the system between windows.

Choose a cluster and pathway. The `main` directory is Claisen condensation and the `side` directory is lactonization. For example, from the repository root:

```bash
cd enzyme_qm_mm_md/CYL/cluster_1/main
python3 prepare_umbrella_windows.py
bash umbrella_windows/run_QMMM.sh
```

The setup script reads the pathway’s starting restart and `md_dftb3.in` template and uses the topology shared by that state or environment. It generates the window inputs and restraints inside `umbrella_windows/`. The runner initializes velocities for the first window and passes the restart from each window to the next. To regenerate the inputs, move or archive any existing `umbrella_windows/` directory first.

The QM/MM reaction coordinate is the forming bond distance minus the breaking thioester bond distance. The setup uses 0.1 Å window spacing and a harmonic force constant of 100 kcal mol⁻¹ Å⁻². Chapter 3 describes combining the sampled coordinates with WHAM to obtain potentials of mean force (PMFs) and checking window overlap. The generators prepare the baseline sampling runs. The published repository excludes reference PMF tables. Reproducing the thesis PMFs and their reported uncertainties requires the corresponding replicas, sampling data, and WHAM settings, including the longer windows used for the CYL convergence analysis.

## Gas-phase archive status

The archived `cluster1` inputs use B3LYP/6-31G(d), and the `cluster2` inputs use HF/6-31G(d). Three logs end with Gaussian errors and the fourth has no termination marker. These files document partial scans. Reproducing the gas-phase electronic energy barriers reported in Chapter 3 requires the verified B3LYP scans. The enzyme and aqueous PMFs report activation free energies.

## Citation

Mohammad Yousefi (2026). *Enhancing Chalcone Synthase Performance through Rational Enzyme Engineering and Reaction-Medium Optimization*. Dissertation, Martin Luther University Halle-Wittenberg. Chapter 3.
