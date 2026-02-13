#!/bin/bash
# ============================================================
# Stream test audio to ODAS at real-time speed, output to viz
# Usage: bash /odas/test_data/stream_to_web.sh
# ============================================================

PIPE="/tmp/odas_audio_pipe"
RAW_FILE="/odas/test_data/test_scene.raw"
CONFIG_TEMPLATE="/odas/test_data/respeaker_4_file_to_web.cfg"
CONFIG="/tmp/odas_web.cfg"
ODASLIVE="/odas/build/bin/odaslive"

# Audio parameters (must match config)
SAMPLE_RATE=16000
N_CHANNELS=4
BYTES_PER_SAMPLE=4  # 32-bit = 4 bytes
HOP_SIZE=128

# Bytes per hop: hopSize * nChannels * bytesPerSample
HOP_BYTES=$((HOP_SIZE * N_CHANNELS * BYTES_PER_SAMPLE))

# Resolve host IP (Docker Desktop for Mac) - prefer IPv4
HOST_IP=$(getent ahostsv4 host.docker.internal 2>/dev/null | head -1 | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    # Fallback to any address
    HOST_IP=$(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}')
fi
if [ -z "$HOST_IP" ]; then
    echo "ERROR: Could not resolve host.docker.internal"
    echo "Are you running inside Docker Desktop?"
    exit 1
fi
echo "Host IP: $HOST_IP"

# Patch config: resolve host IP and redirect input to the named pipe
sed -e "s/__HOST_IP__/$HOST_IP/g" \
    -e "s|/odas/test_data/test_scene.raw|$PIPE|g" \
    "$CONFIG_TEMPLATE" > "$CONFIG"
echo "Patched config: $CONFIG"

# Clean up on exit
cleanup() {
    echo "Cleaning up..."
    kill $FEEDER_PID 2>/dev/null
    kill $ODAS_PID 2>/dev/null
    rm -f "$PIPE"
    exit 0
}
trap cleanup EXIT INT TERM

# Create named pipe
rm -f "$PIPE"
mkfifo "$PIPE"
echo "Created named pipe: $PIPE"

# Start the real-time feeder in background
python3 -c "
import time, sys, os

raw_file = '$RAW_FILE'
pipe_path = '$PIPE'
hop_bytes = $HOP_BYTES
hop_time = $HOP_SIZE / $SAMPLE_RATE  # ~8ms per hop

with open(raw_file, 'rb') as f:
    data = f.read()

total_hops = len(data) // hop_bytes
duration = total_hops * hop_time
print(f'Streaming {total_hops} hops ({duration:.1f}s) at real-time speed...')

# Loop forever so the viz keeps showing data
while True:
    try:
        with open(pipe_path, 'wb') as pipe:
            for i in range(0, len(data), hop_bytes):
                chunk = data[i:i+hop_bytes]
                if len(chunk) < hop_bytes:
                    break
                pipe.write(chunk)
                pipe.flush()
                time.sleep(hop_time)
            print('Loop complete, restarting...')
    except BrokenPipeError:
        print('ODAS disconnected, stopping.')
        break
    except Exception as e:
        print(f'Feeder error: {e}')
        break
" &
FEEDER_PID=$!
echo "Started real-time audio feeder (PID: $FEEDER_PID)"

# Give the feeder a moment to open the pipe
sleep 1

# Run ODAS reading from the pipe
echo "Starting ODAS..."
$ODASLIVE -c "$CONFIG" &
ODAS_PID=$!

echo ""
echo "=== ODAS is streaming to viz server ==="
echo "=== Open http://localhost:8080       ==="
echo "=== Press Ctrl+C to stop             ==="
echo ""

wait $ODAS_PID
