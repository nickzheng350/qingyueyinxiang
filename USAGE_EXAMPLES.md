# 多级缓存优先队列与并发结构 - 使用示例

**版本**: 1.0.0
**日期**: 2026-05-12

---

## 一、多级缓存优先队列

### 1.1 基本使用

```python
from src.cache import MultiLevelCache, PriorityLevel

# 创建缓存
cache = MultiLevelCache(l1_max_size=1000, l2_max_size=10000)

# 普通放入
cache.put("key1", "value1")

# 高优先级
cache.put_high_priority("key2", "value2")

# 关键优先级
cache.put_critical("key3", "value3")

# 带 TTL
cache.put("key4", "value4", ttl=3600)  # 1小时

# 获取
value = cache.get("key1")
print(value)  # "value1"

# 获取最高优先级项
highest = cache.get_highest_priority()
print(highest.key)  # "key3"

# 弹出最高优先级项
item = cache.pop_highest_priority()
print(item.value)  # "value3"

# 统计
print(cache.stats())
```

### 1.2 异步缓存

```python
from src.cache import AsyncMultiLevelCache, PriorityLevel

async def async_example():
    cache = AsyncMultiLevelCache()

    await cache.put_critical("key", "value")
    value = await cache.get("key")
    print(value)

    stats = await cache.stats()
    print(stats)

# 运行
import asyncio
asyncio.run(async_example())
```

### 1.3 全局缓存

```python
from src.cache import get_global_cache, get_global_async_cache

# 同步全局缓存
sync_cache = get_global_cache()
sync_cache.put("global_key", "global_value")

# 异步全局缓存
async def async_global():
    async_cache = get_global_async_cache()
    await async_cache.put("async_global_key", "async_value")
```

---

## 二、同步/异步/并行结构机制

### 2.1 同步执行

```python
from src.core import ConcurrencyManager

def compute(n: int) -> int:
    return n * n

# 单任务
result = ConcurrencyManager.sync(compute, 42)
print(result.success)    # True
print(result.result)     # 1764
print(result.execution_time)

# 批量任务
tasks = [
    (compute, (1,), {}),
    (compute, (2,), {}),
    (compute, (3,), {}),
]
batch_result = ConcurrencyManager.sync_batch(tasks)
print(f"成功: {batch_result.success_count}, 失败: {batch_result.failed_count}")
```

### 2.2 异步执行

```python
from src.core import ConcurrencyManager

async def async_compute(n: int) -> int:
    await asyncio.sleep(0.1)
    return n * n

async def async_example():
    # 单任务
    result = await ConcurrencyManager.async_(async_compute, 42)
    print(result.result)

    # 批量任务
    tasks = [
        (async_compute, (1,), {}),
        (async_compute, (2,), {}),
        (async_compute, (3,), {}),
    ]
    batch_result = await ConcurrencyManager.async_batch(tasks, max_concurrent=2)
    print(batch_result.total_time)
```

### 2.3 并行执行

```python
from src.core import ConcurrencyManager, parallel_context

def io_intensive_task(n: int) -> int:
    import time
    time.sleep(0.1)
    return n * n

# 单任务并行
result = ConcurrencyManager.parallel(io_intensive_task, 42)
print(result.result)

# 批量并行
tasks = [
    (io_intensive_task, (i,), {}) for i in range(10)
]
batch_result = ConcurrencyManager.parallel_batch(
    tasks,
    executor_name="io_tasks",
    max_workers=5,
)

# 上下文管理器
with parallel_context("temp", max_workers=4) as executor:
    futures = [executor.submit(io_intensive_task, i) for i in range(10)]
    results = [f.result() for f in futures]
```

### 2.4 同步 ↔ 异步转换

```python
from src.core import sync_to_async, async_to_sync

# 同步转异步
@sync_to_async
def sync_func(n: int) -> int:
    return n * n

async def use_sync():
    result = await sync_func(42)
    print(result)

# 异步转同步
@async_to_sync
async def async_func(n: int) -> int:
    await asyncio.sleep(0.1)
    return n * n

def use_async():
    result = async_func(42)
    print(result)
```

### 2.5 统一执行器

```python
from src.core import UnifiedExecutor, ExecutionMode

def my_func(n: int) -> int:
    return n * n

# 自动选择模式
result = UnifiedExecutor.execute(my_func, 42)
print(result.mode)  # ExecutionMode.SYNC

# 指定模式
result = UnifiedExecutor.execute(
    my_func, 42,
    mode=ExecutionMode.PARALLEL,
)
print(result.mode)  # ExecutionMode.PARALLEL
```

---

## 三、结合使用示例

### 3.1 任务处理流水线

```python
from src.cache import MultiLevelCache, PriorityLevel
from src.core import ConcurrencyManager

class TaskProcessor:
    def __init__(self):
        self.cache = MultiLevelCache()

    def process_task(self, task_id: str, data: Any) -> Any:
        # 先检查缓存
        cached = self.cache.get(task_id)
        if cached is not None:
            return cached

        # 处理任务
        result = self._compute(data)

        # 缓存结果
        self.cache.put_high_priority(task_id, result, ttl=3600)
        return result

    def _compute(self, data: Any) -> Any:
        return data * 2


def main():
    processor = TaskProcessor()

    # 批量处理
    tasks = [
        (processor.process_task, (f"task_{i}", i), {})
        for i in range(100)
    ]

    # 并行执行
    result = ConcurrencyManager.parallel_batch(
        tasks,
        max_workers=8,
    )

    print(f"完成: {result.success_count}/{result.total_count}")
```

---

## 四、完整示例

见项目根目录的示例代码。
