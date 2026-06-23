# EarnForex PositionSizer for MyPlatform

This directory contains the **EarnForex Position Sizer** (v3.15) — an open-source, professional floating trade panel for MT5, integrated into the MyPlatform ecosystem.

## Source

- **Original**: https://github.com/EarnForex/PositionSizer
- **License**: MIT — full open source, free to use and modify

## How to Use

### 1. Deploy to MT5

The files are already deployed to:
```
MQL5/Experts/Position Sizer/
```

If you need to redeploy:
1. Open **MetaEditor** (F4 from MT5)
2. Navigate to `MQL5/Experts/Position Sizer/`
3. Open `Position Sizer.mq5`
4. Press **F5** (Compile)
5. It will produce `Position Sizer.ex5`

### 2. Attach to Chart

1. Drag **Position Sizer** from the Navigator onto any chart (EURUSD, GBPUSD, etc.)
2. The panel appears instantly with:
   - Proper window frame (CAppDialog-based)
   - Professional dark/light mode
   - Tabbed interface: Main → Risk → Margin → Swaps → Trading
   - Draggable SL/TP lines on chart
   - 6+ position sizing modes
   - Order placement with confirmation dialog

### 3. Deploy Bridge for Backend Integration

The bridge EA `MyPlatformPositionSizerBridge.mq5` runs alongside the Position Sizer:

1. Drag **MyPlatformPositionSizerBridge** onto the same chart
2. It silently monitors trades placed with magic number `2022052714`
3. Forwards all trade events to `Common\Files\MyPlatform\sizer_outbox\`
4. Polls `Common\Files\MyPlatform\sizer_inbox\` for config updates from the backend

### 4. Backend Receives Events

The existing `mt5_file_bridge_adapter.py` automatically polls the `sizer_outbox` directory and normalizes order events into MyPlatform's event system.

## File Structure

```
integrations/mt5/
├── EarnForexPositionSizer/        ← EarnForex source (as-is)
│   ├── Position Sizer.mq5         → Main EA
│   ├── Position Sizer.mqh         → UI panel (CAppDialog subclass)
│   ├── Position Sizer Trading.mqh → Order execution
│   ├── Defines.mqh                → Settings struct, enums
│   ├── HorizontalRadioGroup.mqh   → Custom radio group control
│   ├── errordescription.mqh       → Error code descriptions
│   ├── English.mqh                → Translations
│   │   ...                        → Other translations
│   ├── Images/                    → Checkbox/radio button bitmaps
│   └── README.md                  ← This file
│
├── MyPlatformPositionSizer/       ← Legacy custom implementation
│   └── ...                        → (kept for reference)
│
├── MyPlatformPositionSizer.mq5    ← Legacy main EA (kept for reference)
├── MyPlatformPositionSizerBridge.mq5 ← Bridge overlay (NEW)
└── MyPlatformBridgeEA.mq5         ← Existing sync-only bridge
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     MT5 TERMINAL                             │
│                                                              │
│  Chart: EURUSD                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Position Sizer (EarnForex) ← Dragged onto chart    │    │
│  │  → Full professional panel                           │    │
│  │  → Draggable SL/TP/Entry lines                       │    │
│  │  → Order placement with confirmation                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  MyPlatformPositionSizerBridge ← Dragged alongside   │    │
│  │  → Monitors magic number: 2022052714                 │    │
│  │  → Writes events to sizer_outbox/                    │    │
│  │  → Polls sizer_inbox/ for config updates             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  MyPlatformBridgeEA (any chart / no chart)                   │
│  → Handles sync-only inbox processing                       │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼ (File System)
          Common\Files\MyPlatform\
          ├── inbox/          ← Events from BridgeEA
          ├── sizer_outbox/   ← Order events from PositionSizerBridge
          └── sizer_inbox/    ← Config updates from backend
                       │
                       ▼
          mt5_file_bridge_adapter.py
          → Polls both inbox and sizer_outbox
          → Normalizes all events
          → Feeds into MyPlatform event system
```

## Notes

- The EarnForex Position Sizer is **unmodified** — we deploy it as-is for the perfect UI/UX
- Our custom `MyPlatformPositionSizer` modules are kept for reference but are **no longer needed** for deployment
- The bridge EA is the only custom component — it's lightweight and doesn't interfere with the Position Sizer