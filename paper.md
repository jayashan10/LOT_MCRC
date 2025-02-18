---
title: "Defining Treatment Regimens and Lines of Therapy Using Real-World Data in Oncology"
authors:
- Lisa M Hess
- Xiaohong Li
- Yixun Wu
- Robert J Goodloe
- Zhanglin Lin Cui
journal: "Future Oncology"
volume: 17
issue: 15
pages: 1865-1877
year: 2021
doi: "10.2217/fon-2020-1041"
url: "https://doi.org/10.2217/fon-2020-1041"
issn: "(Print) (Online)"
journal_homepage: "www.tandfonline.com/journals/ifon20"
citation: "Lisa M Hess, Xiaohong Li, Yixun Wu, Robert J Goodloe & Zhanglin Lin Cui (2021) Defining Treatment Regimens and Lines of Therapy Using Real-World Data in Oncology, Future Oncology, 17:15, 1865-1877, DOI: 10.2217/fon-2020-1041"

abstract: |
  Retrospective observational research relies on databases that do not routinely record lines of therapy or reasons for treatment change. Standardized approaches to estimate lines of therapy were developed and evaluated in this study. A number of rules were developed, assumptions varied and macros developed to apply to large datasets. Results were investigated in an iterative process to refine line of therapy algorithms in three different cancers (lung, colorectal and gastric). Three primary factors were evaluated and included in the estimation of lines of therapy in oncology: defining a treatment regimen, addition/removal of drugs and gap periods. Algorithms and associated Statistical Analysis Software (SAS®) macros for line of therapy identification are provided to facilitate and standardize the use of real-world databases for oncology research.

lay_abstract: |
  Most, if not all, real-world healthcare databases do not contain data explaining treatment changes, requiring that rules be applied to estimate when treatment changes may reflect advancement of underlying disease. This study investigated three tumor types (lung, colorectal and gastric cancer) to develop and provide rules that researchers can apply to real-world databases. The resulting algorithms and associated SAS® macros from this work are provided for use in the Supplementary data.

first_draft_submitted: "13 October 2020"
accepted_for_publication: "22 January 2021"
published_online: "25 Feb 2021"
article_views: 12204
citing_articles: 11

keywords:
- administrative claims
- colorectal cancer
- electronic medical records
- gastric cancer
- line of therapy
- lung cancer
- retrospective research
- SAS macro

---

## Introduction

Cancer is a global public health problem leading to an estimated over 17.2 million new cases diagnosed and 8.9 million deaths each year [1].  Among patients whose disease has become metastatic, cure is rarely possible.  Treatment guidelines define lines of therapy.  The sequence or 'line of therapy' is the cornerstone of planning systemic therapy. Electronic data for billing/reimbursement (administrative claims) and clinical care (EMRs) are available.  These don't specify treatment regimen or line of therapy. Researchers must evaluate the data. Rules used by researchers are rarely transparent and are likely inconsistent.

Retrospective database studies operationalized by defining the first line as drugs used after advanced/metastatic diagnosis. This first step is dependent on the correct identification of an advanced/metastatic cohort. Subsequent lines are more difficult, must evaluate order and timing of drugs. Some studies limit the cohort.

Rules can be applied, but specific treatment strategies must be considered. e.g., maintenance therapy, drug holidays, biologic agents. Details of the rules are often lacking [10,11]. Replication is not possible.  Detailed rules provided have been focused [12-15]. Consistencies: time period, addition/discontinuation, treatment interruptions. Tumor agnostic rules developed only from melanoma and NSCLC in [15].

This work provides standardization. Primary goal: provide SAS macros.  Allow for more transparent assumptions.  Macros applied to claims or EMR.

## Materials & Methods

### Tumor Types

Three tumor types: NSCLC, CRC, and gastric cancer. NSCLC is complex. CRC is slower growing. Gastric cancer is aggressive.  Rules have been developed and applied [4, 21-26].  Rules developed through guidelines and clinical experts.

