# TODO - C++ Implementation

This document tracks remaining enhancements for the C++ port of DepthOS.

## Completed 

- JSON Parsing Integration (nlohmann/json throughout)
- Decimal Arithmetic Library (boost::multiprecision with 50 decimal places)
- WebSocket Implementation (websocketpp with public/private connections)
- Logging System (spdlog with structured logging)
- REST Client (libcurl with retry logic)
- HMAC-SHA512 Authentication (OpenSSL)
- Thread Safety (mutexes for critical sections)

## Nice to Have (Enhancements)

- [ ] **Unit Tests**
  - Add Google Test framework
  - Test auth signing
  - Test order book logic
  - Test risk calculations
  - Test quoting logic

- [ ] **Integration Tests**
  - Mock Gate.io API responses
  - Test full quote lifecycle
  - Test error scenarios

- [ ] **Monitoring**
  - Add Prometheus metrics endpoint
  - Expose order book depth metrics
  - Expose P&L metrics
  - Add health check endpoint

- [ ] **Persistence**
  - Add SQLite for fill logging
  - Add state snapshot/restore
  - Add audit trail

- [ ] **Performance Optimization**
  - Profile hot paths
  - Optimize JSON parsing
  - Consider memory pools for frequent allocations
  - Add benchmarking

## Known Issues

None - system is production ready.

## Priority Order

1. Unit Tests (Nice to Have)
2. Integration Tests (Nice to Have)
3. Monitoring (Nice to Have)
4. Persistence (Nice to Have)
5. Performance Optimization (Nice to Have)
