---
paths:
  - "**/*_test.go"
---

# Go testing

Reference shape from [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) (`scheduler/resource/standard/*_test.go`, `pkg/**/*_test.go`). Names: `naming.md`.

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

- No comments in test code. Unit tests in dragonfly contain zero `//` lines: none on `TestXxx`, on fixtures, inside cases or in `expect`. The case name carries the meaning; a case that needs explaining gets a better name. The only `//` allowed is a lint pragma such as `//nolint: errcheck`. E2e in `test/e2e/` may use a step comment for a timing wait.
- Libraries: `github.com/stretchr/testify/assert` with `assert := assert.New(t)` inside each case, and `go.uber.org/mock/gomock`. Never bare `if got != want { t.Errorf }`.
- Every test is table-driven: `tests := []struct{ name string; <inputs>; mock func(...MockRecorder); expect func(t *testing.T, ...) }`. Mock setup in `mock`, assertions in `expect`. Cases without mocks drop the `mock` field.
- Loop is `for _, tc := range tests { t.Run(tc.name, ...) }`. Build the subject inside `t.Run`, after `tc.mock(...)`. `ctl := gomock.NewController(t); defer ctl.Finish()`.
- Mocks come from `//go:generate mockgen`: same-package `gc.NewMockGC(ctl)`, library `mocks.NewMockClient(ctl)`.
- Fixtures are package-level `var ( mockXxx = ... )` at the top of the test file, reused across tests. Inline literals only when a case needs a variation. On-disk fixtures go in `testdata/`.
- Failure paths return `errors.New("foo")` from mocks; assert with `assert.Error(err)` or `assert.EqualError(err, "...")`.
- Files: `x_test.go` beside `x.go`, same package (white-box). Cross-binary e2e in `test/e2e/` with ginkgo and gomega; no sleeps for synchronization, use `Eventually`.
- Benchmarks live in the same `_test.go` as the code they measure; shape and flags: `performance.md`.
- Run the narrow target first: `go test ./scheduler/resource/... -run TestHostManager_Load`. Finish with `make test`; concurrent code also with `go test -race`.