### Systemic Therapy

All systemic anticancer drugs were included. Surgical/radiation therapies were not. Chemotherapy or targeted/biologic. Consideration of interchangeable drugs.

Drug interchangeability evaluated.  5-FU and capecitabine (fluoropyrimidines). Cisplatin and carboplatin (platinum agents). Dates for each drug. Supportive care drugs not considered.

### Regimen Definition

Regimen: single drug or set of drugs within initial 28-day period. Based on cycle length in labels. Regimen name updated if biologic/targeted added. Maintenance: agent included in regimen.

### Starting a Line of Therapy

First line: date of first drug within initial 28-day period. New line: first date of subsequent drug.

### Stopping a Line of Therapy

Discontinuation rules differed by tumor type.  Consistent factors: time to progression, adverse events, drug holidays.  Stopping rule: gap period, new chemotherapy, new biologic/targeted, complete change.  Discontinuation date: last day of drug.

### Testing & Revision

Stopping rules: gap periods (60, 90, 180 days); new biologic; new chemotherapy.  Specific considerations: maintenance (NSCLC), supplementation (CRC).  Applied to datasets, visually evaluated, inspected by oncologists.

## Results

The rules identified to develop the line of therapy macros are summarized in Tables 1–3, and the final SAS macros are presented in the Supplementary data. The macros include options as summarized in the tables, allowing investigator flexibility.

**Table 1. Line of therapy rules in oncology.**

| Rule                                                                                                 | Option A             | Option B          | Option C           | Option D                                                                     | Optimal rule and considerations                                                                                                            |
| :--------------------------------------------------------------------------------------------------- | :------------------- | :---------------- | :----------------- | :--------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| **Line therapy *changes* when:**                                                                      |                      |                   |                   |                                                                              |                                                                                                                                      |
| Patient has had no treatment for a gap of greater than ... and then restarts the same treatment      | 60 days              | 90 days           | 180 days          | The line of therapy never changes when this happens                             | NSCLC - option A, Gastric cancer - option B, CRC - option C                                                                            |
| Any biologic/targeted is added to a regimen greater than ... of the start of the line of therapy     | After initial 28-day period | 90 days           | 180 days          | The line of therapy never changes with adding a biologic                          | NSCLC - option D, Gastric cancer – option D, CRC - option C (except for panitumumab or cetuximab which follow option B)              |
| Any biologic/targeted agent is started with discontinuation of all agents in the initial regimen    | Upon initiation of biologic targeted agent |                   |                   |                                                                              | In general, the start of a new drug with discontinuation of all prior drugs indicates a new line of therapy                       |
| Adding one or more chemotherapy drugs in a regimen will constitute a change in line of therapy      | After initial 28-day period |                   |                   |                                                                              | In general, a new chemotherapy agent (with or without discontinuing all other agents) that is not considered to be interchangeable ... |
| **Line of therapy *does not change* when:**                                                              |                      |                   |                   |                                                                              |                                                                                                                                      |
| Any biologic/targeted agent is added to a regimen less than or equal to ... days of the start of therapy | 28 days           | 90 days          | 180 days          | The line of therapy never changes with adding a biologic                          | NSCLC - option D, Gastric cancer - option D, CRC - option C (except for panitumumab or cetuximab which follow option B)            |
| Exchange of cisplatin or carboplatin (these agents are considered equivalent)                       | Never changes line of therapy |                   |                   |                                                                              | Any interchangeable agent should never change a line of therapy. ... platinums are provided as they apply to all three tumor types    |
| Exchange of 5-fluorouracil or capecitabine (these agents are considered equivalent)                  | Never changes line of therapy |                   |                   |                                                                              | Any interchangeable agent should never change a line of therapy. ... Fluoropyrimidines are provided as they are used in both CRC and GC |

**Table 2. Additional considerations for maintenance therapy (example is specific to non-small cell lung cancer).**

