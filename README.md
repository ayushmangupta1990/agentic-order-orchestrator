# Agentic Order Orchestrator

[![CI](https://github.com/ayushmangupta1990/agentic-order-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/ayushmangupta1990/agentic-order-orchestrator/actions/workflows/ci.yml)

A small, executable reference implementation of a supervisor-worker order
workflow. It demonstrates typed state, deterministic routing, idempotency,
inventory reservation, bounded execution, and an auditable event trail.

This public portfolio version uses in-memory services and synthetic orders. It
contains no employer code, client data, model weights, or production claims.

## Run

```bash
python order_orchestrator.py
python -m unittest -v
```

## Architecture

`validate → reserve inventory → dispatch → complete`

The supervisor stops on rejection and caches terminal results using a payload
hash. The worker boundaries are intentionally simple so real database, queue,
LLM, and optimization adapters can be introduced without changing state
transitions.

## Production extensions

- Durable state and transactional outbox
- Kafka-backed workers with retry/dead-letter policies
- Human approval interrupts for low-confidence extraction
- OpenTelemetry traces and per-worker service-level objectives
- Policy-constrained alternative-SKU and fleet optimization tools

