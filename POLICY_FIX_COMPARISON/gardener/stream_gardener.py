import sys
import os
import argparse
from instance import read_from_file
from stream_game import StreamGame

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stream Gardener - Continuous streaming mode')
    parser.add_argument('instance_file', help='Path to instance file (.lp)')
    parser.add_argument('--tick_rate', type=int, default=1000, help='Tick rate in milliseconds (default: 1000)')
    parser.add_argument('--horizon', type=int, default=5, help='Horizon for ASP reasoning (default: 5)')
    parser.add_argument('--radius', type=int, default=6, help='Radius for ASP reasoning (default: 6)')
    parser.add_argument('--multi', type=int, default=1, help='Multiplier for rewards (default: 1)')
    parser.add_argument('--size', type=int, default=30, help='Size of the grid (default: 30)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.instance_file):
        print(f"Instance file not found: {args.instance_file}")
        sys.exit(1)

    print(f"Loading instance {args.instance_file}...")
    instance = read_from_file(args.instance_file)
    
    print(f"Starting StreamGame with tick rate {args.tick_rate}ms...")
    print(f"Parameters: horizon={args.horizon}, radius={args.radius}, multi={args.multi}")
    game = StreamGame(instance, show=True, tick_rate_ms=args.tick_rate, 
                      horizon=args.horizon, radius=args.radius, multi=args.multi,size=args.size)
    game.run()
    print("\n=== Game Finished ===")
    instance.print_report("stream_eval")
