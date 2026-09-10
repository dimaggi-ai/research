# Infrastructure Intelligence: existing implementation and extension plan

Source of truth: [the organization inventory](https://github.com/orgs/dimaggi-ai/repositories), then the checked-out code. Assessment recorded before implementation. This is a research portfolio, not one deployed Infrastructure Intelligence product. No new repository is justified for this pass.

## Public portfolio classification

Each repository has one primary classification; a supporting role does not imply that its model is calibrated for a different domain.

| Repository | Classification | Code evidence and boundary |
| --- | --- | --- |
| [scheduler-vs-more-gpus](https://github.com/dimaggi-ai/scheduler-vs-more-gpus) | Core system | `sim/simulator.py`: seeded fleet allocation, three policies, training/inference mix, failure events, surges, power caps, checkpoint/resize overhead and a capacity ledger. `calculator/stranded_capacity.py` is factor accounting. No Kubernetes or Slurm client; those are policy analogies and case studies. Placement is abstract, inference demand aggregate. |
| [network-vs-more-gpus](https://github.com/dimaggi-ai/network-vs-more-gpus) | Research model | `src/netcap/accounting.py`, `collectives.py`, `performance.py`, `metrics.py`: four-fate accelerator-time accounting, hierarchical communication, scaling and substitution-equivalent accelerators. Model-derived network loss, not a fabric telemetry collector. |
| [reliability-economics](https://github.com/dimaggi-ai/reliability-economics) | Research model | `sim/reliability_sim.py`: shared latent events, common-cause bursts, finite spares, repair/requalification/reload clocks, checkpoint costs, legal-shape shrink, ETTR/goodput and dollar costs. One gang training job, not a second general scheduler. MTTF/MTTR diagnostics are explicit; do not silently relabel them MTBF. |
| [ai-cluster-chaos-fidelity](https://github.com/dimaggi-ai/ai-cluster-chaos-fidelity) | Standard / contract | `catalog/validate.py`, `test_validate.py`, `coverage.py`: validates fault-layer fidelity, bounded experiments, undo and autonomous-action prohibitions. The 25-spec catalog describes experiments; it does not execute GPU, DCGM or InfiniBand faults. |
| [slice-packer-torus](https://github.com/dimaggi-ai/slice-packer-torus) | Core system | `src/slicepacker/packing.py`, `tenant.py`, `cordon.py`, `reconstitute.py`: rectangular allocation, fragmentation, hardware exclusion, isolation and permission-aware reconstitution. No scheduler service, link-routing simulator or general fat-tree placement engine. |
| [span-contract](https://github.com/dimaggi-ai/span-contract) | Standard / contract | `src/spancontract/envelope.py`, `rules.py`, `validator.py`: local/span/shrink/move/escalate/deny, freshness, topology, power, checkpoint and tenant predicates. Preserves explicit `not_checked` gaps. Compile cache is NOT inference prefix/KV cache. |
| [compute-power-placement](https://github.com/dimaggi-ai/compute-power-placement) | Research model | `calc/move_vs_stay.py`, `fleet/fleet_sim.py`, `span/stay_stitch_move.py`: energy scarcity, curtailment policy, migration and stay/stitch/move economics. Destination capacity and linear scaling are material assumptions. Moving workload does not transfer electricity between sites. |
| [governed-autonomy](https://github.com/dimaggi-ai/governed-autonomy) | Standard / contract | `gate/validate_promotion.py` implements autonomy-promotion rules; `gate/synthetic_gate_check.py` tests refusals. Five-plane architecture and latency exhibit exist. No production reconciler or cluster actuator here; experiment references are not proof of execution. |
| [airan-neocloud-resiliency](https://github.com/dimaggi-ai/airan-neocloud-resiliency) | Supporting infrastructure model | `resiliency/sim.py`, `transports.py`, `site.py`: shared storms, SRLG cuts, transport eligibility, power/timing and capacity retention by workload class. Monte Carlo model, not measured GPU-fabric health. |
| [edge-continuum-placement](https://github.com/dimaggi-ai/edge-continuum-placement) | Supporting infrastructure model | `continuum/place.py`, `physics.py`, `fleet.py`: fabric/power/latency/gravity gates and discrete site capacity. Siting engine, not per-request inference routing. |
| [cooling-pue-ladder](https://github.com/dimaggi-ai/cooling-pue-ladder) | Supporting infrastructure model | `cooling/capacity.py`, `admission.py`: feed/PUE capacity, rack density, thermal ride-through, hall headroom and feeder-step admission. Physical feasibility must not be replaced by a generic scheduler power percentage. |
| [optical-circuit-intent](https://github.com/dimaggi-ai/optical-circuit-intent) | Supporting infrastructure model | `src/ocintent/radix.py`, `drift.py`, `hedge.py`, `adapters/tapi.py`: port allocation, retune/checkpoint costs, optical drift and measured-data analysis; TAPI plans are rendered, not sent. Optical precursors are not NCCL causality. |
| [research](https://github.com/dimaggi-ai/research) | Portfolio/index | `README.md` and `index.html` aggregate research. Put ownership/interface navigation here, not runtime engines. |

Two additional private infrastructure repositories were assessed in a separate local appendix. Their implementation and licensing do not become public dependencies or source material through this report.

## Required capability mapping (before coding)

“Improve existing” identifies the destination, not a claim that a production feature already exists. Near-term modules must retain the existing repositories' independent scope and release lifecycle.

| Capability | Existing implementation | Best destination | Action |
| --- | --- | --- | --- |
| Prefix/cache-aware inference routing | Aggregate inference demand in scheduler; site eligibility in edge placement. No request-level KV/prefix cache router found. Span's compile cache is unrelated. | Scheduler: bounded inference-routing simulation module; edge model supplies regional eligibility. | Improve existing first; no standalone router justified until an actual serving interface and release lifecycle are established. Deferred beyond this integration slice. |
| Fleet simulation | Scheduler already implements workload arrivals, allocation policies, failures, surges, power envelopes and usable-capacity reporting; compute-power has price/curtailment fleet simulation. | Scheduler for allocation; compute-power for scarcity economics. | Improve existing: add reproducible JSON replay/reporting. Reject a duplicate `fleet-sim` repository. |
| Workload-native capacity units | Scheduler GPU-hour ledger; network tokens/s and substitution metrics; power useful GPU-hour costs. Different denominators and productive-work definitions. | Scheduler report module with explicit workload calibration; network keeps its own accounting. | Improve existing: workload-specific projections and comparable-baseline checks. Reject a universal hardware-equivalence scalar and a new `capunit` repo. |
| NCCL observability | Network communication models; chaos taxonomy distinguishes NCCL timeout layers. No live collector/parser in inspected public implementations. | Network `netcap` observability module. | Improve existing with offline, explicitly matched benchmark evidence first; production collection requires real traces and instrumentation validation. No `nccl-lens` repository now. |
| Fabric degradation detection | Network efficiency inputs; optical declared/measured drift and HEDGE analysis; chaos layer taxonomy. | Network for collective degradation evidence, optical for optical path physics. | Improve existing. A slowdown is evidence, not proof of a network fault. No separate `fabric-probe` simulator. |
| Cross-layer fault correlation | Chaos fault/layer contracts, optical timelines, reliability event models; no validated end-to-end causal correlator. | Network offline evidence module, referencing chaos scenario IDs and topology scope. | Improve existing with evidence association before causal inference; preserve unknown cause. Do not create another reliability engine. |
| Topology-aware scheduling | Slice-packer supplies geometric allocation/isolation/reconstitution; span supplies admission. Scheduler currently abstracts placement. | Scheduler adapter consuming slice-packer and span, not copied algorithms. | Improve existing: offline placement preview, independent admission verdicts and safe refusals. Production Kubernetes/Slurm bindings remain future work. |
| Capacity twin | Several executable scenario models; no synchronized, observed-fleet state/twin. | Scheduler replay/report interface with source/config provenance; downstream domain adapters. | Improve existing: scenario replay foundation. Reject the claim that replay alone is a live digital twin. |
| Closed-loop infrastructure actions | Governed-autonomy promotion gate and architecture; public optical plans are inert. Private infrastructure control implementation assessed separately. | Keep public promotion policy in governed-autonomy; use existing domain execution boundary where authorized. | Improve existing integration boundaries, not another generic controller. No live actions in this assignment. |
| Shared infrastructure schema | Span envelopes, chaos experiment contracts, optical intent types and unrelated domain-specific ledgers already exist. | Small versioned scheduler capacity-report contract; each domain retains its own schema. Research documents relationships. | Improve existing with a narrow exchange schema, not an all-purpose infrastructure ontology or schema monorepo. |

## Accidental overlap and interfaces

1. **Two fleet simulators are not the same simulator.** Scheduler owns job allocation/time; compute-power owns price/scarcity/curtailment. Share time-window and workload identifiers at the boundary, not the engines.
2. **Recovery is modeled three times at different fidelities.** Scheduler's coarse interruptions and network's analytical/Monte Carlo recovery are bounded assumptions; reliability-economics owns detailed recovery-policy experiments. A future event adapter must define failure scope, node/accelerator conversion, seed, repair clocks and handling of concurrent faults. Do not replay a failure and multiply a recovery penalty for that same event.
3. **Capacity labels collide.** Scheduler “productive” credits allocated inference up to aggregate demand and training progress including communication abstractions; network productive time excludes exposed communication and discarded work. Network UCF, scheduler realization, reliability goodput, edge retention and PUE are not independent factors. Preserve numerator, denominator, unit, workload, window and evidence kind.
4. **Topology and admission already have owners.** Slice-packer returns placement candidates; span returns permission and missing checks; optical owns circuit provisioning/retune constraints; cooling owns physical start constraints. A geometrically placeable job can still be inadmissible. A denied or partially checked decision is not repaired by a favorable economic score.
5. **Similar communication formulas do not establish interchangeable models.** Network hierarchical collectives, edge distance envelopes and compute-power's named-cut tax answer different questions. Consume explicit evaluated results where their domains match; do not copy one formula over another without cross-model tests.
6. **A scenario fixture is not a fault injector or certification.** Chaos remains the source of fault identity/fidelity and safety constraints. Consumers must separately declare synthetic parameters; catalog presence or a “green” local simulation does not authorize promotion.
7. **Optical drift is already implemented.** Reuse that domain model rather than build another generic path-health simulator. NCCL benchmark regression and optical degradation can be associated by scope/time; neither alone proves the other.
8. **Prefix routing is genuinely missing, but absence is insufficient for a new repo.** Start with a bounded scheduler experiment and realistic trace data. A real router needs cache ownership/eviction, queueing, model identity, placement feasibility and TTFT/TPOT validation before it merits an independently operated service.

## Implementation slice chosen

Implement a narrow, offline capacity interface inside scheduler: repeatable simulator replay, versioned output, explicitly qualified workload-rate projections, strict comparison guards, and a placement preview that imports existing torus and span APIs. Add matched offline collective-benchmark comparison inside netcap, with no automatic model calibration, fabric root-cause claims or live probes.

This connects existing implementations without changing the original study algorithms or published numerical results. Further routing, live telemetry, event replay across engines, production reconciliation and causal fault attribution remain separate tested increments, not features to announce as completed.

## Evidence revisions

These revisions identify the inspected baseline, before the local extensions.
The implemented increment adds scheduler replay/reporting and geometry/admission
previews, plus normalized offline collective comparison in netcap. It does not
complete the deferred live capabilities listed above. No new repository was created.

- [research @ 009cbf39f0d4](https://github.com/dimaggi-ai/research/tree/009cbf39f0d4ba2f04909328577cd1718b1d904b)
- [scheduler-vs-more-gpus @ dd4f012f0501](https://github.com/dimaggi-ai/scheduler-vs-more-gpus/tree/dd4f012f0501f4f7cda951b7dc35d3c125342168)
- [network-vs-more-gpus @ 462dfd981cbe](https://github.com/dimaggi-ai/network-vs-more-gpus/tree/462dfd981cbe341d1ddb094767dbf1728446cc9b)
- [reliability-economics @ 0989c6ef1fb8](https://github.com/dimaggi-ai/reliability-economics/tree/0989c6ef1fb896ffcbfe0ab50d308b77a79c1d51)
- [ai-cluster-chaos-fidelity @ 11be3796f66c](https://github.com/dimaggi-ai/ai-cluster-chaos-fidelity/tree/11be3796f66cd8b70d7d181ae7ed801c7fe22fae)
- [slice-packer-torus @ b758791c5bce](https://github.com/dimaggi-ai/slice-packer-torus/tree/b758791c5bce05f28b946438534513f0a578c0e1)
- [span-contract @ 8400ada63e20](https://github.com/dimaggi-ai/span-contract/tree/8400ada63e20e87f297003a78c6229e65c57c251)
- [compute-power-placement @ babaa54fcd39](https://github.com/dimaggi-ai/compute-power-placement/tree/babaa54fcd3910ba35d9e512e89060ccdbc715d1)
- [governed-autonomy @ 8e23f89f3ce9](https://github.com/dimaggi-ai/governed-autonomy/tree/8e23f89f3ce909e70cb1b190ec7442b3fca0a708)
- [airan-neocloud-resiliency @ 44a0ee4b8922](https://github.com/dimaggi-ai/airan-neocloud-resiliency/tree/44a0ee4b8922f00bcc3826ea91099ff52e867ee4)
- [edge-continuum-placement @ a5a7db031317](https://github.com/dimaggi-ai/edge-continuum-placement/tree/a5a7db03131798353a392e37117aff639ef4f7c0)
- [optical-circuit-intent @ 836e2cc04414](https://github.com/dimaggi-ai/optical-circuit-intent/tree/836e2cc0441488940f4ad0ca11807c44c49a3bef)
- [cooling-pue-ladder @ 85fa5223e974](https://github.com/dimaggi-ai/cooling-pue-ladder/tree/85fa5223e9745b93dee49e6f23d0458e0db08bd5)
