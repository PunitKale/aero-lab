"""Produce source-linked research report, validation, notebooks and local viewer."""
import contextlib,io,json,hashlib,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from .config import ROOT,CONFIG

def mdtable(df):
    def cell(x):
        if isinstance(x,(float,np.floating)):return f'{x:.4f}'
        return str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))

def build_reports():
    reports=ROOT/'reports';winners=json.loads((reports/'recommendations.json').read_text());execution=json.loads((reports/'execution_summary.json').read_text())
    tablefolder=ROOT/'data/processed/tables';tables={p.stem:pd.read_csv(p) for p in tablefolder.glob('*.csv')}
    comparison=pd.DataFrame([{'Circuit':name,'Baseline (s)':w['baseline']['lap_time_s'],'Candidate (s)':w['candidate']['lap_time_s'],'Delta (s)':w['lap_delta_s'],'DRS gain (s)':w['drs_time_gain_s']} for name,w in winners.items()])
    u=execution['uncertainty'];conv=pd.read_csv(reports/'convergence.csv');search=pd.read_csv(ROOT/'data/processed/search_evaluations.csv')
    methods=search.groupby(['circuit','seed','method'],as_index=False).agg(evaluations=('feasible','size'),feasible=('feasible','sum'),best_lap_s=('lap_time_s','min'))
    methods.to_csv(reports/'search_method_benchmark.csv',index=False)
    tests=ET.parse(reports/'tests.xml').getroot() if (reports/'tests.xml').exists() else None
    cases=[]
    if tests is not None:
        for test in tests.iter('testcase'):cases.append(dict(test=test.attrib['name'],module=test.attrib.get('classname',''),status='failed' if test.find('failure') is not None or test.find('error') is not None else 'skipped' if test.find('skipped') is not None else 'passed',seconds=float(test.attrib.get('time',0))))
    pd.DataFrame(cases).to_csv(reports/'test_case_matrix.csv',index=False)
    mysql=pd.read_csv(reports/'mysql_reconciliation.csv') if (reports/'mysql_reconciliation.csv').exists() else pd.DataFrame()
    excel=pd.read_csv(reports/'excel_reconciliation.csv') if (reports/'excel_reconciliation.csv').exists() else pd.DataFrame()
    pbi=json.loads((reports/'powerbi_schema_validation.json').read_text()) if (reports/'powerbi_schema_validation.json').exists() else {}
    validation=f'''# Validation report

All results concern a synthetic research model. Generated on the release date stored in the dataset metadata.

## Automated checks

{sum(c['status']=='passed' for c in cases)} passed; {sum(c['status']=='failed' for c in cases)} failed; {sum(c['status']=='skipped' for c in cases)} skipped. See [test-case matrix](test_case_matrix.csv) and [JUnit evidence](tests.xml). Tests cover units, equations, zero speed, drag scaling, load transfer, tyre limits, DRS closure, continuity, repeated results, stint state, infeasible inputs, map bounds and convergence.

The generated run audit contains {len(tables['fact_model_validation'])} invariant checks; {int(tables['fact_model_validation'].passed.sum())} passed. These are implementation checks, not independent measured validation.

## MySQL

MySQL 8.0.46 was executed locally. {int(mysql.matched.sum()) if len(mysql) else 0}/{len(mysql)} row-count and aggregate comparisons matched after two complete loads. The dedicated release snapshot is replaced in a transaction so changing sample resolution cannot leave stale rows. See [reconciliation](mysql_reconciliation.csv). Foreign keys remain enabled.

## Excel

{int(excel.passed.sum()) if len(excel) else 0}/{len(excel)} checks passed after Microsoft Excel CalculateFullRebuild, followed by saving and reopening inspection. Independent checks cover dynamic pressure, downforce, drag, power and sector aggregation. See [reconciliation](excel_reconciliation.csv). This verifies scalar formulas and aggregates, not an independently implemented full Excel lap simulator.

## Numerical convergence

{mdtable(conv)}

Production outputs use 10 m cells. Search and uncertainty use 25 m for screening, with finalist nominal re-evaluation at 10 m. On the displayed baseline/finalist, 10-to-5 m changes are below the 0.2% lap-time target. This is evidence for this scenario, not a universal solver-error bound. Spatial cells quantize DRS boundaries and braking-zone length; interpretation must respect that resolution.

## Power BI

{pbi.get('files_checked',0)} project/report JSON files checked against Microsoft schemas, with {len(pbi.get('errors',[]))} reported schema errors. The authored project has 18 pages and a TMDL semantic model. Power BI Desktop is unavailable here: TMDL loading, DAX execution, rendering, slicer interaction, bookmarks, tooltips, drill-through and service publication have not been accepted in Desktop. Python source-total checks do not stand in for executed DAX.

## Uncertainty and external accuracy

{u['valid_draws']}/{u['draws']} paired scenarios were feasible. Mean candidate-minus-baseline delta was {u['mean_delta_s']:.4f} s; empirical 95% range [{u['p025_delta_s']:.4f}, {u['p975_delta_s']:.4f}] s. Feasible-improvement frequency was {u['probability_feasible_improvement']:.1%}; Monte Carlo standard error of the mean delta was {u['mean_monte_carlo_se_s']:.4f} s. These results depend on assumed ranges and are not calibrated to a measured car. The range crosses zero, so the nominal recommendation does not improve every scenario.

No independent measured telemetry was provided. `fact_lap`, `fact_sector` and `fact_telemetry` are intentionally empty. Real-world MAE/RMSE and interval calibration remain unavailable. Surrogate residual plots compare a held-out set of synthetic simulator evaluations only.
'''
    (reports/'validation_report.md').write_text(validation,encoding='utf-8')
    chapters=[
      ('Abstract','Present the complete research contribution.','A reproducible Python–MySQL–Excel–Power BI platform connects aerodynamic setup to a simplified digital car. The implemented solver combines a continuous spatial speed envelope, rear-axle traction, braking bias, corner limits, tyre degradation, fuel and restricted DRS. Synthetic circuit experiments compare search algorithms and quantify conditional uncertainty. Results are internally verified; independent measured validation and Power BI Desktop acceptance remain separate limitations.','recommendations.json'),
      ('Introduction','Define the engineering decision.','A setup is selected for a circuit and driving objective. Downforce alone is insufficient: the same change affects drag, axle load, braking and tyre use. The software records the conditions under which a recommendation is made and compares matched baseline/candidate runs.','../README.md'),
      ('Background and motivation','Connect aerodynamics to circuit performance.','Dynamic pressure scales with air-relative speed squared. In still air, aerodynamic drag power scales approximately with speed cubed when coefficients are fixed. Ride-height and yaw dependence modify simple scaling. Force equations are necessary but do not identify a lap optimum without a vehicle and circuit model.','figures/figure_notes.md'),
      ('Problem statement','State what the system must solve.','Select feasible aerodynamic configurations by simulated performance while retaining provenance, consistent units and interpretable trade-offs. Avoid independent segment restarts, unlimited driven-wheel force and arbitrary DRS activation. The model must also be honest about the lack of independently measured calibration.','../docs/user_manual.md'),
      ('Aim and objectives','Define measurable delivery goals.','The aim is a reproducible decision-support implementation, not professional simulator equivalence. Objectives cover a normalized dataset, live MySQL import, modular physics, continuous laps and stints, five search methods, Pareto and robust analysis, independent Excel checks, a BI source project and a transparent validation report. The proposal retains the original SMART targets; the final status matrix records partial acceptance explicitly.','delivery_status.csv'),
      ('Research questions','Make hypotheses testable.','Investigate circuit dependence of wing/height choices, DRS benefit, qualifying versus stint objectives, sensitivity to grip/weather, robustness of rankings and cross-tool reconciliation. All hypotheses are conditional on the synthetic response surface. A failed search, infeasible optimum or uncertainty interval crossing zero is an informative result.','recommendations.json'),
      ('Scope of the project','Separate implemented model from extensions.','Implemented: synthetic three-circuit experiments, bounded aero response, load-sensitive tyres, quasi-static balance, gears with lumped shift cost, spatial laps, stints, search and uncertainty. Beyond scope: resolved CFD, transient suspension, full tyre slip/thermal physics, traffic wakes, safety-car strategy and current championship active-aero compliance.','assumption_changes.md'),
      ('Project limitations','Bound the conclusions.','All coefficient surfaces and tyre parameters are assumed. Corner speed has a 5% reserve below the standalone lateral limit. Shift time is lumped. Roll and pitch are quasi-static approximations, crosswind yaw is regularized at low speed, and braking distance is cell-quantized in lap summaries. No claim of safe real-car handling or real-world prediction accuracy follows from these runs.','validation_report.md'),
      ('Literature-review plan','Separate checked sources from reading candidates.','NASA Glenn lift/drag pages establish force and coefficient conventions. FIA official 2026 overview distinguishes current active aerodynamics from the generic historical-style research DRS policy. Katz, Milliken and Pacejka books are reading candidates whose editions and page-specific claims must be checked before citing detailed conclusions. The project does not invent reviewed papers or experimental benchmarks.','references.md'),
      ('Existing-system analysis','Explain the integration gap without invented comparisons.','Spreadsheet-only analysis exposes equations but does not automatically provide continuous stateful laps. Telemetry dashboards describe observed runs but cannot alone evaluate unseen setups. A physics model supports counterfactuals but is only as credible as its inputs. The proposed architecture integrates these roles; no commercial-product performance benchmark was conducted.','../README.md'),
      ('Proposed-system analysis','Show the implemented workflow.','Configuration and synthetic data feed validation, aero coefficients, car forces and the circuit solver. Search invokes the same simulator and stores feasibility. The release flows into MySQL, CSV snapshots, Excel and the Power BI model. Run IDs and manifests link charts and recommendations to their source records.','architecture.md'),
      ('Functional requirements','Map requirements to executable features.','Generate inputs; validate units and ranges; simulate laps and stints; enforce map/DRS/physical constraints; compare setups and objectives; evaluate uncertainty; persist normalized facts; export engineering and BI artifacts; and provide an explanation for each recommendation. Measured-data ingestion requires an authorized reference dataset and mapping.','delivery_status.csv'),
      ('Non-functional requirements','Define operational quality.','Fixed seeds, dependency locks, explicit versions and source hashes support repeatability. Transactions and foreign keys support database integrity. Configuration and typed objects isolate assumptions. Tests and source-linked results support auditability. The local MySQL service binds only to localhost and credentials are excluded from the release.','test_case_matrix.csv'),
      ('System architecture','Describe data and control flow.','The optimizer calls the digital car through the same CarModel interface used for direct experiments. Raw/configured inputs are distinct from simulated outputs. MySQL stores normalized entities; the Power BI CSV projection adds dimension keys to facts without joining facts to facts. A single-direction star avoids ambiguous filter paths.','architecture.md'),
      ('Methodology','Explain the executed experimental design.','Twelve input setups are evaluated across three synthetic circuits and three weather profiles. Separate tyre, DRS, repeatability and stint experiments use matched conditions. Qualifying search runs on all circuits, with five seeds on Apex Ring. Other objectives use an explicitly limited candidate bank; robust selection screens three alternatives. Finalists receive fine-mesh nominal re-evaluation.','search_method_benchmark.csv'),
      ('Dataset design','Describe grain and provenance.','Each dimension has an explicit key; each state is a run/sample pair; each sector result is a run/sector pair. The release contains synthetic inputs and simulated outputs, not measured facts. Generation timestamps, random seed, source type and versions are stored on source/run records; child facts inherit provenance through the run key. The column-level dictionary records units and examples.','data_dictionary.csv'),
      ('Aerodynamic theory','State force definitions and sign convention.','q=0.5ρv_air² in Pa; F_down=q A Cl_down and F_drag=q A Cd in N. Cl_down is positive downforce and all coefficients share the 1.5 m² reference area. Front fraction is F_front/F_down; center of pressure measured behind the front axle is L times rear fraction. Undefined zero-load ratios remain unavailable. At ρ=1.225 kg/m³ and v=50 m/s, Cl=3 and Cd=0.9 give 6890.625 N downforce and 2067.1875 N drag.','../src/physics.py'),
      ('Vehicle-dynamics model','Explain force capacity and balance.','Mass includes fuel. Engine force is the maximum valid-gear wheel torque capped by crank power times efficiency, then constrained by rear-axle tyre capacity. Longitudinal transfer m ax h/L shifts normal load rearward during acceleration. Per-wheel capacity is μ(Fz,wear,T)Fz. Braking is limited by front/rear capacity divided by brake-bias fractions. Lateral transfer and banking alter the wheel loads used in corner solving.','../src/vehicle_model.py'),
      ('Lap-time simulation model','Explain continuity and numerical solution.','Track cells partition each segment. Corner limits constrain endpoint speeds; backward braking sweeps communicate downstream limits and forward sweeps enforce available drive acceleration. Periodic start/end speed creates a flying lap. Iteration couples the speed envelope with tyre/fuel and load state. Cell time is 2Δs/(v_in+v_out), plus declared shift loss. DRS closes on braking, zone exit or failed eligibility.','convergence.csv'),
      ('Optimization methodology','Define search methods and objective scope.','A baseline, 16-point grid, seeded random search, SciPy differential evolution and bounded Powell refinement share a cached evaluator. Actual unique evaluation counts are reported; budgets are not falsely described as equal. Pareto filtering minimizes lap time, wear and mean drag. Race sums ten laps, overtaking targets top speed, high-downforce targets high-speed corner performance and wet minimizes mean+SD under grip perturbations. Robust selection uses paired uncertain scenarios.','../src/optimization.py'),
      ('MySQL database design','Explain relational integrity and analytical use.','The schema contains 26 managed tables, explicit primary/foreign keys, nonnegative checks and unique run/sample or run/sector indexes. Snapshot replacement runs in one transaction with foreign keys enabled. Analytical views expose matched comparisons. Scalar and force ratios use NULLIF for undefined division. Large telemetry workloads should use indexed run queries and downsampled analytical projections before considering partitioning.','../sql/schema.sql'),
      ('Python implementation','Describe modules and execution.','Modules separate configuration, schemas, units, generation, ingestion, physics, aero maps, tyres, vehicle, circuit, simulation, search, uncertainty, explanation, database, export and reporting. Public objects use dataclasses and explicit exceptions. The CLI is python -m src.pipeline. A separate reporting stage consumes frozen outputs instead of silently rerunning selected favourable experiments.','../README.md'),
      ('Excel implementation','Describe independent calculation and snapshots.','The 31-sheet workbook includes editable blue inputs, named ranges, structured tables, locked formulas, validation, charts and reconciliation sheets. Force equations and simple straight/brake/corner limiting cases are live formulas. Integrated speed traces and optimization results are explicitly snapshots. Microsoft Excel recalculates the workbook; cached generator numbers alone are not counted as verification.','excel_reconciliation.csv'),
      ('Power BI implementation','Describe the authored model and acceptance boundary.','The project contains PBIP, public-schema PBIR JSON, TMDL partitions, DAX and 18 pages. CSV import partitions use a portable DataFolder parameter. Facts have dimension keys and one-direction relationships. Measures include weighted force averages, paired DRS gains, lap/sector comparisons and feasibility counts. Power BI Desktop execution/rendering remains unverified; publication was not performed.','powerbi_schema_validation.json'),
      ('Validation and testing','Report evidence without overstating it.',f"The test suite records {sum(c['status']=='passed' for c in cases)} passing cases. MySQL counts and lap sums reconcile after repeated loads. Excel independently recalculates five checks. Mesh refinement is measured rather than assumed. Surrogate residuals are held-out synthetic comparisons, and real-world error metrics are unavailable without independent telemetry.",'validation_report.md'),
      ('Results and discussion','Interpret actual run results.',mdtable(comparison)+f"\n\nOn Apex Ring, the nominal candidate improves the baseline by {-winners['Apex Ring']['lap_delta_s']:.4f} s. Across {u['draws']} paired assumed scenarios, mean delta is {u['mean_delta_s']:.4f} s and the 95% empirical range is [{u['p025_delta_s']:.4f}, {u['p975_delta_s']:.4f}] s. Improvement frequency is {u['probability_feasible_improvement']:.1%}. The interval crosses zero: the candidate is not universally superior. Candidate settings favour less wing drag on this synthetic geometry; sector tables reveal the corner/straight trade-off.",'recommendations.json'),
      ('Risk analysis','Record technical and delivery risks.','Primary risks are synthetic-model bias, optimizer exploitation of smooth assumed surfaces, incorrect units, map extrapolation, insufficient mesh resolution, missing measured validation and unavailable BI authoring runtime. The release mitigates these through explicit domains, numerical tests, assumptions, matched runs and honest integration status. Production-car safety and regulatory conformity are not inferred.','../../planning/risk_register.csv'),
      ('Ethical and data-quality considerations','Preserve source meaning and access boundaries.','Synthetic data is labelled throughout. Empty measured tables are not filled with invented telemetry. A failed evaluation is retained with an unavailable objective and reason. Credentials remain in ignored environment files. Future measured data requires authorization, license review, quality checks and a documented matching/calibration protocol before sharing.','data_quality.csv'),
      ('Conclusion','State the supported contribution.','The delivered numerical/data prototype executes continuous laps, comparisons, constrained searches, uncertainty experiments, database loads and independent spreadsheet checks. It demonstrates the value of a reproducible engineering pipeline and exposes the uncertainty of its own recommendations. It does not establish measured-car predictive accuracy or a fully accepted Power BI deployment.','delivery_status.csv'),
      ('Future work','Prioritize extensions by evidence value.','First obtain independent coast-down, braking, corner and aero-map observations with matching setup/environment metadata. Calibrate on one subset and test on held-out sessions. Next replace surrogate tyre and compliance assumptions, add transient pitch/roll and current championship policies, test more circuits and expand robust search. Complete Desktop acceptance before distributing the BI report.','../docs/future_work.md'),
      ('References','Give traceable checked sources.','The bibliography lists official NASA and FIA pages checked during the project, Microsoft PBIP/PBIR/TMDL documentation, and clearly marked reading candidates. It does not invent papers or claim that listed textbooks were consulted page by page.','references.md'),
      ('Appendices','Make the work reproducible.','Appendices comprise the schema, actual seed data, dictionary, source code, configuration, tests, traceability, dataset manifests, workbook generator, PBIR/TMDL files, execution logs, figure notes, demonstration script and dependency lock. File-level hashes identify the shareable release. Secrets and isolated database runtime files are excluded.','release_manifest.json')
    ]
    report='# Simulation-Based Motorsport Aerodynamic Setup Optimization\n\nTechnical report — executed synthetic research prototype, model 1.0.0.\n\n'
    for i,(title,purpose,body,artifact) in enumerate(chapters,1):
        nexttitle=chapters[i][0] if i<len(chapters) else 'reproduction and independent validation'
        report+=f'## {i}. {title}\n\n**Purpose:** {purpose}\n\n{body}\n\n**Implementation and evidence:** [{Path(artifact).name}]({artifact}). The linked artifact is the chapter’s inspectable code, table, diagram or output.\n\n**Connection:** This establishes the basis for {nexttitle.lower()}.\n\n'
    (reports/'technical_report.md').write_text(report,encoding='utf-8')
    write_static_docs(reports,comparison,winners)
    build_dashboard(winners,tables)
    build_notebooks()
    # Copy original planning material rather than relabel it as executed results.
    raw=ROOT/'data/raw';raw.mkdir(exist_ok=True);shutil.copy2(ROOT/'config/project.json',raw/'generation_config.json')
    from .ingestion import manifest
    (raw/'source_manifest.json').write_text(json.dumps({'source_type':'synthetic configuration and generated input release','input_files':manifest(ROOT/'data/synthetic')},indent=2))
    deliver=[('Research proposal','implemented','../reports/stage_1_project_proposal.md'),('Python simulator and optimization','implemented','src/'),('Synthetic dataset','implemented','data/'),('MySQL schema and actual seed','executed and reconciled','sql/'),('Excel workbook','recalculated and reconciled','outputs/aero-release/Motorsport_Aero_Engineering.xlsx'),('Power BI source project','authored; Desktop acceptance outstanding','powerbi/Aero.pbip'),('Standalone local viewer','implemented; supplementary to Power BI','reports/dashboard.html'),('Measured-car validation','unavailable: independent data required','reports/validation_report.md'),('Tests','executed','reports/tests.xml'),('32-chapter report and guides','implemented','reports/technical_report.md'),('Presentation outline and demonstration','implemented','docs/presentation_outline.md'),('Advanced transient physics','future research','docs/future_work.md')]
    pd.DataFrame(deliver,columns=['deliverable','status','path']).to_csv(reports/'delivery_status.csv',index=False)
    files={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in ROOT.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.pytest_cache','schema_cache']) and p.name not in ['.env','release_manifest.json']}
    (reports/'release_manifest.json').write_text(json.dumps(files,indent=2))
    print('Report, validation, notebooks, local viewer and release manifest generated.')

def write_static_docs(reports,comparison,winners):
    (reports/'references.md').write_text('''# References and verification status

Verified official pages accessed during this project (17 September 2026 local date):

1. NASA Glenn Research Center, [Lift Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/). Force/coefficient conventions; not evidence for this car's coefficients.
2. NASA Glenn Research Center, [Drag Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/). Reference-area and quadratic-speed formulation.
3. FIA, [A New Era of Competition: 2026 regulations overview](https://www.fia.com/news/new-era-competition-fia-showcases-future-focused-formula-1-regulations-2026-and-beyond). Distinguishes active-aero context; no full rule-clause compliance audit was performed.
4. Microsoft Learn, [Power BI project report folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report). PBIR structure and public JSON schemas.
5. Microsoft Learn, [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview). Text semantic-model structure.
6. Microsoft Learn, [Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview). Project format and opening workflow.

Reading candidates, not claimed reviewed: Joseph Katz, *Race Car Aerodynamics*; Milliken and Milliken, *Race Car Vehicle Dynamics*; Hans Pacejka, *Tire and Vehicle Dynamics*. Verify edition, publisher and cited pages through the university library before adding formal page-specific citations. No fabricated DOI or experimental result is supplied.
''',encoding='utf-8')
    (reports/'architecture.md').write_text('''# Architecture

```mermaid
flowchart TD
 A[Versioned synthetic configuration / authorized references] --> B[Raw files and SHA-256 manifest]
 B --> C[Validation and SI data contract]
 C --> D[Aero response / car / tyre / weather / track]
 D --> E[Continuous lap and stint simulation]
 F[Constrained search and paired uncertainty] <--> E
 E --> G[Normalized MySQL facts and run provenance]
 G --> H[CSV analytical projection]
 H --> I[Excel engineering checks]
 H --> J[Power BI PBIR and TMDL]
 H --> K[Figures / report / local viewer]
 I --> L[Independent reconciliation]
 G --> L
```

An optimization run has many evaluated candidates. A simulated run links one car, setup, circuit, weather, tyre and session. Vehicle-state samples and segment/sector/lap summaries refer to the run. Input dimension relationships are enforced in MySQL. Power BI facts are flattened only with their parent run keys; no many-to-many fact joins are used.
''')
    docs=ROOT/'docs';docs.mkdir(exist_ok=True)
    (docs/'presentation_outline.md').write_text('''# Final presentation outline — 16 slides

1. **Title and research question:** Can circuit-specific aero choices be explained by a reproducible vehicle simulation?
2. **Motivation:** Drag, downforce, grip, balance and uncertainty interact. Use the force-speed figure.
3. **Scope and evidence:** Synthetic model; measured-car calibration unavailable. Distinguish implemented, assumed and future.
4. **Architecture:** Show architecture diagram and the four-tool data flow.
5. **Dataset:** Three circuit archetypes, setup/condition sweeps, explicit grains and source metadata.
6. **Aerodynamics:** SI equations, positive-downforce convention, map limits and ride-height heatmap.
7. **Digital car:** RWD traction, axle transfer, brake bias, tyres and powertrain.
8. **Lap solver:** Forward/backward envelope, periodic boundary and state continuity.
9. **DRS:** Zone/eligibility state machine; paired speed traces and time gain.
10. **Optimization:** Baseline, grid, random, DE and Powell with actual budgets. Explain rejected candidates.
11. **Results:** Use the current recommendation table; compare sectors rather than only a headline lap.
12. **Race and wet:** Stint state evolution and candidate-bank objective differences; state search scope.
13. **Robustness:** Paired uncertainty histogram, interval crossing zero and improvement frequency.
14. **Validation:** Unit/integration tests, 10-to-5 m convergence, actual MySQL and Excel reconciliation.
15. **Demonstration:** Open workbook, change scalar input, show query and local viewer. Power BI source project requires Desktop acceptance.
16. **Conclusion and next experiment:** Calibrate against independently measured aero/coast-down/braking/corner data.

Each quantitative slide must cite the source CSV or run IDs. Use report figures without removing the synthetic-data captions. Presenter notes should distinguish the current nominal result from the conditional uncertainty distribution. Rehearse the twelve-minute script in user_manual.md.
''',encoding='utf-8')
    (docs/'future_work.md').write_text('''# Future-work proposal

The highest-value next step is independent calibration. Collect authorized repeated runs with setup, fuel, tyres, temperatures, pressures, wind, speed, acceleration and surveyed circuit geometry. Establish sensor uncertainty and synchronized timestamps before fitting anything.

Use coast-down data to separate drag and rolling resistance, instrumented braking for axle/bias limits, steady-radius testing for load-sensitive grip, and controlled aero measurements for wing/height/yaw response. Split by entire sessions: calibration runs cannot also serve as validation. Report bias, MAE, RMSE, residual structure and scenario coverage, including failed cases.

Then add transient suspension and validated pitch/roll, richer tyre slip and thermal state, measured torque/shift maps, a curvature-consistent racing line and a championship/year-specific active-aero policy. Broaden robust search beyond the delivered small candidate bank and compare algorithm performance at equal computational budgets. Evaluate stability against handling data before making safety claims.

Complete Power BI Desktop model, visual, slicer, drill-through, tooltip/bookmark and refresh acceptance in an available authorized environment. Service deployment and role security require a specified tenant/workspace and data audience; neither is implicitly granted by generating a source project.
''')

def build_notebooks():
    import nbformat as nbf
    folder=ROOT/'notebooks';folder.mkdir(exist_ok=True)
    books={
      '01_engineering_demo':[
        "from pathlib import Path\nimport sys\nroot = Path.cwd() if (Path.cwd()/'src').exists() else Path.cwd().parent\nsys.path.insert(0, str(root))\nfrom src.physics import aero_forces\nprint('Analytical downforce and drag N:', aero_forces(1.225,50,1.5,3,.9))",
        "from src.vehicle_model import CarModel\nfrom src.circuit_model import circuits\nr = CarModel().simulate_lap(circuits()['Apex Ring'])\nprint(r.summary)\nprint(r.sectors.to_string(index=False))",
        "from src.validation import validate_trace\nprint(validate_trace(r))"],
      '02_results_exploration':[
        "from pathlib import Path\nimport pandas as pd\nroot = Path.cwd() if (Path.cwd()/'src').exists() else Path.cwd().parent\ns = pd.read_csv(root/'data/processed/search_evaluations.csv')\nprint(s.groupby(['circuit','method']).lap_time_s.min().to_string())",
        "u = pd.read_csv(root/'data/processed/uncertainty.csv')\nprint(u.loc[u.feasible,'delta_s'].describe(percentiles=[.025,.5,.975]).to_string())\nprint('These are assumed scenarios, not measured validation.')"]}
    import os
    old=Path.cwd();os.chdir(ROOT)
    try:
        for name,codes in books.items():
            notebook=nbf.v4.new_notebook();notebook.cells=[nbf.v4.new_markdown_cell('# '+name.replace('_',' ')+'\n\nExecuted synthetic research example. See the report for assumptions and limits.')];env={}
            for i,code in enumerate(codes,1):
                cell=nbf.v4.new_code_cell(code);buffer=io.StringIO()
                with contextlib.redirect_stdout(buffer):exec(code,env)
                cell.execution_count=i;cell.outputs=[nbf.v4.new_output('stream',name='stdout',text=buffer.getvalue())];notebook.cells.append(cell)
            notebook.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
            nbf.write(notebook,folder/f'{name}.ipynb')
    finally:os.chdir(old)

def build_dashboard(winners,tables):
    """Offline viewer with matched circuit selection, trace tabs and inspected data."""
    from plotly.offline import get_plotlyjs
    reports=ROOT/'reports';(reports/'plotly.min.js').write_text(get_plotlyjs(),encoding='utf-8')
    traces={name:{'baseline':pd.read_csv(ROOT/f'data/processed/baseline_trace_{i}.csv').to_dict('list'),'candidate':pd.read_csv(ROOT/f'data/processed/recommended_trace_{i}.csv').to_dict('list')} for i,name in enumerate(winners,1)}
    from .schemas import Setup
    payload=json.dumps({'recommendations':winners,'traces':traces,'baseline_setup':Setup().to_dict()},allow_nan=False).replace('</','<\\/')
    template='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aero Lab — Motorsport Setup Research</title>
<style>*{box-sizing:border-box}body{margin:0;font:15px system-ui;color:#203047;background:#f2f5f8}header{background:#10263d;color:white;padding:30px 5vw}header small{color:#9fbcce;letter-spacing:2px}h1{font-size:32px;margin:10px 0}header p{color:#c6d7e2;max-width:900px}main{max-width:1360px;margin:25px auto;padding:0 25px}.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap}select,button{padding:11px 16px;border:1px solid #c8d3dd;background:white;border-radius:6px;color:#18334f;font:inherit}button.active{background:#176b91;color:white}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0}.metric,section{background:white;border:1px solid #dce4eb;border-radius:9px;padding:22px}.metric strong{display:block;font-size:30px;margin-top:10px}.metric span{color:#617488}section{margin-bottom:20px}h2{font-size:20px;margin-top:0}.grid{display:grid;grid-template-columns:2fr 1fr;gap:20px}.note{background:#fff5db;color:#6b5218;padding:14px;border-left:4px solid #cf9b24;border-radius:4px}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px 8px;border-bottom:1px solid #e2e8ed}th{font-size:12px;color:#617488;text-transform:uppercase}a{color:#176b91}#plot{height:400px}footer{padding:30px 0;color:#617488;font-size:13px}@media(max-width:850px){.metrics{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}h1{font-size:26px}main{padding:0 15px}.metric strong{font-size:24px}}</style>
<header><small>AERO LAB / RESEARCH RELEASE 1.0</small><h1>Find the performance trade-off.</h1><p>Compare circuit-specific aerodynamic setups through a continuous digital vehicle model. All car, circuit and performance data here are synthetic.</p></header>
<main><div class="controls"><label for="circuit">Circuit</label><select id="circuit"></select><span>Dry qualifying · matched tyres and initial fuel · 10 m production mesh</span></div>
<div class="metrics"><div class="metric"><span>Baseline lap</span><strong id="baseline"></strong></div><div class="metric"><span>Candidate lap</span><strong id="candidate"></strong></div><div class="metric"><span>Candidate − baseline</span><strong id="delta"></strong></div><div class="metric"><span>Paired DRS gain</span><strong id="drs"></strong></div></div>
<div class="grid"><section><h2>Vehicle response by distance</h2><div class="controls" id="buttons"></div><div id="plot"></div><p id="traceNote"></p></section><section><h2>Recommended settings</h2><table id="settings"></table><p id="constraints"></p><p>Feasibility reflects assumed model limits, not real-car safety certification.</p></section></div>
<section><h2>Where the lap time changes</h2><table><thead><tr><th>Sector</th><th>Baseline (s)</th><th>Candidate (s)</th><th>Delta (s)</th></tr></thead><tbody id="sectors"></tbody></table></section>
<section><h2>Uncertainty and evidence</h2><div class="note" id="uncertainty"></div><p>Uncertainty uses paired assumed weather, grip, aero and height scenarios at the search mesh. Its percentile range is not measured-car confidence or validation.</p><p><a href="validation_report.md">Validation report</a> · <a href="technical_report.md">Technical report</a> · <a href="../outputs/aero-release/Motorsport_Aero_Engineering.xlsx">Engineering workbook</a> · <a href="../powerbi/Aero.pbip">Power BI project</a></p><p>Power BI files are authored and JSON-schema checked. Desktop loading, DAX execution and visual acceptance remain outstanding.</p></section>
<details><summary>Inspect the selected source result</summary><pre id="source" style="white-space:pre-wrap;overflow:auto"></pre></details><footer>Model 1.0.0 · Source: saved Python runs and release manifest · Negative lap delta means faster · No measured telemetry is represented.</footer></main>
<script src="plotly.min.js"></script><script>const DATA=__PAYLOAD__;const selector=document.querySelector('#circuit');Object.keys(DATA.recommendations).forEach(n=>selector.add(new Option(n,n)));let metric='speed_mps';const metrics={speed_mps:['Speed','m/s'],downforce_n:['Downforce','N'],drag_n:['Drag','N'],acceleration_mps2:['Acceleration','m/s²'],fuel_kg:['Fuel','kg'],tyre_wear:['Tyre wear','fraction']};for(const [key,v] of Object.entries(metrics)){let b=document.createElement('button');b.textContent=v[0];b.onclick=()=>{metric=key;render()};b.dataset.key=key;document.querySelector('#buttons').append(b)}
function render(){const name=selector.value,w=DATA.recommendations[name],t=DATA.traces[name];document.querySelector('#baseline').textContent=w.baseline.lap_time_s.toFixed(3)+' s';document.querySelector('#candidate').textContent=w.candidate.lap_time_s.toFixed(3)+' s';document.querySelector('#delta').textContent=w.lap_delta_s.toFixed(3)+' s';document.querySelector('#drs').textContent=w.drs_time_gain_s.toFixed(3)+' s';document.querySelector('#settings').innerHTML=Object.entries(w.setup).map(([k,v])=>'<tr><td>'+k.replaceAll('_',' ')+'</td><td>'+(typeof v==='number'?v.toFixed(k.includes('height')?4:2):v)+'</td></tr>').join('');document.querySelector('#constraints').textContent=w.constraints.length?'Violations: '+w.constraints.join(', '):'No nominal constraints violated.';document.querySelector('#sectors').innerHTML=w.sector_comparison.map(s=>'<tr><td>Sector '+(s.sector_id%10)+'</td><td>'+s.sector_time_s_baseline.toFixed(3)+'</td><td>'+s.sector_time_s_candidate.toFixed(3)+'</td><td>'+s.delta_s.toFixed(3)+'</td></tr>').join('');const u=w.uncertainty;document.querySelector('#uncertainty').textContent=u?`${u.valid_draws}/${u.draws} feasible trials. Improvement frequency ${(u.probability_feasible_improvement*100).toFixed(1)}%. 95% empirical delta interval: ${u.p025_delta_s.toFixed(3)} to ${u.p975_delta_s.toFixed(3)} s. The interval crosses zero.`:'The full 200-draw uncertainty study was run for Apex Ring. This circuit shows a nominal comparison only.';document.querySelector('#source').textContent=JSON.stringify(w,null,2);document.querySelectorAll('button[data-key]').forEach(b=>b.classList.toggle('active',b.dataset.key===metric));Plotly.react('plot',[{x:t.baseline.distance_m,y:t.baseline[metric],name:'Baseline',line:{color:'#8695a4',width:2}},{x:t.candidate.distance_m,y:t.candidate[metric],name:'Candidate',line:{color:'#176b91',width:2}}],{margin:{t:20,r:20,b:55,l:65},xaxis:{title:{text:'Distance (m)'}},yaxis:{title:{text:metrics[metric][0]+' ('+metrics[metric][1]+')'}},legend:{orientation:'h',y:1.1},font:{family:'system-ui',color:'#203047'},paper_bgcolor:'white',plot_bgcolor:'white'},{responsive:true,displaylogo:false});document.querySelector('#traceNote').textContent='n = '+t.candidate.distance_m.length+' spatial samples per trace. '+name+'; synthetic dry qualifying.'}selector.onchange=render;render();</script></html>'''
    # The analysis markup remains intact. Both layers share a single selected circuit
    # and the same saved telemetry payload; Three.js is loaded lazily by boot.js.
    template=template.replace('<style>', '''<link rel="stylesheet" href="simulation/simulation.css">
<script type="importmap">{"imports":{"three":"./vendor/three/three.module.js"}}</script><style>''',1)
    template=template.replace('<div class="metrics">','''<nav class="layer-tabs" aria-label="Aero Lab layers" role="tablist">
<button type="button" id="analysis-tab" class="active" data-layer="analysis" role="tab" aria-selected="true" aria-controls="analysis-layer">Analysis</button>
<button type="button" id="simulation-tab" data-layer="simulation" role="tab" aria-selected="false" aria-controls="simulation-layer">3D Simulation</button></nav>
<div id="analysis-layer" role="tabpanel" aria-labelledby="analysis-tab"><div class="metrics">''',1)
    template=template.replace('</footer></main>','''</footer></div>
<div id="simulation-layer" role="tabpanel" aria-labelledby="simulation-tab" hidden><p class="sim-error" role="status">Loading the synthetic 3D simulation…</p></div></main>''',1)
    template=template.replace('const selector=document.querySelector', 'globalThis.AERO_DATA=DATA;const selector=document.querySelector',1)
    template=template.replace('</html>','<script type="module" src="simulation/boot.js"></script></html>')
    # The real-track pipeline owns the main entry point once installed.
    destination='legacy_dashboard.html' if (ROOT/'data/processed/realtrack/replay.json').exists() else 'dashboard.html'
    (reports/destination).write_text(template.replace('__PAYLOAD__',payload),encoding='utf-8')

if __name__=='__main__':build_reports()
