"""
Options Greeks Calculator using Black-Scholes Model
Calculates Delta, Gamma, Theta, Vega, Rho for options
"""

from __future__ import annotations

import math
from datetime import datetime, date
from typing import Dict, Any

from scipy.stats import norm


class OptionsGreeksCalculator:
    """
    Calculate Options Greeks using Black-Scholes model

    Greeks calculated:
    - Delta: Rate of change of option price with respect to stock price
    - Gamma: Rate of change of Delta with respect to stock price
    - Theta: Rate of change of option price with respect to time (time decay)
    - Vega: Rate of change of option price with respect to volatility
    - Rho: Rate of change of option price with respect to interest rate
    """

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize calculator

        Args:
            risk_free_rate: Annual risk-free interest rate (default: 5% = 0.05)
        """
        self.risk_free_rate = risk_free_rate

    def _calculate_d1_d2(
        self,
        stock_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        dividend_yield: float = 0.0
    ) -> tuple[float, float]:
        """Calculate d1 and d2 for Black-Scholes formula"""

        if time_to_expiry <= 0:
            time_to_expiry = 0.001  # Avoid division by zero

        if volatility <= 0:
            volatility = 0.01  # Avoid division by zero

        d1 = (
            math.log(stock_price / strike_price) +
            (self.risk_free_rate - dividend_yield + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * math.sqrt(time_to_expiry))

        d2 = d1 - volatility * math.sqrt(time_to_expiry)

        return d1, d2

    def calculate_greeks(
        self,
        stock_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = "call",
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option

        Args:
            stock_price: Current stock price
            strike_price: Option strike price
            time_to_expiry: Time to expiration in years
            volatility: Implied volatility (as decimal, e.g., 0.25 for 25%)
            option_type: "call" or "put"
            dividend_yield: Annual dividend yield (as decimal)

        Returns:
            Dictionary with Delta, Gamma, Theta, Vega, Rho
        """

        if time_to_expiry <= 0:
            # Option has expired or is expiring today
            if option_type.lower() == "call":
                delta = 1.0 if stock_price > strike_price else 0.0
            else:
                delta = -1.0 if stock_price < strike_price else 0.0

            return {
                "delta": delta,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }

        d1, d2 = self._calculate_d1_d2(
            stock_price, strike_price, time_to_expiry, volatility, dividend_yield
        )

        # Calculate Greeks
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
            rho = strike_price * time_to_expiry * math.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100
        else:  # put
            delta = norm.cdf(d1) - 1
            rho = -strike_price * time_to_expiry * math.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100

        # Gamma is same for calls and puts
        gamma = norm.pdf(d1) / (stock_price * volatility * math.sqrt(time_to_expiry))

        # Theta (per day, not per year)
        if option_type.lower() == "call":
            theta = (
                -(stock_price * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiry)) -
                self.risk_free_rate * strike_price * math.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2)
            ) / 365
        else:  # put
            theta = (
                -(stock_price * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiry)) +
                self.risk_free_rate * strike_price * math.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            ) / 365

        # Vega (per 1% change in volatility)
        vega = stock_price * norm.pdf(d1) * math.sqrt(time_to_expiry) / 100

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "rho": round(rho, 4)
        }

    def calculate_time_to_expiry(self, expiry_date: str) -> float:
        """
        Calculate time to expiry in years

        Args:
            expiry_date: Expiry date in format "YYYY-MM-DD"

        Returns:
            Time to expiry in years
        """
        if isinstance(expiry_date, str):
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        else:
            expiry = expiry_date

        today = date.today()
        days_to_expiry = (expiry - today).days

        return max(days_to_expiry / 365.0, 0.001)  # Minimum 0.001 to avoid division by zero

    def add_greeks_to_option(
        self,
        option: Dict[str, Any],
        stock_price: float,
        expiry_date: str,
        option_type: str,
        dividend_yield: float = 0.0
    ) -> Dict[str, Any]:
        """
        Add Greeks to an option contract dictionary

        Args:
            option: Option contract dict with strike, impliedVolatility, etc.
            stock_price: Current stock price
            expiry_date: Expiry date
            option_type: "call" or "put"
            dividend_yield: Dividend yield

        Returns:
            Option dict with Greeks added
        """
        time_to_expiry = self.calculate_time_to_expiry(expiry_date)

        greeks = self.calculate_greeks(
            stock_price=stock_price,
            strike_price=option["strike"],
            time_to_expiry=time_to_expiry,
            volatility=option.get("impliedVolatility", 0.25),
            option_type=option_type,
            dividend_yield=dividend_yield
        )

        # Add Greeks to option dict
        option["delta"] = greeks["delta"]
        option["gamma"] = greeks["gamma"]
        option["theta"] = greeks["theta"]
        option["vega"] = greeks["vega"]
        option["rho"] = greeks["rho"]

        return option


# Example usage
if __name__ == "__main__":
    calculator = OptionsGreeksCalculator(risk_free_rate=0.05)

    # Example: Calculate Greeks for AAPL call option
    greeks = calculator.calculate_greeks(
        stock_price=274.23,
        strike_price=275.0,
        time_to_expiry=30/365,  # 30 days
        volatility=0.24,  # 24% IV
        option_type="call",
        dividend_yield=0.0038  # 0.38%
    )

    print("Greeks for AAPL $275 Call (30 days to expiry):")
    print(f"  Delta: {greeks['delta']:.4f}")
    print(f"  Gamma: {greeks['gamma']:.4f}")
    print(f"  Theta: {greeks['theta']:.4f}")
    print(f"  Vega:  {greeks['vega']:.4f}")
    print(f"  Rho:   {greeks['rho']:.4f}")
