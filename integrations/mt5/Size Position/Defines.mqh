//+------------------------------------------------------------------+
//|                                                          Defines.mqh |
//|                                              Size Position for MT5 |
//+------------------------------------------------------------------+
#include <Controls\Button.mqh>
#include <Controls\ComboBox.mqh>
#include <Controls\Dialog.mqh>
#include <Controls\CheckBox.mqh>
#include <Controls\Label.mqh>
#include "HorizontalRadioGroup.mqh"
#include <Arrays\List.mqh>
#include <Trade\Trade.mqh>

// Additional checkbox bitmaps:
#resource "Images\\CheckBoxOnDark.bmp"
#resource "Images\\CheckBoxOffDark.bmp"
#resource "Images\\CheckBoxOnDark17.bmp"
#resource "Images\\CheckBoxOffDark17.bmp"
#resource "Images\\CheckBoxOn17.bmp"
#resource "Images\\CheckBoxOff17.bmp"

// Additional radiogroup button bitmaps:
#resource "Images\\RadioButtonOnDark.bmp"
#resource "Images\\RadioButtonOffDark.bmp"
#resource "Images\\RadioButtonOn16Dark.bmp"
#resource "Images\\RadioButtonOff16Dark.bmp"
#resource "Images\\RadioButtonOn16.bmp"
#resource "Images\\RadioButtonOff16.bmp"

color CONTROLS_EDIT_COLOR_ENABLE  = C'255,255,255';
color CONTROLS_EDIT_COLOR_DISABLE = C'221,221,211';

color CONTROLS_BUTTON_COLOR_ENABLE  = C'200,200,200';
color CONTROLS_BUTTON_COLOR_DISABLE = C'224,224,224';

color DARKMODE_BG_DARK_COLOR = 0x444444;
color DARKMODE_CONTROL_BORDER_COLOR = 0x888888;
color DARKMODE_MAIN_AREA_BORDER_COLOR = 0x333333;
color DARKMODE_MAIN_AREA_BG_COLOR = 0x666666;
color DARKMODE_EDIT_BG_COLOR = 0xAAAAAA;
color DARKMODE_BUTTON_BG_COLOR = 0xA19999;
color DARKMODE_TEXT_COLOR = 0x000000;

#define MULTIPLIER_VALUE_CONTROL 10
#define MULTIPLIER_VALUE_SHIFT 100
#define MULTIPLIER_VALUE_CONTROL_SHIFT 1000

// Hotkeys.
enum HOTKEY_ID
{
    HK_Trade,
    HK_SwitchOrderType,
    HK_SwitchEntryDirection,
    HK_SwitchHideShowLines,
    HK_SetStopLoss,
    HK_SetTakeProfit,
    HK_SetEntry,
    HK_MinimizeMaximize,
    HK_SwitchSLPointsLevel,
    HK_SwitchTPPointsLevel,
    HK_COUNT
};

struct HotkeyDef
{
    uchar main_key;
    bool  ctrl_required;
    bool  shift_required;
    HotkeyDef() { main_key = 0; ctrl_required = false; shift_required = false; }
};

enum ENTRY_TYPE
{
    Instant,
    Pending,
    StopLimit
};

enum ACCOUNT_BUTTON
{
    Balance,
    Equity,
    Balance_minus_Risk
};

enum TABS
{
    MainTab,
    RiskTab,
    MarginTab,
    SwapsTab,
    TradingTab
};

enum TRADE_DIRECTION
{
    Long,
    Short
};

enum PROFIT_LOSS
{
    Profit,
    Loss
};

enum CANDLE_NUMBER
{
    Current_Candle = 0,
    Previous_Candle = 1
};

enum VOLUME_SHARE_MODE
{
    Equal,
    Decreasing,
    Increasing
};

enum SHOW_SPREAD
{
    No,
    Points,
    Ratio
};

enum SYMBOL_CHART_CHANGE_REACTION
{
    SYMBOL_CHART_CHANGE_EACH_OWN,
    SYMBOL_CHART_CHANGE_HARD_RESET,
    SYMBOL_CHART_CHANGE_KEEP_PANEL
};

enum COMMISSION_TYPE
{
    COMMISSION_CURRENCY,
    COMMISSION_PERCENT,
};

enum CALCULATE_RISK_FOR_TRADING_TAB
{
    CALCULATE_RISK_FOR_TRADING_TAB_NO,
    CALCULATE_RISK_FOR_TRADING_TAB_TOTAL,
    CALCULATE_RISK_FOR_TRADING_TAB_PER_SYMBOL
};

enum ADDITIONAL_TP_SCHEME
{
    ADDITIONAL_TP_SCHEME_INWARD,
    ADDITIONAL_TP_SCHEME_OUTWARD
};

