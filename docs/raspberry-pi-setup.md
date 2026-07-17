# Raspberry Pi setup

Recommended starting hardware:

- Raspberry Pi 5, 8GB preferred
- Official 27W USB-C power supply
- Active cooler
- USB SSD for reliable write endurance
- Optional Raspberry Pi AI Camera
- Optional Raspberry Pi AI HAT+ or AI HAT+ 2 for accelerated AI workloads

## Install

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-venv python3-pip git

git clone https://github.com/ZenKOH/ClawGuard-Pi.AI.git
cd ClawGuard-Pi.AI
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8080
```

Open the dashboard from another machine on the same network:

```text
http://<pi-ip-address>:8080
```

## Security baseline

- Keep `CLAWGUARD_MODE=simulator` until hardware-specific policies are written and tested.
- Do not run ClawGuard as root.
- Do not expose port 8080 to the public internet.
- Prefer SSH tunnelling or a private VPN for remote operator access.
- Use a separate Pi or OS user per trust boundary.
