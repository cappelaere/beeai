"""
Management command to seed prompt suggestions from business-intelligence.md
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from agent_app.models import PromptSuggestion


class Command(BaseCommand):
    help = "Seed prompt suggestions from business-intelligence.md"

    def handle(self, *args, **options):
        # Read business-intelligence.md
        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        bi_file = repo_root / "docs" / "business-intelligence.md"

        if not bi_file.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {bi_file}"))
            return

        with open(bi_file, encoding="utf-8") as f:
            f.read()

        # Extract prompts from various sections
        prompts = []

        # 1. Property Analysis prompts
        prompts.extend(
            [
                "List all properties in the database",
                "Show me properties sold in the last 30 days",
                "What are the most expensive properties currently listed?",
                "Find properties with square footage greater than 3000",
                "Show properties by zip code 20001",
                "List properties with more than 4 bedrooms",
                "What properties were sold for more than $1 million?",
                "Show me properties with waterfront access",
                "Find properties with a pool",
                "List recently renovated properties",
            ]
        )

        # 2. Sales and Transaction prompts
        prompts.extend(
            [
                "What were the total sales for last month?",
                "Show me the average sale price by neighborhood",
                "Calculate the median home price in the city",
                "What is the price per square foot trend?",
                "Show sales volume by quarter",
                "Compare year-over-year sales growth",
                "What percentage of properties sold above asking price?",
                "Show me the fastest selling properties",
                "Calculate days on market by property type",
                "What are the current inventory levels?",
            ]
        )

        # 3. Market Analysis prompts
        prompts.extend(
            [
                "Generate a market trend report for this year",
                "What neighborhoods are showing the most appreciation?",
                "Show me price trends by zip code",
                "Compare market conditions to last year",
                "What is the current supply and demand ratio?",
                "Show me seasonal market patterns",
                "Identify emerging hot neighborhoods",
                "Calculate market absorption rate",
                "What are the foreclosure rates by area?",
                "Show me price distribution across all listings",
            ]
        )

        # 4. Agent and Broker prompts
        prompts.extend(
            [
                "List top performing agents this quarter",
                "Show agent performance by total sales volume",
                "What is the average commission rate?",
                "Calculate agent productivity metrics",
                "Show brokerage market share",
                "List agents with most closed transactions",
                "Compare agent performance year over year",
                "What are the most successful listing strategies?",
                "Show agent specializations by property type",
                "Calculate average time to close by agent",
            ]
        )

        # 5. Financial Analysis prompts
        prompts.extend(
            [
                "Calculate ROI for investment properties",
                "Show cash flow projections",
                "What are the property tax rates by area?",
                "Calculate cap rate for rental properties",
                "Show mortgage rate impact on affordability",
                "What percentage of sales are cash transactions?",
                "Calculate debt-to-income ratios for buyers",
                "Show financing trends over time",
                "What are the average closing costs?",
                "Calculate break-even analysis for flips",
            ]
        )

        # 6. Buyer and Seller Analysis prompts
        prompts.extend(
            [
                "What is the demographic profile of buyers?",
                "Show first-time buyer statistics",
                "Calculate seller equity positions",
                "What motivates sellers in this market?",
                "Show buyer preferences by age group",
                "What percentage of buyers are investors?",
                "Track buyer migration patterns",
                "Show seller holding periods",
                "Calculate buyer purchasing power trends",
                "What are the most desired property features?",
            ]
        )

        # 7. Comparative Market Analysis prompts
        prompts.extend(
            [
                "Perform a CMA for 123 Main Street",
                "Show comparable sales in the area",
                "What are similar properties priced at?",
                "Calculate suggested listing price",
                "Show active competition in the neighborhood",
                "Compare property features to comps",
                "What adjustments should be made for condition?",
                "Show pending sales that might affect pricing",
                "Calculate competitive market position",
                "Generate a pricing strategy recommendation",
            ]
        )

        # 8. Reporting and Visualization prompts
        prompts.extend(
            [
                "Generate a monthly market report",
                "Create a sales performance dashboard",
                "Show me year-end statistics",
                "Generate client presentation materials",
                "Create a neighborhood profile report",
                "Show market snapshot for investors",
                "Generate broker production report",
                "Create property marketing analysis",
                "Show quarterly performance metrics",
                "Generate annual market forecast",
            ]
        )

        # 9. GRES-specific prompts (based on the document)
        prompts.extend(
            [
                "Show me all GRES property listings",
                "What documents are available in GRES?",
                "Search GRES database by property ID",
                "Show GRES transaction history",
                "Generate GRES compliance report",
                "What are the GRES data quality metrics?",
                "Show GRES system usage statistics",
                "List recent GRES updates",
                "Search GRES by owner name",
                "Show GRES property classifications",
            ]
        )

        # 9b. SAM.gov Exclusions prompts (Federal contract compliance)
        prompts.extend(
            [
                "Is ACME Corporation excluded from federal contracts?",
                "Search for exclusions by TREAS-OFAC",
                "Show me SAM.gov exclusion statistics",
                "Check if John Smith is excluded",
                "List all excluding agencies in SAM.gov",
                "Find all firms excluded by HHS",
                "Show me individuals excluded by DOJ",
                "Search for exclusions from Treasury OFAC",
                "What are the most common exclusion types?",
                "Show exclusions from the last 6 months",
                "Find all indefinite exclusions",
                "Check exclusion status for vendor XYZ",
                "List all vessel exclusions",
                "Show Special Entity Designations",
                "Find exclusions by company name",
                "Get details for SAM number S4MR3R7D6",
                "How many exclusions are there total?",
                "Show me exclusions by country",
                "Find all EPA exclusions",
                "Check if a contractor is excluded",
            ]
        )

        # 10. Advanced Analytics prompts
        prompts.extend(
            [
                "Predict future market values using AI",
                "What properties are likely to appreciate?",
                "Identify undervalued properties",
                "Show risk assessment for investments",
                "Calculate market volatility index",
                "Predict optimal listing timing",
                "What factors most influence sale price?",
                "Show correlation between features and price",
                "Identify market anomalies",
                "Generate predictive pricing model",
            ]
        )

        # Save all prompts to database
        created = 0
        skipped = 0

        for prompt_text in prompts:
            prompt_text = prompt_text.strip()
            if not prompt_text or len(prompt_text) < 5:
                continue

            # Check if prompt already exists
            if PromptSuggestion.objects.filter(prompt=prompt_text).exists():
                skipped += 1
                continue

            # Create new prompt suggestion
            PromptSuggestion.objects.create(prompt=prompt_text, is_predefined=True, usage_count=0)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {created} prompt suggestions (skipped {skipped} duplicates)"
            )
        )
