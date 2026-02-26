"""
Test Yahoo Finance Service - Demonstrates all features with real data
Run this script to test the Python Yahoo Finance implementation
"""

import asyncio
import json
import sys
import os

# Add services/be to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'be'))

from app.services.yahoo_finance import YahooFinanceService

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


async def test_quote():
    """Test single stock quote with 70+ metrics"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 1: Get Stock Quote (AAPL){Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()
    result = await service.get_quote("AAPL")

    print(f"{Colors.OKGREEN}✓ Success!{Colors.ENDC} Latency: {Colors.WARNING}{result['latencyMs']}ms{Colors.ENDC}\n")

    # Display key metrics
    print(f"{Colors.OKCYAN}Basic Info:{Colors.ENDC}")
    print(f"  Symbol: {result['symbol']}")
    print(f"  Name: {result['name']}")
    print(f"  Price: ${result['price']:.2f}" if result['price'] else "  Price: N/A")
    print(f"  Change: {result['changePercent']:.2f}%" if result['changePercent'] else "  Change: N/A")
    print(f"  Volume: {result['volume']:,}" if result['volume'] else "  Volume: N/A")
    print(f"  Market Cap: ${result['marketCap']:,.0f}" if result['marketCap'] else "  Market Cap: N/A")

    print(f"\n{Colors.OKCYAN}Valuation Metrics:{Colors.ENDC}")
    print(f"  Beta: {result['beta']:.2f}" if result['beta'] else "  Beta: N/A")
    print(f"  P/E Ratio: {result['trailingPE']:.2f}" if result['trailingPE'] else "  P/E Ratio: N/A")
    print(f"  PEG Ratio: {result['pegRatio']:.2f}" if result['pegRatio'] else "  PEG Ratio: N/A")
    print(f"  Price/Book: {result['priceToBook']:.2f}" if result['priceToBook'] else "  Price/Book: N/A")

    print(f"\n{Colors.OKCYAN}Profitability:{Colors.ENDC}")
    print(f"  EPS (TTM): ${result['trailingEps']:.2f}" if result['trailingEps'] else "  EPS (TTM): N/A")
    print(f"  ROE: {result['returnOnEquity']*100:.2f}%" if result['returnOnEquity'] else "  ROE: N/A")
    print(f"  ROA: {result['returnOnAssets']*100:.2f}%" if result['returnOnAssets'] else "  ROA: N/A")
    print(f"  Profit Margin: {result['profitMargins']*100:.2f}%" if result['profitMargins'] else "  Profit Margin: N/A")

    print(f"\n{Colors.OKCYAN}Dividends:{Colors.ENDC}")
    print(f"  Dividend Rate: ${result['dividendRate']}" if result['dividendRate'] else "  Dividend Rate: N/A")
    print(f"  Dividend Yield: {result['dividendYield']*100:.2f}%" if result['dividendYield'] else "  Dividend Yield: N/A")

    print(f"\n{Colors.OKCYAN}Financial Health:{Colors.ENDC}")
    print(f"  Total Cash: ${result['totalCash']:,.0f}" if result['totalCash'] else "  Total Cash: N/A")
    print(f"  Total Debt: ${result['totalDebt']:,.0f}" if result['totalDebt'] else "  Total Debt: N/A")
    print(f"  Debt/Equity: {result['debtToEquity']:.2f}" if result['debtToEquity'] else "  Debt/Equity: N/A")

    print(f"\n{Colors.OKCYAN}Analyst Data:{Colors.ENDC}")
    print(f"  Target Price: ${result['targetMeanPrice']:.2f}" if result['targetMeanPrice'] else "  Target Price: N/A")
    print(f"  Recommendation: {result['recommendationKey']}" if result['recommendationKey'] else "  Recommendation: N/A")
    print(f"  Analysts: {result['numberOfAnalystOpinions']}" if result['numberOfAnalystOpinions'] else "  Analysts: N/A")

    return result


async def test_multiple_quotes():
    """Test multiple stock quotes"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 2: Get Multiple Quotes{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    results = await service.get_quotes(symbols)

    print(f"{Colors.OKGREEN}✓ Success!{Colors.ENDC} Fetched {len(results)} quotes\n")

    print(f"{Colors.BOLD}{'Symbol':<10} {'Price':<12} {'Change %':<12} {'Volume':<15} {'Market Cap':<15}{Colors.ENDC}")
    print(f"{'-'*70}")

    for quote in results:
        price = f"${quote['price']:.2f}" if quote['price'] else "N/A"
        change = f"{quote['changePercent']:.2f}%" if quote['changePercent'] else "N/A"
        volume = f"{quote['volume']:,}" if quote['volume'] else "N/A"
        mcap = f"${quote['marketCap']/1e9:.1f}B" if quote['marketCap'] else "N/A"

        print(f"{quote['symbol']:<10} {price:<12} {change:<12} {volume:<15} {mcap:<15}")


