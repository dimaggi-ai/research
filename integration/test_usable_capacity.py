from usable_capacity import scenario
import math


def test_joined_conservation_and_interaction():
    blocked=scenario()
    assert blocked['count_only_admission_gpus']>0
    assert blocked['actual_allocated_gpus']==0
    assert scenario(network_efficiency=.9)['buckets']['useful_compute_gpu_h']==0
    base=scenario(degraded=False)
    faster=scenario(degraded=False,network_efficiency=.9)
    assert base['actual_allocated_gpus']>0
    assert faster['buckets']['useful_compute_gpu_h']>base['buckets']['useful_compute_gpu_h']
    assert scenario(degraded=False,feed_mw=.1)['actual_allocated_gpus']==0


def test_matrix_conservation_and_rank_changes():
    from scenario_matrix import experiment
    matrix=experiment(seeds=[0])
    for case in matrix['scenarios']:
        for rows in case['runs'].values():
            for result in rows:
                assert math.isclose(sum(result['buckets'].values()),result['nominal_gpu_h'],abs_tol=1e-6)
                assert all(v>=0 for v in result['buckets'].values())
        assert all(v>=-1e-6 for v in case['single_intervention_delta_gpu_h'].values())
    ranks={tuple(c['ranking']) for c in matrix['scenarios']}
    assert len(ranks)>1
