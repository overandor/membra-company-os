# Quick Start Guide - DepthOS C++

## Prerequisites

- C++20 compiler (GCC 10+, Clang 12+, MSVC 2022+)
- CMake 3.16+
- OpenSSL development libraries
- libcurl development libraries
- Boost 1.70+ (with multiprecision, system, thread components)

## Installation

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install build-essential cmake libssl-dev libcurl4-openssl-dev libboost-all-dev
```

### macOS

```bash
# Option 1: Manual installation
brew install cmake openssl curl boost

# Option 2: Use the setup script (recommended)
./setup_deps.sh
```

Note: On macOS, you may need to set OpenSSL paths:
```bash
export OPENSSL_ROOT_DIR=$(brew --prefix openssl)
```

## Building

### Using the build script

```bash
cd files_cpp
./build.sh
```

### Manual build

```bash
mkdir build
cd build
cmake ..
make -j$(nproc)
```

The executable will be at `build/depthos`.

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Gate.io API credentials:
```bash
GATE_API_KEY=your_actual_api_key
GATE_API_SECRET=your_actual_api_secret
DRY_RUN=1  # Start with dry run enabled
```

## Running

### Direct execution

```bash
export GATE_API_KEY=your_key
export GATE_API_SECRET=your_secret
export DRY_RUN=1

./build/depthos
```

### Using Docker

```bash
# Build the Docker image
docker-compose build

# Run with environment variables from .env
docker-compose up
```

## Testing in Dry Run Mode

Always start with `DRY_RUN=1` to verify the system works without placing real orders:

```bash
export DRY_RUN=1
./build/depthos
```

You should see:
- Bootstrap messages showing contract specs loaded
- WebSocket connection messages
- Quote decision logs (but no actual orders placed)

## Going Live

1. Ensure sufficient balance in your Gate.io futures account
2. Set `DRY_RUN=0` or remove the environment variable
3. Start with small position limits in `config.hpp`
4. Monitor the logs closely
5. Have a stop-loss plan ready

## Troubleshooting

### Build errors

If you get OpenSSL errors on macOS:
```bash
export OPENSSL_ROOT_DIR=$(brew --prefix openssl)
cmake .. -DOPENSSL_ROOT_DIR=$OPENSSL_ROOT_DIR
```

If you get curl errors:
```bash
# Ubuntu/Debian
sudo apt-get install libcurl4-openssl-dev

# macOS
brew install curl
```

### Runtime errors

If you get "Missing required environment variables":
```bash
export GATE_API_KEY=your_key
export GATE_API_SECRET=your_secret
```

If WebSocket connection fails:
- Check your internet connection
- Verify Gate.io WebSocket URL is accessible
- Check firewall settings

## Next Steps

- Review `TODO.md` for implementation status
- Edit `MICRO_CONTRACTS` in `include/config.hpp` to target specific contracts
- Adjust risk parameters in `include/config.hpp` as needed
- Set up monitoring and logging for production use

## Safety Reminders

- **Never commit API keys or secrets** to version control
- **Always test in dry run mode first**
- **Start with small position limits**
- **Monitor daily PnL** to avoid exceeding loss limits
- **Keep sufficient balance** in your account
