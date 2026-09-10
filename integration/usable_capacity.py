"""Joined, static-window research experiment; no fleet control or hidden losses.

Physical admission -> actual rectangular allocation -> healthy communication
model -> recovery timeline -> retained compute service. Existing packages own
each model. Uniform healthy-step conversion of retained runtime is an explicit
assumption here, NOT a general product of portfolio capacity fractions.
"""
import argparse
import dataclasses
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

REPOS=Path(__file__).resolve().parents[2]
for name in ('cooling-pue-ladder','scheduler-vs-more-gpus','slice-packer-torus','network-vs-more-gpus'):
    sys.path.insert(0,str(REPOS/name));sys.path.insert(0,str(REPOS/name/'src'))
from cooling.admission import Hall, Feeder, Start, admit
from cooling.ladder import rung
from slicepacker import Fabric, Topology, Request, NoPlacement
from capacity.placement import placement_preview
from netcap.config import load_scenario, replace_nested
from netcap.performance import step_breakdown
import numpy as np

def reliability_module():
    path=REPOS/'reliability-economics/sim/reliability_sim.py'
    spec=importlib.util.spec_from_file_location('joined_reliability',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def scenario(*, feed_mw=.6, degraded=True, network_efficiency=.65, reload_h=.25, seed=0,
             shape=(8,8,8), gang_size=128, seq_len=8192, failure_rate=1.58e-4):
    nominal=math.prod(shape); horizon=24*30
    if gang_size not in (64,128,256) or any(type(x) is not int or x<1 for x in shape):
        raise ValueError('supported gangs are 64/128/256; dimensions must be positive integers')
    racks=gang_size/64
    # 64 accelerators/rack at 1.275 kW system power each. Power conversion is
    # a scenario based on the DGX maximum system/node ratio, not measured draw.
    hall=Hall('h','f',rung('direct-to-chip'),81.6,0,feed_mw)
    feeder=Feeder('f',feed_mw,feed_mw)
    fabric=Fabric(Topology(shape,(True,True,True)))
    if degraded:
        fabric.unhealthy.update((x,y,z) for x in range(1,shape[0],2) for y in range(shape[1]) for z in range(shape[2]))
    requests=[Request(f'job-{i}',gang_size) for i in range(nominal//gang_size)]
    count_only=min(fabric.free_chips()//gang_size, int(feed_mw/hall.facility_mw(racks)))*gang_size
    rows=[]; retained=0.; communication=0.; recovery_loss=0.; allocated=0
    r=reliability_module()
    for request in requests:
        admission=admit(Start(request.job_id,{'h':racks},min_ride_through_s=5),{'h':hall},{'f':feeder})
        if not admission.admitted:
            rows.append(dict(job=request.job_id,decision=admission.verdict,reasons=list(admission.reasons)));continue
        preview=placement_preview(fabric,[request])
        if preview['requests'][0]['status']!='placeable':
            rows.append(dict(job=request.job_id,decision='no-rectangle',preview=preview));continue
        rect=fabric.place(request)
        hall=dataclasses.replace(hall,racks_running=hall.racks_running+racks)
        allocated += request.chips
        net=load_scenario(REPOS/'network-vs-more-gpus/configs/scenarios/reference_405b_16k.yaml')
        net=replace_nested(net,**{'parallelism.dp':1,'parallelism.pp':gang_size//8,
                                 'model.seq_len':seq_len,'topology.net_efficiency':network_efficiency})
        assert net.parallelism.world_size==rect.chips
        step=step_breakdown(net)
        cfg=r.Config(nodes=rect.chips//8,horizon_h=horizon,seed=seed,reload_h=reload_h,spare_nodes=0,
                     single_rate_per_node_h=failure_rate)
        events=r.latent_events(cfg,np.random.default_rng(seed))
        recovered=r.Sim(cfg,'auto-restart',events).run()
        retained_runtime=recovered['productive_gpu_h']
        healthy_compute_share=step.t_compute/step.t_step
        useful=retained_runtime*healthy_compute_share
        comm=retained_runtime-useful
        lost=request.chips*horizon-retained_runtime
        retained+=useful;communication+=comm;recovery_loss+=lost
        rows.append(dict(job=request.job_id,decision='allocated',origin=rect.origin,extent=rect.extent,
                         recovery=recovered,healthy_step_s=step.t_step,compute_step_s=step.t_compute,
                         useful_compute_gpu_h=useful))
    unavailable=(nominal-allocated)*horizon
    buckets=dict(not_admitted_gpu_h=unavailable,recovery_and_discard_gpu_h=recovery_loss,
                 retained_communication_and_bubble_gpu_h=communication,useful_compute_gpu_h=retained)
    assert math.isclose(sum(buckets.values()),nominal*horizon,abs_tol=1e-6)
    return dict(evidence_class='simulated',input_class='scenario',seed=seed,horizon_h=horizon,
                feed_mw=feed_mw,degraded=degraded,network_efficiency=network_efficiency,reload_h=reload_h,
                shape=shape,gang_size=gang_size,seq_len=seq_len,failure_rate_per_node_h=failure_rate,
                nominal_gpu_h=nominal*horizon,count_only_admission_gpus=count_only,
                actual_allocated_gpus=allocated,buckets=buckets,jobs=rows,
                limitations=['Static simultaneous gang allocation, not a time-varying fleet scheduler.',
                             'Local hall only; span admission is not applicable and is not claimed.',
                             'Torus provides geometry, not a calibrated H100 fabric performance mapping.',
                             'Independent node failures during the window; initial degraded geometry is distinct.',
                             'Recovery owns checkpoint/restart/lost work; netcap supplies healthy steps ONLY.',
                             'Constant healthy-step mix splits retained runtime; no overlapping UCF multiplication.',
                             'No job completion/deadline or training convergence modeled.',
                             'No intervention cost evidence: rank recovered compute, not investment ROI.'])


def experiment():
    variants={'baseline':{},'restore_geometry':{'degraded':False},
              'wider_network':{'network_efficiency':.9},'more_power':{'feed_mw':1.2},
              'restore_and_network':{'degraded':False,'network_efficiency':.9},
              'restore_and_recovery':{'degraded':False,'reload_h':.05}}
    runs={name:[scenario(seed=s,**kw) for s in range(12)] for name,kw in variants.items()}
    means={name:float(np.mean([r['buckets']['useful_compute_gpu_h'] for r in rows])) for name,rows in runs.items()}
    return dict(schema_version='joined-capacity/v1',runs=runs,mean_useful_compute_gpu_h=means,
                finding='Network or power alone cannot recover capacity that lacks an admissible rectangle.',
                network_geometry_interaction_gpu_h=means['restore_and_network']-means['restore_geometry']-means['wider_network']+means['baseline'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=Path('integration/results.json'))
    a=p.parse_args();report=experiment();a.out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['mean_useful_compute_gpu_h'],indent=2))
