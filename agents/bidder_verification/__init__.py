"""
Bidder Verification Agent
Orchestrates SAM.gov and OFAC compliance checks for bidder eligibility
"""

from agents.bidder_verification.tools.verify_bidder_eligibility import verify_bidder_eligibility

__all__ = ["verify_bidder_eligibility"]
