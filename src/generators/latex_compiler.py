"""
LaTeX compilation utilities with multiple backend options
"""
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging
import time

logger = logging.getLogger(__name__)


class CompilationError(Exception):
    """Exception raised when LaTeX compilation fails"""
    pass


class LaTeXCompiler:
    """Base class for LaTeX compilers"""

    def compile(self, tex_file: str, output_dir: Optional[str] = None) -> str:
        """
        Compile .tex file to PDF.

        Args:
            tex_file: Path to .tex file
            output_dir: Directory for output files (default: same as tex_file)

        Returns:
            Path to generated PDF file

        Raises:
            CompilationError: If compilation fails
        """
        raise NotImplementedError("Subclass must implement compile()")

    def cleanup_aux_files(self, tex_file: str):
        """
        Remove auxiliary files created during compilation.

        Args:
            tex_file: Path to .tex file
        """
        tex_path = Path(tex_file)
        aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot']

        for ext in aux_extensions:
            aux_file = tex_path.with_suffix(ext)
            if aux_file.exists():
                try:
                    aux_file.unlink()
                    logger.debug(f"Removed auxiliary file: {aux_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove {aux_file}: {e}")


class LocalLaTeXCompiler(LaTeXCompiler):
    """Compile LaTeX using local pdflatex installation"""

    def __init__(self, pdflatex_path: str = 'pdflatex'):
        """
        Initialize local compiler.

        Args:
            pdflatex_path: Path to pdflatex binary (default: searches PATH)
        """
        self.pdflatex_path = pdflatex_path

        # Check if pdflatex is available
        if not shutil.which(pdflatex_path):
            raise FileNotFoundError(
                f"pdflatex not found at {pdflatex_path}. "
                "Please install LaTeX (TeX Live or MiKTeX) or use DockerLaTeXCompiler."
            )

        logger.info(f"Local LaTeX compiler initialized: {pdflatex_path}")

    def compile(self, tex_file: str, output_dir: Optional[str] = None) -> str:
        """
        Compile using local pdflatex.

        Args:
            tex_file: Path to .tex file
            output_dir: Directory for output (default: same as tex_file)

        Returns:
            Path to generated PDF

        Raises:
            CompilationError: If compilation fails
        """
        tex_path = Path(tex_file)

        if not tex_path.exists():
            raise FileNotFoundError(f"TeX file not found: {tex_file}")

        # Determine output directory
        if output_dir is None:
            output_dir = tex_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Compiling {tex_path.name} with local pdflatex...")

        # Run pdflatex twice (for references)
        for run in [1, 2]:
            logger.debug(f"pdflatex run {run}/2")

            result = subprocess.run(
                [
                    self.pdflatex_path,
                    '-interaction=nonstopmode',
                    '-output-directory', str(output_dir),
                    str(tex_path)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                # Parse error from log
                log_file = output_dir / tex_path.with_suffix('.log').name
                error_msg = self._parse_error_log(log_file)

                logger.error(f"pdflatex failed (run {run}): {error_msg}")
                raise CompilationError(f"LaTeX compilation failed: {error_msg}")

        # Check PDF was created
        pdf_path = output_dir / tex_path.with_suffix('.pdf').name
        if not pdf_path.exists():
            raise CompilationError("PDF file was not generated")

        logger.info(f"✓ PDF generated: {pdf_path}")

        # Cleanup auxiliary files
        self.cleanup_aux_files(str(output_dir / tex_path.name))

        return str(pdf_path)

    def _parse_error_log(self, log_file: Path) -> str:
        """Extract error message from .log file"""
        if not log_file.exists():
            return "No log file generated"

        try:
            log_content = log_file.read_text(encoding='utf-8', errors='ignore')

            # Look for error indicators
            error_lines = []
            for line in log_content.split('\n'):
                if line.startswith('!') or 'Error' in line:
                    error_lines.append(line)

            if error_lines:
                return '\n'.join(error_lines[:5])  # First 5 errors

            return "Compilation failed (check log file for details)"

        except Exception:
            return "Could not parse log file"


class DockerLaTeXCompiler(LaTeXCompiler):
    """Compile LaTeX using Docker container"""

    def __init__(self, image: str = 'texlive/texlive:latest', keep_running: bool = False):
        """
        Initialize Docker compiler.

        Args:
            image: Docker image to use
            keep_running: Keep container running between compilations (faster)
        """
        self.image = image
        self.keep_running = keep_running
        self.container_id = None

        # Check if Docker is available
        if not shutil.which('docker'):
            raise FileNotFoundError(
                "Docker not found. Please install Docker or use LocalLaTeXCompiler."
            )

        # Check if image exists, pull if needed
        result = subprocess.run(
            ['docker', 'images', '-q', image],
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            logger.info(f"Pulling Docker image: {image}")
            subprocess.run(['docker', 'pull', image], check=True)

        logger.info(f"Docker LaTeX compiler initialized: {image}")

    def compile(self, tex_file: str, output_dir: Optional[str] = None) -> str:
        """
        Compile using Docker pdflatex.

        Args:
            tex_file: Path to .tex file
            output_dir: Directory for output (default: same as tex_file)

        Returns:
            Path to generated PDF

        Raises:
            CompilationError: If compilation fails
        """
        tex_path = Path(tex_file).absolute()

        if not tex_path.exists():
            raise FileNotFoundError(f"TeX file not found: {tex_file}")

        # Determine output directory
        if output_dir is None:
            work_dir = tex_path.parent
        else:
            work_dir = Path(output_dir).absolute()
            work_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Compiling {tex_path.name} with Docker...")

        # Copy .tex file to output directory if different
        if tex_path.parent != work_dir:
            work_tex = work_dir / tex_path.name
            work_tex.write_text(tex_path.read_text(encoding='utf-8'), encoding='utf-8')
            tex_file_name = tex_path.name
        else:
            tex_file_name = tex_path.name

        # Run pdflatex in Docker container (twice for references)
        for run in [1, 2]:
            logger.debug(f"Docker pdflatex run {run}/2")

            result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-v', f'{work_dir}:/data',
                    self.image,
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory=/data',
                    f'/data/{tex_file_name}'
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"Docker compilation failed (run {run})")
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")

                # Try to parse error from log
                log_file = work_dir / Path(tex_file_name).with_suffix('.log').name
                error_msg = self._parse_error_log(log_file) if log_file.exists() else result.stderr

                raise CompilationError(f"Docker LaTeX compilation failed: {error_msg}")

        # Check PDF was created
        pdf_path = work_dir / Path(tex_file_name).with_suffix('.pdf').name
        if not pdf_path.exists():
            raise CompilationError("PDF file was not generated by Docker")

        logger.info(f"✓ PDF generated: {pdf_path}")

        # Cleanup auxiliary files
        self.cleanup_aux_files(str(work_dir / tex_file_name))

        return str(pdf_path)

    def _parse_error_log(self, log_file: Path) -> str:
        """Extract error message from .log file"""
        # Same implementation as LocalLaTeXCompiler
        if not log_file.exists():
            return "No log file generated"

        try:
            log_content = log_file.read_text(encoding='utf-8', errors='ignore')

            error_lines = []
            for line in log_content.split('\n'):
                if line.startswith('!') or 'Error' in line:
                    error_lines.append(line)

            if error_lines:
                return '\n'.join(error_lines[:5])

            return "Compilation failed (check log file for details)"

        except Exception:
            return "Could not parse log file"


def auto_select_compiler() -> LaTeXCompiler:
    """
    Automatically select best available compiler.

    Returns:
        LaTeXCompiler instance (Docker or Local)
    """
    # Try Docker first (recommended)
    try:
        return DockerLaTeXCompiler()
    except FileNotFoundError:
        logger.info("Docker not available, trying local pdflatex...")

    # Fall back to local pdflatex
    try:
        return LocalLaTeXCompiler()
    except FileNotFoundError:
        raise RuntimeError(
            "No LaTeX compiler available. Please install Docker or LaTeX (TeX Live/MiKTeX)."
        )


def compile_with_retry(tex_file: str, output_dir: Optional[str] = None,
                       max_retries: int = 2) -> Tuple[str, Optional[Exception]]:
    """
    Compile LaTeX with automatic retry and error recovery.

    Args:
        tex_file: Path to .tex file
        output_dir: Output directory
        max_retries: Maximum compilation attempts

    Returns:
        Tuple of (pdf_path, error) - error is None on success
    """
    compiler = auto_select_compiler()

    for attempt in range(max_retries):
        try:
            logger.info(f"Compilation attempt {attempt + 1}/{max_retries}")

            pdf_path = compiler.compile(tex_file, output_dir)

            logger.info(f"✓ Compilation successful: {pdf_path}")
            return pdf_path, None

        except CompilationError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt == max_retries - 1:
                logger.error(f"All compilation attempts failed")
                return None, e

            # Wait before retry
            time.sleep(1)

    return None, CompilationError("Max retries exceeded")


def test_compiler():
    """Test LaTeX compiler with minimal document"""
    print("Testing LaTeX Compiler...")

    # Create simple test document
    test_tex = r"""\documentclass{article}
\begin{document}
Hello from LaTeX!
\end{document}
"""

    test_dir = Path(__file__).parent.parent.parent / 'test_output'
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / 'test.tex'
    test_file.write_text(test_tex, encoding='utf-8')

    print(f"Created test file: {test_file}")

    # Try compilation
    try:
        pdf_path, error = compile_with_retry(str(test_file))

        if error:
            print(f"✗ Compilation failed: {error}")
            return False

        print(f"✓ PDF generated: {pdf_path}")
        print(f"✓ Compiler test passed!")
        return True

    except Exception as e:
        print(f"✗ Compiler test failed: {e}")
        return False


if __name__ == '__main__':
    test_compiler()
