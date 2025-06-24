---
applyTo: '**'
---

# 总体要求
- 胖服务端策略：前后端沟通的核心是 websocket 里的 insights。后端直接生成完整 insights message，前端不应该动态更新数据。
- 不要 Overengineering！不要 Overengineering！不要 Overengineering！保持代码实现简短简单。如果可能，减少代码的更改。

# 具体代码提示
- 对多摄像头（多 monitor.py）的支持要格外留意。
- 时间的数据类型统一采用 time.time() 转 int 的秒级时间戳。不要用 datetime。这样在嵌入式端也更好操作。
