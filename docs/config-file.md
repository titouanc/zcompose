# The `zcompose` configuration file

`zcompose` is driven by a single YAML file — by convention `zcompose.yml` — that
declares a named group of Zephyr applications and the virtual networks they
share. This document describes every section, key, default and validation rule.

## Table of contents

- [File location and selection](#file-location-and-selection)
- [Document structure](#document-structure)
- [Top-level keys](#top-level-keys)
  - [`name`](#name)
  - [`networks`](#networks)
  - [`applications`](#applications)
- [Network definition](#network-definition)
- [Application definition](#application-definition)
  - [`extra-build`](#extra-build)
  - [`extra-run`](#extra-run)
- [Automatic address allocation](#automatic-address-allocation)
- [Automatic Kconfig injection](#automatic-kconfig-injection)
- [Variable substitution](#variable-substitution)
- [YAML anchors and merge keys](#yaml-anchors-and-merge-keys)
- [Identifier and length rules](#identifier-and-length-rules)
- [Derived state on disk](#derived-state-on-disk)
- [Complete example](#complete-example)

## File location and selection

By default `zcompose` reads `./zcompose.yml` (the constant `DEFAULT_FILE`) from
the current working directory. A different file can be selected with the global
`-f/--file` option:

```console
zcompose -f path/to/my-setup.yml show
```

All relative paths inside the file (notably each application's `source`) are
resolved **relative to the directory containing the compose file**, not the
current working directory.

## Document structure

The top level of the document must be a YAML **mapping**. Anything else (a list,
a scalar, an empty file) is rejected:

```
<file>: top-level YAML must be a mapping
```

Only three keys are recognised at the top level. Any other key — except helper
keys whose name starts with `.` (see [YAML anchors](#yaml-anchors-and-merge-keys))
— is a fatal error:

```
<file>: unknown key(s) under <root>: <key> (allowed: applications, name, networks)
```

This strict-key validation is applied at **every** level of the document
(top level, each network, each application, `extra-build`, `extra-run`), so
typos surface immediately rather than being silently ignored.

## Top-level keys

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | **yes** | Human-readable name for the group. |
| `networks` | mapping | no | Named virtual networks. Omitting it means no networking. |
| `applications` | mapping | **yes** | Named applications. At least one is required. |

### `name`

A non-empty string identifying the group. It is **slugified** to derive the
on-disk state directory (see [Derived state](#derived-state-on-disk)).

Slugification lowercases the name, replaces every run of non-alphanumeric
characters with a single `-`, and strips leading/trailing `-`. Examples:

| `name` | slug |
| --- | --- |
| `Network echo samples` | `network-echo-samples` |
| `  trim me  ` | `trim-me` |
| `A---B` | `a-b` |
| `abc.def/ghi` | `abc-def-ghi` |

If `name` is missing, not a string, or blank:

```
<file>: top-level `name` is required and must be a string
```

If the name slugifies to the empty string (e.g. `"---"`):

```
<file>: `name` slugifies to empty string
```

### `networks`

An optional mapping of network name → [network definition](#network-definition).
If omitted or `null`, the group has no networks and applications run without any
virtual interfaces. If present it must be a mapping.

### `applications`

A **required** mapping of application name → [application definition](#application-definition).
It must contain at least one entry; an empty or missing `applications` section is
an error:

```
<file>: `applications` must contain at least one entry
```

## Network definition

Each entry under `networks` is a mapping (an empty/`null` body is allowed and
treated as all-defaults). Recognised keys:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `type` | string | `bridge` | Network type. Only `bridge` is supported. |
| `host-veth` | boolean | `false` | Whether to also expose the network to the host via a veth pair. |
| `ipv4` | CIDR string or `false` | `192.0.2.0/24` | IPv4 subnet, or `false` to disable IPv4. |
| `ipv6` | CIDR string or `false` | `2001:db8::/64` | IPv6 subnet, or `false` to disable IPv6. |

**`type`** — the only supported value is `bridge`, which creates a Linux bridge
interface. Any other value:

```
<file>: network <name>: unsupported type <type> (supported: bridge)
```

**`host-veth`** — when `true`, in addition to the bridge `zcompose` creates a
veth pair so the host can communicate with the simulated nodes. The host side
takes the **`.1`** address of each enabled subnet (e.g. `192.0.2.1` /
`2001:db8::1`). When `false`, only the bridge and per-application TAP interfaces
exist and there is no host-reachable address.

**`ipv4` / `ipv6`** — a CIDR string parsed with non-strict semantics (host bits
are allowed, e.g. `192.0.2.5/24` is accepted and normalised). The literal value
`false` (or `null`) disables that address family for the network, in which case
attached applications receive no address of that family. An unparseable value:

```
<file>: networks.<name>.ipv4: invalid CIDR <value>: <reason>
```

The defaults use the documentation/test ranges from
[RFC 5737](https://datatracker.ietf.org/doc/html/rfc5737) (`192.0.2.0/24`) and
[RFC 3849](https://datatracker.ietf.org/doc/html/rfc3849) (`2001:db8::/64`).

### Derived interface names

From the network name `<net>`, `zcompose` derives Linux interface names:

| Interface | Name | Exists when |
| --- | --- | --- |
| Bridge | `<net>` | always |
| Host veth (host side) | `<net>-host` | `host-veth: true` |
| Host veth (bridge side) | `<net>-br` | `host-veth: true` |
| Per-app TAP | `<net>tap<i>` | one per attached application |

Because Linux interface names are capped at 15 characters, network names are
limited to 10 characters (see [Identifier and length rules](#identifier-and-length-rules)).

## Application definition

Each entry under `applications` is a mapping (an empty/`null` body is treated as
all-defaults, but note `source` is required). Recognised keys:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `source` | string (path) | **required** | Path to the Zephyr application directory. |
| `board` | string | `native_sim` | Board passed to `west build -b`. |
| `network` | string | none | Name of a network (declared under `networks`) to attach to. |
| `extra-build` | mapping | none | Extra build configuration (see below). |
| `extra-run` | mapping | none | Extra run-time arguments (see below). |

**`source`** — required, non-empty string. If relative, it is resolved against
the compose file's directory and made absolute. Missing:

```
<file>: applications.<name>.source is required
```

**`board`** — the Zephyr board target. Defaults to `native_sim`. The
[automatic Kconfig injection](#automatic-kconfig-injection) for the native TAP
Ethernet driver only applies when the board is exactly `native_sim`.

**`network`** — optional; if set it must name a network declared under the
top-level `networks` mapping. An unknown reference:

```
<file>: applications.<name>.network: unknown network <network> (declared: ...)
```

Applications without a `network` get no interface or address and run in
isolation.

### `extra-build`

Optional mapping controlling how the application is built. Recognised keys:

| Key | Type | Description |
| --- | --- | --- |
| `args` | list of strings | Extra arguments appended to the `west build` command line. |
| `snippets` | list of strings | Zephyr snippets, each passed as `west build -S <snippet>`. |
| `config` | mapping | Kconfig options (see below). |

**`config`** is a mapping of Kconfig symbol → value. Keys are the symbol name
**without** the `CONFIG_` prefix (it is added automatically). Values are
normalised:

- booleans → `y` / `n`
- integers → their decimal string
- strings → kept as-is, and **automatically quoted** when emitted as
  `-DCONFIG_<KEY>=...` (unless the value is exactly `y`)

Other value types are rejected:

```
<file>: applications.<name>.extra-build.config.<key>: value must be a string, int or bool
```

`args` and `snippets` must each be a list of strings, otherwise:

```
<file>: applications.<name>.extra-build.args must be a list of strings
```

### `extra-run`

Optional mapping controlling how the application is run. The only recognised key:

| Key | Type | Description |
| --- | --- | --- |
| `args` | list of strings | Extra arguments appended to the run command. |

For `native_sim` the run command is the built `zephyr.exe` followed by these
args; for other boards it is `west build -t run`.

## Automatic address allocation

For every application attached to a network, `zcompose` deterministically
allocates an interface, MAC and addresses. Allocation walks the applications in
**declaration order**, maintaining a per-network counter `i` starting at `0`:

| Property | Formula | Example (`i = 0`, subnet `192.0.2.0/24`) |
| --- | --- | --- |
| TAP interface | `<net>tap<i>` | `zethtap0` |
| MAC | `00:00:5E:00:53:<low>` (hex) | `00:00:5E:00:53:02` |
| IPv4 | subnet network address `+ low` | `192.0.2.2` |
| IPv6 | subnet network address `+ low` | `2001:db8::2` |

where `low = 2 + i` (host `.1` is reserved for the `host-veth` side, addresses
start at `.2`). Each network counts independently, so two networks both start
their apps at `.2`.

Constraints checked during allocation:

- The low byte must stay ≤ `0xFF`; too many apps on one network is an error.
- Each allocated address must fall within the network's subnet.
- Derived interface names must not exceed 15 characters.

If a family is disabled on the network (`ipv4: false` / `ipv6: false`), no
address of that family is assigned and the corresponding field is empty.

## Automatic Kconfig injection

For network-attached applications, `zcompose` injects Kconfig options so the
firmware comes up on the virtual network without manual wiring. **Anything you
set explicitly in `extra-build.config` overrides the auto-injected value**, and a
warning is printed when an override differs from the automatic value.

For `native_sim` boards:

| Kconfig | Value |
| --- | --- |
| `ETH_NATIVE_TAP_DRV_NAME` | the app's TAP interface name |
| `ETH_NATIVE_TAP_RANDOM_MAC` | `n` (when a MAC was allocated) |
| `ETH_NATIVE_TAP_MAC_ADDR` | the allocated MAC (lower-case) |

When the app has an IPv4 address:

| Kconfig | Value |
| --- | --- |
| `NET_CONFIG_SETTINGS` | `y` |
| `NET_CONFIG_NEED_IPV4` | `y` |
| `NET_CONFIG_MY_IPV4_ADDR` | the app's IPv4 |
| `NET_CONFIG_MY_IPV4_NETMASK` | the subnet netmask |
| `NET_CONFIG_MY_IPV4_GW` | the host veth IPv4 (only with `host-veth: true`) |

When the app has an IPv6 address:

| Kconfig | Value |
| --- | --- |
| `NET_CONFIG_SETTINGS` | `y` |
| `NET_CONFIG_NEED_IPV6` | `y` |
| `NET_CONFIG_MY_IPV6_ADDR` | the app's IPv6 |

## Variable substitution

Inside the following string fields you may reference another application's
allocated values:

- `extra-build.args` (each element)
- `extra-build.config` (each value)
- `extra-run.args` (each element)

The syntax is `${<app>:<prop>}`, where `<app>` is an application name and
`<prop>` is one of:

| Property | Meaning |
| --- | --- |
| `ipv4` | the referenced app's IPv4 address |
| `ipv6` | the referenced app's IPv6 address |
| `mac` | the referenced app's MAC address |

Substitution happens **after** allocation, so a client can point at a server's
address without hardcoding it:

```yaml
applications:
  server:
    source: ./srv
    network: zeth
  client:
    source: ./cli
    network: zeth
    extra-build:
      config:
        NET_CONFIG_PEER_IPV4_ADDR: ${server:ipv4}
        NET_CONFIG_PEER_IPV6_ADDR: ${server:ipv6}
        NET_CONFIG_PEER_MAC:       ${server:mac}
    extra-run:
      args:
        - --peer=${server:ipv4}
```

Error cases:

- Unknown application — `substitution ${nope:ipv4} references unknown application 'nope'`
- Unsupported property — `substitution ${a:bogus} references unsupported property 'bogus' (supported: ipv4, ipv6, mac)`
- Empty value (e.g. referencing an `ipv6` on an app whose network disabled IPv6) — `substitution ${a:ipv6}: application 'a' has no ipv6 configured`

Multiple references may appear in a single string, and surrounding text is
preserved (as in `--peer=${server:ipv4}`).

## YAML anchors and merge keys

Standard YAML anchors (`&name`), aliases (`*name`) and merge keys (`<<:`) are
supported, since the file is parsed with PyYAML's safe loader. To define a
reusable block at the top level without tripping the strict unknown-key check,
prefix its key with a dot (`.`) — such keys are **dropped before validation**:

```yaml
name: Anchor merge

.common-config: &common
  NET_CONFIG_NEED_IPV6: n
  NET_IPV6: n

applications:
  one:
    source: .
    extra-build:
      config:
        <<: *common
        EXTRA_KEY: 1
```

Here `one`'s config resolves to `NET_CONFIG_NEED_IPV6: n`, `NET_IPV6: n`,
`EXTRA_KEY: "1"`.

## Identifier and length rules

- **Network and application names** must match `^[a-z][a-z0-9_-]*$`: start with a
  lowercase letter, then lowercase letters, digits, `-` or `_`.
- **Network names** are additionally limited to **10 characters**, because they
  seed Linux interface names which are capped at 15 characters (room is left for
  the `-host` / `-br` / `tap<i>` suffixes).
- **Derived interface names** are re-checked against the 15-character limit after
  allocation; an over-long derived name is a fatal error.

Violations produce errors such as:

```
<file>: network name <name> must be a lowercase identifier
<file>: network name <name> exceeds 10 characters (Linux interface-name limit)
<file>: application name <name> must be a lowercase identifier
```

## Derived state on disk

State is kept per group in a directory next to the compose file:

```
<compose-dir>/.zcompose/<slug>/
```

where `<slug>` is the slugified `name`. Inside it `zcompose` stores per-app build
directories, a `run.log` per application (used by `zcompose console` to find the
PTY), and a `state.json` recording which networks are up and which apps are
running. None of this is configured in the compose file — it is listed here for
completeness.

## Complete example

```yaml
# Group name — slugified to derive .zcompose/echo-demo/
name: Echo demo

networks:
  zeth:
    type: bridge          # only supported type; may be omitted
    host-veth: true       # expose the net to the host (host gets .1)
    ipv4: 192.0.2.0/24    # default value, shown for clarity
    ipv6: 2001:db8::/64   # default value; use `false` to disable a family

applications:
  server:
    source: ./echo-server # relative to this file
    board: native_sim     # default; shown for clarity
    network: zeth

  client:
    source: ./echo-client
    network: zeth
    extra-build:
      snippets:
        - cdc-acm-console
      config:
        # Point the client at the server's auto-allocated addresses
        NET_CONFIG_PEER_IPV4_ADDR: ${server:ipv4}
        NET_CONFIG_PEER_IPV6_ADDR: ${server:ipv6}
        LOG_DEFAULT_LEVEL: 4
      args:
        - -DEXTRA_CONF_FILE=debug.conf
    extra-run:
      args:
        - --seed=42
```
