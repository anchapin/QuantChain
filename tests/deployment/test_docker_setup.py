"""Tests for Docker deployment configuration and GPU support."""

import pytest
import subprocess
import os
from pathlib import Path
from typing import Dict, Any


class TestDockerConfiguration:
    """Test Docker configuration files and setup."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def dockerfile_gpu_path(self, project_root: Path) -> Path:
        """Path to GPU Dockerfile."""
        return project_root / "Dockerfile.gpu"

    @pytest.fixture
    def docker_compose_gpu_path(self, project_root: Path) -> Path:
        """Path to GPU docker-compose file."""
        return project_root / "docker-compose.gpu.yml"

    def test_gpu_dockerfile_exists(self, dockerfile_gpu_path: Path) -> None:
        """Test that GPU Dockerfile exists."""
        assert dockerfile_gpu_path.exists(), "GPU Dockerfile should exist"
        assert dockerfile_gpu_path.is_file(), "GPU Dockerfile should be a file"

    def test_docker_compose_gpu_exists(self, docker_compose_gpu_path: Path) -> None:
        """Test that GPU docker-compose file exists."""
        assert docker_compose_gpu_path.exists(), "GPU docker-compose file should exist"
        assert docker_compose_gpu_path.is_file(), "GPU docker-compose should be a file"

    def test_gpu_dockerfile_cuda_version(self, dockerfile_gpu_path: Path) -> None:
        """Test that GPU Dockerfile uses appropriate CUDA version."""
        content = dockerfile_gpu_path.read_text()
        assert "nvidia/cuda:12.1" in content, "Should use CUDA 12.1 base image"
        assert "runtime" in content, "Should use runtime variant"

    def test_gpu_dockerfile_pytorch_cuda(self, dockerfile_gpu_path: Path) -> None:
        """Test that GPU Dockerfile installs CUDA-enabled PyTorch."""
        content = dockerfile_gpu_path.read_text()
        assert "torch==2.1.0+cu121" in content, "Should install CUDA-enabled PyTorch"
        assert "download.pytorch.org/whl/cu121" in content, "Should use CUDA index URL"

    def test_docker_compose_gpu_runtime(self, docker_compose_gpu_path: Path) -> None:
        """Test that GPU docker-compose uses NVIDIA runtime."""
        content = docker_compose_gpu_path.read_text()
        assert "runtime: nvidia" in content, "Should specify NVIDIA runtime"
        assert (
            "CUDA_VISIBLE_DEVICES" in content
        ), "Should set CUDA environment variables"

    def test_docker_compose_gpu_resources(self, docker_compose_gpu_path: Path) -> None:
        """Test GPU resource allocation in docker-compose."""
        content = docker_compose_gpu_path.read_text()
        assert "reservations:" in content, "Should specify resource reservations"
        assert "driver: nvidia" in content, "Should specify NVIDIA driver"
        assert "capabilities: [gpu]" in content, "Should request GPU capabilities"

    def test_docker_compose_services(self, docker_compose_gpu_path: Path) -> None:
        """Test required services are defined in docker-compose."""
        content = docker_compose_gpu_path.read_text()
        required_services = ["quantchain-gpu", "chromadb", "redis"]
        for service in required_services:
            assert service in content, f"Service {service} should be defined"

    def test_gpu_dockerfile_health_check(self, dockerfile_gpu_path: Path) -> None:
        """Test that GPU Dockerfile includes health check."""
        content = dockerfile_gpu_path.read_text()
        assert "HEALTHCHECK" in content, "Should include health check"
        assert "quantchain" in content.lower(), "Health check should verify QuantChain"

    def test_docker_security_config(self, dockerfile_gpu_path: Path) -> None:
        """Test Docker security configuration."""
        content = dockerfile_gpu_path.read_text()
        assert "useradd" in content, "Should create non-root user"
        assert "USER quantchain" in content, "Should switch to non-root user"


@pytest.mark.skipif(
    not os.getenv("RUN_DOCKER_TESTS"),
    reason="Docker tests require RUN_DOCKER_TESTS environment variable",
)
class TestDockerBuild:
    """Test actual Docker build and execution (integration tests)."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture(scope="class")
    def gpu_available(self) -> bool:
        """Check if GPU is available for testing."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and len(result.stdout.strip()) > 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def test_build_gpu_docker_image(self, project_root: Path) -> None:
        """Test building GPU Docker image."""
        cmd = [
            "docker",
            "build",
            "-f",
            "Dockerfile.gpu",
            "-t",
            "quantchain:test",
            str(project_root),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"

    @pytest.mark.skipif(
        not os.getenv("RUN_DOCKER_TESTS") or not True,  # GPU check moved to fixture
        reason="Requires GPU and explicit test run",
    )
    def test_gpu_container_startup(self, gpu_available: bool) -> None:
        """Test GPU container startup and CUDA detection."""
        if not gpu_available:
            pytest.skip("No GPU available for testing")

        cmd = [
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            "quantchain:test",
            "python3",
            "-c",
            "import torch; "
            "assert torch.cuda.is_available(), 'CUDA not available'; "
            "print('GPU test passed')",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, f"GPU container test failed: {result.stderr}"
        assert "GPU test passed" in result.stdout

    def test_container_import_quantchain(self) -> None:
        """Test that QuantChain can be imported in container."""
        cmd = [
            "docker",
            "run",
            "--rm",
            "quantchain:test",
            "python3",
            "-c",
            "import quantchain; " "print('QuantChain import test passed')",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, f"Import test failed: {result.stderr}"
        assert "QuantChain import test passed" in result.stdout


class TestDockerComposeValidation:
    """Test docker-compose configuration validation."""

    @pytest.fixture
    def docker_compose_content(self) -> Dict[str, Any]:
        """Load and parse docker-compose configuration."""
        project_root = Path(__file__).parent.parent.parent
        compose_file = project_root / "docker-compose.gpu.yml"
        content = compose_file.read_text()

        # Simple parsing for basic validation
        # Note: For production, use pyyaml for proper YAML parsing
        return {"content": content, "lines": content.splitlines()}

    def test_version_specified(self, docker_compose_content: Dict[str, Any]) -> None:
        """Test that docker-compose version is specified."""
        content = docker_compose_content["content"]
        assert "version:" in content, "Should specify docker-compose version"
        assert "'3.8'" in content or '"3.8"' in content, "Should use version 3.8"

    def test_network_configuration(
        self, docker_compose_content: Dict[str, Any]
    ) -> None:
        """Test network configuration."""
        content = docker_compose_content["content"]
        assert "networks:" in content, "Should define networks"
        assert "default:" in content, "Should have default network"
        assert "driver: bridge" in content, "Should use bridge driver"

    def test_volume_configuration(self, docker_compose_content: Dict[str, Any]) -> None:
        """Test volume configuration."""
        content = docker_compose_content["content"]
        assert "volumes:" in content, "Should define volumes"
        assert "chroma_data:" in content, "Should define chroma_data volume"
        assert "redis_data:" in content, "Should define redis_data volume"

    def test_environment_variables(
        self, docker_compose_content: Dict[str, Any]
    ) -> None:
        """Test environment variable configuration."""
        content = docker_compose_content["content"]
        env_vars = ["CUDA_VISIBLE_DEVICES", "PYTHONPATH", "MODEL_TYPE", "QUANTIZATION"]

        for var in env_vars:
            assert var in content, f"Should define {var} environment variable"

    def test_port_configuration(self, docker_compose_content: Dict[str, Any]) -> None:
        """Test port configuration."""
        content = docker_compose_content["content"]
        assert "8501:8501" in content, "Should expose Streamlit port"
        assert "8001:8000" in content, "Should expose ChromaDB port"
        assert "6379:6379" in content, "Should expose Redis port"

    def test_restart_policies(self, docker_compose_content: Dict[str, Any]) -> None:
        """Test restart policies."""
        content = docker_compose_content["content"]
        assert "restart: unless-stopped" in content, "Should define restart policy"


class TestDeploymentDocumentation:
    """Test deployment documentation completeness."""

    @pytest.fixture
    def docs_dir(self) -> Path:
        """Get documentation directory."""
        return Path(__file__).parent.parent.parent / "docs"

    def test_hardware_requirements_exists(self, docs_dir: Path) -> None:
        """Test that hardware requirements documentation exists."""
        hw_doc = docs_dir / "hardware-requirements.md"
        assert hw_doc.exists(), "Hardware requirements documentation should exist"

        content = hw_doc.read_text()
        required_sections = [
            "VRAM Required",
            "GPU Recommendations",
            "Performance Benchmarks",
            "Model Categories",
        ]

        for section in required_sections:
            assert section in content, f"Should include {section} section"

    def test_environment_setup_exists(self, docs_dir: Path) -> None:
        """Test that environment setup documentation exists."""
        setup_doc = docs_dir / "environment-setup.md"
        assert setup_doc.exists(), "Environment setup documentation should exist"

        content = setup_doc.read_text()
        required_sections = [
            "Docker",
            "Local Development",
            "CUDA Setup",
            "Configuration",
        ]

        for section in required_sections:
            assert section in content, f"Should include {section} section"

    def test_docker_examples_in_docs(self, docs_dir: Path) -> None:
        """Test that documentation includes Docker examples."""
        setup_doc = docs_dir / "environment-setup.md"
        content = setup_doc.read_text()

        docker_commands = [
            "docker compose",
            "Dockerfile.gpu",
            "nvidia-container-toolkit",
            "runtime: nvidia",
        ]

        for cmd in docker_commands:
            assert cmd in content, f"Should include {cmd} in documentation"
