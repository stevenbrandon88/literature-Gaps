#!/usr/bin/env python3
"""
reorganize_repo.py
==================
Run this ONCE in the root of the literature-Gaps repo.
It creates the stream subdirectories and moves all files into them.
The ingest pipeline will then work immediately.

USAGE:
  cd /path/to/literature-Gaps
  python reorganize_repo.py          # dry run (shows what would happen)
  python reorganize_repo.py --commit  # actually moves files

After running with --commit:
  git add .
  git commit -m "Reorganize into stream subdirectories — ingest pipeline ready"
  git push
"""

import os, sys, shutil
from pathlib import Path

DRY_RUN = "--commit" not in sys.argv

# ── STREAM DIRECTORY MAPPING ──────────────────────────────────────────
# Based on the README.md in the repo — every file mapped to its stream folder

MOVES = {
    # ── S01 — MDB ECONOMETRICS ────────────────────────────────────────
    "s01": [
        "STREAM 01 - conclusion summary.docx",
        "Stream 001 review of literature vs my project.docx",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (1).docx",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (2).docx",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (1).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (2).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (3).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (4).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (5).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (6).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (7).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (8).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (9).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (10).pdf",
        "Stream 001 — MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (11).pdf",
        "stream1 complete.docx",
        "Stream 1 summary and review.docx",
        "MDB_Econometrics_Stream_Complete.docx",
        "aid-projects-abstracts.docx",
        "The Economic Journal - 2001 - Dollar - What Explains the Success or Failure of Structural Adjustment Programmes.pdf",
        "59wane.pdf",
        "Good_countries_or_good_projects_Macro_an.pdf",
        "What0differenc0roject0performance00.pdf",
        "annurev-economics-080218-030333.pdf",
        "Published_Version.pdf",
        "s11558-016-9256-x.pdf",
        "s11558-021-09414-4.pdf",
        "ssrn-1296115.pdf",
        "ssrn-1678347.pdf",
        "ssrn-1678347 (1).pdf",
        "ssrn-1871590.pdf",
        "s11558-013-9164-2.pdf",
        "rap2012_vol1_0.pdf",
        "report-Concept_Note-RAP_2025.pdf",
        "616420WP0Resul10BOX358351B01PUBLIC1.pdf",
        "IEG-Results-and-Performance-of-the-World-Bank-Group-2013-concept-note.pdf",
        "379590REVISED01OFFICIAL0USE0ONLY1.pdf",
        "high-level-structures-world-bank.pdf",
        "Quality simmary.docx",
    ],
    # ── S02 — DEVELOPMENT PROJECT MANAGEMENT ─────────────────────────
    "s02": [
        "stream 2 - development pm.docx",
        "Developmental PM - abstracts.docx",
        "AssistingAfricatoAchieveDecisiveChange.pdf",
        "Foreign+aid+efficacy+and+implementation+delays.pdf",
        "Scrum_Method_Implementation_in_a_Softwar.pdf",
        "With_the_Projectisation_of_the_World_The.pdf",
        "P180786-68abbc33-c0e7-404e-bc6f-b9edf768a982.pdf",
        "BrowningDSM.pdf",
        "v26n2r.pdf",
        "NIRN-MonographFull-01-2005.pdf",
        "AMISH 2023 Developing collaborative online (VOR).pdf",
    ],
    # ── S03 — PROJECT PREPARATION QUALITY ────────────────────────────
    "s03": [
        "Stream 3 -- output summary.docx",
        "947530WP0P14770ation0web00400802015.pdf",
        "Comparative-Analysis-of-Project-Development-Effectiveness-Management-Tools-for-Sovereign-Guaranteed-Operations-of-the-AfDB-ADB-IDB-IFAD-and-WB.pdf",
        "impact-analysis-handbook_0.pdf",
        "guidelines-evaluation-public-sector.pdf",
        "IDB-9-Corporate-Results-Framework.pdf",
        "Evaluation_of_the_Fund_for_Special_Operations_during_the_Eighth_Replenishment_(1994-2010)_Part_IIEv.pdf",
        "Universal_Metrics_to_Compare_the_Effecti.pdf",
        "An_Empirical_Study_on_Identifying_Perfor.pdf",
        "om-a1.pdf",
        "adb-am-requirements-manual.pdf",
        "pvr-2929_3.pdf",
        "ppar_solomonislands_01042017.pdf",
        "Cabo Verde - Evaluation of the Bank's Country Strategy and Program 2008-2017_0.pdf",
        "EB-2015-114-R-4.pdf",
    ],
    # ── S04 — PRINCIPAL-AGENT / DISBURSEMENT ─────────────────────────
    "s04": [
        "stream 4 - conclusion.docx",
        "principal agent - abstract.docx",
        "102_80_1429023624355_LimodioManagerSelectionandAidEffectiveness.pdf",
        "DT+2015-04.pdf",
        "ssrn-1881683.pdf",
        "ssrn-2349954.pdf",
        "sdwp-039.pdf",
        "financial_sector_evaluation.pdf",
        "lines_of_credit_eval.pdf",
        "lines_of_credit_eval (1).pdf",
        "peru_pensions_wp.pdf",
        "tn-13-assessing-use-private-distribution.pdf",
    ],
    # ── S05 — ADB IED EVALUATION ──────────────────────────────────────
    "s05": [
        "adb_ied_stream_synthesis.docx",
        "The Asian Development Bank and Evaluation in Asia and the Pacific.docx",
        "Vanuatu-Second-Rural-Electrification-Project-Stage-Project.pdf",
        "environmental-flows-assessment-adb-projects.pdf",
        "rrp-ban-29041.pdf",
        "rrp-pak-34333.pdf",
    ],
    # ── S06 — IEG WORLD BANK SLR ──────────────────────────────────────
    "s06": [
        "WB_IEG_SLR_Output.docx",
        "ICR_Review_Manual_for_IEG_Validators_IPF.pdf",
        "EvaluatingourEvaluations_RecognizingandCounteringPerformanc.pdf",
        "Annex.pdf",
        "The-management-action-record.pdf",
        "lhaf001.pdf",
    ],
    # ── S07 — POLITICAL ECONOMY OF AID ───────────────────────────────
    "s07": [
        "ssrn-1926471.pdf",
        "ssrn-2095648.pdf",
        "ssrn-2900329.pdf",
        "Dual-objective-Donors-and-Investment-across-Economic-Regions-Theory-and-Evidence.pdf",
        "failure-of-foreign-aid-in-developing-countries.pdf",
        "Enke-EconomistsDevelopmentRediscovering-1969.pdf",
        "MAHARATNA-DevelopmentWhatPolitics-2011.pdf",
        "hal-03710381.pdf",
        "w14690.pdf",
        "dgo_30th_speech.pdf",
        "religions-10-00362-v2.pdf",
    ],
    # ── S08 — SIDS CLIMATE FINANCE / GCF ─────────────────────────────
    "s08": [
        "CAF_Stream_Output.docx",
        "ClimateFinanceStream_SynthesisOutput.docx",
        "CDF_Stream_Output.docx",
        "s41558-021-01170-y.pdf",
        "cff11-2025-eng-gcf-digital.pdf",
        "CFF2-2024-ENG-Global-Architecture-DIGITAL.pdf",
        "CFF2-2025-ENG-Global-Architecture-DIGITAL.pdf",
        "2019-Global-Landscape-of-Climate-Finance.pdf",
        "The-Global-Landscape-of-Climate-Finance-2013.pdf",
        "1670929776_green-investment-december-2022.pdf",
        "CEEW-CEF-Climate-Finance.pdf",
        "Multilateral_climate_funds_-_Working_paper_October_2022.pdf",
        "Policy_Brief_Climate-smart_reform_of_multilateral_development_banks_priorities_R8cSAYd.pdf",
        "Strengthening Capacity of National Government to Develop Bankable Project Pipelines for Mobilizing Climate Finance.pdf",
        "improving-the-practice-of-economic-analysis-of-climate-change-adaptation.pdf",
        "annurev-environ-012320-083355.pdf",
        "s13280-021-01571-5.pdf",
        "s44168-025-00220-x.pdf",
        "terminal-evaluations-2023.pdf",
        "TerminalEvaluationTE_2568 TE.pdf",
        "22683iied.pdf",
        "1-s2.0-S0006320724005019-mainbmackey.pdf",
        "1-s2.0-S0959378025000068-mainbmackey.pdf",
    ],
    # ── S09 — EVALUATION BIAS ─────────────────────────────────────────
    "s09": [
        "EvalBias_LiteratureStream_Brandon_2026.docx",
        "IEG SELF-EVALUATION SUMMARY.docx",
        "cross_institutional_coding.docx",
        "2023BiasHaloEffectandHornEffectASystematicLiteratureReview-1.pdf",
        "Beautiful is Good and Good is Reputable_ Multiple-Attribute Chari.pdf",
        "Lunenburg, Fred C. Performance Appraisal-Methods And Rating Errors IJSAID V14 N1 2012.pdf",
        "Projecting_the_future_A_discourse_on_qu.pdf",
        "IJCCV3N2A3-Ahamer_131219_RG.pdf",
    ],
    # ── S10 — HETEROGENEOUS TREATMENT EFFECTS ────────────────────────
    "s10": [
        "HTE_Stream_Synthesis.docx",
        "athey-imbens-2016-recursive-partitioning-for-heterogeneous-causal-effects.pdf",
        "NeurIPS-2020-robust-recursive-partitioning-for-heterogeneous-treatment-effects-with-uncertainty-quantification-Paper.pdf",
        "CausalInferenceinHeterogeneousPopulations.pdf",
        "PrecisionMedicineApplicationsofRecursivePartitioningandFlexibleTreatmentEffectModelsinChronicDiseaseManagement.pdf",
        "EffectEstimationUsingModel.pdf",
        "1and23.pdf",
        "1and25.pdf",
        "1and5.pdf",
        "su09a.pdf",
    ],
    # ── S11 — AIDDATA / TUFF / CHINESE DEVELOPMENT FINANCE ───────────
    "s11": [
        "AidData_TUFF_Stream_Coding.docx",
        "Towards complete development finance data.docx",
        "Banking_on_the_Belt_and_Road__Insights_from_a_new_global_dataset_of_13427_Chinese_development_projects.pdf",
        "AidDataTUFF_Methodology_1.3.pdf",
        "AidData_CFTM_1_0_Methodology.pdf",
        "TUFF_codebook_Version1.2.pdf",
        "Tracking_Chinese_Loans_and_Grants_TUFF_4_Methodology.pdf",
        "2021-Ahmed et al-Understanding-Chinese-Foreign-Aid.pdf",
        "177_China_aid.pdf",
        "LSE_Ideas_banking_on_beijing_july_2015.pdf",
        "Disrupting_the_worlds_money-_Chinas_ambitions_for_global_finance.pdf",
        "MAK 2022 Banking on Beijing (VOR).pdf",
        "sais-cari-wp04.pdf",
        "zeitz-emulation-or-differentiation-aug2018.pdf",
        "purwins-2022-same-same-but-different-ghana-s-sinohydro-deal-as-evolved-angola-model.pdf",
        "2025GuzuraResource-BackedLoans.pdf",
        "GCI-WP-034-RBLs-FIN.pdf",
        "Resource_backed_investment_finance_in_le.pdf",
        "s41597-024-03341-w.pdf",
    ],
    # ── S12 — CROSS-INSTITUTIONAL COMPARISON ─────────────────────────
    "s12": [
        "93252_mdb_gpg_literature_review.pdf",
        "American J Political Sci - 2022 - Honig - When Does Transparency Improve Institutional Performance Evidence from 20 000.pdf",
        "AIDB-Asian-Infrastructure-Development-Bank-by-CRS-2017.pdf",
        "AIIB_EM.pdf",
        "Agreement-on-the-New-Development-Bank.pdf",
        "Agreement_Establishing_the_EBRD_with_signatures....pdf",
        "basic-documents-of-the-ebrd-july-2025-english.pdf",
        "basic_document_english-bank_articles_of_agreement.pdf",
        "bispap120.pdf",
        "Alexander Trepelkov.pdf",
        "BOSIB0ee57703403908f290d2c3d7b00222.pdf",
        "BOSIB1629ad78009e18ee1111bcda6043c0.pdf",
        "20061122_NDBs-MSC-SA-Report-DRAFT-1206.pdf",
        "Should-the-Government-Be-in-the-Banking-Business-The-Role-of-State-Owned-and-Development-Banks (1).pdf",
        "StateOwnedEnterprises.pdf",
    ],
    # ── S13 — CREDIT RISK / DEVELOPMENT RETURNS ──────────────────────
    "s13": [
        "DebtSustainability_StreamCoding.docx",
        "stream - 13WorkingPaper186-BalancingDevelopmentReturnsandCreditRisks-EvidencefromtheAfDBsExperience.pdf",
        "jrfm-13-00025-v2.pdf",
        "ssrn-3693638.pdf",
        "ssrn-4009924.pdf",
        "ssrn-2836548 (1).pdf",
        "ssrn-2479666 (1).pdf",
    ],
    # ── S14 — CAUSAL IDENTIFICATION ───────────────────────────────────
    "s14": [
        "ssrn-2522732.pdf",
        "ssrn-2104608 (1).pdf",
        "ssrn-2238047.pdf",
        "ssrn-2278262.pdf",
        "ssrn-3268038.pdf",
        "ssrn-3274529.pdf",
        "Fischer.Levy.2012.Proofs.pdf",
        "f6e42745842f96d1348f98951b3b2542.pdf",
    ],
    # ── S15 — SPECIFICATION ROBUSTNESS ───────────────────────────────
    "s15": [
        "spec_robustness_stream.docx",
        "investigating-data-driven-biological-subtypes-of-psychiatric-disorders-using-specification-curve-analysis.pdf",
        "Understanding the effects of conceptual and analytical choices on finding the privacy paradox A specification curve analysis of large-scale survey .pdf",
        "01242024_Paper2_OSF.pdf",
        "MLRV_2015_41_2-4.pdf",
        "s13428-017-0937-z.pdf",
        "ssrn-3331818.pdf",
        "ssrn-4819904.pdf",
        "ssrn-4819904 (1).pdf",
    ],
    # ── S16 — RCT EVIDENCE ────────────────────────────────────────────
    "s16": [
        "rct-evidence summary.docx",
        "ssrn-1678347.pdf",
        "2211.10805v3.pdf",
        "4.pdf",
        "3.pdf",
    ],
    # ── S17 — FCS ─────────────────────────────────────────────────────
    "s17": [
        "FCS_Literature_Stream_Coding.docx",
        "7.-Livelihood-strategies-and-interventions-in-fragile-and-conflict-affected-areas_-2012-to-2016.pdf",
        "Early_Economic_Recovery_in_Fragile_State.pdf",
        "ssoar-2023-faust_et_al-Under_Challenging_Conditions_Development_Cooperation.pdf",
        "SECBOS1a43bff50e019609110773aaa8d12.pdf",
        "ESFFramework.pdf",
        "4013_RI_IndustrialPolicyReport_2025.pdf",
        "Disaster_Risk_Financing_forSIDS_DraftFinalReport.pdf",
    ],
    # ── S18 — SIDS DEVELOPMENT FINANCE ───────────────────────────────
    "s18": [
        "SIDS_DevelopmentFinance_StreamCoding.docx",
        "136799-sids-and-sustainable-finance-a-systems-based-risk-approach-to-improve-access-to-private-investment.pdf",
        "KalaidjianRobinson_2022_MultilateralFinanceandSIDS.pdf",
        "Development Policy Review - 2021 - Wood - Why are aid projects less effective in the Pacific.pdf",
        "WIREs Climate Change - 2010 - Wong - Small island developing states.pdf",
        "Public Participation in Solid Waste Management in small island developing states (1).pdf",
        "Seeboo_2019_IOP_Conf._Ser.__Mater._Sci._Eng._603_032022.pdf",
        "Seeboo_2019_IOP_Conf._Ser.__Mater._Sci._Eng._603_032022 (1).pdf",
        "Jamaica-Catastrophe-Bond-for-Increased-Financial-Resilience-to-Natural-Disasters-and-Climate-Shocks-Project.pdf",
        "Project-Information-Document-Jamaica-Catastrophe-Bond-for-increased-Financial-Resilience-to-Natural-Disasters-and-Climate-Shocks-P173012.pdf",
        "WORKING 107 PDF E33.pdf",
        "s10113-017-1254-x.pdf",
        "s10584-020-02762-x.pdf",
        "IJIFER-S-21-2025.pdf",
        "1-s2.0-S0959378025000068-mainrobhales.pdf",
    ],
    # ── S19 — DEBT SUSTAINABILITY ─────────────────────────────────────
    "s19": [
        "A-Framework-for-the-Continuation-of-Resources-to-Address-Fiscal-Distress.pdf",
        "brics-econ_article_145573_en_1.pdf",
        "ssrn-4727249.pdf",
        "ssrn-4747576.pdf",
        "ssrn-5040515.pdf",
        "ssrn-5935987.pdf",
        "ssrn-5287468.pdf",
        "ssrn-5976375.pdf",
        "DP_12.2025.pdf",
        "English_Bridgetown-Initiative-Reform_Design_v3-1 (1).pdf",
        "Accra-Marrakech-Agenda_Adopted_15October2023-compressed.pdf",
    ],
    # ── S20 — CLIMATE FINANCE ARCHITECTURE ───────────────────────────
    "s20": [
        "Green-Bond-Principles-June-2021-140621.pdf",
        "20231206-KfW-Green-Bond-Framework.pdf",
        "Handbook-Harmonised-Framework-for-Impact-Reporting-June-2021-100621.pdf",
        "verma-bansal-2021-stock-market-reaction-on-green-bond-issue-evidence-from-indian-green-bond-issuers.pdf",
        "NEF_Greening-public-finance.pdf",
        "Form 18-K_A 2009 Annual Report of KfW.pdf",
        "CGH-15-Wessal.pdf",
        "LLN-2022-0012.pdf",
        "ari91-2021-prizzon-financing-for-development-what-role-for-post-pandemic-development-in-low-and-middle-income-countries.pdf",
        "395c9956-en.pdf",
        "9789264094857-en.pdf",
    ],
    # ── S21 — CLIMATE ADAPTATION FINANCE ─────────────────────────────
    "s21": [
        "A global assessment of policy tools to support climate adaptation.pdf",
    ],
    # ── S22 — INFRASTRUCTURE COST OVERRUN ────────────────────────────
    "s22": [
        "ICO_Stream_Output.docx",
        "Nss-Forecastinginaccuracies-2015.pdf",
        "Combining+Reference+Class+Forecasting.pdf",
        "Reference class forecasting in Icelandic transport infrastructure projects.pdf",
        "r06_07.pdf",
        "chen-et-al-2023-toward-a-deeper-understanding-of-optimism-bias-and-transport-project-cost-overrun.pdf",
        "Machiavellian_Megaprojects.pdf",
        "The absurd as normal_ why megaprojects are decadent _ International Journal of Managing Projects in Business _ Emerald Publishing.pdf",
        "ssrn-3042378.pdf",
        "Getting-Better-Outcomes-on-Construction-Projects-f.pdf",
        "Negative_Effects_of_Design-Bid-Build_Procurement_o.pdf",
        "PLAN-98852-OTHERS-TUNC.pdf",
        "PPPinCostoverrrun.pdf",
        "dot_28655_DS1.pdf",
        "land-13-00041-v2.pdf",
        "The economic impact of transport infrastructure a review of project-level vs. aggregate-level evidence.pdf",
        "Reengineering_Urban_Infrastructure_How_t.pdf",
        "ssrn-5968455.pdf",
        "buildings-13-02163.pdf",
        "procurement.pdf",
        "HMT_Orange_Book_May_2023.pdf",
        "Resilient-Public-Private-Partnerships-a-regional-and-multi-sectoral-toolkit-from-preparation-to-sustainable-project-financing.pdf",
        "UKIB_Final_Annual_Report_and_Accounts_2022-23_Accessible_24.10.23.pdf",
        "UK_Infrastructure_Bank_Framework_Document.pdf",
        "Strategic_steer_to_the_UK_Infrastructure_Bank_180322.pdf",
        "McArthur_The UK Infrastructure Bank and the financialisation of public infrastructures amidst neoliberal-nationalism_AAM.pdf",
        "mcarthur-2023-the-uk-infrastructure-bank-and-the-financialisation-of-public-infrastructures-amidst-nationalist.pdf",
        "mcarthur-2023-the-uk-infrastructure-bank-and-the-financialisation-of-public-infrastructures-amidst-nationalist (1).pdf",
        "Decentralizing-DevelopmentFinancethroughCapitalMarketsIntegration.pdf",
        "Reducing_Emissions_from_Transport_Projec.pdf",
        "TechnoEconomicandEnvironmental.pdf",
    ],
    # ── S23 — REFERENCE CLASS FORECASTING ────────────────────────────
    "s23": [
        "RCF_Stream_Coding.docx",
    ],
    # ── S24 — PROCUREMENT ARCHITECTURE ───────────────────────────────
    "s24": [
        "Procurement_Architecture_Stream_Output.docx",
        "policy_on_prohibited_practices.pdf",
        "policy_on_prohibited_practices (1).pdf",
    ],
    # ── S25 — POLITICAL ECONOMY ───────────────────────────────────────
    "s25": [
        "SLR_Political_Economy_Infrastructure_Approval.docx",
    ],
    # ── S26 — NON-LINEAR COLLAPSE THEORY ─────────────────────────────
    "s26": [
        "NCT_Stream_Synthesis_Output.docx",
        "butzer-2012-collapse-environment-and-society.pdf",
        "s11071-018-4365-0.pdf",
        "mmnp201510p186.pdf",
        "Full article_ Mathematical modeling of infectious disease dynamics.pdf",
        "Mathematical Modeling of Complex Biological Systems_ From Parts Lists to Understanding Systems Behavior - PMC.pdf",
        "Mathematical and Computational Modeling in Complex Biological Systems - Ji - 2017 - BioMed Research International - Wiley Online Library.pdf",
        "v17no3p327.pdf",
        "P1027.pdf",
        "2503.04290v1.pdf",
        "s41467-025-64497-6.pdf",
    ],
    # ── SYNTHESIS ─────────────────────────────────────────────────────
    "synthesis": [
        "LSR_Synthesis_Brandon2026.docx",
        "LSR_Synthesis_Tracker_Brandon2026.docx",
        "LSR_21_Stream_Reference.docx",
        "LSR_Streams_22_26_OCDI_Brandon2026.docx",
        "Literature_Gap_Analysis.docx",
        "systematic_lit_coding.docx",
        "Brandon_LitCoding_ProjectEval_Stream.docx",
    ],
    # ── SUPERVISOR (3 cite, rest context only) ────────────────────────
    "supervisor": [
        "1-s2.0-S0921800924001927-main.pdf",
        "1-s2.0-S0965856425001600-main.pdf",
        "1-s2.0-S2185556023000093-main.pdf",
        "Eleksiani10467752bmackey.pdf",
        "Hales8159800robhales.pdf",
        "Achanta10344695robhales.pdf",
        "Birdthistle9605143robhales.pdf",
        "Buckley10477588robhales.pdf",
        "Dashzeveg10040722robhales.pdf",
        "Jeewanthi10084662robhales.pdf",
        "Keith10475094.pdf",
        "Kinney10475036bmackey.pdf",
        "Mackey10070955bmackey.pdf",
        "Nalau10026727.pdf",
        "Nedopil10061534robhales.pdf",
        "Shrestha10475056robhales.pdf",
    ],
    # ── AUSTRALIA AWARDS / CUP ────────────────────────────────────────
    "cup": [
        "aus-awards-scholarships-policy-handbook.pdf",
        "australia-awards-annual-investment-reporting-content-guide.docx",
        "australia-awards-global-monitoring-and-evaluation-framework-2022.pdf",
        "australia-awards-global-strategic-framework-2021-24.pdf",
        "australia-awards-guidance-note-1-program-logic.docx",
        "australia-awards-guidance-note-2-monitoring-and-evaluation-across-the-australia-awards-cycle.docx",
        "australia-awards-guidance-note-3-core-global-indicators.docx",
        "australia-awards-pacific-scholarships-handbook.pdf",
        "ncp-2024-mobility-guidelines.pdf",
    ],
    # ── ADMIN (templates, stray files) ───────────────────────────────
    "admin": [
        "policy-brief-template-01.doc",
        "policy-brief-template-02.docx",
        "policy-brief-template-03.doc",
        "policy-brief-template-04.doc",
        "policy-brief-template-05.docx",
        "policy-brief-template-06.docx",
        "policy-brief-template-07.docx",
        "policy-brief-template-08.docx",
        "policy-brief-template-09.doc",
        "Policy template.docx",
        "Project Plan template.docx",
        "template-1-theory-change.docx",
        "template-2-program-logic.docx",
        "template-3-evaluation-framework.docx",
        "template-4-evaluation-tor.docx",
        "template-5-evaluation-plan.docx",
        "template-6-identifying-stakeholders.docx",
        "template-7-data-matrix.docx",
        "template-8-data-sharing-agreement.doc",
        "template-9-evaluation-report.docx",
        "template-10-evaluation-action-plan.docx",
        "template-11-evaluation-closure-report.docx",
        "template-pre-analysis.docx",
        "Research Data Management Guidelines.pdf",
        "Excel_20260222_002846.xlsx",
        "Physical-Activity-Surveillence-in-Australia_-Policy-Brief_19-April-2021.pdf",
        "Policy-brief-tobacco-control-19-April-2021.pdf",
        "First-2000-days-Policy-Brief-FINAL.pdf",
        "TheLancet.com_20260221.zip",
    ],
    # ── THESES (cite with caution) ────────────────────────────────────
    "theses": [
        "Ordoyan-Norayr-thesis-2021.pdf",
        "Alberti Vazquez_10215480_Thesis.pdf",
        "Boakye_lg_thesis.pdf",
        "Bynta Melissa _MME.pdf",
        "DISSERTATION - ABDUL-AZIZ SHAIB MOHAMED - FINAL.doc",
        "PhD_thesis_Kryg_N_for publication.pdf",
        "k12447_thesis.pdf",
        "Final Thesis.pdf",
        "Dissertation_Manh Hung Do_Final_TIB.pdf",
        "theses_4324_1.pdf",
    ],
}

