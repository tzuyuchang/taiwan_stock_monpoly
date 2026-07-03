# System Design Document  
**Project:** FinTech Gaming Platform (Hybrid Financial & Gaming Experience)  
**Author:** Principal Systems Architect – FinTech & Gaming  
**Date:** 2026‑06‑13  

---  

## 1. Overview  

The platform combines real‑time market data, portfolio management, and gamified trading mechanics. Users can trade stocks/crypto, earn game‑style rewards, and compete on leader‑boards. The system must be highly available, low‑latency for market feeds, and provide a seamless cross‑platform experience on iOS, Android, Web, and desktop (via Unity).

---

## 2. High‑Level Architecture  

```
+-------------------+          +-------------------+          +--------------------+
|  Front‑end Clients|          |   API Gateway     |          |  Admin / Analytics |
| (React Native,    |  HTTPS   | (NGINX/Envoy)     |  gRPC    |   Dashboard        |
|  Web React, Unity|<-------->|  Auth, Rate‑Limit |<-------->|  (Grafana/ELK)     |
+--------+----------+          +----+--------+-----+          +---------+----------+
         |                         |   |    |                      |
         |                         |   |    |                      |
         |                         |   |    |                      |
+--------v----------+    gRPC     v   v    v   Kafka (event)   +---v-----------------+
|  Backend Services |----------->| Trade Service |<----------------| Real‑time Feed   |
| (Micro‑services)  |  HTTP/REST | (order‑book,  |   +---+        | Service (Kafka) |
|  - Auth Service   |            |  matching)   |   |   |        +-------------------+
|  - User Service   |            +--------------+   |   |
|  - Portfolio svc  |                               |   |
|  - Market Data svc|---+                           |   |
|  - Game Logic svc |   |    +----------------------+   |
|  - Notification   |   |    |   Event Bus (Kafka)  |   |
+--------+----------+   |    +----------------------+   |
         |              |                               |
         |              |                               |
         |              v                               v
         |        +------------+                 +-------------+
         |        |  Cache Layer|                 |  Persistence |
         |        | (Redis,    |                 | (PostgreSQL, |
         |        |  Memcached)|                 |  TimescaleDB)|
         |        +------+-----+                 +------+------+
         |               |                               |
         |               |                               |
         v               v                               v
   +-----+-----+   +-----+-----+                 +-------+-------+
   |  CDN (Edge) |   |  Search   |                 |  Object Store |
   | (Akamai/   |   | Service   |                 | (S3/MinIO)    |
   | CloudFront)|   | (Elasticsearch)           |               |
   +------------+   +-----------+                 +---------------+

```

### Key Components  

| Layer | Service | Responsibilities |
|-------|---------|------------------|
| **API Gateway** | NGINX/Envoy | TLS termination, request routing, auth, rate limiting |
| **Auth Service** | OAuth2 + JWT (Keycloak) | User registration, MFA, token issuance |
| **User Service** | CRUD for profile, preferences | Handles KYC status, device links |
| **Portfolio Service** | Aggregates positions, calculates P&L | Uses read‑through cache, writes to PostgreSQL |
| **Trade Service** | Order validation, matching engine (limit/market) | Real‑time processing via gRPC, publishes trade events |
| **Market Data Service** | Ingests vendor feeds, normalises, stores time‑series | Uses TimescaleDB for OHLCV, provides subscription API |
| **Game Logic Service** | Quest/mission engine, reward calculations | Consumes trade & market events, updates player achievements |
| **Notification Service** | Push (FCM/APNs), email, in‑app alerts | Subscribes to event topics |
| **Search Service** | Player leaderboards, asset lookup | Elasticsearch indices refreshed from DB change‑streams |
| **Real‑time Feed Service** | WebSocket / Server‑Sent Events for market ticks | Publishes to Redis pub/sub for low‑latency front‑end consumption |
| **Event Bus** | Apache Kafka (3‑node cluster) | Guarantees ordered, durable event streams |
| **Cache Layer** | Redis (cluster) | Session store, hot market data, rate limiting counters |
| **Persistence** | PostgreSQL (primary) + TimescaleDB extension for time‑series | Strong ACID guarantees for transactional data |
| **Object Store** | AWS S3 (or self‑hosted MinIO) | Avatar images, replay videos, asset bundles |
| **CDN** | Akamai / CloudFront | Static assets, game bundles, OTA updates |

