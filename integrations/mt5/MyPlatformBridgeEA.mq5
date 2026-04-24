#property strict
#property version   "1.00"
#property description "MyPlatform MT5 bridge: reads prepared tickets from outbox, renders assistant levels, and exports trade events to inbox."

input string MyPlatformInboxFolder = "MyPlatform\\inbox";
input string MyPlatformOutboxFolder = "MyPlatform\\outbox";
input string BridgeAccountId = "";
input int PollIntervalSeconds = 1;
input bool SyncOpenPositionsOnInit = true;
input bool SyncHistoryOnInit = true;
input int HistoryLookbackDays = 90;

input color EntryLineColor = clrDodgerBlue;
input color StopLineColor = clrRed;
input color TargetLineColor = clrLimeGreen;
input color MinimumTargetLineColor = clrOrange;
input int AssistantPanelCorner = CORNER_LEFT_UPPER;
input int AssistantPanelX = 18;
input int AssistantPanelY = 18;
input int AssistantPanelWidth = 420;
input int AssistantPanelHeight = 240;
input color AssistantPanelBackground = C'18,18,18';
input color AssistantPanelBorder = clrDimGray;
input color AssistantPanelText = clrWhite;

struct PreparedTicket
  {
   bool   valid;
   string client_ticket_id;
   string symbol;
   string side;
   string order_type;
   double entry_price;
   double stop_loss_price;
   double target_price;
   double minimum_target_price;
   double quantity;
   string strategy_setup;
   string probability_bucket;
   string notes;
   string checklist[];
  };

PreparedTicket g_ticket;
datetime       g_ticket_loaded_at = 0;
string         g_status_message   = "Waiting for prepared ticket";

int OnInit()
  {
   ResetTicket();
   EventSetTimer(MathMax(PollIntervalSeconds,1));
   if(SyncOpenPositionsOnInit)
      SyncOpenPositionsSnapshot();
   if(SyncHistoryOnInit)
      SyncHistoricalTrades();
   RenderAssistant();
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   ClearRenderedLines();
   ClearAssistantPanel();
   Comment("");
  }

void OnTimer()
  {
   ProcessPreparedTicketCommands();
   RenderAssistant();
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
  {
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD && trans.deal > 0)
      EmitBrokerEventsFromDeal(trans.deal);
  }

void ResetTicket()
  {
   g_ticket.valid = false;
   g_ticket.client_ticket_id = "";
   g_ticket.symbol = "";
   g_ticket.side = "";
   g_ticket.order_type = "";
   g_ticket.entry_price = 0.0;
   g_ticket.stop_loss_price = 0.0;
   g_ticket.target_price = 0.0;
   g_ticket.minimum_target_price = 0.0;
   g_ticket.quantity = 0.0;
   g_ticket.strategy_setup = "";
   g_ticket.probability_bucket = "";
   g_ticket.notes = "";
   ArrayResize(g_ticket.checklist,0);
  }

void ProcessPreparedTicketCommands()
  {
   string file_name = "";
   long search_handle = FileFindFirst(MyPlatformOutboxFolder + "\\*.json",file_name,FILE_COMMON);
   if(search_handle == INVALID_HANDLE)
      return;

   while(true)
     {
      if(StringLen(file_name) > 0)
         ProcessPreparedTicketFile(file_name);

      if(!FileFindNext(search_handle,file_name))
         break;
     }

   FileFindClose(search_handle);
  }

void ProcessPreparedTicketFile(const string file_name)
  {
   string relative_path = MyPlatformOutboxFolder + "\\" + file_name;
   string json = ReadCommonTextFile(relative_path);
   if(StringLen(json) == 0)
     {
      FileDelete(relative_path,FILE_COMMON);
      return;
     }

   string command_type = "";
   if(!ExtractJsonString(json,"command_type",command_type))
     {
      FileDelete(relative_path,FILE_COMMON);
      return;
     }

   if(command_type != "OPEN_ORDER_TICKET")
     {
      FileDelete(relative_path,FILE_COMMON);
      return;
     }

   PreparedTicket ticket;
   if(ParsePreparedTicket(json,ticket))
     {
      g_ticket = ticket;
      g_ticket.valid = true;
      g_ticket_loaded_at = TimeCurrent();
      g_status_message = "Prepared ticket loaded. Confirm manually inside MT5.";
      if(_Symbol == g_ticket.symbol)
         RenderPreparedLines();
      else
         ClearRenderedLines();
     }

   FileDelete(relative_path,FILE_COMMON);
  }

