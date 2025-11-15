"""Tests for smart contract auditor module."""

import pytest
from unittest.mock import Mock, patch
from quantchain.agents.smart_contract_auditor import (
    SmartContractAuditorConfig,
    ContractRetriever,
    SmartContractAuditorAgent,
    VulnerabilityScanner,
    FinancialAnalyzer,
    ContractSource,
    VulnerabilityReport,
    Vulnerability,
    TokenomicsAnalysis,
    QuantChainError,
)


class TestSmartContractAuditorConfig:
    """Test SmartContractAuditorConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = SmartContractAuditorConfig()
        assert config.deep_analysis_enabled is True
        assert config.gas_analysis_enabled is True
        assert config.minimum_security_score == 70.0
        assert config.critical_vulnerabilities_threshold == 0


class TestContractRetriever:
    """Test ContractRetriever."""

    @pytest.fixture
    def config(self) -> SmartContractAuditorConfig:
        """Create test configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"etherscan": "test_key"}
        return config

    @pytest.fixture
    def retriever(self, config) -> ContractRetriever:
        """Create a ContractRetriever instance."""
        return ContractRetriever(config)

    @pytest.fixture
    def mock_response_data(self) -> dict:
        """Mock API response data."""
        return {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "SourceCode": "contract Test {}",
                    "ABI": '[]',
                    "ContractName": "Test",
                    "CompilerVersion": "v0.8.0",
                    "OptimizationUsed": "1",
                }
            ],
        }

    @patch("urllib.request.urlopen")
    def test_get_contract_source_success(
        self, mock_urlopen, retriever, mock_response_data
    ) -> None:
        """Test successful contract source retrieval."""
        mock_response = Mock()
        mock_response.read.return_value = str(mock_response_data).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        contract = retriever.get_contract_source("0x123", "ethereum")
        assert contract.address == "0x123"
        assert contract.chain == "ethereum"
        assert contract.source_code == "contract Test {}"


class TestSmartContractAuditorAgent:
    """Test SmartContractAuditorAgent."""

    @pytest.fixture
    def mock_config(self) -> SmartContractAuditorConfig:
        """Create mock configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"etherscan": "test_key"}
        return config

    @pytest.fixture
    def agent_config(self) -> dict:
        """Create agent configuration."""
        return {
            "name": "test_auditor",
            "description": "Test auditor agent",
            "use_paper": True,
            "initial_capital": 10000,
        }

    @pytest.fixture
    def agent(self, mock_config, agent_config) -> SmartContractAuditorAgent:
        """Create a SmartContractAuditorAgent instance."""
        return SmartContractAuditorAgent(mock_config, agent_config)

    def test_audit_contract_success(self, agent) -> None:
        """Test successful contract audit."""
        with patch.object(agent, 'get_contract_source') as mock_get_source, \
             patch.object(agent, 'scan_vulnerabilities') as mock_scan:

            # Setup mocks
            mock_contract = ContractSource(
                address="0x123",
                chain="ethereum",
                name="TestContract",
                source_code="contract Test {}",
                abi=[],
                bytecode=b"",
                compiler_version="v0.8.0",
                optimization_enabled=True,
                inherited_contracts=[],
            )
            mock_get_source.return_value = mock_contract

            mock_report = VulnerabilityReport(
                contract_address="0x123",
                chain="ethereum",
                vulnerabilities=[],
                overall_security_score=100.0,
                audit_status="PASS",
                timestamp=None,
            )
            mock_scan.return_value = mock_report

            # Run test
            result = agent.audit_contract("0x123", "ethereum")
            assert result == mock_report
