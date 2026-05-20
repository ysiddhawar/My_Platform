#property strict
#property version   "2.00"
#property description "MyPlatform MT5 sync bridge: exports historical trades, open positions, and live lifecycle updates to MyPlatform."

input string MyPlatformInboxFolder = "MyPlatform\\inbox";
input string BridgeAccountId = "dd38e1db-2a2a-4c34-9a65-38128d00d0b3";
input int PollIntervalSeconds = 1;
input bool SyncOpenPositionsOnInit = true;
input bool SyncHistoryOnInit = true;
input int HistoryLookbackDays = 90;
input int SyncOpenPositionsIntervalMinutes = 5;

struct PositionSnapshot
  {
   ulong    position_id;
   string   symbol;
   string   side;
   double   volume;
   double   entry_price;
   double   stop_loss;
   double   take_profit;
   datetime entry_time;
   double   swap_value;
  };

PositionSnapshot g_position_cache[];
string           g_status_message = "MT5 sync bridge active";
datetime          g_last_open_positions_sync = 0;

int OnInit()
  {
   ArrayResize(g_position_cache,0);

   if(SyncHistoryOnInit)
      SyncHistoricalTrades();
   if(SyncOpenPositionsOnInit)
      SyncOpenPositionsSnapshot();

   SyncAccountState();

   LoadCurrentPositionCache();
   g_last_open_positions_sync = TimeCurrent();
   EventSetTimer(MathMax(PollIntervalSeconds,1));
   Comment("");
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   Comment("");
  }

void OnTimer()
  {
   EmitPositionModificationEvents();
   LoadCurrentPositionCache();
   SyncAccountState();

   // macOS Wine reliability: OnTradeTransaction() may not fire. Periodically re-sync
   // all open positions so the backend can detect missed closes via diffing.
   int interval_seconds = MathMax(SyncOpenPositionsIntervalMinutes * 60, 60);
   if(TimeCurrent() - g_last_open_positions_sync >= interval_seconds)
     {
      SyncOpenPositionsSnapshot();
      g_last_open_positions_sync = TimeCurrent();
     }
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
  {
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD && trans.deal > 0)
      EmitBrokerEventsFromDeal(trans.deal);
  }

void LoadCurrentPositionCache()
  {
   ArrayResize(g_position_cache,0);

   int total = PositionsTotal();
   for(int index=0; index<total; index++)
     {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;

      PositionSnapshot snapshot;
      if(BuildCurrentPositionSnapshot(snapshot))
         AppendPositionSnapshot(g_position_cache,snapshot);
     }
  }

void EmitPositionModificationEvents()
  {
   PositionSnapshot current_positions[];
   ArrayResize(current_positions,0);

   int total = PositionsTotal();
   for(int index=0; index<total; index++)
     {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;

      PositionSnapshot snapshot;
      if(!BuildCurrentPositionSnapshot(snapshot))
         continue;

      AppendPositionSnapshot(current_positions,snapshot);

      int previous_index = FindPositionSnapshot(g_position_cache,snapshot.position_id);
      if(previous_index < 0)
         continue;

      PositionSnapshot previous = g_position_cache[previous_index];
      if(!PricesEqual(previous.stop_loss,snapshot.stop_loss) || !PricesEqual(previous.take_profit,snapshot.take_profit))
         WriteEventFile(
            BuildEventFileName("modify",snapshot.position_id,0),
            "POSITION_MODIFIED",
            BuildPositionModifiedPayload(snapshot)
         );
     }

   ArrayResize(g_position_cache,ArraySize(current_positions));
   for(int i=0; i<ArraySize(current_positions); i++)
      g_position_cache[i] = current_positions[i];
  }

void SyncOpenPositionsSnapshot()
  {
   int total = PositionsTotal();
   string open_ids = "[";
   for(int index=0; index<total; index++)
     {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;

      PositionSnapshot snapshot;
      if(!BuildCurrentPositionSnapshot(snapshot))
         continue;

      WriteEventFile(
         BuildEventFileName("open_position",snapshot.position_id,0),
         "TRADE_FILLED",
         BuildFilledPayload(snapshot,0,"","")
      );

      if(open_ids != "[")
         open_ids += ",";
      open_ids += "\"" + FormatUnsigned(snapshot.position_id) + "\"";
     }
   open_ids += "]";

   // Write a single OPEN_POSITIONS_SYNC event with all open position IDs
   // so the backend can detect closes by comparing against its last snapshot.
   string sync_payload = "{";
   sync_payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
   sync_payload += "\"open_position_ids\":" + open_ids + ",";
   sync_payload += JsonNumberPair("position_count",total);
   sync_payload += "}";
   WriteEventFile("open_positions_sync_" + IntegerToString((int)TimeCurrent()),"OPEN_POSITIONS_SYNC",sync_payload);
  }

