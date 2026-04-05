# Characterization of Mixing Performance in Sigma-Blade Kneaders

**Authors**: T. Nakamura, A. Kowalski, R. Patel  
**Affiliation**: Department of Chemical Engineering, Tokyo Institute of Technology  
**Received**: 2024-05-20 | **Accepted**: 2024-09-10 | **Published**: 2024-12-01  
**DOI**: 10.1002/aic.2024.18134

---

## Abstract

The mixing performance of three blade configurations — sigma blade, Z-type blade, and dispersive blade — was evaluated in a 10-liter laboratory kneader operating at 30–120 RPM. Mixing uniformity, power draw, and temperature rise were measured for each configuration using a model paste system. The sigma blade achieved the highest mixing uniformity (94%) at moderate power consumption, while the dispersive blade produced the highest shear rates but with significant temperature rise. Results provide quantitative blade selection guidelines for processing thermally sensitive materials in industrial kneaders.

**Keywords**: sigma blade, Z-type blade, dispersive blade, mixing uniformity, kneader, blade selection

---

## 1. Introduction

Sigma-blade kneaders are essential equipment in industries processing high-viscosity materials, including adhesives, rubber compounds, pharmaceutical pastes, and energetic formulations. The blade geometry directly influences mixing efficiency, shear rate distribution, power consumption, and heat generation within the mixing chamber [1].

Three common blade designs are used in industrial practice: the sigma (or "S") blade, the Z-type blade, and the dispersive (or "D") blade. Each geometry produces distinct flow patterns and shear rate distributions, making blade selection a critical process design decision. Despite the industrial importance of this choice, systematic comparative studies under controlled conditions remain scarce in the open literature.

The sigma blade features a double-arm design that folds and refolds the material, providing excellent distributive mixing. The Z-type blade generates higher axial flow and is preferred for materials requiring end-to-end transport within the chamber. The dispersive blade creates intense localized shear zones, effective for breaking agglomerates but at the cost of higher energy input and temperature rise [2].

This study presents a systematic comparison of all three blade types in the same kneader body, eliminating equipment-to-equipment variability and providing direct performance comparisons.

---

## 2. Methods

### 2.1 Equipment

A 10-liter double-arm kneader (Model DK-10, Jaygo Inc.) equipped with interchangeable blade sets was used. The vessel was jacketed and connected to a circulating bath at 25°C. Blade rotational speeds of 30, 60, 90, and 120 RPM were evaluated.

### 2.2 Model Material

A standardized paste system consisting of 70 wt% calcium carbonate in a silicone oil matrix (viscosity 10,000 cP at 25°C) was used. This system provides consistent rheological properties and allows tracer-based uniformity measurements without safety concerns.

### 2.3 Measurements

- **Mixing uniformity**: Measured by coefficient of variation (CoV) of tracer concentration at 8 sampling points after 30 minutes of mixing. Uniformity = (1 - CoV) × 100%.
- **Power draw**: Measured via torque sensor on the drive shaft, averaged over the final 10 minutes of mixing.
- **Temperature rise**: Recorded as the rate of bulk temperature increase (°C/min) during the first 15 minutes of mixing at each RPM.

---

## 3. Results

### 3.1 Blade Performance Comparison

Table 3 summarizes the performance metrics for each blade type at the optimal RPM (60 RPM for sigma and Z-type, 90 RPM for dispersive).

**Table 3: Blade Type vs Mixing Performance Comparison**

| Blade Type | Mixing Uniformity (%) | Power Draw (kW) | Temp Rise (°C/min) | Recommended Use |
|------------|----------------------|-----------------|--------------------|--------------------|
| Sigma | 94 | 2.1 | 0.8 | General-purpose, thermally sensitive materials |
| Z-type | 87 | 1.8 | 0.5 | Low-viscosity pastes, axial transport required |
| Dispersive | 91 | 3.4 | 1.6 | Agglomerate breakup, deagglomeration |

The sigma blade achieves the highest uniformity at moderate power input. The dispersive blade approaches similar uniformity but at 62% higher power consumption and double the temperature rise rate. The Z-type blade shows the lowest power consumption and temperature rise but delivers inferior uniformity for high-viscosity systems.

### 3.2 RPM Effects

See Figure 2 for RPM vs discharge temperature curves for different blade types.

Across all blade types, mixing uniformity improves with increasing RPM up to an optimal point, beyond which further increases provide diminishing returns while disproportionately increasing temperature rise. For the sigma blade, the optimal RPM was found to be 60 RPM, achieving 94% uniformity. At 120 RPM, uniformity increased only marginally to 96% while power draw increased by 85%.

Temperature rise rate scales approximately linearly with RPM for all blade types, with the dispersive blade showing the steepest relationship (1.6°C/min at 90 RPM vs. 0.8°C/min for the sigma blade at the same speed).

---

## 4. Discussion

The results confirm that blade selection must balance mixing quality against thermal constraints. For thermally sensitive materials such as energetic compounds, the sigma blade offers the best compromise: near-optimal uniformity with controlled temperature rise.

The dispersive blade should be reserved for applications where agglomerate breakup is the primary objective and where the material can tolerate the associated temperature increase. For processing Material X (decomposition onset as low as 176°C at high RPM, as reported by Kim et al. [3]), the dispersive blade's temperature rise rate of 1.6°C/min would reach potentially dangerous temperatures within 90 minutes at 120 RPM starting from ambient conditions, whereas the sigma blade's 0.8°C/min rate provides substantially more operational headroom.

The Z-type blade's lower uniformity for high-viscosity systems is attributed to reduced radial mixing and less intensive fold-and-refold action compared to the sigma blade. However, its low power consumption and minimal temperature rise make it suitable for pre-blending or initial incorporation steps before final mixing with a sigma blade.

A staged mixing approach — Z-type blade for initial incorporation at high RPM, followed by sigma blade at moderate RPM for final homogenization — may offer both efficiency and thermal safety advantages for sensitive formulations.

---

## 5. Conclusion

1. The sigma blade provides the best overall performance for high-viscosity paste mixing, achieving 94% uniformity at moderate power consumption and temperature rise.
2. Blade selection should be based on the thermal sensitivity of the processed material, with the sigma blade preferred for heat-sensitive applications.
3. Operating beyond the optimal RPM yields diminishing uniformity gains while significantly increasing power draw and thermal load.
4. A staged mixing protocol using different blade types may optimize both efficiency and safety.

---

## References

[1] Paul, E. L., Atiemo-Obeng, V., & Kresta, S. M. (2004). *Handbook of Industrial Mixing*. John Wiley & Sons.

[2] Cheng, H., & Manas-Zloczower, I. (2018). "Distributive mixing in sigma-blade kneaders: DEM simulation and experimental validation." *Powder Technology*, 338, 601–612.

[3] Kim, J., Park, S., & Lee, M. (2025). "Thermal stability analysis of Material X in high-shear mixing processes." *Journal of Materials Processing Technology*, 315, 117902.

[4] Connelly, R. K., & Kokini, J. L. (2007). "Examination of the mixing ability of single and twin screw mixers using 2D finite element method simulation with particle tracking." *Journal of Food Engineering*, 79(3), 956–969.

[5] Vyakaranam, K. V., Ashokan, B. K., & Kokini, J. L. (2012). "Evaluation of effect of paddle element stagger angle on the local velocity profiles in a twin-screw continuous mixer." *Journal of Food Engineering*, 108(4), 585–599.