enum ADDITIONAL_TRADE_BUTTONS
{
    ADDITIONAL_TRADE_BUTTONS_NONE,
    ADDITIONAL_TRADE_BUTTONS_LINE,
    ADDITIONAL_TRADE_BUTTONS_MAIN,
    ADDITIONAL_TRADE_BUTTONS_BOTH
};

enum INCLUDE_SYMBOLS
{
    INCLUDE_SYMBOLS_ALL,
    INCLUDE_SYMBOLS_CURRENT,
    INCLUDE_SYMBOLS_OTHER,
};

enum INCLUDE_ORDERS
{
    INCLUDE_ORDERS_ALL,
    INCLUDE_ORDERS_OPEN,
    INCLUDE_ORDERS_PENDING,
};

enum INCLUDE_DIRECTIONS
{
    INCLUDE_DIRECTIONS_ALL,
    INCLUDE_DIRECTIONS_BUY,
    INCLUDE_DIRECTIONS_SELL,
};

enum MARGIN_UTILIZATION_BASE
{
    MUB_BALANCE,
    MUB_STARTING_BALANCE,
    MUB_FREE_MARGIN
};

struct Settings
{
    ENTRY_TYPE EntryType;
    double EntryLevel;
    double StopLossLevel;
    double TakeProfitLevel;
    double TPMultiplier;
    int  TakeProfitsNumber;
    double StopPriceLevel;
    double Risk;
    double MoneyRisk;
    double CommissionPerLot;
    COMMISSION_TYPE CommissionType;
    bool UseMoneyInsteadOfPercentage;
    bool RiskFromPositionSize;
    double PositionSize;
    ACCOUNT_BUTTON AccountButton;
    double CustomBalance;
    bool DeleteLines;
    INCLUDE_ORDERS IncludeOrders;
    bool IgnoreOrdersWithoutSL;
    bool IgnoreOrdersWithoutTP;
    INCLUDE_SYMBOLS IncludeSymbols;
    INCLUDE_DIRECTIONS IncludeDirections;
    bool HideAccSize;
    bool ShowLines;
    TABS SelectedTab;
    double CustomLeverage;
    int MagicNumber;
    string Commentary;
    bool DisableTradingWhenLinesAreHidden;
    double TP[];
    int TPShare[];
    int MaxSlippage;
    int MaxSpread;
    int MaxEntrySLDistance;
    int MinEntrySLDistance;
    double MaxRiskPercentage;
    double MaxMarginPerc;
    bool SLDistanceInPoints;
    bool TPDistanceInPoints;
    int StopLoss;
    int TakeProfit;
    TRADE_DIRECTION TradeDirection;
    bool SubtractPositions;
    bool SubtractPendingOrders;
    bool DoNotApplyStopLoss;
    bool DoNotApplyTakeProfit;
    bool AskForConfirmation;
    bool CommentAutoSuffix;
    int TrailingStopPoints;
    int BreakEvenPoints;
    int MaxNumberOfTrades;
    double MaxTotalRisk;
    int MaxNumberOfTradesTotal;
    int MaxNumberOfTradesPerSymbol;
    double MaxPositionSizeTotal;
    double MaxPositionSizePerSymbol;
    double MaxRiskTotal;
    double MaxRiskPerSymbol;
    double MaxMarginPercTotal;
    double MaxMarginPercPerSymbol;
    int ExpiryMinutes;
    int ATRPeriod;
    double ATRMultiplierSL;
    double ATRMultiplierTP;
    ENUM_TIMEFRAMES ATRTimeframe;
    bool SpreadAdjustmentSL;
    bool SpreadAdjustmentTP;
    bool WasSelectedEntryLine;
    bool WasSelectedStopLossLine;
    bool WasSelectedTakeProfitLine;
    bool WasSelectedStopPriceLine;
    bool WasSelectedAdditionalTakeProfitLine[];
    bool IsPanelMinimized;
    bool TPLockedOnSL;
    VOLUME_SHARE_MODE ShareVolumeMode;
    bool TemplateChanged;
    ADDITIONAL_TP_SCHEME LastAdditionalTPScheme;
    MARGIN_UTILIZATION_BASE MarginUtilizationBase;
    double MUBStartingBalance;
} sets;

class CStringForList : public CObject
{
    public:
        string      Name;
        CWnd*       Obj;
        bool        Hidden;
        CStringForList() {Hidden = false;}
};

class CPanelList : public CList
{
    public:
        void DeleteListElementByName(const string name);
        void MoveListElementByName(const string name, const int index);
        void CreateListElementByName(CObject &obj, const string name);
        void SetHiddenByName(const string name, const bool hidden);
};
//+------------------------------------------------------------------+