void SyncAccountState()
  {
   string payload = "{";
   payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
   payload += JsonNumberPair("balance",AccountInfoDouble(ACCOUNT_BALANCE)) + ",";
   payload += JsonNumberPair("equity",AccountInfoDouble(ACCOUNT_EQUITY)) + ",";
   payload += JsonNumberPair("margin",AccountInfoDouble(ACCOUNT_MARGIN)) + ",";
   payload += JsonNumberPair("free_margin",AccountInfoDouble(ACCOUNT_MARGIN_FREE));
   payload += "}";

   WriteEventFile("account_state_" + IntegerToString((int)TimeCurrent()),"ACCOUNT_STATE",payload);
  }

void SyncHistoricalTrades()
  {
   datetime to_time = TimeCurrent();
   if(!HistorySelect(0,to_time))
      return;

   long seen_positions[];
   ArrayResize(seen_positions,0);

   int deals_total = HistoryDealsTotal();
   for(int index=0; index<deals_total; index++)
     {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         continue;

      long deal_entry = HistoryDealGetInteger(deal_ticket,DEAL_ENTRY);
      long position_id = HistoryDealGetInteger(deal_ticket,DEAL_POSITION_ID);
      if(position_id <= 0)
         continue;
      if(!(deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_OUT_BY || deal_entry == DEAL_ENTRY_INOUT))
         continue;
      if(LongArrayContains(seen_positions,position_id))
         continue;

      AppendLong(seen_positions,position_id);
     }

   for(int i=0; i<ArraySize(seen_positions); i++)
     {
      EmitHistoricalTradeByPosition((ulong)seen_positions[i]);
     }
  }

void EmitHistoricalTradeByPosition(const ulong position_id)
  {
   if(!HistorySelectByPosition(position_id))
      return;

   int deals_total = HistoryDealsTotal();
   if(deals_total <= 0)
      return;

   ulong entry_deal = 0;
   ulong exit_deal = 0;
   datetime first_entry_time = D'3000.01.01 00:00';
   datetime last_exit_time = 0;
   double total_commission = 0.0;
   double total_swap = 0.0;
   double final_stop = 0.0;
   double final_target = 0.0;

   for(int index=0; index<deals_total; index++)
     {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         continue;

      long deal_type = HistoryDealGetInteger(deal_ticket,DEAL_TYPE);
      if(deal_type != DEAL_TYPE_BUY && deal_type != DEAL_TYPE_SELL)
         continue;

      long deal_entry = HistoryDealGetInteger(deal_ticket,DEAL_ENTRY);
      datetime deal_time = (datetime)HistoryDealGetInteger(deal_ticket,DEAL_TIME);
      total_commission += HistoryDealGetDouble(deal_ticket,DEAL_COMMISSION);
      total_swap += HistoryDealGetDouble(deal_ticket,DEAL_SWAP);

      if((deal_entry == DEAL_ENTRY_IN || deal_entry == DEAL_ENTRY_INOUT) && deal_time < first_entry_time)
        {
         first_entry_time = deal_time;
         entry_deal = deal_ticket;
        }
      if((deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_OUT_BY || deal_entry == DEAL_ENTRY_INOUT) && deal_time >= last_exit_time)
        {
         last_exit_time = deal_time;
         exit_deal = deal_ticket;
         final_stop = HistoryDealGetDouble(deal_ticket,DEAL_SL);
         final_target = HistoryDealGetDouble(deal_ticket,DEAL_TP);
        }
     }

   if(entry_deal == 0 || exit_deal == 0)
      return;

   PositionSnapshot snapshot;
   snapshot.position_id = position_id;
   snapshot.symbol = HistoryDealGetString(entry_deal,DEAL_SYMBOL);
   snapshot.side = DealTypeToSide(HistoryDealGetInteger(entry_deal,DEAL_TYPE));
   snapshot.entry_price = HistoryDealGetDouble(entry_deal,DEAL_PRICE);
   snapshot.volume = HistoryDealGetDouble(entry_deal,DEAL_VOLUME);
   snapshot.stop_loss = final_stop;
   snapshot.take_profit = final_target;
   snapshot.entry_time = first_entry_time;
   snapshot.swap_value = total_swap;

   string trade_id = FormatTradeId(position_id);
   string fill_payload = BuildFilledPayload(snapshot,entry_deal,"","");
   string close_payload = BuildClosedPayload(
      trade_id,
      HistoryDealGetDouble(exit_deal,DEAL_PRICE),
      last_exit_time,
      total_commission,
      total_swap,
      "history_sync",
      0.0
   );

   WriteEventFile(BuildEventFileName("history_fill",position_id,entry_deal),"TRADE_FILLED",fill_payload);
   WriteEventFile(BuildEventFileName("history_close",position_id,exit_deal),"TRADE_CLOSED",close_payload);
  }

