# Suite B: On-device Performance Methodology

Suite B evaluates measured local model performance on iPhone, iPad, and Apple Silicon.

This suite is independent from Suite E. Suite B focuses on device-level performance observations, while Suite E compares runtime characteristics and integration tradeoffs.

This MVP does not define official benchmark numbers.

## Metrics

Record:

- tokens per second
- first token latency
- peak memory usage
- thermal behavior
- battery or energy observations
- model size and quantization
- runtime
- device model
- OS version

## Measurement Guidance

Submissions should avoid synthetic claims without reproducible details. Prefer raw measurements, environment notes, and repeated runs where practical.

Thermal and battery observations may be qualitative during the MVP stage, but should be clearly labeled as observations rather than controlled measurements.

## Suite Boundary

Raw device benchmark results belong in Suite B. Runtime comparison templates and cross-runtime evaluation methodology belong in Suite E.
