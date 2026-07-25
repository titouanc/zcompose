# zcompose

Orchestrate multiple [Zephyr](https://www.zephyrproject.org/) applications on your
machine, inspired by `docker compose`.

A single `zcompse.yml` file describes a group of Zephyr applications and the virtual
networks they share. `zcompose` then builds them, wires up the host networking,
runs them together and tears everything down againn, so you can develop and test
multi-node Zephyr setups (a server and a client, a gateway and sensors, ...)
entirely on your laptop using `native_sim` or an emulator such as QEMU.

## Features

- **Declarative**: describe applications, networks and build options in one `zcompose.yml`.
- **Virtual networking**: creates Linux bridges, TAP interfaces and (optionally) a host-side veth so the host can talk to the simulated nodes.
- **Automatic addressing**: each network-attached app gets a deterministic MAC, IPv4 and IPv6 address, injected into its Kconfig automatically.
- **Cross-references**: refer to another app's address with `${app:prop}` substitution
- **Parallel builds** your apps (and yes, they have progress bars)
- **Aggregated output** of all your apps in a single place

## Requirements

- Python >= 3.10
- A working [Zephyr development environment](https://docs.zephyrproject.org/latest/develop/getting_started/index.html) with `west` on your `PATH`.
- Linux, with `sudo` access to `ip` (used to manage bridges/TAP/veth interfaces).
- Optional: `picocom` (for `console`), `usbip` (for `attach-usb`).

## Installation

```bash
pip install git+https://github.com/titouanc/zcompose
```

## Quick start

Create a `zcompose.yml` file to describe your applications and their networks.
Read more on the [configuration file format](docs/config-file.md).

Here is a short example:

```yaml
name: Echo demo

networks:
  zeth:
    host-veth: true          # also expose the network to the host
    ipv4: 192.0.2.0/24
    ipv6: 2001:db8::/64

applications:
  server:
    source: ./echo-server
    network: zeth

  client:
    source: ./echo-client
    network: zeth
    extra-build:
      config:
        # Reference the server's auto-assigned addresses
        NET_CONFIG_PEER_IPV4_ADDR: ${server:ipv4}
        NET_CONFIG_PEER_IPV6_ADDR: ${server:ipv6}
```

Then:

```bash
# Inspect the resolved configuration (addresses, interfaces, status)
zcompose show

# Create the bridge / TAP / veth interfaces (needs sudo)
zcompose up

# Build all apps and run them together (Ctrl-C stops them)
zcompose run

# Tear the network interfaces back down
zcompose down
```

`up` is intentionally separate from `run`: bringing networking up requires root,
while building and running your applications does not.

## Commands

Run `zcompose <command>`. The compose file defaults to `./zcompose.yml`; override
it with `-f/--file`.

| Command | Description |
| --- | --- |
| `show` | Print the resolved networks and applications, with their addresses and interface status. |
| `up` | Bring up all networks: create bridges, host veth and one TAP per app (uses `sudo ip`). |
| `down` | Tear down all networks (refuses if apps are still running). |
| `build [APP]` | Build all apps in parallel, or a single app. |
| `run [APP]` | Build then run all apps (or one), streaming their output. Requires `up` first. |
| `clean [APP]` | Run `west build -t clean` for all apps or one. |
| `menuconfig APP` | Open `menuconfig` for one app's build. |
| `debug APP` | Launch `west debug` for one app's build. |
| `console APP` | Attach a serial console (`picocom`) to a running app's PTY. |
| `attach-usb [APP]` | Attach a remote USB device over USB/IP to the app(s). |

Global options:

- `-f, --file FILE`: path to the compose file (default `./zcompose.yml`).
- `-p, --pristine`: pristine build (`west build -p always`).

## Development

```bash
pip install -e .
pip install pytest ruff
pytest          # run the test suite
ruff check .    # lint
```

## License

Apache-2.0. Copyright (c) 2026 Titouan Christophe.