void EmitBrokerEventsFromDeal(const ulong deal_ticket)
  {
   if(!HistoryDealSelect(deal_ticket))
      return;

   long deal_type = HistoryDealGetInteger(deal_ticket,DEAL_TYPE);
   if(deal_type != DEAL_TYPE_BUY && deal_type != DEAL_TYPE_SELL)
      return;

   long position_id = HistoryDealGetInteger(deal_ticket,DEAL_POSITION_ID);
   if(position_id <= 0)
      return;

   long deal_entry = HistoryDealGetInteger(deal_ticket,DEAL_ENTRY);
   double deal_volume = HistoryDealGetDouble(deal_ticket,DEAL_VOLUME);
   double deal_price = HistoryDealGetDouble(deal_ticket,DEAL_PRICE);
   double deal_commission = HistoryDealGetDouble(deal_ticket,DEAL_COMMISSION);
   double deal_swap = HistoryDealGetDouble(deal_ticket,DEAL_SWAP);
   datetime deal_time = (datetime)HistoryDealGetInteger(deal_ticket,DEAL_TIME);
   string side = DealTypeToSide(deal_type);
   string symbol = HistoryDealGetString(deal_ticket,DEAL_SYMBOL);

   int previous_index = FindPositionSnapshot(g_position_cache,(ulong)position_id);
   bool had_previous = previous_index >= 0;
   PositionSnapshot previous;
   if(had_previous)
      previous = g_position_cache[previous_index];

   PositionSnapshot current;
   bool has_current = SelectPositionSnapshotById((ulong)position_id,current);
   string trade_id = FormatTradeId((ulong)position_id);

   if(deal_entry == DEAL_ENTRY_IN)
     {
      if(!had_previous)
        {
         if(has_current)
            WriteEventFile(
               BuildEventFileName("fill",(ulong)position_id,deal_ticket),
               "TRADE_FILLED",
               BuildFilledPayload(current,deal_ticket,"","")
            );
         else
            WriteEventFile(
               BuildEventFileName("fill",(ulong)position_id,deal_ticket),
               "TRADE_FILLED",
               BuildFallbackFillPayload(trade_id,symbol,side,deal_price,deal_time,deal_volume,deal_commission,deal_swap)
            );
        }
      else
        {
         double additional_quantity = deal_volume;
         if(has_current && current.volume > previous.volume)
            additional_quantity = current.volume - previous.volume;
         WriteEventFile(
            BuildEventFileName("scale_in",(ulong)position_id,deal_ticket),
            "SCALE_IN",
            BuildScaleInPayload(trade_id,additional_quantity,deal_price,deal_time,deal_commission,deal_swap,has_current ? current : previous)
         );
        }
     }
   else if(deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_OUT_BY)
     {
      if(had_previous && has_current && current.volume > 0.0 && current.volume + 0.0000001 < previous.volume)
        {
         double closed_quantity = previous.volume - current.volume;
         WriteEventFile(
            BuildEventFileName("partial_close",(ulong)position_id,deal_ticket),
            "PARTIAL_CLOSE",
            BuildPartialClosePayload(trade_id,closed_quantity,deal_price,deal_time,deal_commission,deal_swap,current)
         );
        }
      else
        {
         WriteEventFile(
            BuildEventFileName("close",(ulong)position_id,deal_ticket),
            "TRADE_CLOSED",
            BuildClosedPayload(trade_id,deal_price,deal_time,deal_commission,deal_swap,"mt5_exit",0.0)
         );
        }
     }
   else if(deal_entry == DEAL_ENTRY_INOUT)
     {
      WriteEventFile(
         BuildEventFileName("close",(ulong)position_id,deal_ticket),
         "TRADE_CLOSED",
         BuildClosedPayload(trade_id,deal_price,deal_time,deal_commission,deal_swap,"mt5_reverse",0.0)
      );
      if(has_current)
        {
         WriteEventFile(
            BuildEventFileName("fill",(ulong)position_id,deal_ticket),
            "TRADE_FILLED",
            BuildFilledPayload(current,deal_ticket,"","")
         );
        }
     }

   LoadCurrentPositionCache();
  }

