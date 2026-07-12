#include <catch2/catch_test_macros.hpp>

#include "eden/ingest_policy.hpp"

TEST_CASE("classifies the Eden land, astro-node, and data lanes") {
  REQUIRE(eden::classifySource("land/region-map.json") ==
          eden::RecordKind::Land);
  REQUIRE(eden::classifySource("lunar/moon-node.json") ==
          eden::RecordKind::AstroNode);
  REQUIRE(eden::classifySource("inbox/notes.json") == eden::RecordKind::Data);
}

TEST_CASE("accepts bounded local metadata and keeps the moon gate sealed") {
  eden::MetadataCatalog catalog;

  const auto decision = catalog.absorb(
      {eden::RecordKind::Land, "land/region-map.json", "digest-land", 12, 0});

  REQUIRE(decision.accepted);
  REQUIRE(catalog.records().size() == 1);
  REQUIRE(catalog.records().front().bytes == 12);
  REQUIRE(eden::MetadataCatalog::lunarMoonTarget() == 18);
}

TEST_CASE("rejects remote, secret-named, and out-of-bounds records") {
  eden::MetadataCatalog catalog(eden::IngestPolicy{2, 10, 100, 50});

  REQUIRE_FALSE(catalog.absorb({eden::RecordKind::Data,
                                "https://example.invalid/data.json",
                                "digest-remote", 1, 0})
                    .accepted);
  REQUIRE_FALSE(catalog.absorb({eden::RecordKind::Data,
                                "private/api_key.json",
                                "digest-secret", 1, 0})
                    .accepted);
  REQUIRE_FALSE(catalog.absorb({eden::RecordKind::AstroNode,
                                "lunar/moon-node.json",
                                "digest-deep", 1, 3})
                    .accepted);
}

TEST_CASE("enforces record, total-byte, and duplicate limits") {
  eden::MetadataCatalog catalog(eden::IngestPolicy{2, 1, 10, 5});

  REQUIRE(catalog.absorb(
                   {eden::RecordKind::Data, "data/one.json", "digest-one", 5, 0})
              .accepted);
  REQUIRE(catalog.absorb(
                   {eden::RecordKind::Data, "data/one.json", "digest-two", 1, 0})
              .reason == "duplicate_path");
  REQUIRE(catalog.absorb(
                   {eden::RecordKind::Data, "data/two.json", "digest-one", 1, 0})
              .reason == "duplicate_content");
  REQUIRE(catalog.absorb(
                   {eden::RecordKind::Data, "data/three.json", "digest-three", 1, 0})
              .reason == "entry_limit_exceeded");
}
