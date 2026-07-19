using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace ShadowGarden.RecursiveBridge;

public sealed class RecursiveNodeBridgeOptions
{
    public const int DefaultNodeCount = 9;
    public const int MaxNodeCount = 9;
    public const double MaxGain = 8.0;
    public const int MaxFeedEntries = 256;

    public int NodeCount { get; }
    public double Gain { get; }
    public int FeedLimit { get; }
    public double MinimumIntervalSeconds { get; }
    public string RouteName { get; }
    public string RouteModel { get; }
    public string RouteEndpoint { get; }

    public RecursiveNodeBridgeOptions(
        int nodeCount = DefaultNodeCount,
        double gain = 1.0,
        int feedLimit = MaxFeedEntries,
        double minimumIntervalSeconds = 0.02,
        string routeName = "local-open-weights",
        string routeModel = "deepseek-local",
        string routeEndpoint = "http://127.0.0.1:11434/v1")
    {
        if (nodeCount is < 1 or > MaxNodeCount)
            throw new ArgumentOutOfRangeException(nameof(nodeCount));
        if (gain <= 0 || gain > MaxGain)
            throw new ArgumentOutOfRangeException(nameof(gain));
        if (feedLimit is < 1 or > MaxFeedEntries)
            throw new ArgumentOutOfRangeException(nameof(feedLimit));
        if (minimumIntervalSeconds <= 0)
            throw new ArgumentOutOfRangeException(nameof(minimumIntervalSeconds));

        NodeCount = nodeCount;
        Gain = gain;
        FeedLimit = feedLimit;
        MinimumIntervalSeconds = minimumIntervalSeconds;
        RouteName = routeName;
        RouteModel = routeModel;
        RouteEndpoint = routeEndpoint;
    }
}

public sealed class SovereignNode
{
    public double Dexterity { get; internal set; } = 1.0;
    public double CyclePower { get; internal set; }
    public double FeedRate { get; internal set; } = 1.0;
    public double SensoryDepth { get; internal set; } = 1.0;
    public long Cycles { get; internal set; }
}

public sealed class MatriarchNode
{
    public int NodeId { get; }
    public double Activation { get; internal set; }
    public List<string> SignalFeed { get; } = new();
    public double SignalRippleFactor { get; internal set; } = 1.0;
    public long Cycles { get; internal set; }

    public MatriarchNode(int nodeId)
    {
        NodeId = nodeId;
    }
}

public sealed class RecursiveNodeSnapshot
{
    public string Kind { get; init; } = "shadow_garden_recursive_node_status";
    public DateTimeOffset GeneratedAt { get; init; }
    public string Status { get; init; } = "ready";
    public bool LocalOnly { get; init; } = true;
    public bool SymbolicOnly { get; init; } = true;
    public IReadOnlyList<string> Guardrails { get; init; } = Array.Empty<string>();
    public RecursiveNodeBridgeOptions Options { get; init; } = new();
    public object Route { get; init; } = new();
    public IReadOnlyDictionary<string, Frequency> Chronology { get; init; } = new Dictionary<string, Frequency>();
    public DateTimeOffset? StartedAt { get; init; }
    public DateTimeOffset? LastCycleAt { get; init; }
    public string? LastError { get; init; }
    public SovereignNode Sovereign { get; init; } = new();
    public IReadOnlyList<MatriarchNode> Matriarchs { get; init; } = Array.Empty<MatriarchNode>();
    public IReadOnlyList<string> ContentPool { get; init; } = Array.Empty<string>();
}

public sealed class RecursiveNodeBridge : IAsyncDisposable
{
    private const double MaxCyclePower = 8.0;
    private readonly object sync = new();
    private readonly CancellationTokenSource stopSource = new();
    private readonly List<string> contentPool = new();
    private readonly List<MatriarchNode> matriarchs;
    private readonly RecursiveNodeBridgeOptions options;
    private Task? worker;
    private DateTimeOffset? startedAt;
    private DateTimeOffset? lastCycleAt;
    private string? lastError;

    public SovereignNode Sovereign { get; } = new();
    public IReadOnlyList<MatriarchNode> Matriarchs => matriarchs;
    public bool Running => worker is { IsCompleted: false };

    public RecursiveNodeBridge(RecursiveNodeBridgeOptions? options = null)
    {
        this.options = options ?? new RecursiveNodeBridgeOptions();
        matriarchs = Enumerable.Range(0, this.options.NodeCount)
            .Select(index => new MatriarchNode(index))
            .ToList();
    }

    public void NodeResonance(MatriarchNode node)
    {
        lock (sync)
        {
            node.Activation = Math.Min(1.0, node.Activation + 0.03 * Sovereign.Dexterity * options.Gain);
            node.SignalRippleFactor = Math.Min(2.0, node.SignalRippleFactor + 0.02 * options.Gain);
            node.Cycles++;
            AppendFeed($"node_{node.NodeId}_resonance_feed_v2");
            Sovereign.CyclePower = Math.Min(MaxCyclePower, Sovereign.CyclePower + 0.01 * options.Gain);
            Sovereign.FeedRate = 1.0 + Sovereign.CyclePower;
            Sovereign.SensoryDepth = Math.Min(4.0, 1.0 + Sovereign.CyclePower * 0.5);
        }
    }