bool BuildCurrentPositionSnapshot(PositionSnapshot &snapshot)
  {
   long position_identifier = PositionGetInteger(POSITION_IDENTIFIER);
   if(position_identifier <= 0)
      position_identifier = PositionGetInteger(POSITION_TICKET);
   if(position_identifier <= 0)
      return(false);

   snapshot.position_id = (ulong)position_identifier;
   snapshot.symbol = PositionGetString(POSITION_SYMBOL);
   snapshot.side = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "buy" : "sell";
   snapshot.volume = PositionGetDouble(POSITION_VOLUME);
   snapshot.entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
   snapshot.stop_loss = PositionGetDouble(POSITION_SL);
   snapshot.take_profit = PositionGetDouble(POSITION_TP);
   snapshot.entry_time = (datetime)PositionGetInteger(POSITION_TIME);
   snapshot.swap_value = PositionGetDouble(POSITION_SWAP);
   return(true);
  }

bool SelectPositionSnapshotById(const ulong position_id,PositionSnapshot &snapshot)
  {
   int total = PositionsTotal();
   for(int index=0; index<total; index++)
     {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;

      long current_identifier = PositionGetInteger(POSITION_IDENTIFIER);
      if(current_identifier <= 0)
         current_identifier = PositionGetInteger(POSITION_TICKET);
      if((ulong)current_identifier != position_id)
         continue;

      return(BuildCurrentPositionSnapshot(snapshot));
     }
   return(false);
  }

int FindPositionSnapshot(PositionSnapshot &snapshots[],const ulong position_id)
  {
   for(int index=0; index<ArraySize(snapshots); index++)
     {
      if(snapshots[index].position_id == position_id)
         return(index);
     }
   return(-1);
  }

void AppendPositionSnapshot(PositionSnapshot &snapshots[],PositionSnapshot &snapshot)
  {
   int size = ArraySize(snapshots);
   ArrayResize(snapshots,size + 1);
   snapshots[size] = snapshot;
  }

