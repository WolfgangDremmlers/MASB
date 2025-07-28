"""Web server launcher for MASB."""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.web.app import MASBWebApp
from src.utils.logger import logger
from src.utils.config_validator import config_manager


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MASB Web Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings
  python web_server.py
  
  # Start on custom host and port
  python web_server.py --host 0.0.0.0 --port 8080
  
  # Start with configuration file
  python web_server.py --config config.yml
  
  # Start in debug mode
  python web_server.py --debug
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--no-auto-reload",
        action="store_true",
        help="Disable auto-reload in debug mode"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    try:
        # Load configuration
        config = {}
        if args.config:
            config = config_manager.load_config(args.config)
        else:
            try:
                config = config_manager.load_config()
            except Exception:
                logger.warning("No configuration file found, using defaults")
        
        # Override with command line arguments
        web_config = config.get('web', {})
        web_config.update({
            'host': args.host,
            'port': args.port,
            'debug': args.debug
        })
        
        # Create and run web application
        webapp = MASBWebApp(web_config)
        
        logger.info(f"Starting MASB Web Interface")
        logger.info(f"Access the interface at: http://{args.host}:{args.port}")
        
        webapp.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()