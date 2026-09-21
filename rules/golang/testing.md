---
paths:
  - "**/*_test.go"
---

# Go testing

Reference shape from [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) (`scheduler/resource/standard/*_test.go`, `pkg/**/*_test.go`).

```go
var (
	mockHostGCConfig = &config.GCConfig{
		HostGCInterval: 1 * time.Second,
	}
)

func TestHostManager_Load(t *testing.T) {
	tests := []struct {
		name   string
		mock   func(m *gc.MockGCMockRecorder)
		expect func(t *testing.T, hostManager HostManager, mockHost *Host)
	}{
		{
			name: "load host",
			mock: func(m *gc.MockGCMockRecorder) {
				m.Add(gomock.Any()).Return(nil).Times(1)
			},
			expect: func(t *testing.T, hostManager HostManager, mockHost *Host) {
				assert := assert.New(t)
				hostManager.Store(mockHost)
				host, loaded := hostManager.Load(mockHost.ID)
				assert.True(loaded)
				assert.Equal(mockHost.ID, host.ID)
			},
		},
		{
			name: "host does not exist",
			mock: func(m *gc.MockGCMockRecorder) {
				m.Add(gomock.Any()).Return(nil).Times(1)
			},
			expect: func(t *testing.T, hostManager HostManager, mockHost *Host) {
				assert := assert.New(t)
				_, loaded := hostManager.Load(mockHost.ID)
				assert.False(loaded)
			},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ctl := gomock.NewController(t)
			defer ctl.Finish()
			gc := gc.NewMockGC(ctl)
			tc.mock(gc.EXPECT())

			hostManager, err := newHostManager(mockHostGCConfig, gc)
			assert.NoError(t, err)
			tc.expect(t, hostManager, mockRawHost)
		})
	}
}
```

- Libraries: `github.com/stretchr/testify/assert` with `assert := assert.New(t)` inside each case, and `go.uber.org/mock/gomock`. Never bare `if got != want { t.Errorf }` in this codebase.
- Every test is table-driven: `tests := []struct{ name string; <inputs>; mock func(...MockRecorder); expect func(t *testing.T, ...) }`. Assertions live in `expect`, mock setup in `mock`. Cases without mocks drop the `mock` field.
- Loop is `for _, tc := range tests { t.Run(tc.name, ...) }`. Build the subject inside `t.Run`, after `tc.mock(...)`.
- Mocks come from `//go:generate mockgen`. Same-package mocks: `gc.NewMockGC(ctl)`. Library mocks: `mocks.NewMockClient(ctl)` from the `mocks/` subpackage. `ctl := gomock.NewController(t); defer ctl.Finish()`.
- Names: `TestType_Method`. Cases are short lowercase phrases describing the scenario, `"new dfpath by logDir"`, `"scheduling failed because of no candidate parents"`.
- Fixtures are package-level `var ( mockXxx = ... )` at the top of the test file, reused across tests. Inline literals only when a case needs a variation.
- Failure paths return `errors.New("foo")` from mocks; assert with `assert.Error(err)` or `assert.EqualError(err, "...")`.
- Files: `x_test.go` beside `x.go`, same package (white-box). Fixtures on disk go in `testdata/`. Cross-binary e2e in `test/e2e/` with ginkgo + gomega.
- Run the narrow target first: `go test ./scheduler/resource/... -run TestHostManager_Load`. Finish with `make test`; coverage gates via codecov.
- Concurrent code: `go test -race ./...`. Don't sleep for synchronization; use channels or `Eventually` in e2e.
