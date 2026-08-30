# Potential Fishing Zone (PFZ) Guide

## What is a PFZ?

A Potential Fishing Zone (PFZ) is an area in the ocean identified by satellite remote sensing as having a high likelihood of fish aggregation. PFZ advisories are issued by INCOIS (Indian National Centre for Ocean Information Services) based on analysis of:

- **Sea Surface Temperature (SST):** Fish tend to aggregate along temperature fronts — boundaries where warm and cold water meet.
- **Chlorophyll Concentration:** High chlorophyll indicates phytoplankton blooms, which attract small fish, which in turn attract larger commercial species.
- **Ocean Color Data:** Satellite sensors like Oceansat-3 and Sentinel-3 detect variations in ocean color that correlate with biological productivity.

## How PFZ Advisories Are Generated

1. ISRO satellites (Oceansat-3, INSAT-3D) capture ocean color and SST data.
2. INCOIS scientists analyze the satellite imagery to identify temperature fronts and chlorophyll concentration patterns.
3. Areas with favorable conditions for fish aggregation are marked as PFZ.
4. Advisories are disseminated via the INCOIS website, mobile apps, and electronic display boards at fishing harbors.

## How to Interpret PFZ Data

- **PFZ is NOT a guarantee of fish.** It indicates where fish are LIKELY to be based on ocean conditions.
- **PFZ validity is typically 24-48 hours.** Ocean conditions change rapidly.
- **Multiple PFZ areas may be issued.** Fishers should consider the closest PFZ to minimize fuel consumption and transit time.
- **PFZ advisories are not issued during cloud cover.** Satellite sensors cannot see through clouds.

## PFZ and ORCA

ORCA uses PFZ data as one input to the Marine Intelligence Agent. When a fisher requests a trip to "the best fishing spot" or "the recommended PFZ," ORCA:

1. Retrieves the latest PFZ advisory from INCOIS/MOSDAC.
2. Identifies the PFZ closest to the fisher's origin.
3. Incorporates PFZ coordinates into the trajectory calculation.
4. Evaluates weather and safety conditions along the route to the PFZ.

## Sources

- INCOIS PFZ Advisory Service: https://incois.gov.in/MarineFisheries/PfzWebGis
- MOSDAC (ISRO): https://mosdac.gov.in
- SATCATCH PFZ API: https://satcatch.com/data/api
