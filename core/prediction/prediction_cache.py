"""
Prediction Cache (Phase-2 User Intelligence)
Constraint 7: Prediction Throttling.
Maintains a prediction cache for the current planning cycle.
"""

_cache = {}
_current_cycle_id = None

def get_prediction(prediction_type: str, cycle_id: str):
    global _current_cycle_id, _cache
    if cycle_id != _current_cycle_id:
        _current_cycle_id = cycle_id
        _cache.clear()
    return _cache.get(prediction_type)

def set_prediction(prediction_type: str, cycle_id: str, result: dict):
    global _current_cycle_id, _cache
    if cycle_id != _current_cycle_id:
        _current_cycle_id = cycle_id
        _cache.clear()
    _cache[prediction_type] = result