bool ParsePreparedTicket(const string json,PreparedTicket &ticket)
  {
   ticket.valid = false;
   ArrayResize(ticket.checklist,0);

   if(!ExtractJsonString(json,"client_ticket_id",ticket.client_ticket_id))
      return(false);
   if(!ExtractJsonString(json,"symbol",ticket.symbol))
      return(false);

   ExtractJsonString(json,"side",ticket.side);
   ExtractJsonString(json,"order_type",ticket.order_type);
   ExtractJsonDouble(json,"entry_price",ticket.entry_price);
   ExtractJsonDouble(json,"stop_loss_price",ticket.stop_loss_price);
   ExtractJsonDouble(json,"target_price",ticket.target_price);
   ExtractJsonDouble(json,"minimum_target_price",ticket.minimum_target_price);
   ExtractJsonDouble(json,"quantity",ticket.quantity);
   ExtractJsonString(json,"strategy_setup",ticket.strategy_setup);
   ExtractJsonString(json,"probability_bucket",ticket.probability_bucket);
   ExtractJsonString(json,"notes",ticket.notes);
   ExtractJsonStringArray(json,"selected_checklist",ticket.checklist);

   ticket.valid = true;
   return(true);
  }

void RenderAssistant()
  {
   string text = "MyPlatform MT5 Bridge\n";
   text += "Status: " + g_status_message + "\n";
   text += "Broker account: " + ResolveAccountId() + "\n";

   if(g_ticket.valid)
     {
      text += "Prepared ticket: " + g_ticket.client_ticket_id + "\n";
      text += "Symbol: " + g_ticket.symbol + " | Side: " + g_ticket.side + " | Type: " + g_ticket.order_type + "\n";
      text += "Entry: " + DoubleToString(g_ticket.entry_price,_Digits) + " | Stop: " + DoubleToString(g_ticket.stop_loss_price,_Digits) + " | Target: " + DoubleToString(g_ticket.target_price,_Digits) + "\n";
      if(g_ticket.minimum_target_price > 0.0)
         text += "Minimum target: " + DoubleToString(g_ticket.minimum_target_price,_Digits) + "\n";
      if(StringLen(g_ticket.strategy_setup) > 0)
         text += "Setup: " + g_ticket.strategy_setup + "\n";
      if(StringLen(g_ticket.probability_bucket) > 0)
         text += "Probability: " + g_ticket.probability_bucket + "\n";
      if(ArraySize(g_ticket.checklist) > 0)
         text += "Checklist: " + JoinStringArray(g_ticket.checklist,", ") + "\n";
      if(StringLen(g_ticket.notes) > 0)
         text += "Notes: " + g_ticket.notes + "\n";
      if(_Symbol != g_ticket.symbol)
         text += "Attach this EA to " + g_ticket.symbol + " chart to view chart lines.\n";
      else
         text += "Confirm the order manually in MT5.\n";
     }
   else
     {
      text += "No active prepared ticket.\n";
     }

   RenderAssistantPanel(text);
  }

void RenderPreparedLines()
  {
   if(!g_ticket.valid || _Symbol != g_ticket.symbol)
     {
      ClearRenderedLines();
      return;
     }

   DrawHorizontalLine("MyPlatform_EntryLine",g_ticket.entry_price,EntryLineColor);
   DrawHorizontalLine("MyPlatform_StopLine",g_ticket.stop_loss_price,StopLineColor);
   DrawHorizontalLine("MyPlatform_TargetLine",g_ticket.target_price,TargetLineColor);
   if(g_ticket.minimum_target_price > 0.0)
      DrawHorizontalLine("MyPlatform_MinimumTargetLine",g_ticket.minimum_target_price,MinimumTargetLineColor);
   else
      ObjectDelete(0,"MyPlatform_MinimumTargetLine");
  }