| Rule                                                                                                                     | Option A                  | Option B | Option C | Option D | Optimal rule and considerations                                                                                                                                                                |
| :----------------------------------------------------------------------------------------------------------------------- | :------------------------ | :------- | :------- | :------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Line of therapy *changes* when:**                                                                                       |                           |          |          |          |                                                                                                                                                                                           |
| Patient receiving a first-line regimen containing pemetrexed ... and reinitiates single-agent pemetrexed or ... therapy   | Never changes line of therapy | 60 days  | 90 days  | 180 days | NSCLC - option C. For other cancers ... 'pemetrexed' and 'bevacizumab' may be replaced by maintenance drugs used in the specific cancer type                                               |
| Patient receiving a first-line regimen containing bevacizumab ... and reinitiates single-agent bevacizumab or ... therapy | Never changes line of therapy | 60 days  | 90 days  | 180 days | NSCLC - option C.  For other cancers ... 'pemetrexed' and 'bevacizumab' may be replaced by maintenance drugs used in the specific cancer type                                               |
| **Line of therapy *does not change* when:**                                                                                |                           |          |          |          |                                                                                                                                                                                           |
| Patient receiving a first-line regimen containing pemetrexed ... *less than or equal to* ... and reinitiates ... therapy    | Never changes line of therapy | 60 days  | 90 days  | 180 days | NSCLC - option C. For other cancers ... 'pemetrexed' and 'bevacizumab' may be replaced by maintenance drugs used in the specific cancer type                                               |
| Patient receiving a first-line regimen containing bevacizumab ... *less than or equal to* ... and reinitiates ... therapy | Never changes line of therapy | 60 days  | 90 days  | 180 days | NSCLC - option C. For other cancers ... 'pemetrexed' and 'bevacizumab' may be replaced by maintenance drugs used in the specific cancer type                                               |

**Table 3. Additional considerations for diseases where drug supplementation is not uncommon (example is specific to colorectal cancer).**

| Rule                                                                                                                                                           | Option A                  | Option B | Option C | Option D                                                      | Optimal rule and considerations                                                                                                         |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------ | :------- | :------- | :------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------- |
| **Line of therapy *changes* when:**                                                                                                                            |                           |          |          |                                                               |                                                                                                                                     |
| Any biologic/targeted (except cetuximab or panitumumab) is added to a regimen greater than ... of the start of the line of therapy                               | After initial 28-day period | 90 days  | 180 days | The line of therapy never changes with adding a biologic     | CRC - option C. ... consider replacing 'cetuximab' and 'panitumumab' with other drugs that are used in this manner                      |
| Cetuximab or panitumumab is added to a regimen greater than ... of the start of the line of therapy                                                             | 60 days                   | 90 days  | 180 days | The line of therapy never changes with adding a biologic     | CRC - option B. ... consider replacing 'cetuximab' and 'panitumumab' with other drugs that are used in this manner                      |
| A new chemotherapy drug is added to single-agent fluoropyrimidine ... greater than ... of the start of single-agent therapy                                       | 60 days                   | 90 days  | 180 days | The addition of these agents does not change a line of therapy | CRC - option A. For other cancers ... consider replacing 'fluoropyrimidine' with other drugs that are used in this manner                |
| Adding one or more chemotherapy drugs in a regimen will constitute a change ... except for drugs added to ... single-agent fluoropyrimidine ...                | After initial 28-day period |          |          |                                                               | CRC - option A. For other cancers ... consider replacing 'fluoropyrimidine' with other drugs that are used in this manner                |
| **Line of therapy *does not change* when:**                                                                                                                     |                           |          |          |                                                               |                                                                                                                                     |
| Any biologic/targeted agent (except cetuximab or panitumumub) is added to a regimen less than or equal to ... days of the start of therapy                    | 28 days                   | 90 days  | 180 days | The line of therapy never changes with adding a biologic     | CRC - option C. ... consider replacing 'cetuximab' and 'panitumumab' with other drugs that are used in this manner                      |
| Cetuximab or panitumumab is added to a regimen less than or equal to ... of the start of the line of therapy                                                    | 60 days                   | 90 days  | 180 days | The line of therapy never changes with adding a biologic     | CRC - option B.  ... consider replacing 'cetuximab' and 'panitumumab' with other drugs that are used in this manner                     |
| A new chemotherapy drug is added to single-agent fluoropyrimidine ... *less than or equal to* ... of the start of single-agent therapy                            | 60 days                   | 90 days  | 180 days | The addition of these agents does not change a line of therapy | CRC - option A.  ... consider replacing 'fluoropyrimidine' with other drugs that are used in this manner                               |
|A new chemotherapy drug is added to single-agent fluoropyrimidine ... *less than or equal*... | 60 Days | 90 Days | 180 days | The addition of these agents does not change a line of therapy. | CRC Option A. |

