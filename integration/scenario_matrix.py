"""Predeclared contrasting scenarios; not samples of production fleet prevalence."""
import json
from pathlib import Path
from itertools import combinations
from usable_capacity import scenario

# Chosen by physical/model axes, not by retaining runs with desirable rankings.
# All scenarios and all seeds are reported, including zero-effect interventions.
CASES={
 'healthy_balanced':dict(degraded=False,feed_mw=1.2),
 'power_limited':dict(degraded=False,feed_mw=.3),
 'geometry_limited':dict(degraded=True,feed_mw=1.2),
 'small_gang_long_context':dict(degraded=True,feed_mw=.6,gang_size=64,seq_len=16384),
 'large_gang_flat_geometry':dict(degraded=False,shape=(4,8,16),gang_size=256,feed_mw=.6),
 'network_and_failures':dict(degraded=False,feed_mw=1.2,network_efficiency=.25,
                             reload_h=1.,failure_rate=.001,seq_len=4096),
}
INTERVENTIONS={
 'geometry':dict(degraded=False), 'power':dict(feed_mw=1.5),
 'network':dict(network_efficiency=.95), 'recovery':dict(reload_h=.05),
}

def experiment(seeds=range(4)):
    seeds=list(seeds); output=[]
    for name,base in CASES.items():
        variants={'baseline':{}}
        variants.update(INTERVENTIONS)
        for a,b in combinations(INTERVENTIONS,2): variants[a+'+'+b]={**INTERVENTIONS[a],**INTERVENTIONS[b]}
        runs={k:[scenario(**{**base,**v},seed=s) for s in seeds] for k,v in variants.items()}
        means={k:sum(x['buckets']['useful_compute_gpu_h'] for x in rows)/len(rows) for k,rows in runs.items()}
        delta={k:means[k]-means['baseline'] for k in INTERVENTIONS}
        interaction={a+'+'+b:means[a+'+'+b]-means[a]-means[b]+means['baseline'] for a,b in combinations(INTERVENTIONS,2)}
        output.append(dict(name=name,inputs=base,runs=runs,mean_useful_gpu_h=means,
                           single_intervention_delta_gpu_h=delta,pair_interaction_gpu_h=interaction,
                           ranking=sorted(delta,key=delta.get,reverse=True),
                           no_effect=[k for k,v in delta.items() if abs(v)<1e-6]))
    return dict(schema_version='joined-scenario-matrix/v1',evidence_class='simulated',input_class='scenario',
                seeds=seeds,scenarios=output,
                limitations=['Axes selected before execution; not randomized fleet sampling or prevalence estimates.',
                             'Identical seeds within comparisons are common random numbers, not independent job failures.',
                             'Static homogeneous gangs; PP degree changes with gang size; no convergence equivalence claim.',
                             'Intervention ranks compare useful GPU-hours, not costs or universal investment value.',
                             'Healthy geometry and power/noise margins are synthetic, not measured or calibrated.'])

if __name__=='__main__':
    report=experiment();Path('integration/scenario-matrix.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for s in report['scenarios']:
        print(s['name'],json.dumps(s['single_intervention_delta_gpu_h']),s['no_effect'])