# Files to KEEP in root (never move)
KEEP_IN_ROOT = {
    "1_ingest_literature.py",
    "2_test_retrieval.py",
    "3_build_evidence_briefs.py",
    "4_wire_into_backend.py",
    "lit_repo_downloader.py",
    "lit_retry_missing.py",
    "README.md",
}

def main():
    root = Path(".")
    moved = 0
    skipped = 0
    not_found = 0

    print(f"{'DRY RUN' if DRY_RUN else 'COMMITTING'} — reorganize_repo.py")
    print(f"Root: {root.resolve()}")
    print()

    for stream, files in MOVES.items():
        dest_dir = Path("literature") / "raw" / stream
        if not DRY_RUN:
            dest_dir.mkdir(parents=True, exist_ok=True)

        for fname in files:
            src = root / fname
            dst = dest_dir / fname

            if not src.exists():
                not_found += 1
                # Don't print every missing file — just count
                continue

            if dst.exists():
                skipped += 1
                continue

            print(f"  {'WOULD MOVE' if DRY_RUN else 'MOVING'}: {fname}")
            print(f"    → literature/raw/{stream}/")

            if not DRY_RUN:
                shutil.move(str(src), str(dst))
            moved += 1

    print()
    print(f"{'Would move' if DRY_RUN else 'Moved'}: {moved} files")
    print(f"Already in place: {skipped}")
    print(f"Not found in root: {not_found}")

    if DRY_RUN:
        print()
        print("Run with --commit to execute:")
        print("  python reorganize_repo.py --commit")
        print()
        print("Then push:")
        print("  git add .")
        print('  git commit -m "Reorganize into stream subdirectories — ingest pipeline ready"')
        print("  git push")
    else:
        print()
        print("Done. Now run:")
        print("  git add .")
        print('  git commit -m "Reorganize into stream subdirectories — ingest pipeline ready"')
        print("  git push")
        print()
        print("Then activate the pipeline:")
        print("  pip install chromadb sentence-transformers pypdf python-docx tqdm")
        print("  python 1_ingest_literature.py")
        print("  python 2_test_retrieval.py --query 'quality at entry OR 27.8 development finance'")

if __name__ == "__main__":
    main()
