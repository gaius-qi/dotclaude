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

- **Placement:** deployable-specific → `<component>/<pkg>/`. Shared but Dragonfly-only → `internal/`. Generic and import-safe → `pkg/`. Never a top-level `util`, `common`, `helpers`.
- One package per directory, package name equals directory name. The component root file (`scheduler/scheduler.go`) owns `Server`, `New`, `Serve`, `Stop`.
- Domain packages split by entity: `host.go`, `host_manager.go`, `peer.go`, `peer_manager.go`. Each `x.go` has `x_test.go` beside it and, when it declares an interface, `x_mock.go` in the same package. `pkg/` and `internal/` libraries put mocks in a `mocks/` subpackage instead (`pkg/dfpath/mocks/`).
- Config per component in `<component>/config/config.go` with `testdata/*.yaml` fixtures. Deployment YAML templates in `deploy/docker-compose/template/`.
- Cross-binary e2e in `test/e2e/` with ginkgo and gomega; e2e fixtures in `test/testdata/`.
- No `src/`, `lib/` or `models/` at the root. `manager/models/` exists only because gorm models are a manager concern.
