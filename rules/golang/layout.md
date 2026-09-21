---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/Makefile"
---

# Go project layout

Reference: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) tree, which follows the official [Organizing a Go module](https://go.dev/doc/modules/layout) with `cmd/`, `internal/`, `pkg/`.

```
repo/
├── cmd/
│   ├── <binary>/main.go          # three lines: cmd.Execute()
│   ├── <binary>/cmd/root.go      # cobra rootCmd, flags, init(), runXxx()
│   └── dependency/               # shared cobra/viper/monitor wiring for all binaries
├── <component>/                  # scheduler/, manager/, client/ — one dir per deployable
│   ├── config/                   # config.go, config_test.go, testdata/
│   ├── rpcserver/                # gRPC server setup
│   ├── service/                  # service_v1.go, service_v2.go — RPC handlers
│   ├── resource/                 # domain model: host.go, peer.go, task.go + managers
│   ├── metrics/                  # prometheus collectors
│   ├── job/, gc/, announcer/     # background workers, one package each
│   └── <component>.go            # New(ctx, cfg, ...) (*Server, error); Serve(); Stop()
├── pkg/                          # reusable, import-safe libraries
│   ├── types/                    # shared enums and value types
│   ├── idgen/, digest/, dfpath/  # one responsibility each
│   ├── net/{ip,fqdn}/            # families nest one level
│   ├── container/set/, graph/dag/
│   └── rpc/<svc>/client/         # gRPC clients + mocks/
├── internal/                     # shared across components, not importable outside
│   ├── dflog/                    # zap logger with WithTaskID/WithPeer helpers
│   ├── dferrors/, dynconfig/, job/, ratelimiter/, dfplugin/
├── api/manager/                  # OpenAPI / swagger docs
├── build/images/, build/plugin-builder/
├── deploy/docker-compose/, deploy/helm-charts/
├── docs/, hack/                  # hack/ holds shell scripts, not Go
├── test/e2e/, test/testdata/     # ginkgo e2e suites and fixtures
├── version/                      # ldflags-injected version info
├── Makefile                      # build, test, test-coverage, lint, fmt, vet, generate, precheck
├── .golangci.yml                 # v2 config, gci sections
└── go.mod                        # module d7y.io/dragonfly/v2
```

- **Decide placement by asking:** deployable-specific → `<component>/<pkg>/`. Shared but Dragonfly-only → `internal/`. Generic and import-safe → `pkg/`. Never a top-level `util`, `common`, `helpers`.
- One package per directory, package name equals directory name. Component root file (`scheduler/scheduler.go`) owns `Server`, `New`, `Serve`, `Stop`.
- Domain packages split by entity: `host.go`, `host_manager.go`, `peer.go`, `peer_manager.go`, `task.go`, `task_manager.go`. Each `x.go` has `x_test.go` and, when it declares an interface, `x_mock.go` beside it.
- `pkg/` and `internal/` libraries put mocks in a `mocks/` subpackage instead (`pkg/dfpath/mocks/`).
- Config per component in `<component>/config/config.go` with `testdata/*.yaml` fixtures. YAML templates for deployment live in `deploy/docker-compose/template/`.
- Generated code: `//go:generate` at the top of the source file, regenerated with `make generate`. Swagger via `make swag`.
- Don't add `src/`, `lib/`, `models/` at the root. `manager/models/` exists only because gorm models are a manager concern.
- Tests sit next to code. Cross-binary e2e goes in `test/e2e/` with ginkgo + gomega.