async def test_historical():
    """Test historical data"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 3: Get Historical Data (AAPL, 5d, 1d){Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()
    result = await service.get_historical_data("AAPL", period="5d", interval="1d")

    print(f"{Colors.OKGREEN}✓ Success!{Colors.ENDC} Latency: {Colors.WARNING}{result['latencyMs']}ms{Colors.ENDC}")
    print(f"Fetched {len(result['bars'])} bars\n")

    print(f"{Colors.BOLD}{'Date':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}{Colors.ENDC}")
    print(f"{'-'*70}")

    for bar in result['bars'][-5:]:  # Show last 5 bars
        date = bar['timestamp'][:10]
        print(f"{date:<12} ${bar['open']:<9.2f} ${bar['high']:<9.2f} ${bar['low']:<9.2f} ${bar['close']:<9.2f} {bar['volume']:,}")


async def test_options():
    """Test options chain"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 4: Get Options Chain (AAPL){Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()
    result = await service.get_options_chain("AAPL")

    print(f"{Colors.OKGREEN}✓ Success!{Colors.ENDC} Latency: {Colors.WARNING}{result['latencyMs']}ms{Colors.ENDC}\n")

    print(f"{Colors.OKCYAN}Expiration Dates Available:{Colors.ENDC}")
    for i, expiry in enumerate(result['expirationDates'][:5], 1):
        print(f"  {i}. {expiry}")
    if len(result['expirationDates']) > 5:
        print(f"  ... and {len(result['expirationDates']) - 5} more")

    print(f"\n{Colors.OKCYAN}Selected Expiry:{Colors.ENDC} {result['selectedExpiry']}")
    print(f"{Colors.OKCYAN}Underlying Price:{Colors.ENDC} ${result['underlyingPrice']:.2f}" if result['underlyingPrice'] else f"{Colors.OKCYAN}Underlying Price:{Colors.ENDC} N/A")
    print(f"{Colors.OKCYAN}Calls:{Colors.ENDC} {len(result['calls'])}")
    print(f"{Colors.OKCYAN}Puts:{Colors.ENDC} {len(result['puts'])}")

    # Show sample calls
    print(f"\n{Colors.BOLD}Sample Call Options:{Colors.ENDC}")
    print(f"{Colors.BOLD}{'Strike':<10} {'Last':<10} {'Bid':<10} {'Ask':<10} {'Volume':<12} {'OI':<12} {'IV':<10}{Colors.ENDC}")
    print(f"{'-'*80}")

    for call in result['calls'][:5]:
        print(f"${call['strike']:<9.2f} ${call['lastPrice']:<9.2f} ${call['bid']:<9.2f} ${call['ask']:<9.2f} "
              f"{call['volume']:<12,} {call['openInterest']:<12,} {call['impliedVolatility']*100:<9.2f}%")


