# game_mechanics.md

## 1. Daily / Real‑Time Update Flow  

| Phase | Trigger | Core Services Involved | Data Flow | Outcome |
|------|---------|------------------------|-----------|---------|
| **Market Data Ingestion** | Vendor feed (FIX / WS / REST) → Kafka Connect | Market Data Service → TimescaleDB → Redis cache | Raw ticks → validated → stored as 1‑minute candles → latest price placed in `price:{symbol}` | Up‑to‑date price data for UI and trade validation |
| **Real‑Time Tick Distribution** | New price written to Redis Pub/Sub `price_updates` | Market Feed Service → WebSocket hub & GraphQL subscription server | Broadcast Δ‑price to all connected clients | UI charts, price tickers update instantly |
| **User Trade Submission** | Player taps *Buy* / *Sell* → gRPC call | Trade Service (validation) → Order Book (in‑process) | Order persisted in PostgreSQL, matched, executed | Trade executed or rejected, order‑status returned |
| **Post‑Trade Processing** | `trade.executed` event on Kafka | Ledger Service → Portfolio Service → Game Logic Service → Notification Service | Ledger entries created, position cache updated, quest progress evaluated, push/email sent | Account balances reflect trade, XP/rewards awarded, user notified |
| **Quest / Reward Evaluation** | Each `trade.executed` or `daily.login` event | Game Logic Service | Reads user quest state, updates progress, marks completed, creates reward record | Player earns XP, tokens, items; quest appears as *claimed* |
| **Leaderboard Refresh** | Scheduled nightly batch (02:30 UTC) or real‑time top‑N updates | Leaderboard Service (reads from Elasticsearch) | Aggregates metric (total profit, XP, etc.) → writes `leaderboard_entries` | Updated ranking shown on HomeScreen |
| **Daily Batch Jobs (02:00‑05:30 UTC)** | Cron scheduler | Various services (Settlement, Reporting, Backup, Search index) | End‑of‑day P&L calc, compliance reports, DB snapshots, search refresh | Financial accuracy, regulatory compliance, disaster recovery |
| **Client Sync** | App foreground / periodic heartbeat | API Gateway → Portfolio Service (REST) | Pull latest portfolio snapshot, positions, cash | UI reflects any out‑of‑band changes (e.g., from another device) |

### Real‑Time Guarantees  

* **Latency**: Market tick → client ≤ 150 ms (Redis → WS).  
* **Ordering**: Kafka topics use partition key = `user_id` for quest/reward events, guaranteeing per‑user order.  
* **Reliability**: All critical events (`trade.executed`, `quest.completed`) are persisted to Kafka with replication factor 3; replayable for recovery.  

---

## 2. Event Card Types & Examples  

Event cards are **playable objects** that modify gameplay, appear in daily draws, quests, or as loot drops. Each card is defined by a JSON schema stored in the `assets` table (type = `in‑game`).  

### 2.1 Card Schema (simplified)

```json
{
  "card_id": "UUID",
  "name": "String",
  "type": "enum[BOOST, PENALTY, CHALLENGE, GIFT]",
  "rarity": "enum[COMMON, RARE, EPIC, LEGENDARY]",
  "description": "String",
  "icon_url": "String",
  "effects": [
    {
      "trigger": "enum[ON_TRADE, ON_LOGIN, ON_QUEST_COMPLETE, DAILY]",
      "action": "enum[ADD_XP, MULTIPLY_REWARD, REDUCE_FEE, GIVE_ITEM]",
      "parameters": { "xp": 500, "multiplier": 1.5, "fee_discount": 0.2, "item_id": "UUID" }
    }
  ],
  "validity": {
    "start": "ISO8601",
    "end": "ISO8601"
  }
}
```

### 2.2 Card Types  

| Type | Gameplay Meaning | Typical Use |
|------|-------------------|-------------|
| **BOOST** | Positive modifier applied **once** when its trigger fires. | “Double XP for the next 5 trades”. |
| **PENALTY** | Negative effect that **reduces** player performance. | “Trading fee increased by 30 % for the next hour”. |
| **CHALLENGE** | Gives a *goal*; completing it yields a reward. | “Make 3 profitable trades on a volatile asset”. |
| **GIFT** | Direct reward, no condition. | “Free 100 token grant”. |

### 2.3 Example Cards  

#### 2.3.1 Boost – “Turbo Trader”