---

## 3. Database ER Diagram  

```
[users] --------< (1) [portfolios] >-------- (M) [positions]
   |                        |                     |
   |                        |                     |
   |                        v                     v
   |                    [transactions]       [assets]
   |                        |
   |                        v
   |                    [ledger_entries]
   |
   v
[auth_providers]

[market_data] (timeseries) <-----> [asset_prices] (FK assets.asset_id)

[games] --------< (M) [quests] >-------- (M) [player_quests]
   |                                   |
   v                                   v
[rewards]                         [leaderboards]

[notifications] (outbox pattern) linked to users
```

### Core Tables  

| Table | Primary Key | Important Columns |
|-------|-------------|-------------------|
| **users** | user_id (UUID) | email, username, status, created_at, kyc_status |
| **auth_providers** | provider_id | user_id (FK), provider (google, apple), external_id, token_hash |
| **portfolios** | portfolio_id | user_id (FK), base_currency, created_at |
| **positions** | position_id | portfolio_id (FK), asset_id (FK), qty, avg_price, last_price |
| **transactions** | txn_id | portfolio_id (FK), asset_id (FK), side, qty, price, fee, ts |
| **ledger_entries** | entry_id | txn_id (FK), account, amount, ts, type (trade, reward) |
| **assets** | asset_id | symbol, type (stock, crypto, in‑game), name, sector |
| **asset_prices** (Timescale hypertable) | (asset_id, ts) | open, high, low, close, volume |
| **games** | game_id | name, version, platform (mobile, desktop) |
| **quests** | quest_id | game_id (FK), description, reward_type, reward_amount |
| **player_quests** | player_quest_id | user_id (FK), quest_id (FK), status, completed_at |
| **rewards** | reward_id | user_id (FK), type, amount, granted_at |
| **leaderboards** | leaderboard_id | scope (global, weekly), metric, generated_at |
| **notifications** | notif_id | user_id (FK), channel, payload, sent_at, status |

---  

## 4. API Specification  

### 4.1 General  

- **Base URL:** `https://api.fintechgame.com/v1/`  
- **Authentication:** Bearer JWT (access token) + optional refresh token endpoint.  
- **Versioning:** URI versioning (`/v1/`). Future major versions will use `/v2/`.  
- **Format:** JSON for REST; GraphQL endpoint at `/graphql`.  

### 4.2 REST Endpoints  

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| **POST** | `/auth/login` | User login, returns JWT & refresh | `{email,password}` | `{access_token, refresh_token}` |
| **POST** | `/auth/refresh` | Refresh JWT | `{refresh_token}` | `{access_token}` |
| **GET** | `/users/me` | Profile summary | – | User object |
| **GET** | `/assets` | Search/list tradable assets | `?type=stock&search=apple` | Array of assets |
| **GET** | `/market/{symbol}/ticks` | Historical OHLCV (candles) | `?interval=1m&limit=500` | Candle array |
| **GET** | `/portfolio` | Current positions & cash | – | Portfolio object |
| **POST** | `/orders` | Submit trade order | `{symbol, side, qty, type, price?}` | Order confirmation |
| **GET** | `/orders/{orderId}` | Order status | – | Order object |
| **GET** | `/games/quests` | List available quests | – | Quest array |
| **POST** | `/games/quests/{questId}/claim` | Claim reward after completion | – | Reward receipt |
| **GET** | `/leaderboards/{scope}` | Get ranking list | – | Leaderboard entries |
| **GET** | `/notifications` | Pull pending notifications (fallback) | – | Array of notif objects |
| **GET** | `/ws/market` (WebSocket) | Subscribe to live tick stream (symbols list) | Message: `{symbols:["AAPL","BTCUSD"]}` | Real‑time tick messages |

### 4.3 GraphQL  

- **Endpoint:** `POST /graphql`  
- **Schema Highlights**  