string BuildFilledPayload(PositionSnapshot &snapshot,
                          const ulong source_ticket,
                          const string strategy_tag,
                          const string setup_name)
  {
   double contract_size = SymbolInfoDouble(snapshot.symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   string payload = "{";
   payload += JsonStringPair("trade_id",FormatTradeId(snapshot.position_id)) + ",";
   payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
   payload += JsonStringPair("broker_id","MT5") + ",";
   payload += JsonStringPair("symbol",snapshot.symbol) + ",";
   payload += JsonStringPair("market_type",DetectMarketType(snapshot.symbol)) + ",";
   payload += JsonStringPair("side",snapshot.side) + ",";
   payload += JsonStringPair("strategy_tag",strategy_tag) + ",";
   payload += JsonStringPair("setup_name",setup_name) + ",";
   payload += JsonNumberPair("entry_price",snapshot.entry_price) + ",";
   payload += JsonStringPair("entry_time",TimeToString(snapshot.entry_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonNumberPair("quantity",snapshot.volume) + ",";
   payload += JsonNumberPair("lot_size",1.0) + ",";
   payload += JsonNumberPair("contract_size",contract_size) + ",";
   payload += JsonNumberPair("leverage_used",1.0) + ",";
   payload += JsonNumberPair("stop_loss_at_entry",snapshot.stop_loss) + ",";
   payload += JsonNumberPair("target_at_entry",snapshot.take_profit) + ",";
   payload += JsonNumberPair("swaps",snapshot.swap_value) + ",";
   payload += "\"metadata\":{";
   payload += JsonStringPair("source",source_ticket > 0 ? "mt5_live_sync" : "mt5_snapshot_sync") + ",";
   payload += JsonStringPair("platform_name","mt5") + ",";
   payload += JsonStringPair("position_id",FormatUnsigned(snapshot.position_id));
   payload += "}";
   payload += "}";
   return(payload);
  }

string BuildFallbackFillPayload(const string trade_id,
                                const string symbol,
                                const string side,
                                const double entry_price,
                                const datetime entry_time,
                                const double quantity,
                                const double commission,
                                const double swap_value)
  {
   double contract_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   string payload = "{";
   payload += JsonStringPair("trade_id",trade_id) + ",";
   payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
   payload += JsonStringPair("broker_id","MT5") + ",";
   payload += JsonStringPair("symbol",symbol) + ",";
   payload += JsonStringPair("market_type",DetectMarketType(symbol)) + ",";
   payload += JsonStringPair("side",side) + ",";
   payload += JsonStringPair("strategy_tag","") + ",";
   payload += JsonStringPair("setup_name","") + ",";
   payload += JsonNumberPair("entry_price",entry_price) + ",";
   payload += JsonStringPair("entry_time",TimeToString(entry_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonNumberPair("quantity",quantity) + ",";
   payload += JsonNumberPair("lot_size",1.0) + ",";
   payload += JsonNumberPair("contract_size",contract_size) + ",";
   payload += JsonNumberPair("leverage_used",1.0) + ",";
   payload += JsonNumberPair("commission",commission) + ",";
   payload += JsonNumberPair("swaps",swap_value) + ",";
   payload += "\"metadata\":{";
   payload += JsonStringPair("source","mt5_live_sync") + ",";
   payload += JsonStringPair("platform_name","mt5");
   payload += "}";
   payload += "}";
   return(payload);
  }

string BuildClosedPayload(const string trade_id,
                          const double exit_price,
                          const datetime exit_time,
                          const double commission,
                          const double swap_value,
                          const string exit_reason,
                          const double slippage_at_exit)
  {
   string payload = "{";
   payload += JsonStringPair("trade_id",trade_id) + ",";
   payload += JsonNumberPair("exit_price",exit_price) + ",";
   payload += JsonStringPair("exit_time",TimeToString(exit_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonStringPair("exit_reason",exit_reason) + ",";
   payload += JsonNumberPair("slippage_at_exit",slippage_at_exit) + ",";
   payload += JsonNumberPair("commission",commission) + ",";
   payload += JsonNumberPair("swaps",swap_value) + ",";
   payload += JsonStringPair("notes","Closed in MT5");
   payload += "}";
   return(payload);
  }

string BuildPositionModifiedPayload(PositionSnapshot &snapshot)
  {
   string payload = "{";
   payload += JsonStringPair("trade_id",FormatTradeId(snapshot.position_id)) + ",";
   payload += JsonNumberPair("stop_loss_at_entry",snapshot.stop_loss) + ",";
   payload += JsonNumberPair("target_at_entry",snapshot.take_profit) + ",";
   payload += JsonStringPair("notes","Updated in MT5") + ",";
   payload += "\"metadata\":{";
   payload += JsonStringPair("source","mt5_position_modify") + ",";
   payload += JsonStringPair("platform_name","mt5") + ",";
   payload += JsonStringPair("position_id",FormatUnsigned(snapshot.position_id));
   payload += "}";
   payload += "}";
   return(payload);
  }

string BuildScaleInPayload(const string trade_id,
                           const double additional_quantity,
                           const double fill_price,
                           const datetime fill_time,
                           const double commission,
                           const double swap_value,
                           PositionSnapshot &snapshot)
  {
   string payload = "{";
   payload += JsonStringPair("trade_id",trade_id) + ",";
   payload += JsonNumberPair("additional_quantity",additional_quantity) + ",";
   payload += JsonNumberPair("quantity_delta",additional_quantity) + ",";
   payload += JsonNumberPair("fill_price",fill_price) + ",";
   payload += JsonNumberPair("entry_price",fill_price) + ",";
   payload += JsonStringPair("entry_time",TimeToString(fill_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonNumberPair("commission",commission) + ",";
   payload += JsonNumberPair("swaps",swap_value) + ",";
   payload += JsonNumberPair("stop_loss_at_entry",snapshot.stop_loss) + ",";
   payload += JsonNumberPair("target_at_entry",snapshot.take_profit) + ",";
   payload += JsonStringPair("notes","Added position in MT5");
   payload += "}";
   return(payload);
  }

string BuildPartialClosePayload(const string trade_id,
                                const double closed_quantity,
                                const double exit_price,
                                const datetime exit_time,
                                const double commission,
                                const double swap_value,
                                PositionSnapshot &snapshot)
  {
   string payload = "{";
   payload += JsonStringPair("trade_id",trade_id) + ",";
   payload += JsonNumberPair("closed_quantity",closed_quantity) + ",";
   payload += JsonNumberPair("quantity_delta",closed_quantity) + ",";
   payload += JsonNumberPair("exit_price",exit_price) + ",";
   payload += JsonStringPair("exit_time",TimeToString(exit_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonStringPair("exit_reason","partial_close") + ",";
   payload += JsonNumberPair("commission",commission) + ",";
   payload += JsonNumberPair("swaps",swap_value) + ",";
   payload += JsonNumberPair("stop_loss_at_entry",snapshot.stop_loss) + ",";
   payload += JsonNumberPair("target_at_entry",snapshot.take_profit) + ",";
   payload += JsonStringPair("notes","Partial close in MT5") + ",";
   payload += JsonStringPair("partial_trade_id",trade_id + "-partial-" + IntegerToString((int)exit_time));
   payload += "}";
   return(payload);
  }

bool WriteEventFile(const string event_id,const string event_type,const string payload_json)
  {
   string relative_path = MyPlatformInboxFolder + "\\" + event_id + ".json";
   string document = "{";
   document += JsonStringPair("event_type",event_type) + ",";
   document += "\"payload\":" + payload_json;
   document += "}";
   bool ok = WriteCommonTextFile(relative_path,document);
   if(ok)
      g_status_message = "Last MT5 sync event: " + event_type;
   return(ok);
  }

bool WriteCommonTextFile(const string relative_path,const string contents)
  {
   int handle = FileOpen(relative_path,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(handle == INVALID_HANDLE)
      return(false);
   FileWriteString(handle,contents);
   FileClose(handle);
   return(true);
  }

string ResolveAccountId()
  {
   if(StringLen(BridgeAccountId) > 0)
      return(BridgeAccountId);
   return(StringFormat("%I64d",AccountInfoInteger(ACCOUNT_LOGIN)));
  }

string DetectMarketType(const string symbol)
  {
   string normalized = symbol;
   StringToUpper(normalized);
   if(StringFind(normalized,"BTC") >= 0 || StringFind(normalized,"ETH") >= 0 || StringFind(normalized,"USDT") >= 0)
      return("crypto");
   if(StringLen(normalized) == 6)
      return("forex");
   return("futures");
  }

string FormatTradeId(const ulong position_id)
  {
   return("mt5_" + FormatUnsigned(position_id));
  }

string BuildEventFileName(const string prefix,const ulong position_id,const ulong source_ticket)
  {
   string name = prefix + "_" + FormatUnsigned(position_id) + "_" + IntegerToString((int)TimeCurrent());
   if(source_ticket > 0)
      name += "_" + FormatUnsigned(source_ticket);
   return(name);
  }

string DealTypeToSide(const long deal_type)
  {
   if(deal_type == DEAL_TYPE_BUY)
      return("buy");
   if(deal_type == DEAL_TYPE_SELL)
      return("sell");
   return("");
  }

bool PricesEqual(const double left,const double right)
  {
   return(MathAbs(left - right) <= 0.0000001);
  }

bool LongArrayContains(long &values[],const long target)
  {
   for(int index=0; index<ArraySize(values); index++)
     {
      if(values[index] == target)
         return(true);
     }
   return(false);
  }

void AppendLong(long &values[],const long target)
  {
   int size = ArraySize(values);
   ArrayResize(values,size + 1);
   values[size] = target;
  }

string JsonEscape(string value)
  {
   StringReplace(value,"\\","\\\\");
   StringReplace(value,"\"","\\\"");
   StringReplace(value,"\r","");
   StringReplace(value,"\n","\\n");
   return(value);
  }

string JsonStringPair(const string key,const string value)
  {
   return("\"" + JsonEscape(key) + "\":\"" + JsonEscape(value) + "\"");
  }

string JsonNumberPair(const string key,const double value)
  {
   return("\"" + JsonEscape(key) + "\":" + DoubleToString(value,8));
  }

string FormatUnsigned(const ulong value)
  {
   return(StringFormat("%I64u",value));
  }