void DrawHorizontalLine(const string object_name,const double price,const color line_color)
  {
   if(price <= 0.0)
      return;

   if(ObjectFind(0,object_name) < 0)
      ObjectCreate(0,object_name,OBJ_HLINE,0,0,price);

   ObjectSetDouble(0,object_name,OBJPROP_PRICE,price);
   ObjectSetInteger(0,object_name,OBJPROP_COLOR,line_color);
   ObjectSetInteger(0,object_name,OBJPROP_WIDTH,2);
   ObjectSetInteger(0,object_name,OBJPROP_STYLE,STYLE_SOLID);
   ObjectSetInteger(0,object_name,OBJPROP_BACK,false);
  }

void ClearRenderedLines()
  {
   ObjectDelete(0,"MyPlatform_EntryLine");
   ObjectDelete(0,"MyPlatform_StopLine");
   ObjectDelete(0,"MyPlatform_TargetLine");
   ObjectDelete(0,"MyPlatform_MinimumTargetLine");
  }

void RenderAssistantPanel(const string text)
  {
   EnsurePanelRectangle("MyPlatform_AssistantPanel",AssistantPanelX,AssistantPanelY,AssistantPanelWidth,AssistantPanelHeight);
   EnsurePanelText("MyPlatform_AssistantTitle","MyPlatform Position Sizer Bridge",AssistantPanelX + 14,AssistantPanelY + 12,12,true);
   EnsurePanelText("MyPlatform_AssistantBody",text,AssistantPanelX + 14,AssistantPanelY + 38,10,false);
  }

void ClearAssistantPanel()
  {
   ObjectDelete(0,"MyPlatform_AssistantPanel");
   ObjectDelete(0,"MyPlatform_AssistantTitle");
   ObjectDelete(0,"MyPlatform_AssistantBody");
  }

void EnsurePanelRectangle(const string object_name,const int x,const int y,const int width,const int height)
  {
   if(ObjectFind(0,object_name) < 0)
      ObjectCreate(0,object_name,OBJ_RECTANGLE_LABEL,0,0,0);

   ObjectSetInteger(0,object_name,OBJPROP_CORNER,AssistantPanelCorner);
   ObjectSetInteger(0,object_name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,object_name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,object_name,OBJPROP_XSIZE,width);
   ObjectSetInteger(0,object_name,OBJPROP_YSIZE,height);
   ObjectSetInteger(0,object_name,OBJPROP_BGCOLOR,AssistantPanelBackground);
   ObjectSetInteger(0,object_name,OBJPROP_BORDER_COLOR,AssistantPanelBorder);
   ObjectSetInteger(0,object_name,OBJPROP_COLOR,AssistantPanelBorder);
   ObjectSetInteger(0,object_name,OBJPROP_STYLE,STYLE_SOLID);
   ObjectSetInteger(0,object_name,OBJPROP_WIDTH,1);
   ObjectSetInteger(0,object_name,OBJPROP_BACK,false);
   ObjectSetInteger(0,object_name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,object_name,OBJPROP_SELECTED,false);
   ObjectSetInteger(0,object_name,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,object_name,OBJPROP_ZORDER,0);
  }