### Key Components of All Macros

Consistent across all tumor types (Table 1): starting new drug, gap periods, drug interchangeability.

New chemo after 28 days advances line.  Biologic/targeted agents frequently supplement. Changes to backbone.  60-day gap for NSCLC.  CRC: longer nonmedication periods, 180-day gap.

### Maintenance Therapy: NSCLC Macro

Table 2 summarizes the advancement rules for maintenance therapy, specifically for NSCLC.  Maintenance is part of clinical practice for NSCLC, and a "treat-to-progression" model applies.  If a patient receives a first-line regimen with agents suitable for maintenance (e.g., pemetrexed, bevacizumab), continuing those agents within a 90-day gap *does not* advance the line.  These maintenance rules *only* apply to the *first-line* setting.  Figure 1 provides a flowchart for the NSCLC macro.

### Drug Supplementation: CRC Macro

Table 3 addresses drug supplementation, which is more common in CRC.  Specific attention is given to the EGFR inhibitors cetuximab and panitumumab.  While other biologics can be added without advancing the line, adding these *later* likely indicates disease progression and *does* advance the line.  A 90-day window is allowed for adding these without advancement.  New chemotherapy drugs added to single-agent capecitabine or 5-fluorouracil within 60 days is considered supplementation and does not advance the line. Figure 2 shows the flowchart for the CRC macro.

### Base Case Conditions: Gastric Cancer Macro

The gastric cancer macro is potentially the most generalizable.  It assumes an aggressive disease with limited treatment options. After metastatic diagnosis, the first anticancer drug is identified, and the regimen is defined by drugs received within the initial 28-day period.  A gap of 90 days or longer advances the line.  Adding a biologic/targeted agent *does not* advance the line *unless* the original regimen is discontinued.  Figure 3 presents a flowchart for the gastric cancer macro.

## Discussion & Conclusion

Method to estimate lines of therapy. Macros in Supplementary data. Require: patient ID, drug names, dates.  Cohort development, identifying drug codes. Non-systemic therapies.  Investigate role of drugs. No single algorithm.

Useful in variety of research. Comparative effectiveness [27,28], real-world control cohort [29,30]. Treatment sequencing [31,32]. Improve standardization.

Initial regimen (28 days) constant.  New drug, type of drug, gap periods. Clinical expertise.

Assumptions: interchangeable drugs.  Research question.  Limitation: no gold standard.

Radiation not included. Macros must be reviewed.

## Future Perspective

EMR or healthcare delivery systems should include line of therapy.

## Summary Points
* Current databases do not contain sufficient fields to allow the identification of line of therapy, requiring rules.
* Each tumor site is unique
* Primary factors: treatment patterns, study cohort, how drugs are changed, typical time between lines of therapy.
* SAS Macros provided
* Guidelines on how to adapt macros.

## Supplementary Data

[Link to supplementary data]

## Author Contributions, Financial & Competing Interests Disclosure, Writing Assistance (provided in the original document)

## References
(Provided in original document, numbered 1-32, with notes on some key references)