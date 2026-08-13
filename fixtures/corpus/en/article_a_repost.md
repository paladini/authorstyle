---
title: Distributed databases overview
date: 2025-02-01
language: en
mode: technical
source: devto
---

# Distributed databases overview

You cannot scale every system by adding a bigger machine. Sometimes you need many nodes.

Partition tolerance matters. When the network fails, what guarantees remain?

## Consistency models

Strong consistency is simple to reason about. Eventual consistency trades latency for availability.

```sql
SELECT * FROM nodes WHERE status = 'healthy';
```

That query is straightforward, but replication lag can surprise you.

## Closing thoughts

Choose the model that matches your failure tolerance—not the trendiest blog post.
