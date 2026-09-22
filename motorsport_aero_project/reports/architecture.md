# Architecture

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