void EnsurePanelText(const string object_name,const string text,const int x,const int y,const int font_size,const bool bold)
  {
   if(ObjectFind(0,object_name) < 0)
      ObjectCreate(0,object_name,OBJ_LABEL,0,0,0);

   ObjectSetInteger(0,object_name,OBJPROP_CORNER,AssistantPanelCorner);
   ObjectSetInteger(0,object_name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,object_name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,object_name,OBJPROP_COLOR,AssistantPanelText);
   ObjectSetInteger(0,object_name,OBJPROP_FONTSIZE,font_size);
   ObjectSetString(0,object_name,OBJPROP_FONT,bold ? "Arial Bold" : "Arial");
   ObjectSetString(0,object_name,OBJPROP_TEXT,text);
   ObjectSetInteger(0,object_name,OBJPROP_BACK,false);
   ObjectSetInteger(0,object_name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,object_name,OBJPROP_SELECTED,false);
   ObjectSetInteger(0,object_name,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,object_name,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
   ObjectSetInteger(0,object_name,OBJPROP_ZORDER,1);
  }

void EmitBrokerEventsFromDeal(const ulong deal_ticket)
  {
   if(!HistoryDealSelect(deal_ticket))
      return;

   long deal_entry = HistoryDealGetInteger(deal_ticket,DEAL_ENTRY);
   long deal_type = HistoryDealGetInteger(deal_ticket,DEAL_TYPE);
   long position_id = HistoryDealGetInteger(deal_ticket,DEAL_POSITION_ID);
   string symbol = HistoryDealGetString(deal_ticket,DEAL_SYMBOL);
   double price = HistoryDealGetDouble(deal_ticket,DEAL_PRICE);
   double volume = HistoryDealGetDouble(deal_ticket,DEAL_VOLUME);
   double commission = HistoryDealGetDouble(deal_ticket,DEAL_COMMISSION);
   double swap_value = HistoryDealGetDouble(deal_ticket,DEAL_SWAP);
   datetime deal_time = (datetime)HistoryDealGetInteger(deal_ticket,DEAL_TIME);
   string side = DealTypeToSide(deal_type);
   if(StringLen(side) == 0 || position_id <= 0)
      return;

   string trade_id = FormatTradeId(position_id);
   string matched_client_ticket_id = MatchPreparedTicket(symbol,side,price);

   if(deal_entry == DEAL_ENTRY_IN || deal_entry == DEAL_ENTRY_INOUT)
     {
      string payload = BuildFilledPayload(trade_id,matched_client_ticket_id,symbol,side,price,deal_time,volume,commission,swap_value,position_id);
      WriteEventFile("fill_" + trade_id + "_" + FormatUnsigned(deal_ticket),"TRADE_FILLED",payload);
     }

   if(deal_entry == DEAL_ENTRY_OUT || deal_entry == DEAL_ENTRY_OUT_BY || deal_entry == DEAL_ENTRY_INOUT)
     {
      string payload = BuildClosedPayload(trade_id,price,deal_time,commission,swap_value);
      WriteEventFile("close_" + trade_id + "_" + FormatUnsigned(deal_ticket),"TRADE_CLOSED",payload);
     }
  }

void SyncOpenPositionsSnapshot()
  {
   int total = PositionsTotal();
   for(int index=0; index<total; index++)
     {
      ulong position_ticket = PositionGetTicket(index);
      if(position_ticket == 0)
         continue;

      string symbol = PositionGetString(POSITION_SYMBOL);
      long position_type = PositionGetInteger(POSITION_TYPE);
      string side = position_type == POSITION_TYPE_BUY ? "buy" : "sell";
      double entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double volume = PositionGetDouble(POSITION_VOLUME);
      double stop_loss = PositionGetDouble(POSITION_SL);
      double target = PositionGetDouble(POSITION_TP);
      double swap_value = PositionGetDouble(POSITION_SWAP);
      datetime entry_time = (datetime)PositionGetInteger(POSITION_TIME);
      string trade_id = FormatTradeId(position_ticket);

      string payload = "{";
      payload += JsonStringPair("trade_id",trade_id) + ",";
      payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
      payload += JsonStringPair("broker_id","MT5") + ",";
      payload += JsonStringPair("symbol",symbol) + ",";
      payload += JsonStringPair("market_type","forex") + ",";
      payload += JsonStringPair("side",side) + ",";
      payload += JsonStringPair("strategy_tag","MT5 Open Position Sync") + ",";
      payload += JsonStringPair("setup_name","MT5 Open Position Sync") + ",";
      payload += JsonNumberPair("entry_price",entry_price) + ",";
      payload += JsonStringPair("entry_time",TimeToString(entry_time,TIME_DATE|TIME_SECONDS)) + ",";
      payload += JsonNumberPair("quantity",volume) + ",";
      payload += JsonNumberPair("lot_size",1.0) + ",";
      payload += JsonNumberPair("leverage_used",1.0) + ",";
      payload += JsonNumberPair("stop_loss_at_entry",stop_loss) + ",";
      payload += JsonNumberPair("target_at_entry",target) + ",";
      payload += JsonNumberPair("swaps",swap_value) + ",";
      payload += "\"metadata\":{\"source\":\"mt5_open_position_sync\",\"platform_name\":\"mt5\"}";
      payload += "}";

      WriteEventFile("open_position_" + trade_id,"TRADE_FILLED",payload);
     }
  }

void SyncHistoricalTrades()
  {
   datetime to_time = TimeCurrent();
   datetime from_time = to_time - (HistoryLookbackDays * 86400);
   if(!HistorySelect(from_time,to_time))
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
      EmitHistoricalTradeByPosition((ulong)position_id);
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
        }
     }

   if(entry_deal == 0 || exit_deal == 0)
      return;

   string symbol = HistoryDealGetString(entry_deal,DEAL_SYMBOL);
   long entry_type = HistoryDealGetInteger(entry_deal,DEAL_TYPE);
   string side = DealTypeToSide(entry_type);
   double entry_price = HistoryDealGetDouble(entry_deal,DEAL_PRICE);
   double exit_price = HistoryDealGetDouble(exit_deal,DEAL_PRICE);
   double volume = HistoryDealGetDouble(entry_deal,DEAL_VOLUME);
   string trade_id = "mt5_history_" + FormatUnsigned(position_id);

   string fill_payload = "{";
   fill_payload += JsonStringPair("trade_id",trade_id) + ",";
   fill_payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
   fill_payload += JsonStringPair("broker_id","MT5") + ",";
   fill_payload += JsonStringPair("symbol",symbol) + ",";
   fill_payload += JsonStringPair("market_type","forex") + ",";
   fill_payload += JsonStringPair("side",side) + ",";
   fill_payload += JsonStringPair("strategy_tag","MT5 Historical Sync") + ",";
   fill_payload += JsonStringPair("setup_name","MT5 Historical Sync") + ",";
   fill_payload += JsonNumberPair("entry_price",entry_price) + ",";
   fill_payload += JsonStringPair("entry_time",TimeToString(first_entry_time,TIME_DATE|TIME_SECONDS)) + ",";
   fill_payload += JsonNumberPair("quantity",volume) + ",";
   fill_payload += JsonNumberPair("lot_size",1.0) + ",";
   fill_payload += JsonNumberPair("leverage_used",1.0) + ",";
   fill_payload += JsonNumberPair("commission",total_commission) + ",";
   fill_payload += JsonNumberPair("swaps",total_swap) + ",";
   fill_payload += "\"metadata\":{\"source\":\"mt5_history_sync\",\"platform_name\":\"mt5\"}";
   fill_payload += "}";

   string close_payload = "{";
   close_payload += JsonStringPair("trade_id",trade_id) + ",";
   close_payload += JsonNumberPair("exit_price",exit_price) + ",";
   close_payload += JsonStringPair("exit_time",TimeToString(last_exit_time,TIME_DATE|TIME_SECONDS)) + ",";
   close_payload += JsonStringPair("exit_reason","history_sync") + ",";
   close_payload += JsonNumberPair("slippage_at_exit",0.0);
   close_payload += "}";

   WriteEventFile("history_fill_" + FormatUnsigned(position_id),"TRADE_FILLED",fill_payload);
   WriteEventFile("history_close_" + FormatUnsigned(position_id),"TRADE_CLOSED",close_payload);
  }