```graphql
type Query {
  me: User!
  asset(symbol: String!): Asset
  assets(filter: AssetFilter, pagination: Pagination): [Asset!]!
  portfolio: Portfolio!
  market(symbol: String!, range: MarketRange!): [Candle!]!
  leaderboards(scope: LeaderboardScope!): [LeaderboardEntry!]!
}

type Mutation {
  placeOrder(input: OrderInput!): Order!
  claimQuest(questId: ID!): Reward!
}
```

- **Subscriptions (via WebSocket)**  

```graphql
type Subscription {
  marketTick(symbols: [String!]!): Tick!
  orderUpdates(orderId: ID!): Order!
}
```

---

## 5. Cross‑Platform Technology Stack  

| Layer | Technology | Reason |
|-------|------------|--------|
| **Mobile (iOS/Android)** | **React Native** (TypeScript) + **Expo** for rapid iteration | Single code‑base, native UI, deep linking, OTA updates |
| **Web** | React (Next.js) | SSR for SEO, same component library as RN via **react-native-web** |
| **Desktop / Console** | **Unity** (C#) with **WebGL** build for browsers, **Standalone** for PC/Mac | Powerful 3D/2D graphics for game‑centric UI, physics, AR/VR extensions |
| **Shared Game Logic** | **C# .NET Standard** library compiled to both Unity and via **Bridge.NET** to JS for RN fallback (optional) | Guarantees identical reward calculations across platforms |
| **State Management** | Redux Toolkit (RN/web) & UniRx (Unity) | Predictable, observable flows |
| **Networking** | gRPC-Web for RN/Web, native gRPC for Unity (C#) | Low latency, contract‑first APIs |
| **Real‑time** | WebSocket (Socket.io compatible) & GraphQL subscriptions | Unified push for market data & order updates |
| **CI/CD** | GitHub Actions → Docker images → Kubernetes (EKS) for services; Fastlane + EAS for mobile; Unity Cloud Build for desktop | Automated, platform‑specific pipelines |
| **Observability** | OpenTelemetry (traces), Prometheus/Grafana (metrics), Loki (logs) | End‑to‑end visibility |

---

## 6. Daily / Real‑Time Update Pipeline  

### 6.1 Market Data Ingestion  

1. **Vendor Connectors** (Kafka Connect source connectors) pull raw feeds from exchanges (FIX, WebSocket, REST).  
2. **Normalization Service** (Java/Kotlin) consumes raw topic, validates, maps to internal schema, writes to `asset_prices` TimescaleDB (hypertable).  
3. **Cache Warm‑up** pushes latest 1‑minute candles into Redis (`price:{symbol}`) for sub‑millisecond reads.  

### 6.2 Real‑Time Tick Distribution  

1. **Market Feed Service** subscribes to Redis Pub/Sub channel `price_updates`.  
2. Publishes to **WebSocket Hub** (Node.js + ws) and **GraphQL Subscription** server (Apollo).  
3. Clients receive delta updates; UI updates via Redux/UniRx store.  

### 6.3 Trading Flow  

1. Client sends **PlaceOrder** via gRPC (binary, low latency).  
2. **Trade Service** validates (risk, KYC, margin) → writes provisional record to PostgreSQL (transaction).  
3. Matching engine (in‑process, lock‑free order book) matches against market side or internal order‑book.  
4. On fill, **Trade Service** emits `trade.executed` event to Kafka.  

### 6.4 Post‑Trade Processing  

1. **Ledger Service** consumes `trade.executed`, creates ledger entries, updates positions.  
2. **Portfolio Service** updates cache, emits `portfolio.updated` event.  
3. **Game Logic Service** consumes trade events → progress quests, award XP/rewards.  
4. **Notification Service** sends push/email alerts to user.  

### 6.5 Daily Batch Jobs (Nightly)  

| Time (UTC) | Job | Description |
|------------|-----|-------------|
| 02:00 | **End‑of‑Day Settlement** | Close positions, calculate daily P&L, generate statements. |
| 02:30 | **Leaderboard Refresh** | Aggregate scores, write to Elasticsearch index for fast ranking queries. |
| 03:00 | **Risk & Compliance Reports** | Export to CSV / S3, trigger alerts for violations. |
| 04:00 | **Backup** | Point‑in‑time backup of PostgreSQL, TimescaleDB snapshots to S3. |
| 04:30 | **Search Index Rebuild** | Incremental update of asset and user search indices. |
| 05:00 | **Cache Eviction** | Remove stale price entries > 24h, pre‑warm next‑day hot symbols. |

---  

## 7. Security & Compliance  

- **Data Encryption:** TLS 1.3 for all in‑flight traffic; AES‑256 at rest for DB, S3.  
- **PCI‑DSS & GDPR:** Tokenization of payment info, data residency options, data‑subject access APIs.  
- **Rate Limiting:** API Gateway + Redis sliding‑window per IP / user.  
- **Audit Trail:** Immutable Kafka log (`audit.*` topics) stored in WORM S3 bucket.  
- **Secrets Management:** HashiCorp Vault for DB passwords, API keys.  

---  

## 8. Scalability & High Availability  

- **Stateless Micro‑services** → horizontal scaling via Kubernetes HPA.  
- **Database Read Replicas** (PostgreSQL) for read‑heavy portfolio queries.  
- **TimescaleDB** sharding by symbol for parallel ingestion.  
- **Kafka** with replication factor 3, tiered storage for long retention of trade events.  
- **Redis Cluster** with 3 masters + replicas, automatic failover.  
- **Multi‑region deployment** (primary US‑East, secondary EU‑West) behind DNS‑based latency routing.  

---  

## 9. Observability & Monitoring  

| Aspect | Tool | Metrics / Logs |
|--------|------|----------------|
| Tracing | OpenTelemetry + Jaeger | End‑to‑end request latency (auth → trade → ledger) |
| Metrics | Prometheus + Grafana | API latency, order throughput, cache hit‑rate |
| Logs | Loki (via Fluent Bit) | Structured JSON logs per service |
| Alerts | Alertmanager | 99th‑pct latency > 200 ms, error rate > 0.5 % |
| Business KPIs | Metabase dashboards | DAU, ARPU, average trade size, quest completion rate |

---  

## 10. Deployment Diagram  

```
[CI/CD] --> Docker images --> EKS Cluster
   |                                 |
   v                                 v
[Ingress (NGINX)] <----> [API GW] <---> [Auth, Trade, Market, Game, ...] (pods)
   |                                 |
   |                                 v
   |                         [Kafka Cluster] <--> [Event Bus]
   |                                 |
   |                                 v
   |                         [Redis Cluster] <--> [Cache]
   |                                 |
   v                                 v
[External DNS]                [PostgreSQL/Timescale] <--- [Read Replicas]
   |
   v
[CDN] --> static assets (React bundle, Unity WebGL)
```

---  

## 11. Risks & Mitigations  

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Market feed latency spikes** | Trade execution delays, user dissatisfaction | Multi‑source vendor redundancy, local cache fallback, SLA monitoring |
| **Regulatory changes (KYC/AML)** | Service interruption | Plug‑in KYC provider framework, feature flags for jurisdiction handling |
| **Cross‑platform state divergence** | Inconsistent rewards, cheating | Canonical C# logic compiled to both Unity & JS, automated parity tests |
| **Scale‑out of matching engine** | Bottleneck under heavy trade volume | Partition order books by asset, use lock‑free data structures, autoscale pods |
| **Data breach** | Legal/financial repercussions | Zero‑trust network, encrypted secrets, regular pen‑tests, bug‑bounty program |

---  

## 12. Future Enhancements  

1. **AI‑driven recommendation engine** for personalized quests.  
2. **Web3 integration** – NFT collectibles linked to portfolio performance.  
3. **AR/VR game mode** using Unity for immersive trading floors.  
4. **Serverless functions** for on‑demand heavy analytics (Spark on EMR).  

---  

*Document generated by the Principal Systems Architect – FinTech & Gaming.*  

---  

**End of System Design Document**  

---  

## Discord Completion Report  

(Handled via internal webhook as required)  

---  

**File:** `system_design_doc.md` (content above)  