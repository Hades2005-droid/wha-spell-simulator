#ifndef SHADOW_GARDEN_EDEN_INGEST_POLICY_HPP
#define SHADOW_GARDEN_EDEN_INGEST_POLICY_HPP

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <string>
#include <unordered_set>
#include <vector>

namespace eden {

enum class RecordKind {
  Land,
  AstroNode,
  Data,
};

inline const char* recordKindName(RecordKind kind) {
  switch (kind) {
    case RecordKind::Land:
      return "land";
    case RecordKind::AstroNode:
      return "astro_node";
    case RecordKind::Data:
      return "data";
  }
  return "data";
}

struct MetadataRecord {
  RecordKind kind;
  std::string source;
  std::string sha256;
  std::size_t bytes;
  std::size_t depth;
};

struct IngestDecision {
  bool accepted;
  std::string reason;
};

struct IngestPolicy {
  std::size_t maxDepth = 2;
  std::size_t maxEntries = 5000;
  std::size_t maxBytes = 64U * 1024U * 1024U;
  std::size_t maxRecordBytes = 16U * 1024U * 1024U;
};

inline bool isRemoteSource(const std::string& source) {
  return source.find("://") != std::string::npos;
}

inline bool looksSecretNamedSource(const std::string& source) {
  std::string lowered;
  lowered.reserve(source.size());
  for (const char character : source) {
    lowered.push_back(static_cast<char>(
        std::tolower(static_cast<unsigned char>(character))));
  }

  const std::string markers[] = {
      ".env", "api_key", "apikey", "password", "secret", "token",
      "credentials", "private_key",
  };
  for (const std::string& marker : markers) {
    if (lowered.find(marker) != std::string::npos) {
      return true;
    }
  }
  return false;
}

inline RecordKind classifySource(const std::string& source) {
  std::string lowered;
  lowered.reserve(source.size());
  for (const char character : source) {
    lowered.push_back(static_cast<char>(
        std::tolower(static_cast<unsigned char>(character))));
  }
  const std::string astroMarkers[] = {
      "astro", "astronomy", "node", "moon", "lunar", "celestial",
  };
  for (const std::string& marker : astroMarkers) {
    if (lowered.find(marker) != std::string::npos) {
      return RecordKind::AstroNode;
    }
  }
  const std::string landMarkers[] = {"land", "terrain", "region", "world"};
  for (const std::string& marker : landMarkers) {
    if (lowered.find(marker) != std::string::npos) {
      return RecordKind::Land;
    }
  }
  return RecordKind::Data;
}

class MetadataCatalog {
 public:
  explicit MetadataCatalog(IngestPolicy policy = IngestPolicy())
      : policy_(policy), totalBytes_(0) {}

  IngestDecision absorb(const MetadataRecord& record) {
    if (record.source.empty()) {
      return reject("empty_source");
    }
    if (isRemoteSource(record.source)) {
      return reject("remote_source_rejected");
    }
    if (looksSecretNamedSource(record.source)) {
      return reject("secret_named_path_rejected");
    }
    if (record.sha256.empty()) {
      return reject("missing_digest");
    }
    if (record.depth > policy_.maxDepth) {
      return reject("depth_limit_exceeded");
    }
    if (record.bytes > policy_.maxRecordBytes) {
      return reject("record_byte_limit_exceeded");
    }
    if (records_.size() >= policy_.maxEntries) {
      return reject("entry_limit_exceeded");
    }
    if (record.bytes > policy_.maxBytes - std::min(totalBytes_, policy_.maxBytes)) {
      return reject("total_byte_limit_exceeded");
    }
    if (!sources_.insert(record.source).second) {
      return reject("duplicate_path");
    }
    if (!digests_.insert(record.sha256).second) {
      sources_.erase(record.source);
      return reject("duplicate_content");
    }

    records_.push_back(record);
    totalBytes_ += record.bytes;
    return {true, ""};
  }

  const std::vector<MetadataRecord>& records() const { return records_; }
  std::size_t totalBytes() const { return totalBytes_; }
  static constexpr int lunarMoonTarget() { return 18; }

 private:
  IngestDecision reject(const char* reason) const {
    return {false, reason};
  }

  IngestPolicy policy_;
  std::vector<MetadataRecord> records_;
  std::unordered_set<std::string> sources_;
  std::unordered_set<std::string> digests_;
  std::size_t totalBytes_;
};

}  // namespace eden

#endif  // SHADOW_GARDEN_EDEN_INGEST_POLICY_HPP
