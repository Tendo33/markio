import pickle
from datetime import datetime

import pytest

from markio.utils.redis_utils import RedisCache


def test_deserialize_rejects_non_json_payload():
    payload = pickle.dumps({"danger": "value"})
    assert RedisCache._deserialize(payload, use_pickle=False) is None


def test_serialize_non_json_value_raises_even_with_pickle_flag():
    with pytest.raises(TypeError):
        RedisCache._serialize({"time": datetime.now()}, use_pickle=True)
