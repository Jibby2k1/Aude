#!/usr/bin/env python3
"""
Replay ODAS JSON output files to the viz server at real-time speed.

Usage (inside Docker):
  1. First, generate the JSON files:
     cd /odas/build && ./bin/odaslive -c /odas/test_data/respeaker_4_file_test.cfg

  2. Then replay to the viz server:
     python3 /odas/test_data/replay_to_web.py

  3. Make sure the viz server is running on your Mac first!
     cd viz && node server.js
"""

import socket
import time
import argparse
import re
import sys


def resolve_host():
    """Auto-detect the Docker host IP."""
    try:
        return socket.gethostbyname('host.docker.internal')
    except socket.gaierror:
        return 'localhost'


def parse_json_frames(filepath):
    """Parse the ODAS JSON output file into individual frames."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Split on }{ boundary (each frame is a JSON object)
    # ODAS outputs frames separated by newlines: }\n{
    frames = []
    raw_frames = re.split(r'\}\s*\{', content)

    for i, frame in enumerate(raw_frames):
        # Re-add braces that were consumed by the split
        if not frame.strip().startswith('{'):
            frame = '{' + frame
        if not frame.strip().endswith('}'):
            frame = frame + '}'
        frame = frame.strip()
        if frame:
            frames.append(frame + '\n')

    return frames


def replay(host, ssl_file, sst_file, hop_time, loop):
    """Connect to the viz server and send frames at real-time speed."""

    ssl_frames = parse_json_frames(ssl_file)
    sst_frames = parse_json_frames(sst_file)

    n_frames = min(len(ssl_frames), len(sst_frames))
    duration = n_frames * hop_time

    print(f"Loaded {len(ssl_frames)} SSL frames, {len(sst_frames)} SST frames")
    print(f"Will replay {n_frames} frames ({duration:.1f}s of audio)")
    print(f"Connecting to viz server at {host}...")
    print()

    while True:
        try:
            # Connect to tracking server (port 9000)
            track_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            track_sock.connect((host, 9000))
            print(f"Connected to tracking server ({host}:9000)")

            # Connect to potential server (port 9001)
            pot_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pot_sock.connect((host, 9001))
            print(f"Connected to potential server ({host}:9001)")

        except ConnectionRefusedError:
            print("ERROR: Could not connect. Is the viz server running?")
            print("  Start it with:  cd viz && node server.js")
            sys.exit(1)

        print(f"\nStreaming {n_frames} frames at real-time speed...")
        print("Press Ctrl+C to stop.\n")

        try:
            for i in range(n_frames):
                # Send SSL (potential) frame
                if i < len(ssl_frames):
                    pot_sock.sendall(ssl_frames[i].encode('utf-8'))

                # Send SST (tracking) frame
                if i < len(sst_frames):
                    track_sock.sendall(sst_frames[i].encode('utf-8'))

                # Print progress every 100 frames
                if (i + 1) % 100 == 0:
                    print(f"  Sent {i+1}/{n_frames} frames "
                          f"({(i+1)*hop_time:.1f}s / {duration:.1f}s)")

                time.sleep(hop_time)

            print(f"\nDone! Sent all {n_frames} frames.")

        except BrokenPipeError:
            print("Viz server disconnected.")
        except KeyboardInterrupt:
            print("\nStopped by user.")
            track_sock.close()
            pot_sock.close()
            return

        track_sock.close()
        pot_sock.close()

        if loop:
            print("Looping... (restarting in 2 seconds)")
            time.sleep(2)
        else:
            break


if __name__ == '__main__':
    default_host = resolve_host()

    parser = argparse.ArgumentParser(description='Replay ODAS output to viz server')
    parser.add_argument('--host', default=default_host,
                        help=f'Viz server host IP (default: {default_host})')
    parser.add_argument('--ssl', default='/odas/test_data/ssl_output.json',
                        help='Path to SSL output JSON file')
    parser.add_argument('--sst', default='/odas/test_data/sst_output.json',
                        help='Path to SST output JSON file')
    parser.add_argument('--loop', action='store_true',
                        help='Loop the replay continuously')
    args = parser.parse_args()

    # hop_time = hopSize / sampleRate = 128 / 16000 = 0.008s
    hop_time = 128.0 / 16000.0

    replay(args.host, args.ssl, args.sst, hop_time, args.loop)