async def test_indices():
    """Test market indices"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 5: Get Market Indices{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()

    # US Indices
    us_symbols = ["^GSPC", "^DJI", "^IXIC"]
    us_results = await service.get_quotes(us_symbols)

    print(f"{Colors.OKCYAN}US Indices:{Colors.ENDC}")
    for quote in us_results:
        price = f"${quote['price']:.2f}" if quote['price'] else "N/A"
        change = f"{quote['changePercent']:.2f}%" if quote['changePercent'] else "N/A"
        print(f"  {quote['symbol']}: {price} ({change})")

    # Indian Indices
    in_symbols = ["^NSEI", "^NSEBANK", "^BSESN"]
    in_results = await service.get_quotes(in_symbols)

    print(f"\n{Colors.OKCYAN}Indian Indices:{Colors.ENDC}")
    for quote in in_results:
        price = f"{quote['price']:.2f}" if quote['price'] else "N/A"
        change = f"{quote['changePercent']:.2f}%" if quote['changePercent'] else "N/A"
        print(f"  {quote['symbol']}: {price} ({change})")


async def test_company_info():
    """Test company information"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 6: Get Company Information (AAPL){Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()
    result = await service.get_company_info("AAPL")

    print(f"{Colors.OKGREEN}✓ Success!{Colors.ENDC} Latency: {Colors.WARNING}{result['latencyMs']}ms{Colors.ENDC}\n")

    print(f"{Colors.OKCYAN}Company:{Colors.ENDC} {result['name']}")
    print(f"{Colors.OKCYAN}Sector:{Colors.ENDC} {result['sector']}" if result['sector'] else f"{Colors.OKCYAN}Sector:{Colors.ENDC} N/A")
    print(f"{Colors.OKCYAN}Industry:{Colors.ENDC} {result['industry']}" if result['industry'] else f"{Colors.OKCYAN}Industry:{Colors.ENDC} N/A")
    print(f"{Colors.OKCYAN}Website:{Colors.ENDC} {result['website']}" if result['website'] else f"{Colors.OKCYAN}Website:{Colors.ENDC} N/A")
    print(f"{Colors.OKCYAN}Employees:{Colors.ENDC} {result['employees']:,}" if result['employees'] else f"{Colors.OKCYAN}Employees:{Colors.ENDC} N/A")

    if result['description']:
        print(f"\n{Colors.OKCYAN}Description:{Colors.ENDC}")
        print(f"  {result['description'][:200]}..." if len(result['description']) > 200 else f"  {result['description']}")


async def test_news():
    """Test news feed"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST 7: Get News (AAPL, 5 items){Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

    service = YahooFinanceService()
    result = await service.get_news("AAPL", max_items=5)

    print(f"{Colors.OKGREEN}✓ Success!{Colors.ENDC} Latency: {Colors.WARNING}{result['latencyMs']}ms{Colors.ENDC}")
    print(f"Fetched {len(result['news'])} news items\n")

    for i, item in enumerate(result['news'], 1):
        print(f"{Colors.OKCYAN}{i}. {item['title']}{Colors.ENDC}")
        print(f"   Publisher: {item['publisher']}")
        print(f"   Link: {item['link'][:60]}..." if len(item['link']) > 60 else f"   Link: {item['link']}")
        print()


async def main():
    """Run all tests"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}Yahoo Finance Python Service - Comprehensive Test Suite{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")

    try:
        await test_quote()
        await test_multiple_quotes()
        await test_historical()
        await test_options()
        await test_indices()
        await test_company_info()
        await test_news()

        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}✓ All Tests Completed Successfully!{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

        print(f"{Colors.OKCYAN}Summary:{Colors.ENDC}")
        print(f"  ✓ Stock quotes with 70+ metrics")
        print(f"  ✓ Multiple quotes fetching")
        print(f"  ✓ Historical OHLCV data")
        print(f"  ✓ Options chain with IV, volume, OI")
        print(f"  ✓ Market indices (US & India)")
        print(f"  ✓ Company information")
        print(f"  ✓ News feed")
        print()
        print(f"{Colors.OKGREEN}All free Yahoo Finance features are working!{Colors.ENDC}\n")

    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())