# Experimental Report: Material Y Jet Mill Grinding

**Report No.**: EXP-2024-MY-007
**Date**: 2024-11-20
**Author**: H. Tanaka, Particle Engineering Team
**Classification**: Internal Use Only
**Equipment**: Jet mill JM-200 (200 mm grinding chamber)

---

## 1. Objective

Establish particle size reduction parameters for Material Y using jet mill grinding. Determine the relationship between grinding pressure, classifier RPM, and resulting particle size distribution (D50). Identify optimal conditions for target D50 of 5–10 μm.

---

## 2. Equipment

- **Jet mill**: JM-200, 200 mm diameter grinding chamber, pancake type
- **Grinding gas**: Compressed nitrogen (99.9% purity, oil-free)
- **Classifier**: Integrated dynamic air classifier, variable speed 5,000–15,000 RPM
- **Feed system**: Vibratory feeder with gravimetric control (±2% accuracy)
- **Particle size analysis**: Malvern Mastersizer 3000, wet dispersion method
- **Air flow control**: Mass flow controller, range 5–20 m³/min

---

## 3. Procedure

1. Material Y (batch MY-2024-11, D50 = 85 μm as-received) was pre-sieved through 200 μm mesh.
2. Jet mill was purged with nitrogen for 10 minutes before operation.
3. Feed rate, grinding pressure, classifier RPM, and air flow were set according to test plan.
4. System was allowed to reach steady state (15 minutes) before sample collection.
5. Three samples were collected at 5-minute intervals and analyzed for particle size.
6. Quality criteria:
   - **Pass**: D50 within ±15% of target, span < 2.0, no amorphization detected by XRD
   - **FAIL**: D50 outside specification, span > 2.5, or amorphization observed

---

## 4. Results

**Table 5: Material Y Jet Mill Grinding Results**

| Test # | Material | Feed Rate (kg/h) | Grinding Pressure (MPa) | Classifier RPM | Air Flow (m³/min) | D50 (μm) | Quality |
|--------|----------|-------------------|--------------------------|----------------|---------------------|-----------|---------|
| 1 | Y | 10 | 0.6 | 10000 | 10 | 8.2 | Pass |
| 2 | Y | 20 | 0.6 | 10000 | 10 | 12.5 | Pass |
| 3 | Y | 10 | 0.9 | 12000 | 15 | 4.1 | Pass |
| 4 | Y | 30 | 0.4 | 8000 | 8 | 22.8 | Pass |
| 5 | Y | 10 | 1.1 | 15000 | 18 | 2.3 | FAIL |

---

## 5. Observations

- Test #1 produced the ideal particle size within the target range of 5–10 μm. Particle morphology under SEM showed clean fracture surfaces with minimal fines.
- Test #2 demonstrated the effect of increased feed rate: D50 increased by 52% due to reduced grinding energy per particle. Increasing feed rate beyond 20 kg/h at these conditions is not recommended for the target size range.
- Test #3 achieved finer grinding through higher pressure and classifier speed. The D50 of 4.1 μm is below the target range but may be acceptable for specialized applications.
- Test #4 with low pressure and low classifier RPM produced coarse particles (D50 = 22.8 μm), confirming that both grinding pressure and classifier speed are critical parameters.
- Test #5 used aggressive conditions (1.1 MPa, 15000 RPM). While D50 of 2.3 μm was achieved, XRD analysis revealed partial amorphization (estimated 12% amorphous content). This level of structural modification is unacceptable for Material Y applications. Grinding pressure above 1.0 MPa should be avoided.
- No significant temperature rise was observed in any test, confirming that jet milling is inherently temperature-safe for Material Y due to the Joule-Thomson cooling effect of expanding gas.

---

## 6. Recommendations

1. **Optimal conditions for D50 = 5–10 μm**: Feed rate 10–15 kg/h, grinding pressure 0.6 MPa, classifier 10,000 RPM, air flow 10 m³/min.
2. **Maximum grinding pressure: 1.0 MPa** for Material Y to avoid amorphization.
3. Feed rate should not exceed 20 kg/h at 0.6 MPa to maintain target particle size.
4. Higher classifier RPM (>12,000) can compensate for increased feed rate but increases energy cost.
5. XRD spot check should be performed when operating above 0.8 MPa grinding pressure.
6. Scale-up factor from JM-200 to production JM-500 is approximately 3.5x on throughput basis — verify with pilot trials.

---

**Reviewed by**: Dr. R. Patel, Head of Particle Engineering
**Date**: 2024-11-25
**Status**: Approved for distribution
