import math
import uuid


# 生成一个随机的 UUID4
def generate_uuid():
    return str(uuid.uuid4())


def handle_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value
