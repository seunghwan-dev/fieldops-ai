# Experimental Report: Material X Kneading Trials

**Report No.**: EXP-2024-MX-003  
**Date**: 2024-10-15  
**Author**: S. Park, Process Engineering Team  
**Classification**: Internal Use Only  
**Equipment**: Sigma-blade kneader SK-5L (5-liter capacity)

---

## 1. Objective

Determine the operational envelope for Material X kneading by systematically varying RPM and jacket temperature. Identify safe processing conditions and document failure modes for future process design reference.

---

## 2. Equipment

- **Kneader**: SK-5L sigma-blade kneader, 5-liter working volume
- **Blade type**: Sigma blade, counter-rotating
- **Temperature control**: Jacketed vessel with circulating bath (±1°C accuracy)
- **Instrumentation**: Type-K thermocouple (discharge), digital RPM meter, torque sensor
- **Data acquisition**: 1 Hz sampling rate, logged to CSV

---

## 3. Procedure

1. Material X (batch MX-2024-07) was weighed to 70% fill ratio (3.5 L).
2. Jacket temperature was set to the target value and stabilized for 15 minutes.
3. Kneading was performed at the target RPM for 60 minutes.
4. Discharge temperature was recorded at the end of the mixing cycle.
5. Product quality was assessed by visual inspection and DSC spot check.
6. Quality criteria:
   - **Pass**: Discharge temp < 180°C, no discoloration, DSC onset within 5°C of baseline
   - **Marginal**: Discharge temp 180–200°C, slight discoloration acceptable
   - **FAIL**: Discharge temp > 200°C, visible discoloration, or DSC onset drop > 10°C

---

## 4. Results

**Table 4: Material X Kneading Trial Results**

| # | Material | RPM | Jacket(°C) | Discharge(°C) | Quality |
|---|----------|-----|-----------|---------------|---------|
| 1 | X | 30 | 25 | 68 | Pass |
| 2 | X | 60 | 25 | 112 | Pass |
| 3 | X | 90 | 25 | 158 | Pass |
| 4 | X | 90 | 100 | 182 | Marginal |
| 5 | X | 90 | 150 | 198 | FAIL |
| 6 | X | 120 | 25 | 175 | Marginal |
| 7 | X | 120 | 100 | 205 | FAIL |
| 8 | X | 120 | 150 | 228 | FAIL |

---

## 5. Observations

- Tests #1–#3 (jacket 25°C) show discharge temperature scales with RPM as expected. Even at 90 RPM, ambient jacket cooling is sufficient to maintain safe conditions.
- Test #4 (90 RPM, jacket 100°C) produced marginal results. Slight yellowing was observed at the discharge point, though DSC spot check showed onset within 5°C of baseline.
- Tests #5, #7, #8 exceeded thermal stability limit. Recommend max 180°C for Material X processing.
- Test #5 (90 RPM, jacket 150°C) reached 198°C — just below the as-received onset of 198°C. DSC spot check confirmed onset drop of 8°C.
- Test #7 (120 RPM, jacket 100°C) reached 205°C with visible brown discoloration. This test was terminated early at 45 minutes when the operator observed discoloration.
- Test #8 (120 RPM, jacket 150°C) reached 228°C. Significant decomposition odor was detected at approximately 40 minutes. Emergency cooldown was initiated. Post-test DSC showed onset depression of 22°C, confirming substantial thermal degradation.
- Temperature rise rate increases non-linearly with RPM at elevated jacket temperatures, suggesting viscous heating amplification effects.

---

## 6. Recommendations

1. **Maximum processing temperature for Material X: 180°C** regardless of RPM setting.
2. For RPM > 90, jacket temperature should not exceed 25°C to maintain safe discharge temperatures.
3. For RPM ≤ 60, jacket temperatures up to 100°C are acceptable but discharge temperature must be monitored continuously.
4. Install automated temperature interlock: trigger alarm at 170°C, initiate cooldown at 180°C.
5. Update standard operating procedure (SOP-MX-001) to reflect these findings.
6. Consider repeating Test #4 conditions (90 RPM, 100°C jacket) with extended monitoring to characterize the marginal zone more precisely.

---

## Appendix: Raw Data Access

Full time-series data for all 8 tests is archived in the process data server:  
`\\server\process_data\2024\MX-003\`

---

**Reviewed by**: Dr. J. Kim, Chief Process Engineer  
**Date**: 2024-10-18  
**Status**: Approved for distribution