    public RecursiveNodeSnapshot SovereignCycle()
    {
        lock (sync)
        {
            foreach (var node in matriarchs)
                NodeResonance(node);

            var averageActivation = matriarchs.Average(node => node.Activation);
            Sovereign.Dexterity = Math.Min(2.0, 1.0 + averageActivation);
            Sovereign.SensoryDepth = Math.Max(1.0, Sovereign.SensoryDepth);
            Sovereign.Cycles++;
            lastCycleAt = DateTimeOffset.UtcNow;
            return Snapshot();
        }
    }

    public async Task<RecursiveNodeSnapshot> RunAsync(
        int? maxCycles = null,
        TimeSpan? maxDuration = null,
        CancellationToken cancellationToken = default)
    {
        if (maxCycles is <= 0)
            throw new ArgumentOutOfRangeException(nameof(maxCycles));
        if (maxDuration is { } duration && duration <= TimeSpan.Zero)
            throw new ArgumentOutOfRangeException(nameof(maxDuration));

        using var linked = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken,
            stopSource.Token);
        var token = linked.Token;
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        lock (sync)
        {
            startedAt = DateTimeOffset.UtcNow;
            lastError = null;
        }

        var completed = 0;
        while (!token.IsCancellationRequested
               && (maxCycles is null || completed < maxCycles)
               && (maxDuration is null || stopwatch.Elapsed < maxDuration))
        {
            SovereignCycle();
            completed++;
            var interval = TimeSpan.FromSeconds(Math.Max(
                options.MinimumIntervalSeconds,
                0.08 / Math.Max(1.0, Sovereign.FeedRate)));
            await Task.Delay(interval, token).ConfigureAwait(false);
        }

        return Snapshot();
    }

    public void Start(int? maxCycles = null, TimeSpan? maxDuration = null)
    {
        lock (sync)
        {
            if (Running)
                throw new InvalidOperationException("recursive loop is already running");
            worker = Task.Run(async () =>
            {
                try
                {
                    await RunAsync(maxCycles, maxDuration).ConfigureAwait(false);
                }
                catch (OperationCanceledException)
                {
                }
                catch (Exception exception)
                {
                    lock (sync)
                        lastError = $"{exception.GetType().Name}: {exception.Message}";
                }
            });
        }
    }

    public async ValueTask StopAsync()
    {
        stopSource.Cancel();
        if (worker is not null)
        {
            try
            {
                await worker.ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
            }
        }
    }

    public RecursiveNodeSnapshot Snapshot()
    {
        lock (sync)
        {
            return new RecursiveNodeSnapshot
            {
                GeneratedAt = DateTimeOffset.UtcNow,
                Status = Running ? "running" : "ready",
                Guardrails = new[]
                {
                    "bounded_gain",
                    "bounded_node_count",
                    "bounded_feed_pool",
                    "cooperative_cancellation",
                    "no_external_network_calls",
                    "no_provider_credentials",
                    "neutral_signal_metadata_only",
                },
                Options = options,
                Route = new
                {
                    name = options.RouteName,
                    model = options.RouteModel,
                    endpoint = options.RouteEndpoint,
                    enabled = false,
                    reason = "metadata-only local route; no model call is made",
                },
                Chronology = ChronologyEngine.AnalyzeDate(DateOnly.FromDateTime(DateTime.UtcNow.Date)),
                StartedAt = startedAt,
                LastCycleAt = lastCycleAt,
                LastError = lastError,
                Sovereign = new SovereignNode
                {
                    Dexterity = Sovereign.Dexterity,
                    CyclePower = Sovereign.CyclePower,
                    FeedRate = Sovereign.FeedRate,
                    SensoryDepth = Sovereign.SensoryDepth,
                    Cycles = Sovereign.Cycles,
                },
                Matriarchs = matriarchs.Select(CloneNode).ToList(),
                ContentPool = contentPool.ToList(),
            };
        }
    }

    private void AppendFeed(string item)
    {
        contentPool.Add(item);
        if (contentPool.Count > options.FeedLimit)
            contentPool.RemoveRange(0, contentPool.Count - options.FeedLimit);
    }

    private static MatriarchNode CloneNode(MatriarchNode node)
    {
        var clone = new MatriarchNode(node.NodeId)
        {
            Activation = node.Activation,
            SignalRippleFactor = node.SignalRippleFactor,
            Cycles = node.Cycles,
        };
        clone.SignalFeed.AddRange(node.SignalFeed);
        return clone;
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync().ConfigureAwait(false);
        stopSource.Dispose();
    }
}