```json
{
  "card_id": "9f1e2b6a-8c4d-4e9a-bc7f-3d5e6a9f2c01",
  "name": "Turbo Trader",
  "type": "BOOST",
  "rarity": "RARE",
  "description": "Earn 2× XP on the next 5 trade executions.",
  "icon_url": "https://cdn.fintechgame.com/cards/turbo_trader.png",
  "effects": [
    {
      "trigger": "ON_TRADE",
      "action": "MULTIPLY_REWARD",
      "parameters": { "xp_multiplier": 2, "limit": 5 }
    }
  ],
  "validity": { "start": "2026-06-13T00:00:00Z", "end": "2026-06-20T00:00:00Z" }
}
```

#### 2.3.2 Penalty – “Market Turbulence”

```json
{
  "card_id": "d4c2a7f9-5b1e-4d8c-9e0a-2f6b3c8e7d44",
  "name": "Market Turbulence",
  "type": "PENALTY",
  "rarity": "COMMON",
  "description": "Trading fee +20 % for the next hour.",
  "icon_url": "https://cdn.fintechgame.com/cards/turbulence.png",
  "effects": [
    {
      "trigger": "ON_TRADE",
      "action": "ADD_FEE",
      "parameters": { "fee_percent": 0.20, "duration_min": 60 }
    }
  ],
  "validity": { "start": "2026-06-13T00:00:00Z", "end": "2026-12-31T23:59:59Z" }
}
```

#### 2.3.3 Challenge – “Sector Conqueror”

```json
{
  "card_id": "a3e9b5c1-7d2f-4a6b-9c3e-1f8d2e6a9b55",
  "name": "Sector Conqueror",
  "type": "CHALLENGE",
  "rarity": "EPIC",
  "description": "Earn 1 000 XP by achieving a 5 % profit on any Technology‑sector stock today.",
  "icon_url": "https://cdn.fintechgame.com/cards/sector_conqueror.png",
  "effects": [
    {
      "trigger": "ON_TRADE",
      "action": "CHECK_CONDITION",
      "parameters": {
        "sector": "Technology",
        "profit_pct": 5,
        "reward": { "type": "xp", "amount": 1000 }
      }
    }
  ],
  "validity": { "start": "2026-06-13T00:00:00Z", "end": "2026-06-14T00:00:00Z" }
}
```

#### 2.3.4 Gift – “Lucky Deposit”

```json
{
  "card_id": "e9f2c4a7-1b3d-4f8e-9c6a-5d2e3b7c9f01",
  "name": "Lucky Deposit",
  "type": "GIFT",
  "rarity": "LEGENDARY",
  "description": "Receive 250 tokens instantly.",
  "icon_url": "https://cdn.fintechgame.com/cards/lucky_deposit.png",
  "effects": [
    {
      "trigger": "DAILY",
      "action": "GIVE_ITEM",
      "parameters": { "item_id": "token_250", "quantity": 1 }
    }
  ],
  "validity": { "start": "2026-06-13T00:00:00Z", "end": "2026-06-13T23:59:59Z" }
}
```

### 2.4 Card Lifecycle  

1. **Draw Phase** – At daily login or quest reward, the `Game Logic Service` pulls *N* random cards from the `cards` pool respecting rarity weights.  
2. **Activation** – When a player “uses” a card, an `event.card_used` Kafka message is published.  
3. **Effect Resolution** – Listeners (Trade Service, Portfolio Service, Notification Service) apply the defined `effects` according to the trigger.  
4. **Expiration** – If `validity.end` passes without activation, the card is auto‑discarded.  

---

## 3. Achievement & Reward System  

### 3.1 Achievement Model  

| Table | Columns | Description |
|-------|---------|-------------|
| **achievements** | `achievement_id`, `title`, `description`, `icon_url`, `category` (e.g., *Trading*, *Social*), `condition_json` (logic), `reward_type` (`xp`, `token`, `item`), `reward_amount` | Master list of possible achievements. |
| **user_achievements** | `user_achievement_id`, `user_id`, `achievement_id`, `status` (`locked`, `unlocked`), `unlocked_at` | Per‑user progress. |

**Condition JSON Example** (for “First Trade”):

```json
{
  "event": "trade_executed",
  "criteria": { "count": 1 }
}
```

The Game Logic Service evaluates incoming events against each unlocked achievement’s condition using a simple rule engine (JSONPath + operators).

### 3.2 Reward Types  

| Type | In‑Game Effect |
|------|----------------|
| **XP** | Increases player level, unlocks higher‑tier quests. |
| **TOKEN** | Platform token usable for fee discounts, avatar skins, or marketplace purchases. |
| **ITEM** | Cosmetic (avatar), badge, or functional (e.g., “Fee Waiver” coupon). |
| **BADGE** | Shown on profile; purely visual, but can be a prerequisite for exclusive events. |

