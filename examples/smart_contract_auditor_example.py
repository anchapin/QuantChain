"""Example script demonstrating the Smart Contract Auditor agent.

This example shows how to set up and run the Smart Contract Auditor that:
1. Retrieves Solidity contract source code from blockchain explorers
2. Scans for security vulnerabilities (reentrancy, access control, etc.)
3. Analyzes tokenomics and contract economics
4. Generates security scores and investment recommendations

Requirements:
- Blockchain explorer API keys (ETHERSCAN_API_KEY, BSCSCAN_API_KEY, etc.)
- LLM provider API key for code analysis (OpenAI or Anthropic recommended)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from quantchain.agents.smart_contract_auditor import (
    SmartContractAuditorAgent,
    SmartContractAuditorConfig,
)
from quantchain.core.config import QuantChainConfig, get_config
from quantchain.core.llm_providers import AnthropicProvider, OpenAIProvider

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def load_configuration() -> "QuantChainConfig":
    """Load QuantChain configuration and validate blockchain explorer API keys.

    Returns:
        QuantChainConfig: The loaded configuration object

    Raises:
        ValueError: If required API keys are missing
    """
    try:
        config = get_config()
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {e}") from e

    # Validate at least one blockchain explorer API key
    explorer_keys = {
        "ETHERSCAN_API_KEY": "Ethereum mainnet",
        "BSCSCAN_API_KEY": "Binance Smart Chain",
        "POLYGONSCAN_API_KEY": "Polygon",
        "ARBISCAN_API_KEY": "Arbitrum",
        "OPTIMISM_API_KEY": "Optimism",
    }

    available_explorers = [
        (key, network) for key, network in explorer_keys.items() if os.getenv(key)
    ]

    if not available_explorers:
        raise ValueError(
            "At least one blockchain explorer API key is required.\n"
            "Set one of the following in your .env file:\n"
            + "\n".join(
                f"  - {key} ({network})" for key, network in explorer_keys.items()
            )
        )

    # Log available explorers
    explorer_names = [network for _, network in available_explorers]
    logging.info(f"Available blockchain explorers: {', '.join(explorer_names)}")

    # Validate LLM provider configuration
    if not hasattr(config, "llm") or not config.llm:
        raise ValueError("LLM configuration not found in config.yaml")

    return config


def initialize_agent(config: "QuantChainConfig") -> SmartContractAuditorAgent:
    """Initialize the Smart Contract Auditor with all required components.

    Args:
        config: QuantChain configuration object

    Returns:
        SmartContractAuditorAgent: Initialized agent instance

    Raises:
        ValueError: If initialization fails
    """
    try:
        # Create agent configuration
        agent_config = SmartContractAuditorConfig(
            blockchain_network="ethereum",  # Default network
            security_checks_enabled=[
                "reentrancy",
                "access_control",
                "arithmetic",
                "unchecked_calls",
                "delegatecall",
                "tx_origin",
                "integer_overflow",
                "logic_gates",
            ],
            financial_analysis_enabled=True,
            min_security_score=70.0,
            min_financial_score=60.0,
            cache_contract_source=True,
            cache_directory="./data/contract_cache",
        )

        # Initialize LLM provider for code analysis
        llm_provider = None
        provider_name = getattr(config.llm, "provider", "openai").lower()

        if provider_name == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY required for OpenAI provider")
            llm_provider = OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=getattr(config.llm, "model", "gpt-4"),
                temperature=getattr(config.llm, "temperature", 0.1),
                max_tokens=getattr(config.llm, "max_tokens", 4000),
            )

        elif provider_name == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY required for Anthropic provider")
            llm_provider = AnthropicProvider(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=getattr(config.llm, "model", "claude-3-opus-20240229"),
                temperature=getattr(config.llm, "temperature", 0.1),
                max_tokens=getattr(config.llm, "max_tokens", 4000),
            )

        else:
            raise ValueError(
                f"LLM provider '{provider_name}' may not be optimal for code analysis. "
                "OpenAI GPT-4 or Anthropic Claude are recommended."
            )

        # Create and return the agent
        agent = SmartContractAuditorAgent(
            config=agent_config, llm_provider=llm_provider
        )

        return agent

    except Exception as e:
        raise ValueError(f"Failed to initialize agent: {e}") from e


def get_example_contracts() -> Dict[str, Dict[str, str]]:
    """Return a dictionary of well-known contract addresses for testing.

    Returns:
        Dict: Mapping of contract descriptions to addresses and blockchains
    """
    return {
        "Ethereum - USDT (Stable Token)": {
            "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "blockchain": "ethereum",
        },
        "Ethereum - USDC (Stable Token)": {
            "address": "0xA0b86a33E6441d6bB8c4d5E3694cA5d2c9A6E4Ae",
            "blockchain": "ethereum",
        },
        "Ethereum - Uniswap V2 Router": {
            "address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "blockchain": "ethereum",
        },
        "BSC - PancakeSwap Router": {
            "address": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
            "blockchain": "bsc",
        },
    }


def audit_contract(
    agent: SmartContractAuditorAgent,
    contract_address: str,
    blockchain: str,
    save_output: bool = False,
) -> Optional[Dict[str, Any]]:
    """Perform a comprehensive audit of a smart contract.

    Args:
        agent: Initialized SmartContractAuditorAgent instance
        contract_address: Contract address to audit
        blockchain: Blockchain network the contract is on
        save_output: Whether to save audit report to JSON

    Returns:
        Dict: Audit results or None if failed
    """
    print(f"\nAuditing contract {contract_address} on {blockchain}...")
    print("-" * 70)

    try:
        # Perform the audit
        audit_report = agent.audit_contract(contract_address, blockchain)

        # Display contract information
        _display_contract_info(audit_report)

        # Display security assessment
        print("\nSECURITY ASSESSMENT")
        print("-" * 20)
        print(f"Security Score: {audit_report['overall_security_score']}/100")
        print(f"Status: {audit_report['audit_status']}")

        # Display vulnerabilities
        if audit_report.get("vulnerabilities"):
            print(f"\nVULNERABILITIES FOUND ({len(audit_report['vulnerabilities'])})")
            print("-" * 30)

            # Group by severity
            by_severity: Dict[str, List[Dict[str, Any]]] = {}
            for vuln in audit_report["vulnerabilities"]:
                severity = vuln["severity"]
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(vuln)

            # Display in order of severity
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                if severity in by_severity:
                    print(f"\n{severity} ({len(by_severity[severity])}):")
                    for vuln in by_severity[severity]:
                        print(f"  • {vuln['vulnerability_type']}")
                        print(f"    {vuln['description']}")
                        if vuln.get("location"):
                            print(f"    Location: {vuln['location']}")
        else:
            print("\nNo vulnerabilities detected ✓")

        # Display financial analysis if available
        if (
            "tokenomics_analysis" in audit_report
            and audit_report["tokenomics_analysis"]
        ):
            tokenomics = audit_report["tokenomics_analysis"]
            print("\nFINANCIAL ANALYSIS")
            print("-" * 18)
            if "total_supply" in tokenomics:
                print(f"Total Supply: {tokenomics['total_supply']:,.0f}")
            if "holder_count" in tokenomics:
                print(f"Holders: {tokenomics['holder_count']:,}")
            if "distribution_score" in tokenomics:
                print(f"Distribution Score: {tokenomics['distribution_score']}/100")
            if "market_cap" in tokenomics:
                print(f"Market Cap: ${tokenomics['market_cap']:,.0f}")

        # Display investment recommendation
        if "investment_recommendation" in audit_report:
            rec = audit_report["investment_recommendation"]
            print("\nINVESTMENT RECOMMENDATION")
            print("-" * 27)
            print(f"Action: {rec.get('action', 'N/A')}")
            print(f"Risk Level: {rec.get('risk_level', 'N/A')}")
            if "reasoning" in rec:
                print(f"Reasoning: {rec['reasoning']}")

        # Save report if requested
        if save_output:
            scan_date = audit_report["scan_date"].strftime("%Y%m%d_%H%M%S")
            filename = f"audit_{contract_address[:10]}_{scan_date}.json"
            with open(filename, "w") as f:
                json.dump(audit_report, f, indent=2, default=str)
            print(f"\nFull audit report saved to: {filename}")

        return audit_report  # type: ignore[no-any-return]

    except Exception as e:
        print(f"Error auditing contract: {str(e)}")
        return None


def main() -> None:
    """Main execution function for the Smart Contract Auditor example."""
    # Parse command line arguments

    # Parse command line arguments

    parser = argparse.ArgumentParser(description="Smart Contract Auditor Example")
    parser.add_argument(
        "address",
        nargs="?",
        help="Contract address to audit (omit for example contracts)",
    )
    parser.add_argument(
        "--blockchain",
        default="ethereum",
        help="Blockchain network (default: ethereum)",
    )
    parser.add_argument(
        "--save", action="store_true", help="Save audit report to JSON file"
    )
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_configuration()
        logger.info("Configuration loaded successfully")

        # Initialize agent
        logger.info("Initializing Smart Contract Auditor...")
        agent = initialize_agent(config)
        logger.info("Agent initialized successfully")

        # Determine which contract to audit
        if args.address:
            # Audit the specified contract
            audit_contract(agent, args.address, args.blockchain, args.save)
        else:
            # Show available example contracts
            examples = get_example_contracts()
            print("\nAvailable example contracts:")
            print("-" * 30)
            for i, (desc, info) in enumerate(examples.items(), 1):
                print(f"{i}. {desc}")
                print(f"   Address: {info['address']}")
                print(f"   Blockchain: {info['blockchain']}")

            # For demonstration, audit the first example
            print("\nAuditing first example contract...")
            first_example = list(examples.values())[0]
            audit_contract(
                agent, first_example["address"], first_example["blockchain"], args.save
            )

        # Print important safety warnings
        print("\n" + "=" * 70)
        print("IMPORTANT SAFETY WARNINGS")
        print("=" * 70)
        print(
            "• This is an automated tool and NOT a substitute for professional audits"
        )
        print("• Always conduct thorough due diligence before investing")
        print("• High security scores do not guarantee safety")
        print("• Report false positives to improve the tool")
        print("• Educational purposes only - not financial or legal advice")

    except Exception as e:
        logger.error(f"Error running Smart Contract Auditor: {str(e)}")
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure blockchain explorer API keys are set in .env file")
        print("2. Check that config.yaml exists and is valid")
        print("3. Verify the contract address is valid and source code is verified")
        print("4. Ensure the specified blockchain network is supported")
        sys.exit(1)


def _display_contract_info(audit_report: Dict[str, Any]) -> None:
    """Display contract information section of audit report."""
    print("\nCONTRACT INFORMATION")
    print("-" * 20)
    print(f"Address: {audit_report['contract_address']}")
    print(f"Blockchain: {audit_report['chain']}")
    if "contract_name" in audit_report:
        print(f"Name: {audit_report['contract_name']}")
    if "contract_type" in audit_report:
        print(f"Type: {audit_report['contract_type']}")
    if "compiler_version" in audit_report:
        print(f"Compiler: {audit_report['compiler_version']}")


if __name__ == "__main__":
    main()
