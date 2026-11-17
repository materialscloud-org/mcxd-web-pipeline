# Two-dimensional altermagnetism calculations

## Motivation

Altermagnets combine compensated magnetic order with momentum-dependent spin splitting. These properties offer opportunities for controlling spin-dependent electronic transport without a macroscopic magnetization. Identifying two-dimensional altermagnets is particularly relevant for thin-film devices and van der Waals heterostructures.

The Materials Cloud 2D Crystals (MC2D) database provides a starting point for discovering such materials among monolayers derived from experimentally known three-dimensional compounds. This study combines symmetry-guided screening with first-principles electronic-structure calculations and self-consistent Hubbard corrections.[^1]

## 2D altermagnets dataset

The screening starts from 2,710 MC2D monolayers. Chemical, symmetry and exfoliation criteria reduce this set to 79 candidates for magnetic calculations. Scanning magnetic configurations and Hubbard U values identifies 42 materials satisfying the screening criteria for at least one U value. Subsequent refinement uses Hubbard parameters calculated from first principles, structural relaxation and reassessment of magnetic order. The revised study and this contribution contain **23 materials**. Mn₄SnS₄ is discussed separately in the manuscript: its AFM state lies 4 meV/atom (9 meV/magnetic atom) below its AM state, outside the 1 meV/atom screening tolerance, so it is excluded from this contribution.

The dataset reports self-consistent Hubbard U values, spin splittings, electronic band gaps, magnetic energy differences and the sampled U values for which altermagnetism was identified. AiiDA workflow references provide links to calculation provenance.

## Symmetry-guided screening

Materials containing potentially magnetic elements are retained, followed by those in which at least one magnetic species has an even number of atoms. Opposite-spin sublattices must be connected by a crystal symmetry compatible with compensated altermagnetic order. Connections through inversion, lattice translation, a twofold rotation about the layer normal, or reflection in the layer plane are excluded because the associated spin symmetries enforce spin degeneracy throughout the two-dimensional Brillouin zone.

Easily exfoliable compounds are selected using binding-energy thresholds of 30 meV/Å² for DF2-C09 or 35 meV/Å² for rVV10. The final chemical selection focuses on V, Cr, Mn, Fe, Co, Ni, Cu, Ru and Re, as listed in the study's workflow diagram.

The automated AiiDA workflow performs the following steps:

1. Generate symmetry-compatible compensated magnetic configurations.
2. Calculate these configurations and a ferromagnetic configuration at U = 0, 2, 4, 6 and 8 eV, using fractional starting magnetizations of 0.1 and 0.5.
3. Identify altermagnetic candidates using magnetic, electronic and energetic criteria.

Further refinement process includes: 

1. Determine self-consistent Hubbard parameters using density-functional perturbation theory (DFPT).
2. Reevaluate magnetic configurations, relax the selected structures and calculate their electronic properties.

## Electronic-structure calculation details

Calculations use Quantum ESPRESSO with the Perdew–Burke–Ernzerhof (PBE) exchange-correlation functional and pseudopotentials from the Standard Solid-State Pseudopotentials (SSSP) library.[^2][^3] Wavefunction and charge-density cutoffs are selected from the SSSP recommendations, using the maximum recommended value among the constituent elements.

The AiiDA PW WorkChain moderate protocol selects the smallest k-point mesh consistent with a reciprocal-space sampling density of 0.15 Å⁻¹. A two-dimensional Coulomb cutoff suppresses interactions between periodic replicas. The initial U scans use Methfessel–Paxton smearing, while the subsequent self-consistent-U and refined calculations use Marzari–Vanderbilt cold smearing.

Hubbard parameters for transition-metal d orbitals are calculated using DFPT in Quantum ESPRESSO.[^4][^5] The automated AiiDA Hubbard workflow uses its balanced protocol.[^6] Where manual iteration is required, successive DFPT calculations are continued until the change in U is less than 0.1 eV. Magnetic states are reassessed at the resulting U values, followed by structural relaxation and reevaluation of the selected altermagnetic configurations.

## Altermagnetic screening criteria

A candidate must satisfy the following conditions at a sampled U value:

| Quantity | Criterion |
| --- | --- |
| Absolute magnetization | Greater than 0.1 μB per cell |
| Net magnetization magnitude | Less than 0.01 μB per cell |
| Maximum spin splitting | Greater than 5 meV |
| Maximum spin splitting at Γ | Less than 5 meV |
| Energy above the lowest-energy configuration considered at the same U | Less than 1 meV per atom |

These numerical criteria are used together with the symmetry analysis. The energetic reference is the lowest-energy state among the configurations examined. The tolerance is normalized per atom, whereas the reported magnetic-energy difference is normalized per magnetic atom.

## Definitions of the reported quantities

- **Maximum spin splitting:** the largest separation between spin-up and spin-down bands across the full two-dimensional Brillouin zone, considering all electronic states included in the calculation irrespective of occupation. It is reported in meV and is not restricted to a high-symmetry path.
- **Maximum spin splitting near the Fermi level:** the largest splitting associated with the highest occupied states in insulators or partially occupied states in metals. For insulators, the energy reference is the valence-band maximum. This quantity is reported in meV.
- **Band gap:** the electronic band gap from the refined DFT+U calculation at the corresponding self-consistent U, reported in eV.
- **Magnetic energy difference:** the reported energy difference between the altermagnetic configuration and the lowest-energy competing non-altermagnetic magnetic state, evaluated at the corresponding unrelaxed structure and normalized per magnetic atom. The convention is ΔE = (E_NAM,min − E_AM)/N_mag: positive values favor the altermagnetic state and negative values favor the competing NAM state among the collinear configurations considered. Zero values indicate equality at the reported precision.
- **AM for U values:** the discrete sampled Hubbard U values at which the screening identifies altermagnetism. These values do not define a continuous interval.

## References and further reading

[^1]: A. Bose, N. Manko, M. Gibertini and A. Marrazzo, *Symmetry-Guided Computational Screening of Two-Dimensional Altermagnets with ab initio Hubbard Corrections*, [arXiv:2608.02925v1](https://arxiv.org/abs/2608.02925v1) (2026). This is the supplied preprint reference; the contribution contains the author-confirmed revised set of 23 materials.
[^2]: J. P. Perdew, K. Burke and M. Ernzerhof, *Generalized gradient approximation made simple*, Physical Review Letters **77**, 3865 (1996).
[^3]: G. Prandini, A. Marrazzo, I. E. Castelli, N. Mounet and N. Marzari, *Precision and efficiency in solid-state pseudopotential calculations*, npj Computational Materials **4**, 72 (2018). [https://doi.org/10.1038/s41524-018-0127-2](https://doi.org/10.1038/s41524-018-0127-2).
[^4]: I. Timrov, N. Marzari and M. Cococcioni, *Hubbard parameters from density-functional perturbation theory*, Physical Review B **98**, 085127 (2018).
[^5]: I. Timrov, N. Marzari and M. Cococcioni, *HP—a code for the calculation of Hubbard parameters using density-functional perturbation theory*, Computer Physics Communications **279**, 108455 (2022).
[^6]: L. Bastonero, C. Malica, E. Macke, M. Bercx, S. Huber, I. Timrov and N. Marzari, *First-principles Hubbard parameters with automated and reproducible workflows*, npj Computational Materials **11**, 183 (2025).
