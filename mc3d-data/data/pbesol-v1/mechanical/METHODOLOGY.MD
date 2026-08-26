## Mechanical properties calculations

### Motivation

Superconductors play an important role in many modern technologies, with applications ranging from magnetic resonance imaging and maglev transportation to large-scale scientific infrastructure.Although many superconducting materials have been discovered, superconductors with high critical temperatures remain relatively rare and often face practical limitations, such as challenging synthesis conditions or instability at ambient pressure.

The theoretical understanding of high-temperature superconductivity remains an active area of research. For conventional phonon-mediated superconductors, electron-phonon interactions are central to determining their superconducting properties. The Materials Cloud Three-Dimensional Crystal Structure Database (MC3D), which contains a large collection of experimentally synthesized inorganic materials, therefore provides a natural starting point for systematic and high-accuracy electron-phonon calculations on experimentally known compounds.

This dataset extends the MC3D PBEsol-v1 dataset. The computational methodology used here differs in some aspects from that of the base dataset; full computational details are provided in the associated publication.

### mechanical database

This dataset contains the results of a high-throughput computational search for novel phonon-mediated superconductors, starting from the experimentally known inorganic stoichiometric compounds available in MC3D.




### mechanical details
We computed stress tensor $\sigma$ and the strain tensor $\varepsilon$ based on the generalized Hooke's law. 
Using Voigt notation, they are defined as:

$$
\begin{align}
	\sigma_{i} &= \sum_j C_{ij} \varepsilon_{j},
\end{align}
$$

From the elastic constants, the Voigt-Reuss-Hill~(VRH) average of the bulk and shear modulus are given by

$$
\begin{align}
    9B^{\rm V} =& C_{11} + C_{22} + C_{33} + 2(C_{12}+ C_{13} + C_{23})\\
    15 G^{\rm V} =& C_{11} + C_{22} + C_{33} - (C_{12}+ C_{13} + C_{23}) \nonumber \\
                  & + 3(C_{44}+ C_{55} + C_{66}) \\ 
    (B^{\rm R})^{-1} =& S_{11}+S_{22}+S_{33}+2(S_{12}+S_{13}+S_{23}) \\
    15(G^{\rm R})^{-1} =& 4(S_{11} + S_{22} + S_{33}) - 4(S_{12}+ S_{13} + S_{23}) \nonumber \\
                  & + 3(S_{44}+ S_{55} + S_{66}),
\end{align}
$$