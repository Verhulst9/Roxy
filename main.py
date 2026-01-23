from tasks import app
from tasks.interaction import process_user_input
from tasks.reflection import consolidate_memory

# 1. 处理用户输入（高优先级，立即执行）
process_user_input.apply_async(
    args=("你好，Nakari", "user_123"),
    queue="high_priority"
)

# 2. 触发记忆整理（低优先级，后台执行）
consolidate_memory.apply_async(
    queue="low_priority"
)