string BuildFilledPayload(const string trade_id,
                          const string client_ticket_id,
                          const string symbol,
                          const string side,
                          const double entry_price,
                          const datetime entry_time,
                          const double quantity,
                          const double commission,
                          const double swap_value,
                          const ulong position_id)
  {
   string payload = "{";
   payload += JsonStringPair("trade_id",trade_id) + ",";
   if(StringLen(client_ticket_id) > 0)
      payload += JsonStringPair("client_ticket_id",client_ticket_id) + ",";
   payload += JsonStringPair("account_id",ResolveAccountId()) + ",";
   payload += JsonStringPair("broker_id","MT5") + ",";
   payload += JsonStringPair("symbol",symbol) + ",";
   payload += JsonStringPair("market_type","forex") + ",";
   payload += JsonStringPair("side",side) + ",";
   payload += JsonNumberPair("entry_price",entry_price) + ",";
   payload += JsonStringPair("entry_time",TimeToString(entry_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonNumberPair("quantity",quantity) + ",";
   payload += JsonNumberPair("lot_size",1.0) + ",";
   payload += JsonNumberPair("leverage_used",1.0) + ",";
   payload += JsonNumberPair("commission",commission) + ",";
   payload += JsonNumberPair("swaps",swap_value) + ",";
   payload += "\"metadata\":{\"source\":\"mt5_live_fill\",\"platform_name\":\"mt5\",\"position_id\":\"" + JsonEscape(FormatUnsigned(position_id)) + "\"}";
   payload += "}";
   return(payload);
  }

string BuildClosedPayload(const string trade_id,
                          const double exit_price,
                          const datetime exit_time,
                          const double commission,
                          const double swap_value)
  {
   string payload = "{";
   payload += JsonStringPair("trade_id",trade_id) + ",";
   payload += JsonNumberPair("exit_price",exit_price) + ",";
   payload += JsonStringPair("exit_time",TimeToString(exit_time,TIME_DATE|TIME_SECONDS)) + ",";
   payload += JsonStringPair("exit_reason","mt5_exit") + ",";
   payload += JsonNumberPair("slippage_at_exit",0.0) + ",";
   payload += JsonStringPair("notes","Closed in MT5") + ",";
   payload += "\"post_trade_capture\":{\"source\":\"mt5_live_close\"}";
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
      g_status_message = "Last bridge event: " + event_type;
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

string ReadCommonTextFile(const string relative_path)
  {
   int handle = FileOpen(relative_path,FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return("");

   string contents = "";
   while(!FileIsEnding(handle))
      contents += FileReadString(handle);
   FileClose(handle);
   return(contents);
  }

string MatchPreparedTicket(const string symbol,const string side,const double fill_price)
  {
   if(!g_ticket.valid)
      return("");
   if(symbol != g_ticket.symbol || side != g_ticket.side)
      return("");

   double point_size = SymbolInfoDouble(symbol,SYMBOL_POINT);
   if(point_size <= 0.0)
      point_size = 0.0001;
   double tolerance = MathMax(point_size * 50.0,MathAbs(g_ticket.entry_price) * 0.01);
   if(MathAbs(fill_price - g_ticket.entry_price) > tolerance)
      return("");

   string matched = g_ticket.client_ticket_id;
   return(matched);
  }

string ResolveAccountId()
  {
   if(StringLen(BridgeAccountId) > 0)
      return(BridgeAccountId);
   return(StringFormat("%I64d",AccountInfoInteger(ACCOUNT_LOGIN)));
  }

string DealTypeToSide(const long deal_type)
  {
   if(deal_type == DEAL_TYPE_BUY)
      return("buy");
   if(deal_type == DEAL_TYPE_SELL)
      return("sell");
   return("");
  }

string FormatTradeId(const ulong position_id)
  {
   return("mt5_pos_" + FormatUnsigned(position_id));
  }

string FormatUnsigned(const ulong value)
  {
   return(StringFormat("%I64u",value));
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

bool ExtractJsonString(const string json,const string key,string &value)
  {
   string pattern = "\"" + key + "\"";
   int key_pos = StringFind(json,pattern);
   if(key_pos < 0)
      return(false);

   int colon_pos = StringFind(json,":",key_pos + StringLen(pattern));
   if(colon_pos < 0)
      return(false);

   int value_start = SkipWhitespace(json,colon_pos + 1);
   if(value_start < 0 || StringGetCharacter(json,value_start) != '\"')
      return(false);

   value_start++;
   int value_end = value_start;
   while(value_end < StringLen(json))
     {
      ushort ch = StringGetCharacter(json,value_end);
      ushort prev = value_end > value_start ? StringGetCharacter(json,value_end - 1) : 0;
      if(ch == '\"' && prev != '\\')
         break;
      value_end++;
     }

   value = StringSubstr(json,value_start,value_end - value_start);
   StringReplace(value,"\\n","\n");
   StringReplace(value,"\\\"","\"");
   StringReplace(value,"\\\\","\\");
   return(true);
  }

bool ExtractJsonDouble(const string json,const string key,double &value)
  {
   string pattern = "\"" + key + "\"";
   int key_pos = StringFind(json,pattern);
   if(key_pos < 0)
      return(false);

   int colon_pos = StringFind(json,":",key_pos + StringLen(pattern));
   if(colon_pos < 0)
      return(false);

   int value_start = SkipWhitespace(json,colon_pos + 1);
   if(value_start < 0)
      return(false);

   int value_end = value_start;
   while(value_end < StringLen(json))
     {
      ushort ch = StringGetCharacter(json,value_end);
      if(ch == ',' || ch == '}' || ch == '\n' || ch == '\r')
         break;
      value_end++;
     }

   string raw = TrimWhitespace(StringSubstr(json,value_start,value_end - value_start));
   if(StringLen(raw) == 0 || raw == "null")
      return(false);
   value = StringToDouble(raw);
   return(true);
  }

bool ExtractJsonStringArray(const string json,const string key,string &values[])
  {
   ArrayResize(values,0);
   string pattern = "\"" + key + "\"";
   int key_pos = StringFind(json,pattern);
   if(key_pos < 0)
      return(false);

   int colon_pos = StringFind(json,":",key_pos + StringLen(pattern));
   if(colon_pos < 0)
      return(false);

   int array_start = StringFind(json,"[",colon_pos);
   if(array_start < 0)
      return(false);

   int array_end = FindMatchingBracket(json,array_start);
   if(array_end < 0)
      return(false);

   string body = StringSubstr(json,array_start + 1,array_end - array_start - 1);
   string parts[];
   int parts_total = StringSplit(body,',',parts);
   for(int index=0; index<parts_total; index++)
     {
      string item = TrimWhitespace(parts[index]);
      if(StringLen(item) < 2)
         continue;
      if(StringGetCharacter(item,0) == '\"' && StringGetCharacter(item,StringLen(item) - 1) == '\"')
         item = StringSubstr(item,1,StringLen(item) - 2);
      StringReplace(item,"\\\"","\"");
      AppendString(values,item);
     }

   return(ArraySize(values) > 0);
  }

int SkipWhitespace(const string text,int index)
  {
   while(index < StringLen(text))
     {
      ushort ch = StringGetCharacter(text,index);
      if(ch != ' ' && ch != '\n' && ch != '\r' && ch != '\t')
         return(index);
      index++;
     }
   return(-1);
  }

int FindMatchingBracket(const string text,const int start_index)
  {
   int depth = 0;
   for(int index=start_index; index<StringLen(text); index++)
     {
      ushort ch = StringGetCharacter(text,index);
      if(ch == '[')
         depth++;
      if(ch == ']')
        {
         depth--;
         if(depth == 0)
            return(index);
        }
     }
   return(-1);
  }

string TrimWhitespace(string value)
  {
   while(StringLen(value) > 0)
     {
      ushort first = StringGetCharacter(value,0);
      if(first != ' ' && first != '\n' && first != '\r' && first != '\t')
         break;
      value = StringSubstr(value,1);
     }

   while(StringLen(value) > 0)
     {
      int last_index = StringLen(value) - 1;
      ushort last = StringGetCharacter(value,last_index);
      if(last != ' ' && last != '\n' && last != '\r' && last != '\t')
         break;
      value = StringSubstr(value,0,last_index);
     }

   return(value);
  }

void AppendString(string &items[],const string value)
  {
   int size = ArraySize(items);
   ArrayResize(items,size + 1);
   items[size] = value;
  }

void AppendLong(long &items[],const long value)
  {
   int size = ArraySize(items);
   ArrayResize(items,size + 1);
   items[size] = value;
  }

bool LongArrayContains(const long &items[],const long value)
  {
   for(int index=0; index<ArraySize(items); index++)
      if(items[index] == value)
         return(true);
   return(false);
  }

string JoinStringArray(const string &items[],const string delimiter)
  {
   string joined = "";
   for(int index=0; index<ArraySize(items); index++)
     {
      if(index > 0)
         joined += delimiter;
      joined += items[index];
     }
   return(joined);
  }