### 3.3 Reward Distribution Flow  

1. **Event Generation** – Any notable player action (`trade_executed`, `quest_completed`, `daily_login`) emits a Kafka event.  
2. **Achievement Engine** – Consumes events, updates `user_achievements` rows, changes status to *unlocked* when condition satisfied.  
3. **Reward Service** – Upon status change, creates a `rewards` row (type + amount) and publishes `reward.granted`.  
4. **Notification Service** – Sends a push/in‑app message: *“Congratulations! You unlocked **First Trade** and earned 500 XP.”*  
5. **Client UI** – Listens to `reward.granted` via GraphQL subscription; displays modal animation and updates progress bars.  

### 3.4 Daily / Weekly Streak Bonuses  

| Streak Type | Requirement | Reward |
|------------|-------------|--------|
| **Login Streak** | Log in 7 consecutive days | 1 000 tokens (once) |
| **Trade Streak** | Execute at least 1 trade per day for 5 days | 2 × XP multiplier for next 10 trades |
| **Profit Streak** | End‑of‑day profit ≥ 5 % for 3 days | Exclusive “Profit Master” badge + 2 500 XP |

Streak counters are stored in Redis (`streak:{user_id}:{type}`) for O(1) increment and TTL‑based expiry; nightly batch persists to PostgreSQL for long‑term analytics.

### 3.5 Leaderboard‑Tied Rewards  

- **Weekly Top‑Trader** (by net profit) → 5 000 tokens + exclusive avatar skin.  
- **Monthly XP Champion** → 10 000 XP boost for the next month.  

Leaderboards are refreshed nightly (02:30 UTC) and the top N users are sent a `reward.granted` event automatically.

### 3.6 Progression Loops  

1. **Core Loop** – Trade → Earn XP / tokens → Level up → Unlock higher‑value quests.  
2. **Event Loop** – Daily login → Draw event cards → Apply effects → Immediate boost/penalty → Influences next trades.  
3. **Social Loop** – Share achievements → Earn “Referral Tokens” → Invite friends → Network effect on daily active users.  

---

## 4. Daily Update Flow (Cron / Scheduler)

| Time (UTC) | Job | Service(s) | Description |
|------------|-----|------------|-------------|
| **02:00** | End‑of‑Day Settlement | Trade Service, Portfolio Service | Close positions, compute daily P&L, write statements to `ledger_entries`. |
| **02:30** | Leaderboard Refresh | Game Logic Service, Search Service | Aggregate scores, rebuild Elasticsearch index, emit `leaderboard.updated`. |
| **03:00** | Risk & Compliance Export | Trade Service, Audit Service | Generate CSV/JSON compliance dump, store in S3, trigger alerts if thresholds breached. |
| **04:00** | Backup | DB Operator (PostgreSQL + TimescaleDB) | Point‑in‑time snapshot → S3, verify checksum. |
| **04:30** | Search Index Rebuild | Search Service | Incremental update of asset/user indices. |
| **05:00** | Cache Eviction & Warm‑up | Redis Cluster, Market Feed Service | Delete price entries > 24 h, pre‑load next‑day high‑volume symbols. |
| **06:00** | Daily Quest Generation | Game Logic Service | Create new `player_quests` for each active user based on previous day’s activity. |
| **06:30** | Daily Card Draw | Game Logic Service | Pull *N* cards for each user, store in `user_cards` table, send `card.drawn` notification. |
| **07:00** | Streak Evaluation | Redis → PostgreSQL sync | Evaluate login/trade/profit streaks, award streak rewards. |
| **08:00** | Push Daily Summary | Notification Service | Email / push summarising portfolio performance, new quests, and any earned cards. |

All cron jobs are orchestrated via **Kubernetes CronJobs** with idempotent logic; each job records its execution timestamp in a `system_jobs` table for auditability.

---

## 5. Summary  

* The platform’s **real‑time pipeline** guarantees sub‑150 ms market updates, immediate trade feedback, and event‑driven quest/reward processing.  
* **Event cards** provide a modular, data‑driven way to introduce temporary buffs, penalties, challenges, and gifts, enriching the daily gameplay loop.  
* The **achievement system** couples deterministic conditions with flexible reward types, feeding directly into the leaderboards and streak bonuses.  
* A well‑defined **daily batch schedule** ensures financial correctness, compliance, and fresh content for players each day.  

These mechanics and flows are now documented in `game_mechanics.md` and ready for implementation.  



---  

**Discord finish:** “機制文件完成，已存 `game_mechanics.md`”。