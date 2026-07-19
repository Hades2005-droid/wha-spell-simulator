# Eden metadata contract

This optional C++14 target provides a native Catch2 v3 contract test for the
same bounded Eden ingestion policy used by `tools/eden_ingest.py`. It covers
the land, astro-node, and data lanes, while rejecting remote sources,
secret-named paths, over-depth records, duplicates, and byte-budget overruns.

The target stores metadata only. It is not a provider connector, does not
fetch source content, and does not replace the repository's JavaScript or
Python tests. Catch2 is intentionally not vendored.

With Catch2 v3 already installed:

```sh
cmake -S cpp -B build/eden
cmake --build build/eden
ctest --test-dir build/eden --output-on-failure
```

For an isolated build that fetches the pinned Catch2 release:

```sh
cmake -S cpp -B build/eden -DEDEN_FETCH_CATCH2=ON
cmake --build build/eden
ctest --test-dir build/eden --output-on-failure
```
