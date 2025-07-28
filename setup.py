"""Setup script for initializing MASB project."""

import os
import sys
from pathlib import Path
import subprocess

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.example not found")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "data/prompts",
        "data/results", 
        "logs",
        "docs",
        "tests"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")
    return True

def generate_example_data():
    """Generate example datasets."""
    print("📝 Generating example datasets...")
    try:
        # Import and run the example generator
        sys.path.insert(0, str(Path(__file__).parent))
        from src.utils.generate_examples import generate_example_datasets
        generate_example_datasets()
        print("✅ Example datasets generated")
        return True
    except Exception as e:
        print(f"❌ Failed to generate example datasets: {e}")
        return False

def run_basic_tests():
    """Run basic functionality tests."""
    print("🧪 Running basic tests...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from tests.test_basic import run_basic_tests
        run_basic_tests()
        return True
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

def print_welcome_message():
    """Print welcome and next steps."""
    print("\n" + "="*60)
    print("🎉 MASB Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your API keys")
    print("2. Test your setup:")
    print("   python evaluate_model.py --list-models")
    print("3. Run your first evaluation:")
    print("   python evaluate_model.py --model claude-3-opus --language en --max-prompts 5")
    print("4. Analyze results:")
    print("   python analyze_results.py --report")
    print("\n📚 Documentation:")
    print("- README.md - Complete usage guide")
    print("- examples.py - Usage examples")
    print("- src/ - Source code")
    print("\n🆘 Support:")
    print("- Check README.md for troubleshooting")
    print("- Run 'python examples.py' for usage examples")
    print("\n" + "="*60)

def main():
    """Main setup function."""
    print("🚀 MASB Project Setup")
    print("="*30)
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Setup steps
    steps = [
        ("Creating directories", create_directories),
        ("Installing dependencies", install_dependencies),
        ("Creating .env file", create_env_file),
        ("Generating example data", generate_example_data),
        ("Running basic tests", run_basic_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            failed_steps.append(step_name)
    
    # Summary
    if failed_steps:
        print(f"\n⚠️  Setup completed with {len(failed_steps)} issues:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n💡 You can continue using MASB, but some features may not work.")
    else:
        print("\n✅ All setup steps completed successfully!")
    
    print_welcome_message()
    return len(failed_steps) == 0

if __name__ == "__main__":
    main()