# Skinfold protocols and population limits

The UI distinguishes adipometer equations from bioimpedance reports. No InBody algorithm or reference range is reproduced from a sample patient's measurements.

- **Jackson–Pollock, men (1978):** original development/cross-validation samples aged 18–61; DOI [10.1079/BJN19780152](https://doi.org/10.1079/BJN19780152). Existing 3- and 7-site equations are retained within their age/sex domain.
- **Jackson–Pollock–Ward, women (1980):** sample aged 18–55; DOI [10.1249/00005768-198023000-00009](https://doi.org/10.1249/00005768-198023000-00009). The publication notes particular care above age 40.
- **Durnin–Womersley (1974):** 481 men/women aged 16–72; DOI [10.1079/BJN19740060](https://doi.org/10.1079/BJN19740060). Uses bicipital, triceps, subscapular and suprailiac, density = a − b log10(sum) and Siri fat% = 495 / density − 450. Includes ages 60–72, but is not a dedicated validation for frail elderly people.
- **Carter–Yuhasz:** athlete/trained population guidance; triceps, subscapular, suprailiac, abdominal, thigh and medial calf. Existing coefficients are retained: women 4.56 + .143 sum, men 3.64 + .097 sum. The app does not automatically apply it to children or elderly people. Reference: J. E. L. Carter (ed.), Physical Structure of Olympic Athletes, Part I (1982).
- **Registration without estimation:** retains site measurements and a count/sum of recorded positive sites, without predicting fat. Comparing sums requires the same sites.
- **Legacy yuhasz6:** previous chest-site configuration and its stored values remain available for consultation. It is not offered for new records; changing to Carter–Yuhasz requires an actual calf measurement. A chest reading is never reassigned to calf.

Durnin–Womersley coefficient pairs (a,b), in age bands 16–19, 20–29, 30–39, 40–49, 50–72:

| Sex | 16–19 | 20–29 | 30–39 | 40–49 | 50–72 |
| --- | --- | --- | --- | --- | --- |
| M | 1.1620, .0630 | 1.1631, .0632 | 1.1422, .0544 | 1.1620, .0700 | 1.1715, .0779 |
| F | 1.1549, .0678 | 1.1599, .0717 | 1.1423, .0632 | 1.1333, .0612 | 1.1339, .0645 |

Missing age is not replaced with an assumed age for the current protocols. Out-of-domain estimates remain unavailable while raw measurements stay saved. Device water measurements are not populated from a skinfold-derived fat-free mass estimate: litres, kilograms and percentage have different units.

Related composition measurements share a visual group, with independent checkboxes for each unit/source. Selected related measurements are stacked in the editor and adjacent in the PDF. Original base fields remain the default; selecting or hiding an additional unit does not convert, delete or overwrite historical values. Legacy unit preferences remain stored but no longer hide another selected measurement.
