#!/usr/bin/env python3
"""
Literature Repo Downloader v1.0
================================
Downloads all ~300 literature files from stevenbrandon88/literature-Gaps (GitHub).
Organises by stream into literature/raw/<stream>/ for direct use by the vector DB pipeline.

USAGE:
  python lit_repo_downloader.py --list                   # list all files by stream
  python lit_repo_downloader.py --all                    # download everything (~300 files)
  python lit_repo_downloader.py --stream s01             # download stream S01 only
  python lit_repo_downloader.py --stream synthesis       # stream synthesis .docx files
  python lit_repo_downloader.py --stream supervisor      # supervisor papers
  python lit_repo_downloader.py --stream admin           # awards/templates (no vectorise)
  python lit_repo_downloader.py --check                  # check what is already downloaded
  python lit_repo_downloader.py --file FILENAME          # download one specific file
  python lit_repo_downloader.py --pdfs-only              # PDFs only (skip .docx/.xlsx etc)
  python lit_repo_downloader.py --vectordb               # streams S01-S26 + synthesis only
                                                         # (excludes admin/supervisor/misc)

OUTPUT:
  Files saved to ./literature/raw/<stream>/ by default.
  Set env var LIT_DATA_DIR to override base directory.

VECTORDB PIPELINE:
  Run --vectordb first, then point 1_ingest_literature.py at ./literature/raw/
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from urllib.parse import quote

# ─── Repo config ──────────────────────────────────────────────────────────────
REPO_USER   = "stevenbrandon88"
REPO_NAME   = "literature-Gaps"
BRANCH      = "main"
RAW_BASE    = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/{BRANCH}"

# Output base dir — override with LIT_DATA_DIR env var
BASE = Path(os.environ.get("LIT_DATA_DIR", "./literature/raw"))

# ─── Stream metadata ──────────────────────────────────────────────────────────
STREAM_LABELS = {
    "s01":        "S01 — MDB Econometrics",
    "s02":        "S02 — Development Project Management",
    "s03":        "S03 — Project Preparation Quality",
    "s04":        "S04 — Principal-Agent / Disbursement",
    "s05":        "S05 — ADB IED Evaluation",
    "s06":        "S06 — IEG World Bank SLR",
    "s07":        "S07 — Political Economy of Aid",
    "s08":        "S08 — SIDS Climate Finance / GCF",
    "s09":        "S09 — Evaluation Bias / Halo Effects",
    "s10":        "S10 — Heterogeneous Treatment Effects",
    "s11":        "S11 — AidData / TUFF / Chinese Development Finance",
    "s12":        "S12 — Cross-Institutional Comparison",
    "s13":        "S13 — Credit Risk / Development Returns",
    "s14":        "S14 — Causal Identification in Development",
    "s15":        "S15 — Specification Robustness",
    "s16":        "S16 — RCT Evidence in Development",
    "s17":        "S17 — Fragile & Conflict-Affected States",
    "s18":        "S18 — SIDS Development Finance",
    "s19":        "S19 — Debt Sustainability / Collateralisation",
    "s20":        "S20 — Climate Finance Architecture",
    "s21":        "S21 — Climate Adaptation Finance",
    "s22":        "S22-26 — OCDI / Infrastructure Cost Overrun",
    "s26":        "S26 — Non-Linear Collapse Theory",
    "synthesis":  "Stream Synthesis Documents (.docx)",
    "supervisor": "Supervisor Papers (Cite 3; Do Not Cite 11)",
    "awards":     "Australia Awards / CUP Programme Materials",
    "templates":  "Policy Brief & Evaluation Templates",
    "misc":       "Miscellaneous / Other",
}

# Streams included in --vectordb mode (exclude admin, templates, misc, awards)
VECTORDB_STREAMS = {
    "s01","s02","s03","s04","s05","s06","s07","s08","s09","s10",
    "s11","s12","s13","s14","s15","s16","s17","s18","s19","s20",
    "s21","s22","s26","synthesis","supervisor"
}

# ─── File catalogue ───────────────────────────────────────────────────────────
# Format: (stream, remote_filename, description)
# All files live in repo root — remote_filename is used as local filename too.
# Filenames with spaces/special chars are URL-encoded automatically.

FILES = [

    # ════════════════════════════════════════════════════════════════════════════
    # STREAM SYNTHESIS DOCUMENTS
    # ════════════════════════════════════════════════════════════════════════════
    ("synthesis", "STREAM 01 - conclusion summary.docx",                        "S01 conclusion summary"),
    ("synthesis", "Stream 001 review of literature vs my project.docx",         "S01 literature vs project"),
    ("synthesis", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (1).docx", "S01 deep read (1)"),
    ("synthesis", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (2).docx", "S01 deep read (2)"),
    ("synthesis", "stream1 complete.docx",                                       "S01 complete"),
    ("synthesis", "Stream 1 summary and review.docx",                           "S01 summary and review"),
    ("synthesis", "stream 2 - development pm.docx",                             "S02 development PM"),
    ("synthesis", "Developmental PM - abstracts.docx",                          "S02 PM abstracts"),
    ("synthesis", "Stream 3 -- output summary.docx",                            "S03 output summary"),
    ("synthesis", "stream 4 - conclusion.docx",                                 "S04 conclusion"),
    ("synthesis", "principal agent - abstract.docx",                            "S04 principal-agent abstract"),
    ("synthesis", "MDB_Econometrics_Stream_Complete.docx",                      "S01 complete (MDB)"),
    ("synthesis", "adb_ied_stream_synthesis.docx",                              "S05 ADB IED synthesis"),
    ("synthesis", "WB_IEG_SLR_Output.docx",                                     "S06 IEG SLR output"),
    ("synthesis", "EvalBias_LiteratureStream_Brandon_2026.docx",                "S09 evaluation bias stream"),
    ("synthesis", "IEG SELF-EVALUATION SUMMARY.docx",                           "S09 IEG self-evaluation summary"),
    ("synthesis", "HTE_Stream_Synthesis.docx",                                  "S10 HTE synthesis"),
    ("synthesis", "AidData_TUFF_Stream_Coding.docx",                            "S11 AidData TUFF coding"),
    ("synthesis", "cross_institutional_coding.docx",                            "S13 cross-institutional coding"),
    ("synthesis", "FCS_Literature_Stream_Coding.docx",                          "S17 FCS stream coding"),
    ("synthesis", "SIDS_DevelopmentFinance_StreamCoding.docx",                  "S18 SIDS finance coding"),
    ("synthesis", "DebtSustainability_StreamCoding.docx",                       "S19 debt sustainability coding"),
    ("synthesis", "ClimateFinanceStream_SynthesisOutput.docx",                  "S20 climate finance synthesis"),
    ("synthesis", "CAF_Stream_Output.docx",                                     "S20/S21 climate adaptation output"),
    ("synthesis", "CDF_Stream_Output.docx",                                     "S20 concessional development finance"),
    ("synthesis", "ICO_Stream_Output.docx",                                     "S22 infrastructure cost overrun output"),
    ("synthesis", "Procurement_Architecture_Stream_Output.docx",                "S24 procurement output"),
    ("synthesis", "SLR_Political_Economy_Infrastructure_Approval.docx",         "S25 political economy SLR"),
    ("synthesis", "NCT_Stream_Synthesis_Output.docx",                           "S26 NCT synthesis"),
    ("synthesis", "RCF_Stream_Coding.docx",                                     "S23 reference class forecasting"),
    ("synthesis", "spec_robustness_stream.docx",                                "S15 specification robustness"),
    ("synthesis", "rct-evidence summary.docx",                                  "S16 RCT evidence summary"),
    ("synthesis", "systematic_lit_coding.docx",                                 "Master coding protocol"),
    ("synthesis", "Brandon_LitCoding_ProjectEval_Stream.docx",                  "Master coding protocol (Brandon)"),
    ("synthesis", "aid-projects-abstracts.docx",                                "S01/S02 abstracts"),
    ("synthesis", "The Asian Development Bank and Evaluation in Asia and the Pacific.docx", "S05 ADB evaluation"),
    ("synthesis", "Towards complete development finance data.docx",              "S11 development finance data"),
    ("synthesis", "Literature_Gap_Analysis.docx",                               "Gap synthesis"),
    ("synthesis", "LSR_Synthesis_Brandon2026.docx",                             "Master synthesis"),
    ("synthesis", "LSR_Synthesis_Tracker_Brandon2026.docx",                     "Master synthesis tracker"),
    ("synthesis", "LSR_21_Stream_Reference.docx",                               "Streams 01-21 reference"),
    ("synthesis", "LSR_Streams_22_26_OCDI_Brandon2026.docx",                    "Streams 22-26 reference"),
    ("synthesis", "Quality simmary.docx",                                       "S01/S09 quality summary"),

    # ════════════════════════════════════════════════════════════════════════════
    # S01 — MDB ECONOMETRICS
    # ════════════════════════════════════════════════════════════════════════════
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (1).pdf",  "S01 deep read (1)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (2).pdf",  "S01 deep read (2)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (3).pdf",  "S01 deep read (3)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (4).pdf",  "S01 deep read (4)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (5).pdf",  "S01 deep read (5)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (6).pdf",  "S01 deep read (6)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (7).pdf",  "S01 deep read (7)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (8).pdf",  "S01 deep read (8)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (9).pdf",  "S01 deep read (9)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (10).pdf", "S01 deep read (10)"),
    ("s01", "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (11).pdf", "S01 deep read (11)"),
    ("s01", "The Economic Journal - 2001 - Dollar - What Explains the Success or Failure of Structural Adjustment Programmes.pdf", "Dollar & Svensson 2001 — structural adjustment"),
    ("s01", "59wane.pdf",                           "Wane 2004 — IDA project performance [N119]"),
    ("s01", "Good_countries_or_good_projects_Macro_an.pdf",  "Macro vs project-level quality"),
    ("s01", "What0differenc0roject0performance00.pdf",       "Isham & Kaufmann-type performance paper"),
    ("s01", "annurev-economics-080218-030333.pdf",           "Annual Review of Economics"),
    ("s01", "Published_Version.pdf",                         "Core published version"),
    ("s01", "s11558-016-9256-x.pdf",                        "Review of International Organizations"),
    ("s01", "s11558-021-09414-4.pdf",                       "Review of International Organizations (2021)"),
    ("s01", "ssrn-1296115.pdf",                             "SSRN working paper"),
    ("s01", "ssrn-1678347.pdf",                             "SSRN working paper"),
    ("s01", "ssrn-1678347 (1).pdf",                         "SSRN working paper (duplicate)"),
    ("s01", "ssrn-1871590.pdf",                             "SSRN working paper"),
    ("s01", "s11558-013-9164-2.pdf",                        "Smets Knack Molenaers 2013 — N150: QE→outcome"),
    ("s01", "rap2012_vol1_0.pdf",                            "IEG RAP 2012"),
    ("s01", "report-Concept_Note-RAP_2025.pdf",              "IEG RAP 2025 concept note"),
    ("s01", "616420WP0Resul10BOX358351B01PUBLIC1.pdf",        "World Bank results paper"),
    ("s01", "IEG-Results-and-Performance-of-the-World-Bank-Group-2013-concept-note.pdf", "IEG R&P 2013"),
    ("s01", "379590REVISED01OFFICIAL0USE0ONLY1.pdf",         "World Bank internal report"),
    ("s01", "high-level-structures-world-bank.pdf",          "World Bank governance"),

    # ════════════════════════════════════════════════════════════════════════════
    # S02 — DEVELOPMENT PROJECT MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════════
    ("s02", "AssistingAfricatoAchieveDecisiveChange.pdf",    "Project management — Africa"),
    ("s02", "Foreign+aid+efficacy+and+implementation+delays.pdf", "Implementation delays"),
    ("s02", "Scrum_Method_Implementation_in_a_Softwar.pdf",  "Agile/Scrum in development"),
    ("s02", "With_the_Projectisation_of_the_World_The.pdf",  "Projectisation of development"),
    ("s02", "P180786-68abbc33-c0e7-404e-bc6f-b9edf768a982.pdf", "World Bank P-document"),
    ("s02", "BrowningDSM.pdf",                               "Development systems methodology"),
    ("s02", "v26n2r.pdf",                                    "Journal article — development PM"),
    ("s02", "NIRN-MonographFull-01-2005.pdf",                "Implementation science monograph"),

    # ════════════════════════════════════════════════════════════════════════════
    # S03 — PROJECT PREPARATION QUALITY
    # ════════════════════════════════════════════════════════════════════════════
    ("s03", "947530WP0P14770ation0web00400802015.pdf",        "World Bank preparation quality WP"),
    ("s03", "Comparative-Analysis-of-Project-Development-Effectiveness-Management-Tools-for-Sovereign-Guaranteed-Operations-of-the-AfDB-ADB-IDB-IFAD-and-WB.pdf", "AfDB/ADB/IDB/IFAD/WB comparison"),
    ("s03", "impact-analysis-handbook_0.pdf",                 "Impact analysis handbook"),
    ("s03", "guidelines-evaluation-public-sector.pdf",        "Public sector evaluation guidelines"),
    ("s03", "IDB-9-Corporate-Results-Framework.pdf",          "IDB results framework"),
    ("s03", "Evaluation_of_the_Fund_for_Special_Operations_during_the_Eighth_Replenishment_(1994-2010)_Part_IIEv.pdf", "IDB FSO evaluation"),
    ("s03", "Universal_Metrics_to_Compare_the_Effecti.pdf",   "Universal metrics comparison"),
    ("s03", "An_Empirical_Study_on_Identifying_Perfor.pdf",   "Empirical performance identification"),
    ("s03", "om-a1.pdf",                                      "ADB Operations Manual A1"),
    ("s03", "adb-am-requirements-manual.pdf",                 "ADB requirements manual"),
    ("s03", "pvr-2929_3.pdf",                                 "ADB project validation report"),
    ("s03", "ppar_solomonislands_01042017.pdf",               "ADB Solomon Islands PPAR"),
    ("s03", "Cabo Verde - Evaluation of the Bank's Country Strategy and Program 2008-2017_0.pdf", "AfDB Cabo Verde evaluation"),
    ("s03", "EB-2015-114-R-4.pdf",                           "MDB evaluation report"),

    # ════════════════════════════════════════════════════════════════════════════
    # S04 — PRINCIPAL-AGENT / DISBURSEMENT
    # ════════════════════════════════════════════════════════════════════════════
    ("s04", "102_80_1429023624355_LimodioManagerSelectionandAidEffectiveness.pdf", "Limodio — manager selection & aid effectiveness"),
    ("s04", "DT+2015-04.pdf",                                "Discussion paper — disbursement"),
    ("s04", "ssrn-1881683.pdf",                              "SSRN — principal-agent"),
    ("s04", "ssrn-2349954.pdf",                              "SSRN — disbursement"),
    ("s04", "sdwp-039.pdf",                                  "Development working paper"),
    ("s04", "financial_sector_evaluation.pdf",               "Financial sector evaluation"),
    ("s04", "lines_of_credit_eval.pdf",                      "Lines of credit evaluation"),
    ("s04", "lines_of_credit_eval (1).pdf",                  "Lines of credit evaluation (duplicate)"),
    ("s04", "peru_pensions_wp.pdf",                          "Peru pensions working paper"),
    ("s04", "tn-13-assessing-use-private-distribution.pdf",  "Private distribution assessment"),

    # ════════════════════════════════════════════════════════════════════════════
    # S05 — ADB IED EVALUATION
    # ════════════════════════════════════════════════════════════════════════════
    ("s05", "Vanuatu-Second-Rural-Electrification-Project-Stage-Project.pdf", "ADB Vanuatu PPAR"),
    ("s05", "environmental-flows-assessment-adb-projects.pdf", "ADB environmental flows"),
    ("s05", "rrp-ban-29041.pdf",                             "ADB RRP Bangladesh [SASEC]"),
    ("s05", "rrp-pak-34333.pdf",                             "ADB RRP Pakistan"),

    # ════════════════════════════════════════════════════════════════════════════
    # S06 — IEG WORLD BANK SYSTEMATIC LITERATURE REVIEW
    # ════════════════════════════════════════════════════════════════════════════
    ("s06", "ICR_Review_Manual_for_IEG_Validators_IPF.pdf",  "IEG ICR Review Manual — N149: halo contamination architecture"),
    ("s06", "EvaluatingourEvaluations_RecognizingandCounteringPerformanc.pdf", "Meta-evaluation bias"),
    ("s06", "Annex.pdf",                                     "IEG annexe"),
    ("s06", "The-management-action-record.pdf",              "IEG management action record"),
    ("s06", "lhaf001.pdf",                                   "IEG learning paper"),

    # ════════════════════════════════════════════════════════════════════════════
    # S07 — POLITICAL ECONOMY OF AID
    # ════════════════════════════════════════════════════════════════════════════
    ("s07", "ssrn-1926471.pdf",                              "SSRN — political economy"),
    ("s07", "ssrn-2095648.pdf",                              "SSRN — political economy"),
    ("s07", "ssrn-2900329.pdf",                              "SSRN — political economy"),
    ("s07", "Dual-objective-Donors-and-Investment-across-Economic-Regions-Theory-and-Evidence.pdf", "Dual-objective donors"),
    ("s07", "failure-of-foreign-aid-in-developing-countries.pdf", "Aid failure (Easterly-type)"),
    ("s07", "Enke-EconomistsDevelopmentRediscovering-1969.pdf", "Enke 1969 — development economics history"),
    ("s07", "MAHARATNA-DevelopmentWhatPolitics-2011.pdf",    "Development politics"),
    ("s07", "hal-03710381.pdf",                              "French development paper"),
    ("s07", "w14690.pdf",                                    "NBER working paper"),
    ("s07", "dgo_30th_speech.pdf",                           "DGO speech"),
    ("s07", "religions-10-00362-v2.pdf",                     "Religion and development"),
    ("s07", "AMISH 2023 Developing collaborative online (VOR).pdf", "Online learning / aid collaboration"),

    # ════════════════════════════════════════════════════════════════════════════
    # S08 — SIDS CLIMATE FINANCE / GCF
    # ════════════════════════════════════════════════════════════════════════════
    ("s08", "s41558-021-01170-y.pdf",                        "Berrang-Ford et al 2021 — GAMI global adaptation stocktake [N145]"),
    ("s08", "cff11-2025-eng-gcf-digital.pdf",               "GCF Climate Finance Fundamentals 11th ed 2025"),
    ("s08", "CFF2-2024-ENG-Global-Architecture-DIGITAL.pdf", "CPI Climate Finance 2024"),
    ("s08", "CFF2-2025-ENG-Global-Architecture-DIGITAL.pdf", "CPI Climate Finance 2025"),
    ("s08", "2019-Global-Landscape-of-Climate-Finance.pdf",  "CPI Global Landscape 2019"),
    ("s08", "The-Global-Landscape-of-Climate-Finance-2013.pdf", "CPI Global Landscape 2013"),
    ("s08", "1670929776_green-investment-december-2022.pdf", "Green investment 2022"),
    ("s08", "CEEW-CEF-Climate-Finance.pdf",                  "CEEW climate finance"),
    ("s08", "Multilateral_climate_funds_-_Working_paper_October_2022.pdf", "Multilateral climate funds"),
    ("s08", "Policy_Brief_Climate-smart_reform_of_multilateral_development_banks_priorities_R8cSAYd.pdf", "MDB climate reform"),
    ("s08", "Strengthening Capacity of National Government to Develop Bankable Project Pipelines for Mobilizing Climate Finance.pdf", "Bankable pipelines"),
    ("s08", "improving-the-practice-of-economic-analysis-of-climate-change-adaptation.pdf", "Climate adaptation economics"),
    ("s08", "annurev-environ-012320-083355.pdf",             "Annual Review environment"),
    ("s08", "s13280-021-01571-5.pdf",                       "Ambio — climate adaptation"),
    ("s08", "s44168-025-00220-x.pdf",                       "npj Climate Action 2025"),
    ("s08", "terminal-evaluations-2023.pdf",                 "UNEP terminal evaluations 2023"),
    ("s08", "TerminalEvaluationTE_2568 TE.pdf",              "UNEP terminal evaluation"),
    ("s08", "22683iied.pdf",                                 "IIED climate paper"),

    # ════════════════════════════════════════════════════════════════════════════
    # S09 — EVALUATION BIAS / HALO EFFECTS
    # ════════════════════════════════════════════════════════════════════════════
    ("s09", "2023BiasHaloEffectandHornEffectASystematicLiteratureReview-1.pdf", "Halo/Horn effect systematic review 2023"),
    ("s09", "Beautiful is Good and Good is Reputable_ Multiple-Attribute Chari.pdf", "Halo effect study"),
    ("s09", "Lunenburg, Fred C. Performance Appraisal-Methods And Rating Errors IJSAID V14 N1 2012.pdf", "Rating error methods"),
    ("s09", "Projecting_the_future_A_discourse_on_qu.pdf",   "Forecasting bias"),
    ("s09", "IJCCV3N2A3-Ahamer_131219_RG.pdf",              "Performance assessment bias"),

    # ════════════════════════════════════════════════════════════════════════════
    # S10 — HETEROGENEOUS TREATMENT EFFECTS
    # ════════════════════════════════════════════════════════════════════════════
    ("s10", "athey-imbens-2016-recursive-partitioning-for-heterogeneous-causal-effects.pdf", "Athey & Imbens 2016 — causal forests"),
    ("s10", "NeurIPS-2020-robust-recursive-partitioning-for-heterogeneous-treatment-effects-with-uncertainty-quantification-Paper.pdf", "NeurIPS 2020 — HTE"),
    ("s10", "CausalInferenceinHeterogeneousPopulations.pdf", "Causal inference HTE"),
    ("s10", "PrecisionMedicineApplicationsofRecursivePartitioningandFlexibleTreatmentEffectModelsinChronicDiseaseManagement.pdf", "Recursive partitioning — precision medicine"),
    ("s10", "EffectEstimationUsingModel.pdf",                "Effect estimation using models"),
    ("s10", "1and23.pdf",                                    "S10 paper"),
    ("s10", "1and25.pdf",                                    "S10 paper"),
    ("s10", "1and5.pdf",                                     "S10 paper"),
    ("s10", "su09a.pdf",                                     "HTE paper"),
    ("s10", "2211.10805v3.pdf",                              "arXiv causal ML"),

    # ════════════════════════════════════════════════════════════════════════════
    # S11 — AIDDATA / TUFF / CHINESE DEVELOPMENT FINANCE
    # ════════════════════════════════════════════════════════════════════════════
    ("s11", "Banking_on_the_Belt_and_Road__Insights_from_a_new_global_dataset_of_13427_Chinese_development_projects.pdf", "Malik et al 2021 — 13,427 Chinese projects"),
    ("s11", "AidDataTUFF_Methodology_1.3.pdf",               "AidData TUFF methodology v1.3"),
    ("s11", "AidData_CFTM_1_0_Methodology.pdf",              "AidData CFTM methodology"),
    ("s11", "TUFF_codebook_Version1.2.pdf",                  "TUFF codebook v1.2"),
    ("s11", "Tracking_Chinese_Loans_and_Grants_TUFF_4_Methodology.pdf", "TUFF v4 methodology"),
    ("s11", "2021-Ahmed et al-Understanding-Chinese-Foreign-Aid.pdf", "Ahmed et al 2021 — Chinese aid"),
    ("s11", "177_China_aid.pdf",                             "China aid paper"),
    ("s11", "LSE_Ideas_banking_on_beijing_july_2015.pdf",    "LSE — Banking on Beijing 2015"),
    ("s11", "Disrupting_the_worlds_money-_Chinas_ambitions_for_global_finance.pdf", "China global finance"),
    ("s11", "MAK 2022 Banking on Beijing (VOR).pdf",         "Banking on Beijing 2022"),
    ("s11", "sais-cari-wp04.pdf",                            "SAIS CARI working paper"),
    ("s11", "zeitz-emulation-or-differentiation-aug2018.pdf","Zeitz 2018 — Chinese aid differentiation"),
    ("s11", "purwins-2022-same-same-but-different-ghana-s-sinohydro-deal-as-evolved-angola-model.pdf", "Purwins 2022 — Angola model"),
    ("s11", "2025GuzuraResource-BackedLoans.pdf",            "Guzura 2025 — resource-backed loans [N151]"),
    ("s11", "GCI-WP-034-RBLs-FIN.pdf",                      "GCI resource-backed loans working paper"),
    ("s11", "Resource_backed_investment_finance_in_le.pdf",  "Resource-backed finance"),
    ("s11", "s41597-024-03341-w.pdf",                       "Scientific Data 2024 — AidData methodology"),

    # ════════════════════════════════════════════════════════════════════════════
    # S12 — CROSS-INSTITUTIONAL COMPARISON
    # ════════════════════════════════════════════════════════════════════════════
    ("s12", "American J Political Sci - 2022 - Honig - When Does Transparency Improve Institutional Performance Evidence from 20 000.pdf", "Honig 2022 — 20,000 projects transparency"),
    ("s12", "93252_mdb_gpg_literature_review.pdf",           "MDB good practice literature review"),
    ("s12", "AIDB-Asian-Infrastructure-Development-Bank-by-CRS-2017.pdf", "AIIB by CRS 2017"),
    ("s12", "AIIB_EM.pdf",                                   "AIIB energy strategy"),
    ("s12", "Agreement-on-the-New-Development-Bank.pdf",     "NDB founding agreement"),
    ("s12", "Agreement_Establishing_the_EBRD_with_signatures....pdf", "EBRD founding agreement"),
    ("s12", "basic-documents-of-the-ebrd-july-2025-english.pdf", "EBRD basic documents 2025"),
    ("s12", "basic_document_english-bank_articles_of_agreement.pdf", "MDB articles of agreement"),
    ("s12", "bispap120.pdf",                                 "BIS paper — MDB finance"),
    ("s12", "Alexander Trepelkov.pdf",                       "MDB institutional design"),
    ("s12", "BOSIB0ee57703403908f290d2c3d7b00222.pdf",       "BOSIB report"),
    ("s12", "BOSIB1629ad78009e18ee1111bcda6043c0.pdf",       "BOSIB report (2)"),
    ("s12", "20061122_NDBs-MSC-SA-Report-DRAFT-1206.pdf",    "National Development Banks report"),
    ("s12", "Should-the-Government-Be-in-the-Banking-Business-The-Role-of-State-Owned-and-Development-Banks (1).pdf", "Luna-Martínez & Vicente — state banks"),
    ("s12", "StateOwnedEnterprises.pdf",                     "SOE paper"),

    # ════════════════════════════════════════════════════════════════════════════
    # S13 — CREDIT RISK / DEVELOPMENT RETURNS
    # ════════════════════════════════════════════════════════════════════════════
    ("s13", "stream - 13WorkingPaper186-BalancingDevelopmentReturnsandCreditRisks-EvidencefromtheAfDBsExperience.pdf", "AfDB WP186 — development returns vs credit risk"),
    ("s13", "jrfm-13-00025-v2.pdf",                         "Journal of Risk and Financial Management"),
    ("s13", "ssrn-3693638.pdf",                             "SSRN — credit risk"),
    ("s13", "ssrn-4009924.pdf",                             "SSRN — development returns"),
    ("s13", "ssrn-2836548 (1).pdf",                         "SSRN"),
    ("s13", "ssrn-2479666 (1).pdf",                         "SSRN"),

    # ════════════════════════════════════════════════════════════════════════════
    # S14 — CAUSAL IDENTIFICATION IN DEVELOPMENT
    # ════════════════════════════════════════════════════════════════════════════
    ("s14", "ssrn-2522732.pdf",                              "Kilby 2015 — SFA preparation quality [S14 causal anchor]"),
    ("s14", "ssrn-2104608 (1).pdf",                         "SSRN IV paper"),
    ("s14", "ssrn-2238047.pdf",                              "SSRN causal"),
    ("s14", "ssrn-2278262.pdf",                              "SSRN causal"),
    ("s14", "ssrn-3268038.pdf",                              "SSRN causal"),
    ("s14", "ssrn-3274529.pdf",                              "SSRN causal"),
    ("s14", "Fischer.Levy.2012.Proofs.pdf",                  "Fischer & Levy 2012 proofs"),
    ("s14", "f6e42745842f96d1348f98951b3b2542.pdf",          "Causal identification paper"),
    ("s14", "CausalInferenceinHeterogeneousPopulations.pdf", "Causal inference"),

    # ════════════════════════════════════════════════════════════════════════════
    # S15 — SPECIFICATION ROBUSTNESS
    # ════════════════════════════════════════════════════════════════════════════
    ("s15", "investigating-data-driven-biological-subtypes-of-psychiatric-disorders-using-specification-curve-analysis.pdf", "SCA application — biological subtypes"),
    ("s15", "Understanding the effects of conceptual and analytical choices on finding the privacy paradox A specification curve analysis of large-scale survey .pdf", "SCA — privacy paradox"),
    ("s15", "01242024_Paper2_OSF.pdf",                       "OSF pre-registration paper"),
    ("s15", "MLRV_2015_41_2-4.pdf",                         "Multiverse methods"),
    ("s15", "s13428-017-0937-z.pdf",                        "Behaviour Research Methods — SCA"),
    ("s15", "ssrn-3331818.pdf",                              "SSRN — robustness"),
    ("s15", "ssrn-4819904.pdf",                              "SSRN — specification"),
    ("s15", "ssrn-4819904 (1).pdf",                         "SSRN — specification (duplicate)"),

    # ════════════════════════════════════════════════════════════════════════════
    # S16 — RCT EVIDENCE IN DEVELOPMENT
    # ════════════════════════════════════════════════════════════════════════════
    ("s16", "ssrn-2349954.pdf",                              "RCT evidence"),
    ("s16", "ssrn-1678347.pdf",                              "RCT paper"),
    ("s16", "4.pdf",                                         "S16 paper"),
    ("s16", "3.pdf",                                         "S16 paper"),

    # ════════════════════════════════════════════════════════════════════════════
    # S17 — FRAGILE & CONFLICT-AFFECTED STATES
    # ════════════════════════════════════════════════════════════════════════════
    ("s17", "7.-Livelihood-strategies-and-interventions-in-fragile-and-conflict-affected-areas_-2012-to-2016.pdf", "FCS livelihoods 2012-2016"),
    ("s17", "Early_Economic_Recovery_in_Fragile_State.pdf",  "Early recovery in FCS"),
    ("s17", "ssoar-2023-faust_et_al-Under_Challenging_Conditions_Development_Cooperation.pdf", "Faust et al 2023 — FCS development"),
    ("s17", "SECBOS1a43bff50e019609110773aaa8d12.pdf",       "World Bank FCS paper"),
    ("s17", "ESFFramework.pdf",                              "WB Environmental & Social Framework"),
    ("s17", "ssrn-2900329.pdf",                              "SSRN — FCS"),
    ("s17", "4013_RI_IndustrialPolicyReport_2025.pdf",       "Industrial policy in fragile states 2025 [N153]"),
    ("s17", "Disaster_Risk_Financing_forSIDS_DraftFinalReport.pdf", "DRF for SIDS"),

    # ════════════════════════════════════════════════════════════════════════════
    # S18 — SIDS DEVELOPMENT FINANCE
    # ════════════════════════════════════════════════════════════════════════════
    ("s18", "136799-sids-and-sustainable-finance-a-systems-based-risk-approach-to-improve-access-to-private-investment.pdf", "World Bank SIDS sustainable finance"),
    ("s18", "KalaidjianRobinson_2022_MultilateralFinanceandSIDS.pdf", "Kalaidjian & Robinson 2022 — multilateral finance & SIDS"),
    ("s18", "Development Policy Review - 2021 - Wood - Why are aid projects less effective in the Pacific.pdf", "Wood et al 2021 — Pacific aid effectiveness"),
    ("s18", "WIREs Climate Change - 2010 - Wong - Small island developing states.pdf", "Wong 2010 — SIDS climate"),
    ("s18", "Public Participation in Solid Waste Management in small island developing states (1).pdf", "SIDS solid waste management"),
    ("s18", "Seeboo_2019_IOP_Conf._Ser.__Mater._Sci._Eng._603_032022.pdf", "SIDS engineering paper"),
    ("s18", "Seeboo_2019_IOP_Conf._Ser.__Mater._Sci._Eng._603_032022 (1).pdf", "SIDS engineering paper (duplicate)"),
    ("s18", "Jamaica-Catastrophe-Bond-for-Increased-Financial-Resilience-to-Natural-Disasters-and-Climate-Shocks-Project.pdf", "Jamaica cat bond"),
    ("s18", "Project-Information-Document-Jamaica-Catastrophe-Bond-for-increased-Financial-Resilience-to-Natural-Disasters-and-Climate-Shocks-P173012.pdf", "Jamaica cat bond PID"),
    ("s18", "s10113-017-1254-x.pdf",                        "Climate & Development — SIDS"),
    ("s18", "s10584-020-02762-x.pdf",                       "Climatic Change — SIDS"),
    ("s18", "WORKING 107 PDF E33.pdf",                      "SIDS working paper"),
    ("s18", "IJIFER-S-21-2025.pdf",                         "SIDS finance 2025 [N163]"),
    ("s18", "Decentralizing-DevelopmentFinancethroughCapitalMarketsIntegration.pdf", "Capital markets integration — SIDS"),

    # ════════════════════════════════════════════════════════════════════════════
    # S19 — DEBT SUSTAINABILITY / COLLATERALISATION
    # ════════════════════════════════════════════════════════════════════════════
    ("s19", "A-Framework-for-the-Continuation-of-Resources-to-Address-Fiscal-Distress.pdf", "Fiscal distress framework"),
    ("s19", "brics-econ_article_145573_en_1.pdf",            "BRICS economics"),
    ("s19", "ssrn-4727249.pdf",                              "SSRN — debt"),
    ("s19", "ssrn-4747576.pdf",                              "SSRN — debt"),
    ("s19", "ssrn-5040515.pdf",                              "SSRN — sovereign debt"),
    ("s19", "ssrn-5935987.pdf",                              "SSRN 2025 — debt sustainability [N157]"),
    ("s19", "ssrn-5287468.pdf",                              "SSRN — sovereign finance"),
    ("s19", "ssrn-5976375.pdf",                              "SSRN 2025 [N158]"),
    ("s19", "DP_12.2025.pdf",                                "Discussion paper 2025 [N152]"),
    ("s19", "English_Bridgetown-Initiative-Reform_Design_v3-1 (1).pdf", "Bridgetown Initiative"),
    ("s19", "Accra-Marrakech-Agenda_Adopted_15October2023-compressed.pdf", "Accra-Marrakech Agenda"),

    # ════════════════════════════════════════════════════════════════════════════
    # S20 — CLIMATE FINANCE ARCHITECTURE
    # ════════════════════════════════════════════════════════════════════════════
    ("s20", "Green-Bond-Principles-June-2021-140621.pdf",    "ICMA Green Bond Principles 2021"),
    ("s20", "20231206-KfW-Green-Bond-Framework.pdf",         "KfW Green Bond Framework 2023"),
    ("s20", "Handbook-Harmonised-Framework-for-Impact-Reporting-June-2021-100621.pdf", "ICMA Impact Reporting Handbook"),
    ("s20", "verma-bansal-2021-stock-market-reaction-on-green-bond-issue-evidence-from-indian-green-bond-issuers.pdf", "Verma & Bansal 2021 — green bond markets"),
    ("s20", "NEF_Greening-public-finance.pdf",               "NEF green public finance"),
    ("s20", "Form 18-K_A 2009 Annual Report of KfW.pdf",    "KfW annual report 2009"),
    ("s20", "bispap120.pdf",                                 "BIS green finance"),
    ("s20", "CGH-15-Wessal.pdf",                             "Climate green bond paper"),
    ("s20", "LLN-2022-0012.pdf",                             "Climate finance law"),
    ("s20", "ari91-2021-prizzon-financing-for-development-what-role-for-post-pandemic-development-in-low-and-middle-income-countries.pdf", "Prizzon 2021 — post-pandemic development finance"),
    ("s20", "395c9956-en.pdf",                               "OECD blended finance"),
    ("s20", "9789264094857-en.pdf",                          "OECD development finance"),

    # ════════════════════════════════════════════════════════════════════════════
    # S21 — CLIMATE ADAPTATION FINANCE
    # ════════════════════════════════════════════════════════════════════════════
    ("s21", "A global assessment of policy tools to support climate adaptation.pdf", "Ulibarri et al 2022 — 1,549 adaptation responses [N146]"),
    ("s21", "1-s2.0-S0959378025000068-mainrobhales.pdf",     "Shrestha & Hales — J Environment & Development 2025 [N_SUP3]"),
    ("s21", "s13280-021-01571-5.pdf",                        "Adaptation outcomes — Ambio"),
    ("s21", "s41558-021-01170-y.pdf",                        "Berrang-Ford et al 2021 — GAMI [N145]"),

    # ════════════════════════════════════════════════════════════════════════════
    # S22-26 — OCDI / INFRASTRUCTURE COST OVERRUN / PROCUREMENT / POLITICAL ECONOMY / NCT
    # ════════════════════════════════════════════════════════════════════════════
    ("s22", "Nss-Forecastinginaccuracies-2015.pdf",          "Flyvbjerg — forecasting inaccuracies"),
    ("s22", "Combining+Reference+Class+Forecasting.pdf",     "Reference class forecasting combination"),
    ("s22", "Reference class forecasting in Icelandic transport infrastructure projects.pdf", "RCF Iceland"),
    ("s22", "r06_07.pdf",                                    "Cost overrun paper"),
    ("s22", "chen-et-al-2023-toward-a-deeper-understanding-of-optimism-bias-and-transport-project-cost-overrun.pdf", "Chen et al 2023 — optimism bias"),
    ("s22", "Machiavellian_Megaprojects.pdf",                "Machiavellian megaprojects"),
    ("s22", "The absurd as normal_ why megaprojects are decadent _ International Journal of Managing Projects in Business _ Emerald Publishing.pdf", "Megaproject critique"),
    ("s22", "ssrn-3042378.pdf",                              "SSRN — cost overrun"),
    ("s22", "Getting-Better-Outcomes-on-Construction-Projects-f.pdf", "Construction outcomes"),
    ("s22", "Negative_Effects_of_Design-Bid-Build_Procurement_o.pdf", "DBB procurement effects"),
    ("s22", "PLAN-98852-OTHERS-TUNC.pdf",                    "Infrastructure planning"),
    ("s22", "PPPinCostoverrrun.pdf",                         "PPP cost overrun"),
    ("s22", "dot_28655_DS1.pdf",                             "Transport cost study"),
    ("s22", "land-13-00041-v2.pdf",                          "Land infrastructure"),
    ("s22", "The economic impact of transport infrastructure a review of project-level vs. aggregate-level evidence.pdf", "Transport infrastructure review"),
    ("s22", "Reengineering_Urban_Infrastructure_How_t.pdf",  "Urban infrastructure"),
    ("s22", "ssrn-5968455.pdf",                              "SSRN 2025 infrastructure [N159]"),
    ("s22", "buildings-13-02163.pdf",                        "Buildings journal"),
    ("s22", "procurement.pdf",                               "Procurement paper"),
    ("s22", "HMT_Orange_Book_May_2023.pdf",                  "HM Treasury Orange Book 2023"),
    ("s22", "Resilient-Public-Private-Partnerships-a-regional-and-multi-sectoral-toolkit-from-preparation-to-sustainable-project-financing.pdf", "PPP toolkit"),
    ("s22", "UKIB_Final_Annual_Report_and_Accounts_2022-23_Accessible_24.10.23.pdf", "UK Infrastructure Bank AR 2022-23"),
    ("s22", "UK_Infrastructure_Bank_Framework_Document.pdf", "UKIB Framework"),
    ("s22", "Strategic_steer_to_the_UK_Infrastructure_Bank_180322.pdf", "UKIB strategic steer"),
    ("s22", "McArthur_The UK Infrastructure Bank and the financialisation of public infrastructures amidst neoliberal-nationalism_AAM.pdf", "McArthur 2023 UKIB (AAM)"),
    ("s22", "mcarthur-2023-the-uk-infrastructure-bank-and-the-financialisation-of-public-infrastructures-amidst-nationalist.pdf", "McArthur 2023 UKIB"),
    ("s22", "mcarthur-2023-the-uk-infrastructure-bank-and-the-financialisation-of-public-infrastructures-amidst-nationalist (1).pdf", "McArthur 2023 UKIB (duplicate)"),
    ("s22", "ssrn-2278262.pdf",                              "SSRN — infrastructure finance"),
    ("s22", "Reducing_Emissions_from_Transport_Projec.pdf",  "Transport emissions"),
    ("s22", "TechnoEconomicandEnvironmental.pdf",            "Techno-economic analysis"),
    ("s22", "Projecting_the_future_A_discourse_on_qu.pdf",   "Infrastructure forecasting"),
    ("s22", "ssrn-2095648.pdf",                              "SSRN systems/infrastructure"),

    # ────────────────────────────────────────────────────────────────
    # S26 — NON-LINEAR COLLAPSE THEORY
    # ────────────────────────────────────────────────────────────────
    ("s26", "butzer-2012-collapse-environment-and-society.pdf", "Butzer 2012 — collapse environment & society"),
    ("s26", "s11071-018-4365-0.pdf",                         "Nonlinear dynamics"),
    ("s26", "mmnp201510p186.pdf",                            "Mathematical modelling in nature"),
    ("s26", "Full article_ Mathematical modeling of infectious disease dynamics.pdf", "Mathematical modelling — infectious disease"),
    ("s26", "Mathematical Modeling of Complex Biological Systems_ From Parts Lists to Understanding Systems Behavior - PMC.pdf", "Complex systems modelling"),
    ("s26", "Mathematical and Computational Modeling in Complex Biological Systems - Ji - 2017 - BioMed Research International - Wiley Online Library.pdf", "Computational modelling complex systems"),
    ("s26", "v17no3p327.pdf",                                "Journal of complex systems"),
    ("s26", "P1027.pdf",                                     "NCT paper"),
    ("s26", "2503.04290v1.pdf",                              "arXiv 2025 — systems [N162]"),
    ("s26", "s41467-025-64497-6.pdf",                       "Nature Communications 2025 [N161]"),

    # ════════════════════════════════════════════════════════════════════════════
    # SUPERVISOR PAPERS
    # ════════════════════════════════════════════════════════════════════════════
    ("supervisor", "1-s2.0-S0006320724005019-mainbmackey.pdf",      "Mackey et al GEC 91 2025 [CITE — N_SUP1] S08+S10"),
    ("supervisor", "1-s2.0-S0959378025000068-mainbmackey.pdf",      "Eleksiani Jackson Mackey & Beal JSDEWES 2025 [CITE — N_SUP2] S18/S21"),
    ("supervisor", "1-s2.0-S0921800924001927-main.pdf",             "Supervisor-adjacent — DO NOT CITE"),
    ("supervisor", "1-s2.0-S0965856425001600-main.pdf",             "Supervisor-adjacent — DO NOT CITE"),
    ("supervisor", "1-s2.0-S2185556023000093-main.pdf",             "Supervisor-adjacent — DO NOT CITE"),
    ("supervisor", "Eleksiani10467752bmackey.pdf",                   "Eleksiani + Mackey — DO NOT CITE"),
    ("supervisor", "Hales8159800robhales.pdf",                       "Hales — DO NOT CITE"),
    ("supervisor", "Achanta10344695robhales.pdf",                    "Achanta + Hales — DO NOT CITE"),
    ("supervisor", "Birdthistle9605143robhales.pdf",                 "Birdthistle + Hales — DO NOT CITE"),
    ("supervisor", "Buckley10477588robhales.pdf",                    "Buckley + Hales — DO NOT CITE"),
    ("supervisor", "Dashzeveg10040722robhales.pdf",                  "Dashzeveg + Hales — DO NOT CITE"),
    ("supervisor", "Jeewanthi10084662robhales.pdf",                  "Jeewanthi + Hales — DO NOT CITE"),
    ("supervisor", "Keith10475094.pdf",                              "Keith — DO NOT CITE"),
    ("supervisor", "Kinney10475036bmackey.pdf",                      "Kinney + Mackey — DO NOT CITE"),
    ("supervisor", "Mackey10070955bmackey.pdf",                      "Mackey — DO NOT CITE"),
    ("supervisor", "Nalau10026727.pdf",                              "Nalau — DO NOT CITE"),
    ("supervisor", "Nedopil10061534robhales.pdf",                    "Nedopil + Hales — DO NOT CITE"),
    ("supervisor", "Shrestha10475056robhales.pdf",                   "Shrestha + Hales — DO NOT CITE"),

    # ════════════════════════════════════════════════════════════════════════════
    # AUSTRALIA AWARDS / CUP PROGRAMME MATERIALS
    # ════════════════════════════════════════════════════════════════════════════
    ("awards", "aus-awards-scholarships-policy-handbook.pdf",        "DFAT Awards policy"),
    ("awards", "australia-awards-annual-investment-reporting-content-guide.docx", "DFAT reporting"),
    ("awards", "australia-awards-global-monitoring-and-evaluation-framework-2022.pdf", "DFAT M&E framework"),
    ("awards", "australia-awards-global-strategic-framework-2021-24.pdf", "DFAT strategic framework"),
    ("awards", "australia-awards-guidance-note-1-program-logic.docx","DFAT program logic"),
    ("awards", "australia-awards-guidance-note-2-monitoring-and-evaluation-across-the-australia-awards-cycle.docx", "DFAT M&E guidance"),
    ("awards", "australia-awards-guidance-note-3-core-global-indicators.docx", "DFAT core indicators"),
    ("awards", "australia-awards-pacific-scholarships-handbook.pdf", "Pacific scholarships handbook"),
    ("awards", "ncp-2024-mobility-guidelines.pdf",                   "DFAT mobility guidelines"),

    # ════════════════════════════════════════════════════════════════════════════
    # POLICY BRIEF & EVALUATION TEMPLATES
    # ════════════════════════════════════════════════════════════════════════════
    ("templates", "policy-brief-template-01.doc",                    "Policy brief template 01"),
    ("templates", "policy-brief-template-02.docx",                   "Policy brief template 02"),
    ("templates", "policy-brief-template-03.doc",                    "Policy brief template 03"),
    ("templates", "policy-brief-template-04.doc",                    "Policy brief template 04"),
    ("templates", "policy-brief-template-05.docx",                   "Policy brief template 05"),
    ("templates", "policy-brief-template-06.docx",                   "Policy brief template 06"),
    ("templates", "policy-brief-template-07.docx",                   "Policy brief template 07"),
    ("templates", "policy-brief-template-08.docx",                   "Policy brief template 08"),
    ("templates", "policy-brief-template-09.doc",                    "Policy brief template 09"),
    ("templates", "Policy template.docx",                            "Policy template"),
    ("templates", "Project Plan template.docx",                      "Project plan template"),
    ("templates", "template-1-theory-change.docx",                   "Evaluation template 1 — theory of change"),
    ("templates", "template-2-program-logic.docx",                   "Evaluation template 2 — program logic"),
    ("templates", "template-3-evaluation-framework.docx",            "Evaluation template 3 — framework"),
    ("templates", "template-4-evaluation-tor.docx",                  "Evaluation template 4 — TOR"),
    ("templates", "template-5-evaluation-plan.docx",                 "Evaluation template 5 — plan"),
    ("templates", "template-6-identifying-stakeholders.docx",        "Evaluation template 6 — stakeholders"),
    ("templates", "template-7-data-matrix.docx",                     "Evaluation template 7 — data matrix"),
    ("templates", "template-8-data-sharing-agreement.doc",           "Evaluation template 8 — data sharing"),
    ("templates", "template-9-evaluation-report.docx",               "Evaluation template 9 — report"),
    ("templates", "template-10-evaluation-action-plan.docx",         "Evaluation template 10 — action plan"),
    ("templates", "template-11-evaluation-closure-report.docx",      "Evaluation template 11 — closure"),
    ("templates", "template-pre-analysis.docx",                      "Pre-analysis plan template"),

    # ════════════════════════════════════════════════════════════════════════════
    # MISCELLANEOUS / OTHER
    # ════════════════════════════════════════════════════════════════════════════
    ("misc", "Excel_20260222_002846.xlsx",                           "Data file — not literature"),
    ("misc", "Research Data Management Guidelines.pdf",              "Research data management admin"),
    ("misc", "Ordoyan-Norayr-thesis-2021.pdf",                      "Thesis — use with caution"),
    ("misc", "Alberti Vazquez_10215480_Thesis.pdf",                  "Thesis — use with caution"),
    ("misc", "Boakye_lg_thesis.pdf",                                 "Thesis — use with caution"),
    ("misc", "Bynta Melissa _MME.pdf",                               "Masters thesis — use with caution"),
    ("misc", "DISSERTATION - ABDUL-AZIZ SHAIB MOHAMED - FINAL.doc",  "Dissertation — use with caution"),
    ("misc", "PhD_thesis_Kryg_N_for publication.pdf",                "PhD thesis — use with caution"),
    ("misc", "k12447_thesis.pdf",                                    "PhD thesis — use with caution"),
    ("misc", "Final Thesis.pdf",                                     "Thesis — use with caution"),
    ("misc", "Dissertation_Manh Hung Do_Final_TIB.pdf",              "Dissertation — use with caution"),
    ("misc", "Daniel+Stephen+Lodinya+_Manuscript_(Final+Draft).pdf", "Manuscript"),
    ("misc", "9cae788db2bade8faff6e4919b6bcdcc174d.pdf",             "Misc paper"),
    ("misc", "out.pdf",                                              "Misc — unknown"),
    ("misc", "en.pdf",                                               "Misc — unknown"),
    ("misc", "data.pdf",                                             "Data PDF"),
    ("misc", "Fulltext.pdf",                                         "Misc fulltext"),
    ("misc", "FULLTEXT01.pdf",                                       "Misc fulltext"),
    ("misc", "28.pdf",                                               "Misc paper"),
    ("misc", "12405.pdf",                                            "Misc paper"),
    ("misc", "Rossati2016.pdf",                                      "Rossati 2016"),
    ("misc", "g2509454.pdf",                                         "Misc paper"),
    ("misc", "cp2023_L08E.pdf",                                      "Misc paper 2023"),
    ("misc", "rbaval-13-2 spe-e130424.pdf",                         "Misc journal paper"),
    ("misc", "submission_77.pdf",                                    "Conference submission"),
    ("misc", "submission_157.pdf",                                   "Conference submission"),
    ("misc", "09-16-08 Council document.pdf",                        "Council document"),
    ("misc", "TheLancet.com_20260221.zip",                           "Lancet zip — extract before use"),
    ("misc", "Physical-Activity-Surveillence-in-Australia_-Policy-Brief_19-April-2021.pdf", "⚠ Stray file — not relevant"),
    ("misc", "Policy-brief-tobacco-control-19-April-2021.pdf",       "⚠ Stray file — not relevant"),
    ("misc", "First-2000-days-Policy-Brief-FINAL.pdf",               "⚠ Stray file — not relevant"),
    ("misc", "Questionnaire Construct Validation in the International Civic and.pdf", "Questionnaire validation"),
    ("misc", "fpsyt-13-744661.pdf",                                  "Psychiatry paper"),
    ("misc", "s12888-025-06829-w.pdf",                               "Mental health paper"),
    ("misc", "s12889-025-23358-z.pdf",                               "Public health paper"),
    ("misc", "Full article_ Mathematical modeling of infectious disease dynamics.pdf", "Infectious disease modelling"),
    ("misc", "Mathematical Modeling of Complex Biological Systems_ From Parts Lists to Understanding Systems Behavior - PMC.pdf", "Biological systems modelling"),
    ("misc", "Mathematical and Computational Modeling in Complex Biological Systems - Ji - 2017 - BioMed Research International - Wiley Online Library.pdf", "Computational bio modelling"),
    ("misc", "mmnp201510p186.pdf",                                   "Math/nature paper"),
    ("misc", "DR LEO 2022-03.pdf",                                   "LEO 2022 [N154]"),
    ("misc", "DR-LEO-2023-04.pdf",                                   "LEO 2023 [N155]"),
    ("misc", "DR LEO 2025-15_merged.pdf",                            "LEO 2025 [N156]"),
    ("misc", "ssrn-5740148.pdf",                                     "SSRN 2025 [N160]"),
    ("misc", "-9781786432629.00019.pdf",                             "Book chapter"),
    ("misc", "-9781786439994.00023.pdf",                             "Book chapter"),
    ("misc", "000000146124.pdf",                                     "Misc paper"),
    ("misc", "022-article-A003-en.pdf",                              "Misc article"),
    ("misc", "10.22034_jom.2024.2026899.1199.pdf",                   "Journal of Management 2024"),
    ("misc", "10.22034_jom.2024.2026899.1199 (1).pdf",              "Journal of Management 2024 (dup)"),
    ("misc", "10.4324_9780367855741_previewpdf.pdf",                 "Book preview"),
    ("misc", "11-2-219.pdf",                                         "Misc paper"),
    ("misc", "12-3-385.pdf",                                         "Misc paper"),
    ("misc", "1998076.1998129.pdf",                                  "Misc paper"),
    ("misc", "1and23.pdf",                                           "S10 paper (also misc)"),
    ("misc", "2019_Report_NeupertSchenker.pdf",                      "Neupert-Schenker 2019"),
    ("misc", "37965974.pdf",                                         "Misc paper"),
    ("misc", "43315068687251.pdf",                                   "Misc paper"),
    ("misc", "56190182-MIT.pdf",                                     "MIT paper"),
    ("misc", "694102.pdf",                                           "Misc"),
    ("misc", "729539.pdf",                                           "Misc"),
    ("misc", "777580047.pdf",                                        "Misc"),
    ("misc", "978-3-030-81139-6.pdf",                                "Book"),
    ("misc", "9cae788db2bade8faff6e4919b6bcdcc174d.pdf",             "Misc"),
    ("misc", "AD1126375.pdf",                                        "DTIC report"),
    ("misc", "AD1216577.pdf",                                        "DTIC report"),
    ("misc", "e010408.full.pdf",                                     "Journal article"),
    ("misc", "IJSRA-2025-1422.pdf",                                  "IJSRA 2025"),
    ("misc", "IDU-055fc4dd-1257-4494-b3db-38b2919bd178.pdf",        "IDU document"),
    ("misc", "g2509454.pdf",                                         "Misc"),
    ("misc", "Kibe+et+al.,+(2024).pdf",                              "Kibe et al 2024"),
    ("misc", "lhaf001.pdf",                                          "IEG paper (also S06)"),
    ("misc", "Main-Report.pdf",                                      "Main report — unknown source"),
    ("misc", "P1755360215bd80b096510e5a5e147f4ed.pdf",               "Misc"),
    ("misc", "P176149081fb2605d0a7d504978f2319025.pdf",              "Misc"),
    ("misc", "productivityPaper.pdf",                                "Productivity paper"),
    ("misc", "Tuhirirwe_2025.pdf",                                   "Tuhirirwe 2025"),
    ("misc", "pkpadmin,+6_Wessel+&+Wescott+&+Espindola_IPMR_Volume+16_Issue+1.pdf", "IPMR paper"),
    ("misc", "pkpadmin,+6_Wessel+&+Wescott+&+Espindola_IPMR_Volume+16_Issue+1 (1).pdf", "IPMR paper (dup)"),
    ("misc", "ssrn-1296115.pdf",                                     "SSRN"),
    ("misc", "ssrn-2522732.pdf",                                     "SSRN"),
    ("misc", "ssrn-3116624.pdf",                                     "SSRN"),
    ("misc", "ssrn-4009924.pdf",                                     "SSRN"),
    ("misc", "ssrn-5287468.pdf",                                     "SSRN"),
    ("misc", "s11115-015-0326-y.pdf",                                "Springer paper"),
    ("misc", "s11135-025-02060-7.pdf",                               "Springer paper 2025"),
    ("misc", "s11138-024-00663-1.pdf",                               "Springer paper 2024"),
    ("misc", "s41598-024-60256-7.pdf",                               "Scientific Reports 2024"),
    ("misc", "s10639-025-13582-w.pdf",                               "Education paper 2025"),
    ("misc", "ti-38-14714.pdf",                                      "Transparency International"),
    ("misc", "theses_4324_1.pdf",                                    "Thesis"),
    ("misc", "v17no3p327.pdf",                                       "Journal v17"),
    ("misc", "ZORA172533.pdf",                                       "ZORA repository paper"),
    ("misc", "Volltext (PDF).pdf",                                   "Fulltext PDF"),
    ("misc", "su09a.pdf",                                            "Misc paper"),
    ("misc", "r06_07.pdf",                                           "Misc paper"),
    ("misc", "pvr-2929_3.pdf",                                       "ADB PVR"),
    ("misc", "2448-7554-rz-29-116-257.pdf",                         "Misc journal"),
    ("misc", "ED675805.pdf",                                         "ERIC document"),
    ("misc", "EJ1341360.pdf",                                        "ERIC journal"),
]

# ─── Download engine ──────────────────────────────────────────────────────────

def url_for(filename: str) -> str:
    """Build raw GitHub URL for a filename, encoding special characters."""
    encoded = quote(filename, safe="")
    return f"{RAW_BASE}/{encoded}"


def dest_for(stream: str, filename: str) -> Path:
    """Build local destination path."""
    return BASE / stream / filename


def download_file(url: str, dest: Path, desc: str) -> str:
    """Download one file. Returns 'ok', 'exists', or 'failed'."""
    if dest.exists() and dest.stat().st_size > 0:
        return "exists"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, timeout=60, stream=True)
        if r.status_code == 404:
            return "404"
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        size_mb = dest.stat().st_size / 1_048_576
        print(f"    ✓ {size_mb:.1f} MB  →  {dest}")
        return "ok"
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return "failed"


def run_download(entries, label=""):
    ok = exists = failed = f404 = 0
    for stream, filename, desc in entries:
        dest = dest_for(stream, filename)
        url  = url_for(filename)
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  [EXISTS] {filename}")
            exists += 1
            continue
        print(f"  ↓ {desc}")
        print(f"    {url}")
        result = download_file(url, dest, desc)
        if result == "ok":      ok += 1
        elif result == "exists": exists += 1
        elif result == "404":
            print(f"    ⚠ 404 — file not found in repo: {filename}")
            f404 += 1
        else:
            failed += 1
        time.sleep(0.05)
    total = ok + exists + failed + f404
    print(f"\n  Results: {ok} downloaded, {exists} already existed, {f404} not found (404), {failed} failed")
    return ok, exists, f404, failed


# ─── CLI ──────────────────────────────────────────────────────────────────────

def cmd_list(args):
    by_stream = {}
    for stream, filename, desc in FILES:
        by_stream.setdefault(stream, []).append((filename, desc))

    width = 70
    print()
    print("=" * 70)
    print("LITERATURE REPO — github.com/stevenbrandon88/literature-Gaps")
    print("=" * 70)
    streams_to_show = [args.stream] if args.stream else sorted(by_stream.keys())
    total = 0
    for stream in streams_to_show:
        entries = by_stream.get(stream, [])
        if not entries:
            continue
        label = STREAM_LABELS.get(stream, stream.upper())
        print(f"\n  [{stream.upper()}] — {label} ({len(entries)} files)")
        for fn, desc in entries:
            print(f"    {fn[:55]:<56} {desc[:50]}")
        total += len(entries)
    print(f"\n  TOTAL: {total} files")
    print(f"  REPO:  {RAW_BASE}")
    print()
    print("  COMMANDS:")
    for s in sorted(by_stream.keys()):
        n = len(by_stream[s])
        print(f"    python lit_repo_downloader.py --stream {s:<12} # {n} files")
    print(f"    python lit_repo_downloader.py --all                   # everything")
    print(f"    python lit_repo_downloader.py --vectordb              # S01-S26 + synthesis (skip admin)")
    print(f"    python lit_repo_downloader.py --pdfs-only             # PDFs only")
    print(f"    python lit_repo_downloader.py --check                 # verify")
    print()


def cmd_check(args):
    by_stream = {}
    for stream, filename, desc in FILES:
        by_stream.setdefault(stream, []).append((stream, filename, desc))
    print("\n  CHECK — scanning downloaded files...")
    total = missing = 0
    for stream in sorted(by_stream.keys()):
        found = 0
        not_found = []
        for s, fn, desc in by_stream[stream]:
            dest = dest_for(s, fn)
            if dest.exists() and dest.stat().st_size > 0:
                found += 1
            else:
                not_found.append(fn)
        label = STREAM_LABELS.get(stream, stream.upper())
        total += found + len(not_found)
        missing += len(not_found)
        status = "✓" if not not_found else "✗"
        print(f"  {status} [{stream.upper()}] {found}/{found+len(not_found)} — {label}")
        for fn in not_found[:3]:
            print(f"      MISSING: {fn}")
        if len(not_found) > 3:
            print(f"      ... and {len(not_found)-3} more missing")
    print(f"\n  TOTAL: {total-missing}/{total} files present ({missing} missing)")
    if missing == 0:
        print("  ✅ All files downloaded.")
    else:
        print(f"  Run --all to fetch missing files.")


def cmd_download_stream(stream_key, pdfs_only=False):
    entries = [(s, fn, d) for s, fn, d in FILES if s == stream_key]
    if pdfs_only:
        entries = [e for e in entries if e[1].lower().endswith(".pdf")]
    label = STREAM_LABELS.get(stream_key, stream_key.upper())
    print("=" * 60)
    print(f"STREAM: {label} ({len(entries)} files)")
    print("=" * 60)
    return run_download(entries)


def main():
    parser = argparse.ArgumentParser(
        description="Download literature from stevenbrandon88/literature-Gaps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--list",      action="store_true",  help="List all files by stream")
    parser.add_argument("--all",       action="store_true",  help="Download all files")
    parser.add_argument("--vectordb",  action="store_true",  help="Download S01-S26 + synthesis only (for vector DB pipeline)")
    parser.add_argument("--pdfs-only", action="store_true",  help="Download PDFs only (skip .docx/.xlsx)")
    parser.add_argument("--stream",    type=str,             help="Download specific stream (e.g. s01, synthesis)")
    parser.add_argument("--file",      type=str,             help="Download one specific file by name")
    parser.add_argument("--check",     action="store_true",  help="Check what is already downloaded")
    parser.add_argument("--outdir",    type=str,             help="Override output directory")
    args = parser.parse_args()

    global BASE
    if args.outdir:
        BASE = Path(args.outdir)

    if args.list:
        cmd_list(args)
        return

    if args.check:
        cmd_check(args)
        return

    if args.file:
        matches = [(s, fn, d) for s, fn, d in FILES if fn == args.file]
        if not matches:
            print(f"  File not found in catalogue: {args.file}")
            sys.exit(1)
        run_download(matches)
        return

    if args.stream:
        valid = set(s for s,_,_ in FILES)
        if args.stream not in valid:
            print(f"  Unknown stream: {args.stream}")
            print(f"  Valid streams: {', '.join(sorted(valid))}")
            sys.exit(1)
        cmd_download_stream(args.stream, pdfs_only=args.pdfs_only)
        return

    if args.vectordb:
        entries = [(s,fn,d) for s,fn,d in FILES if s in VECTORDB_STREAMS]
        if args.pdfs_only:
            entries = [e for e in entries if e[1].lower().endswith(".pdf")]
        streams_in = sorted(set(s for s,_,_ in entries))
        print(f"\nDownloading {len(entries)} files across {len(streams_in)} streams (vector DB mode)")
        print(f"Output: {BASE.resolve()}")
        total_ok = total_exists = total_404 = total_fail = 0
        for stream in streams_in:
            stream_entries = [e for e in entries if e[0] == stream]
            label = STREAM_LABELS.get(stream, stream.upper())
            print(f"\n{'='*60}")
            print(f"STREAM: {label} ({len(stream_entries)} files)")
            print("="*60)
            ok, ex, f4, fa = run_download(stream_entries)
            total_ok += ok; total_exists += ex; total_404 += f4; total_fail += fa
        print(f"\n{'='*60}")
        print(f"COMPLETE — {total_ok} downloaded, {total_exists} existed, {total_404} not found, {total_fail} failed")
        print(f"Run --check to verify. Then run: python 1_ingest_literature.py")
        return

    if args.all:
        entries = list(FILES)
        if args.pdfs_only:
            entries = [e for e in entries if e[1].lower().endswith(".pdf")]
        streams = sorted(set(s for s,_,_ in entries))
        print(f"\nDownloading all {len(entries)} files across {len(streams)} streams")
        print(f"Output: {BASE.resolve()}")
        total_ok = total_exists = total_404 = total_fail = 0
        for stream in streams:
            stream_entries = [e for e in entries if e[0] == stream]
            label = STREAM_LABELS.get(stream, stream.upper())
            print(f"\n{'='*60}")
            print(f"STREAM: {label} ({len(stream_entries)} files)")
            print("="*60)
            ok, ex, f4, fa = run_download(stream_entries)
            total_ok += ok; total_exists += ex; total_404 += f4; total_fail += fa
        print(f"\n{'='*60}")
        print(f"COMPLETE — {total_ok} downloaded, {total_exists} existed, {total_404} not found, {total_fail} failed")
        print(f"Run --check to verify.")
        return

    # No args — show help
    parser.print_help()


if __name__ == "__main__":
    main()
